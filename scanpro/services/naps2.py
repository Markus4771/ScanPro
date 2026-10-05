import os
import re
import subprocess
from pathlib import Path

class Naps2Error(RuntimeError):
    pass

NAPS2_WORKDIR = Path("/var/lib/scanpro")

def _run(
    args: list[str],
    timeout_seconds: int = 60,
    retries: int = 0,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = str(NAPS2_WORKDIR)
    env["XDG_CONFIG_HOME"] = str(NAPS2_WORKDIR / ".config")
    env["XDG_CACHE_HOME"] = str(NAPS2_WORKDIR / ".cache")
    NAPS2_WORKDIR.mkdir(parents=True, exist_ok=True)
    (NAPS2_WORKDIR / ".config").mkdir(parents=True, exist_ok=True)
    (NAPS2_WORKDIR / ".cache").mkdir(parents=True, exist_ok=True)

    attempts = max(1, retries + 1)
    last_error = "NAPS2-Aufruf fehlgeschlagen."
    for attempt in range(1, attempts + 1):
        try:
            return subprocess.run(
                args,
                capture_output=True,
                text=True,
                check=True,
                cwd=NAPS2_WORKDIR,
                env=env,
                timeout=max(5, timeout_seconds),
            )
        except FileNotFoundError as exc:
            raise Naps2Error("NAPS2 wurde nicht gefunden.") from exc
        except subprocess.TimeoutExpired:
            last_error = f"NAPS2-Zeitlimit nach {timeout_seconds} Sekunden überschritten."
        except subprocess.CalledProcessError as exc:
            last_error = exc.stderr.strip() or exc.stdout.strip() or "NAPS2-Aufruf fehlgeschlagen."

        if attempt < attempts:
            import time
            time.sleep(min(5, attempt * 2))

    raise Naps2Error(last_error)

def _console_args(*args: str) -> list[str]:
    return ["naps2", "console", *args]

def list_devices(driver: str = "sane") -> str:
    result = _run(_console_args("--listdevices", "--driver", driver))
    return result.stdout

def discover_devices(driver: str = "sane") -> list[dict[str, str | None]]:
    raw = list_devices(driver)
    devices: list[dict[str, str | None]] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        name = line
        device_id = None
        address = None
        match = re.match(r"^(.*) \(([^()]*)\)$", line)
        if match:
            name = match.group(1).strip()
            device_id = match.group(2).strip()
            ip_match = re.search(r"ip=([0-9a-fA-F:.]+)", device_id)
            if ip_match:
                address = ip_match.group(1)
        devices.append({
            "name": name,
            "driver": driver,
            "device_id": device_id,
            "address": address,
            "raw": line,
        })
    return devices

def scan_to_pdf(
    output: Path,
    device: str,
    driver: str = "sane",
    dpi: int = 300,
    duplex: bool = False,
    color_mode: str = "color",
    timeout_seconds: int = 60,
    retries: int = 0,
) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    source = "duplex" if duplex else "feeder"
    args = _console_args(
        "-o", str(output),
        "--noprofile",
        "--driver", driver,
        "--device", device,
        "--source", source,
        "--dpi", str(dpi),
        "--bitdepth", color_mode,
        "--pagesize", "a4",
        "-v",
    )
    result = _run(args, timeout_seconds=timeout_seconds, retries=retries)
    if not output.exists():
        details = "\n".join(x for x in (result.stdout.strip(), result.stderr.strip()) if x)
        if details:
            raise Naps2Error(
                "NAPS2 erzeugte keine PDF-Datei. Ausgabe:\n" + details
            )
        raise Naps2Error("NAPS2 meldete keinen Fehler, aber es wurde keine PDF-Datei erzeugt.")
    return output
