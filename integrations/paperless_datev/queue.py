"""Atomic per-invoice leasing for client-pull DATEV distribution.

This module is a storage core, not a DATEV protocol adapter.
SQLite is suitable for a single central coordinator using local storage.
Do not put the database on an SMB share or run independent coordinators.
"""
import secrets
import sqlite3
import time
from pathlib import Path

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS invoices (
 id INTEGER PRIMARY KEY,
 paperless_id INTEGER NOT NULL UNIQUE,
 company_id TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'AVAILABLE'
 CHECK(status IN ('AVAILABLE','CLAIMED','STAGING','STAGED','UNCERTAIN','CONFIRMED','FAILED')),
 claimed_by TEXT,
 token_hash TEXT,
 claimed_at INTEGER,
 lease_until INTEGER,
 staged_at INTEGER,
 confirmed_at INTEGER
);
CREATE TABLE IF NOT EXISTS events (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 invoice_id INTEGER NOT NULL REFERENCES invoices(id),
 at INTEGER NOT NULL,
 client_id TEXT,
 event TEXT NOT NULL,
 detail TEXT
);
CREATE INDEX IF NOT EXISTS idx_invoice_queue ON invoices(company_id,status);
"""

class Conflict(Exception):
    pass

class Queue:
    def __init__(self, path):
        self.path = str(Path(path))
        with self.connect() as db:
            db.executescript(SCHEMA)

    def connect(self):
        db = sqlite3.connect(self.path, timeout=15, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=15000")
        return db

    def enqueue(self, paperless_id, company_id):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("INSERT OR IGNORE INTO invoices(paperless_id,company_id) VALUES (?,?)",
                       (paperless_id, company_id))
            row = db.execute("SELECT id,company_id FROM invoices WHERE paperless_id=?",
                             (paperless_id,)).fetchone()
            if row["company_id"] != company_id:
                raise Conflict("Document already assigned to another company")
            db.execute("COMMIT")
            return row["id"]

    def claim(self, client_id, allowed_companies, lease_seconds=300, now=None):
        """Claim exactly one document, atomically, for an authenticated client's companies.

        Returning a token is not authorization; the API must authenticate the client
        and obtain allowed_companies from server-side configuration.
        """
        if not client_id or not allowed_companies or lease_seconds < 30:
            raise ValueError("Invalid client, permitted companies or lease")
        now = int(time.time() if now is None else now)
        companies = list(dict.fromkeys(allowed_companies))
        placeholders = ",".join("?" for _ in companies)
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            # Only CLAIMED invoices with no staged delivery may be reclaimed.
            # STAGED/UNCERTAIN deliveries require explicit reconciliation.
            expired = db.execute(
                "SELECT id,claimed_by FROM invoices WHERE status='CLAIMED' AND lease_until<=?",
                (now,)).fetchall()
            for item in expired:
                db.execute("UPDATE invoices SET status='AVAILABLE',claimed_by=NULL,"
                           "token_hash=NULL,claimed_at=NULL,lease_until=NULL WHERE id=?",
                           (item["id"],))
                db.execute("INSERT INTO events(invoice_id,at,client_id,event) VALUES(?,?,?,?)",
                           (item["id"],now,item["claimed_by"],"LEASE_EXPIRED"))
            row = db.execute(
                f"SELECT id,paperless_id,company_id FROM invoices "
                f"WHERE status='AVAILABLE' AND company_id IN ({placeholders}) "
                "ORDER BY id LIMIT 1", companies).fetchone()
            if row is None:
                db.execute("COMMIT")
                return None
            token = secrets.token_urlsafe(32)
            import hashlib
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            db.execute("UPDATE invoices SET status='CLAIMED',claimed_by=?,token_hash=?,"
                       "claimed_at=?,lease_until=? WHERE id=?",
                       (client_id,token_hash,now,now+lease_seconds,row["id"]))
            db.execute("INSERT INTO events(invoice_id,at,client_id,event) VALUES(?,?,?,?)",
                       (row["id"],now,client_id,"CLAIMED"))
            db.execute("COMMIT")
            return dict(row) | {"claim_token":token,"lease_until":now+lease_seconds}

    def transition(self, invoice_id, client_id, token, action, now=None):
        """ACK staging, renew an unstaged lease, or record externally verified success.

        IMPORTANT: CONFIRMED may only be called by trusted server-side DATEV
        reconciliation, never directly based on a Windows agent's self-report.
        """
        if action not in ("RENEW","STAGING","STAGED","UNCERTAIN"):
            raise ValueError("Unsupported client transition")
        if not token:
            raise Conflict("Missing claim token")
        import hashlib
        now = int(time.time() if now is None else now)
        digest = hashlib.sha256(token.encode()).hexdigest()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,)).fetchone()
            if row is None or row["claimed_by"] != client_id or row["token_hash"] != digest:
                raise Conflict("Claim does not belong to this client")
            if action == "RENEW":
                if row["status"] != "CLAIMED" or row["lease_until"] <= now:
                    raise Conflict("Lease expired or already staged")
                db.execute("UPDATE invoices SET lease_until=? WHERE id=?", (now+300,invoice_id))
            elif action == "STAGING":
                if row["status"] != "CLAIMED" or row["lease_until"] <= now:
                    raise Conflict("Cannot begin staging without active lease")
                # Write-ahead marker before touching DATEV's watched directory.
                # A crash here leaves the invoice blocked for reconciliation.
                db.execute("UPDATE invoices SET status='STAGING',lease_until=NULL WHERE id=?",
                           (invoice_id,))
            elif action == "STAGED":
                if row["status"] != "STAGING":
                    raise Conflict("Must mark STAGING before touching DATEV directory")
                db.execute("UPDATE invoices SET status='STAGED',staged_at=? WHERE id=?",
                           (now,invoice_id))
            else:
                if row["status"] not in ("STAGING","STAGED"):
                    raise Conflict("Only staging/staged invoices may become uncertain")
                db.execute("UPDATE invoices SET status='UNCERTAIN' WHERE id=?", (invoice_id,))
            db.execute("INSERT INTO events(invoice_id,at,client_id,event) VALUES(?,?,?,?)",
                       (invoice_id,now,client_id,action))
            db.execute("COMMIT")

    def verified_result(self, invoice_id, successful, evidence, now=None):
        """Trusted administrator/reconciler only; persist evidence in the journal."""
        if not evidence:
            raise ValueError("DATEV evidence required")
        now = int(time.time() if now is None else now)
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT status,claimed_by FROM invoices WHERE id=?", (invoice_id,)).fetchone()
            if row is None or row["status"] not in ("STAGED","UNCERTAIN"):
                raise Conflict("Invoice is not waiting for DATEV reconciliation")
            status = "CONFIRMED" if successful else "FAILED"
            db.execute("UPDATE invoices SET status=?,confirmed_at=? WHERE id=?",
                       (status,now if successful else None,invoice_id))
            db.execute("INSERT INTO events(invoice_id,at,client_id,event,detail) "
                       "VALUES(?,?,?,?,?)",(invoice_id,now,row["claimed_by"],status,evidence))
            db.execute("COMMIT")
