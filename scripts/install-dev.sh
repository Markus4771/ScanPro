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

echo "== ScanPro 1.1-dev Neuinstallation/Update =="

systemctl stop scanpro.service 2>/dev/null || true
systemctl stop scanpro-inbox.service 2>/dev/null || true
systemctl stop scanpro-samba-reload.path 2>/dev/null || true

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y \
  python3 python3-venv python3-pip nginx samba smbclient sqlite3 rsync sudo \
  ocrmypdf tesseract-ocr tesseract-ocr-deu tesseract-ocr-eng

if ! id scanpro >/dev/null 2>&1; then
  useradd --system --home "$DATA_ROOT" --shell /usr/sbin/nologin scanpro
fi

mkdir -p "$APP_DIR" "$DATA_ROOT"/{inputs,jobs,backups}
chown -R scanpro:scanpro "$DATA_ROOT"
chmod 0750 "$DATA_ROOT" "$DATA_ROOT/inputs" "$DATA_ROOT/jobs" "$DATA_ROOT/backups"

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
  'from scanpro.db import Base, engine, initialize_database; import scanpro.models; initialize_database(); Base.metadata.create_all(bind=engine); print("ScanPro 1.1 Datenbank bereit.")'

nginx -t
testparm -s >/dev/null

systemctl daemon-reload
systemctl enable --now smbd
systemctl enable --now nginx
systemctl enable --now scanpro.service
systemctl enable --now scanpro-inbox.service
systemctl enable --now scanpro-samba-reload.path

echo
echo "ScanPro 1.1-dev läuft über http://<server>/"
echo "Beim ersten Aufruf wird der erste Administrator angelegt."
echo "Jeder Benutzer erhält ein eigenes Samba-Konto und eigene Scan-Freigaben."
echo "Bestehende ScanPro-Daten werden beim Anlegen des ersten Administrators diesem Konto zugeordnet."
