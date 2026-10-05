import re
from pathlib import Path

PROFILE_ROOT = Path("/var/lib/scanpro/profile-inbox")
PROFILE_CONFIG = Path("/var/lib/scanpro/samba-profile-shares.conf")

class ProfileShareError(ValueError):
    pass

def normalize_share_name(value: str) -> str:
    value = value.strip()
    if not value:
        raise ProfileShareError("Freigabename darf nicht leer sein.")
    if len(value) > 80:
        raise ProfileShareError("Freigabename darf maximal 80 Zeichen haben.")
    if not re.fullmatch(r"[A-Za-z0-9ÄÖÜäöüß_. -]+", value):
        raise ProfileShareError("Freigabename enthält nicht erlaubte Zeichen.")
    return value

def profile_path(profile_id: int) -> Path:
    return PROFILE_ROOT / str(profile_id)

def render_config(shares: list[tuple[str, str]]) -> str:
    blocks = []
    for name, path in shares:
        blocks.append(
            f"[{name}]\n"
            f"   path = {path}\n"
            "   browseable = yes\n"
            "   read only = no\n"
            "   guest ok = no\n"
            "   valid users = scanpro\n"
            "   force user = scanpro\n"
            "   create mask = 0660\n"
            "   directory mask = 0770\n"
        )
    return "\n".join(blocks)

def write_profile_samba_config(shares: list[tuple[str, str]]) -> None:
    PROFILE_ROOT.mkdir(parents=True, exist_ok=True)
    PROFILE_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_CONFIG.write_text(render_config(shares), encoding="utf-8")
