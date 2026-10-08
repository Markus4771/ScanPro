#!/usr/bin/env bash
set -euo pipefail

APP_DIR=/opt/scanpro
DATA_ROOT=/var/lib/scanpro-v1
DB_FILE="$DATA_ROOT/scanpro-v1.db"
SAMBA_INCLUDE="$DATA_ROOT/samba-inputs.conf"

if [[ $EUID -ne 0 ]]; then
  echo "Bitte mit sudo/root ausführen."
  exit 1
fi

echo "== ScanPro 1.5.1-dev Neuinstallation/Update =="

systemctl stop scanpro.service 2>/dev/null || true
systemctl stop scanpro-inbox.service 2>/dev/null || true
systemctl stop scanpro-samba-reload.path 2>/dev/null || true

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y \
  python3 python3-venv python3-pip nginx samba smbclient sqlite3 rsync sudo \
  ocrmypdf poppler-utils tesseract-ocr tesseract-ocr-deu tesseract-ocr-eng

if ! id scanpro >/dev/null 2>&1; then
  useradd --system --home "$DATA_ROOT" --shell /usr/sbin/nologin scanpro
fi

mkdir -p "$APP_DIR"   "$DATA_ROOT/Eingang"   "$DATA_ROOT/Verarbeitung/jobs"   "$DATA_ROOT/Verarbeitung/temp"   "$DATA_ROOT/Verarbeitung/failed"   "$DATA_ROOT/Ausgang"   "$DATA_ROOT/Archiv"   "$DATA_ROOT/backups"

# Alte Verzeichnisse sicher in die neue ScanPro-Struktur übernehmen.
# Alte Eingänge waren nach numerischer ID organisiert (z. B. inputs/1).
# Wenn die DB den Freigabenamen kennt, werden die Dateien in den benannten
# Eingang (z. B. Eingang/PDF) übernommen.
if [[ -d "$DATA_ROOT/inputs" ]]; then
  while IFS='|' read -r input_id share_name; do
    [[ -n "$input_id" && -n "$share_name" ]] || continue
    old_dir="$DATA_ROOT/inputs/$input_id"
    new_dir="$DATA_ROOT/Eingang/$share_name"
    if [[ -d "$old_dir" ]]; then
      mkdir -p "$new_dir"
      rsync -a "$old_dir/" "$new_dir/"
      rm -rf "$old_dir"
    fi
  done < <(sqlite3 "$DB_FILE" "SELECT id,share_name FROM scan_inputs;" 2>/dev/null || true)

  # Nicht zuordenbare Reste bleiben sicher im Archiv erhalten.
  if find "$DATA_ROOT/inputs" -mindepth 1 -print -quit | grep -q .; then
    mkdir -p "$DATA_ROOT/Archiv/Legacy-inputs"
    rsync -a "$DATA_ROOT/inputs/" "$DATA_ROOT/Archiv/Legacy-inputs/"
  fi
  rm -rf "$DATA_ROOT/inputs"
fi

# Frühere Updates konnten bereits Eingang/<ID> erzeugt haben.
while IFS='|' read -r input_id share_name; do
  [[ -n "$input_id" && -n "$share_name" ]] || continue
  old_dir="$DATA_ROOT/Eingang/$input_id"
  new_dir="$DATA_ROOT/Eingang/$share_name"
  if [[ "$old_dir" != "$new_dir" && -d "$old_dir" ]]; then
    mkdir -p "$new_dir"
    rsync -a "$old_dir/" "$new_dir/"
    rm -rf "$old_dir"
  fi
done < <(sqlite3 "$DB_FILE" "SELECT id,share_name FROM scan_inputs;" 2>/dev/null || true)

if [[ -d "$DATA_ROOT/jobs" ]]; then
  rsync -a "$DATA_ROOT/jobs/" "$DATA_ROOT/Verarbeitung/jobs/"
  rm -rf "$DATA_ROOT/jobs"
fi

chown -R scanpro:scanpro "$DATA_ROOT"
chmod 0750   "$DATA_ROOT"   "$DATA_ROOT/Eingang"   "$DATA_ROOT/Verarbeitung"   "$DATA_ROOT/Verarbeitung/jobs"   "$DATA_ROOT/Verarbeitung/temp"   "$DATA_ROOT/Verarbeitung/failed"   "$DATA_ROOT/Ausgang"   "$DATA_ROOT/Archiv"   "$DATA_ROOT/backups"

if [[ -f "$DB_FILE" ]]; then
  stamp=$(date +%Y%m%d-%H%M%S)
  sqlite3 "$DB_FILE" ".backup '$DATA_ROOT/backups/scanpro-v1-$stamp.db'"
fi

rsync -a --delete --exclude '.git' --exclude '.venv' ./ "$APP_DIR/"
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip
"$APP_DIR/.venv/bin/pip" install "$APP_DIR"

install -m 0755 "$APP_DIR/scripts/scanpro-samba-user" /usr/local/sbin/scanpro-samba-user
cat >/etc/sudoers.d/scanpro-samba <<'EOF'
scanpro ALL=(root) NOPASSWD: /usr/local/sbin/scanpro-samba-user *
EOF
chmod 0440 /etc/sudoers.d/scanpro-samba
visudo -cf /etc/sudoers.d/scanpro-samba

install -m 0644 "$APP_DIR/deploy/scanpro.service" /etc/systemd/system/scanpro.service
install -m 0644 "$APP_DIR/deploy/scanpro-inbox.service" /etc/systemd/system/scanpro-inbox.service
install -m 0644 "$APP_DIR/deploy/scanpro-samba-reload.service" /etc/systemd/system/scanpro-samba-reload.service
install -m 0644 "$APP_DIR/deploy/scanpro-samba-reload.path" /etc/systemd/system/scanpro-samba-reload.path
install -m 0644 "$APP_DIR/deploy/nginx.conf" /etc/nginx/sites-available/scanpro

ln -sf /etc/nginx/sites-available/scanpro /etc/nginx/sites-enabled/scanpro
rm -f /etc/nginx/sites-enabled/default

touch "$SAMBA_INCLUDE"
chown scanpro:scanpro "$SAMBA_INCLUDE"
chmod 0644 "$SAMBA_INCLUDE"

sed -i '\|^include = /etc/samba/scanpro.conf$|d' /etc/samba/smb.conf
rm -f /etc/samba/scanpro.conf
if ! grep -Fq "include = $SAMBA_INCLUDE" /etc/samba/smb.conf; then
  printf '\n# ScanPro dynamic per-user input shares\ninclude = %s\n' "$SAMBA_INCLUDE" >> /etc/samba/smb.conf
fi

chown -R scanpro:scanpro "$DATA_ROOT"

runuser -u scanpro -- env \
  SCANPRO_DATA_ROOT="$DATA_ROOT" \
  SCANPRO_DATABASE_URL="sqlite:///$DB_FILE" \
  "$APP_DIR/.venv/bin/python" -c \
  'from scanpro.db import Base, engine, initialize_database; import scanpro.models; initialize_database(); Base.metadata.create_all(bind=engine); print("ScanPro Datenbank/Schema bereit.")'

nginx -t
testparm -s >/dev/null

systemctl daemon-reload
systemctl enable --now smbd
systemctl enable --now nginx
systemctl enable --now scanpro.service
systemctl enable --now scanpro-inbox.service
systemctl enable --now scanpro-samba-reload.path

echo
echo "ScanPro 1.5.1-dev läuft über http://<server>/"
echo "Beim ersten Aufruf wird der erste Administrator angelegt."
echo "Jede Scan-Freigabe erhält eigene Samba-Zugangsdaten; WebGUI-Benutzer bleiben davon getrennt."
echo "Bestehende ScanPro-Daten werden beim Anlegen des ersten Administrators diesem Konto zugeordnet."
