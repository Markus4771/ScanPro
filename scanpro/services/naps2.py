import json
import subprocess
from pathlib import Path

class Naps2Error(RuntimeError):
    pass

def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(args, capture_output=True, text=True, check=True)
    except FileNotFoundError as exc:
        raise Naps2Error("NAPS2 wurde nicht gefunden.") from exc
    except subprocess.CalledProcessError as exc:
        raise Naps2Error(exc.stderr.strip() or exc.stdout.strip() or "NAPS2-Aufruf fehlgeschlagen.") from exc

def list_devices(driver: str = "escl") -> str:
    result = _run(["naps2.console", "--listdevices", "--driver", driver])
    return result.stdout

def scan_to_pdf(
    output: Path,
    device: str,
    driver: str = "escl",
    dpi: int = 300,
    duplex: bool = True,
    color_mode: str = "color",
) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    source = "duplex" if duplex else "feeder"
    args = [
        "naps2.console",
        "-o", str(output),
        "--driver", driver,
        "--device", device,
        "--source", source,
        "--dpi", str(dpi),
        "--pagesize", "a4",
    ]
    # Color handling will be normalized after first hardware test.
    _run(args)
    return output
