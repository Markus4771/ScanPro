import socket
from dataclasses import dataclass
from ipaddress import ip_address

from sqlalchemy.orm import Session

from ..models import Scanner, ScannerConnectionSettings


@dataclass
class ReachabilityResult:
    reachable: bool
    method: str
    detail: str


def get_connection_settings(db: Session, scanner: Scanner) -> ScannerConnectionSettings:
    row = (
        db.query(ScannerConnectionSettings)
        .filter(ScannerConnectionSettings.scanner_id == scanner.id)
        .first()
    )
    if row:
        return row

    row = ScannerConnectionSettings(
        scanner_id=scanner.id,
        location="Lokal",
        connection_type="local",
        timeout_seconds=60,
        retries=1,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _host_from_scanner(scanner: Scanner) -> str | None:
    if scanner.address:
        return scanner.address.strip()
    if scanner.device_id and "ip=" in scanner.device_id:
        value = scanner.device_id.split("ip=", 1)[1]
        return value.split(",", 1)[0].split(";", 1)[0].strip()
    return None


def check_reachability(scanner: Scanner, timeout_seconds: float = 2.0) -> ReachabilityResult:
    host = _host_from_scanner(scanner)
    if not host:
        return ReachabilityResult(False, "none", "Keine Scanner-Adresse hinterlegt.")

    # Avoid relying on ICMP, which is frequently blocked across VPNs.
    ports = (443, 80, 631, 6566)
    for port in ports:
        try:
            with socket.create_connection((host, port), timeout=timeout_seconds):
                return ReachabilityResult(True, f"tcp/{port}", f"{host}:{port} erreichbar")
        except (OSError, socket.timeout):
            pass

    return ReachabilityResult(
        False,
        "tcp",
        f"{host} antwortet auf keinem getesteten Scanner-Port ({', '.join(map(str, ports))}).",
    )
