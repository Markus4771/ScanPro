import socket
from dataclasses import dataclass
from ipaddress import ip_address

from sqlalchemy.orm import Session

from ..models import Scanner, ScannerConnectionSettings, ScannerStaticTarget


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



def get_static_target(db: Session, scanner: Scanner) -> ScannerStaticTarget | None:
    return (
        db.query(ScannerStaticTarget)
        .filter(ScannerStaticTarget.scanner_id == scanner.id)
        .first()
    )


def effective_scanner_target(db: Session, scanner: Scanner) -> dict:
    static = get_static_target(db, scanner)
    if static and static.enabled:
        address = static.address or scanner.address or ""
        device_name = static.device_name or scanner.name
        airscan_device = None
        if static.driver == "sane" and address:
            url = address if address.startswith(("http://", "https://")) else f"http://{address}/eSCL"
            airscan_device = f"escl:{device_name}:{url}"
        return {
            "source": "static",
            "driver": static.driver or scanner.driver,
            "device_name": device_name,
            "device_id": static.device_id or scanner.device_id,
            "address": address,
            "airscan_device": airscan_device,
        }
    return {
        "source": "discovered",
        "driver": scanner.driver,
        "device_name": scanner.name,
        "device_id": scanner.device_id,
        "address": scanner.address,
        "airscan_device": None,
    }


def classify_scanner_state(
    discovered: bool,
    reachable: bool,
    last_scan_error: str | None = None,
) -> str:
    if not reachable:
        return "network"
    if not discovered:
        return "discovery"
    if last_scan_error:
        return "scan"
    return "ok"
