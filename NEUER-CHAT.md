# ScanPro – Neuer Chat

## Projekt

Repository: `Markus4771/ScanPro`

Aktueller Stand: **0.5.2-dev**

## Neu in 0.5.2-dev

Datenbank und SQLite-Betrieb wurden gehärtet.

## Persistenter Datenbankpfad

```text
/var/lib/scanpro/scanpro.db
```

Systemd setzt:

```text
SCANPRO_DATABASE_URL=sqlite:////var/lib/scanpro/scanpro.db
```

## Automatische Übernahme alter Daten

Der Installer stoppt zuerst Webdienst und Inbox-Worker.

Wenn noch keine persistente DB existiert und folgende alte DB vorhanden ist:

```text
/opt/scanpro/scanpro.db
```

wird sie per SQLite Backup API übernommen.

Vorhandene persistente Datenbanken werden vor jedem Entwicklungsupdate ebenfalls gesichert.

Backups:

```text
/var/lib/scanpro/backups/
```

## SQLite-Härtung

Aktiv:

- WAL
- foreign_keys=ON
- busy_timeout=30000
- synchronous=NORMAL
- SQLAlchemy timeout=30 Sekunden
- pool_pre_ping

## Schema-Migrationen

Neue Datei:

```text
scanpro/migrations.py
```

Aktuelle Schema-Version:

```text
1
```

Neue Tabelle:

```text
schema_version
```

Zukünftige Änderungen an bestehenden Tabellen können über die interne Migrations-Registry versionsabhängig ausgeführt werden.

## Datenbankstatus API

```text
GET /api/system/database
```

Beispiel:

```json
{
  "database_url":"sqlite:////var/lib/scanpro/scanpro.db",
  "path":"/var/lib/scanpro/scanpro.db",
  "schema_version":1,
  "target_schema_version":1,
  "journal_mode":"wal",
  "foreign_keys":true
}
```

## Health

```text
GET /health
```

liefert jetzt zusätzlich die Schema-Version.

## Update

```bash
cd ~/ScanPro
git pull
sudo bash scripts/install-dev.sh
```

Danach:

```bash
curl http://127.0.0.1:8100/health
curl http://127.0.0.1:8100/api/system/database
```

## Nächster Entwicklungsschritt

Empfohlen:

**0.6.0-dev – Paperless-ngx Integration**

Geplant:

- Paperless-ngx als eigener Zieltyp
- API-Verbindungstest
- Dokumentupload
- OCR-/QR-/Barcode-Metadaten weitergeben
- Korrespondent/Dokumenttyp/Tags später regelbasiert setzen

Danach:

- Foto-/Bildscan JPEG/PNG
- Scanner über VPN / entfernte Standorte

## Weiterer Backlog

- Patch-T Praxistest
- Dokumentklassifikation aus OCR
- zusätzliche Dateinamensregeln
- Aufbewahrungs-/Cleanup-Regeln für alte Jobdateien

## Einstieg in einem neuen Chat

```text
Lies bitte die Datei NEUER-CHAT.md aus meinem GitHub-Projekt Markus4771/ScanPro und führe die Entwicklung ab dem dort dokumentierten Stand weiter.
```
