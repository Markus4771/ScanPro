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

def _console_args(*args: str) -> list[str]:
    return ["naps2", "console", *args]

def list_devices(driver: str = "escl") -> str:
    result = _run(_console_args("--listdevices", "--driver", driver))
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
    args = _console_args(
        "-o", str(output),
        "--driver", driver,
        "--device", device,
        "--source", source,
        "--dpi", str(dpi),
        "--pagesize", "a4",
    )
    _run(args)
    return output
