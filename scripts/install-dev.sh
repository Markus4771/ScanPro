#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Bitte als root ausführen."
  exit 1
fi

apt-get update
apt-get install -y python3 python3-venv nginx git sane-utils samba smbclient sqlite3 libzbar0 tesseract-ocr tesseract-ocr-osd tesseract-ocr-deu tesseract-ocr-eng ocrmypdf

systemctl stop scanpro-inbox 2>/dev/null || true
systemctl stop scanpro 2>/dev/null || true

if ! id scanpro >/dev/null 2>&1; then
  useradd --system --home /var/lib/scanpro --shell /usr/sbin/nologin scanpro
else
  current_home="$(getent passwd scanpro | cut -d: -f6)"
  if [[ "$current_home" != "/var/lib/scanpro" ]]; then
    systemctl stop scanpro 2>/dev/null || true
    usermod --home /var/lib/scanpro scanpro
  fi
fi

mkdir -p /opt/scanpro
mkdir -p /var/lib/scanpro/jobs
mkdir -p /var/lib/scanpro/inbox
mkdir -p /var/lib/scanpro/profile-inbox
mkdir -p /var/lib/scanpro/.config
mkdir -p /var/lib/scanpro/.cache
mkdir -p /var/lib/scanpro/backups
touch /var/lib/scanpro/samba-profile-shares.conf

DB_TARGET="/var/lib/scanpro/scanpro.db"
LEGACY_DB="/opt/scanpro/scanpro.db"
BACKUP_STAMP="$(date +%Y%m%d-%H%M%S)"

if [[ -f "$DB_TARGET" ]]; then
  echo "Sichere bestehende ScanPro-Datenbank..."
  sqlite3 "$DB_TARGET" ".backup '/var/lib/scanpro/backups/scanpro-$BACKUP_STAMP.db'"
elif [[ -f "$LEGACY_DB" ]]; then
  echo "Übernehme bestehende Datenbank von $LEGACY_DB nach $DB_TARGET..."
  sqlite3 "$LEGACY_DB" ".backup '$DB_TARGET'"
  sqlite3 "$LEGACY_DB" ".backup '/var/lib/scanpro/backups/scanpro-pre-0.5.2-$BACKUP_STAMP.db'"
else
  echo "Keine bestehende Datenbank gefunden; ScanPro legt eine neue Datenbank an."
fi

if [[ -f "$DB_TARGET" ]]; then
  integrity="$(sqlite3 "$DB_TARGET" 'PRAGMA integrity_check;')"
  if [[ "$integrity" != "ok" ]]; then
    echo "FEHLER: SQLite-Integritätsprüfung fehlgeschlagen: $integrity"
    exit 1
  fi
fi

cp -a . /opt/scanpro/

python3 -m venv /opt/scanpro/.venv
/opt/scanpro/.venv/bin/pip install --upgrade pip
/opt/scanpro/.venv/bin/pip install /opt/scanpro

chown -R scanpro:scanpro /opt/scanpro
chown -R scanpro:scanpro /var/lib/scanpro
[[ -f "$DB_TARGET" ]] && chmod 0660 "$DB_TARGET" || true
chmod 0770 /var/lib/scanpro/inbox
chmod 0770 /var/lib/scanpro/profile-inbox
chmod 0750 /var/lib/scanpro/jobs
chmod 0660 /var/lib/scanpro/samba-profile-shares.conf

cp /opt/scanpro/deploy/scanpro.service /etc/systemd/system/scanpro.service
cp /opt/scanpro/deploy/scanpro-samba-reload.service /etc/systemd/system/scanpro-samba-reload.service
cp /opt/scanpro/deploy/scanpro-samba-reload.path /etc/systemd/system/scanpro-samba-reload.path
cp /opt/scanpro/deploy/scanpro-inbox.service /etc/systemd/system/scanpro-inbox.service

cp /opt/scanpro/deploy/nginx.conf /etc/nginx/sites-available/scanpro
ln -sf /etc/nginx/sites-available/scanpro /etc/nginx/sites-enabled/scanpro
rm -f /etc/nginx/sites-enabled/default

cp /opt/scanpro/deploy/samba-scanpro.conf /etc/samba/scanpro.conf
if ! grep -Fxq "include = /etc/samba/scanpro.conf" /etc/samba/smb.conf; then
  printf '\ninclude = /etc/samba/scanpro.conf\n' >> /etc/samba/smb.conf
fi

systemctl daemon-reload

echo "ScanPro-Datenbank initialisieren und Schema migrieren..."
runuser -u scanpro -- env \
  HOME=/var/lib/scanpro \
  SCANPRO_DATABASE_URL=sqlite:////var/lib/scanpro/scanpro.db \
  /opt/scanpro/.venv/bin/python -c 'from scanpro.db import Base, engine, initialize_database; import scanpro.models; from scanpro.migrations import run_schema_migrations; initialize_database(); Base.metadata.create_all(bind=engine); print("Schema-Version:", run_schema_migrations(engine))'

systemctl enable scanpro
systemctl restart scanpro
systemctl enable --now scanpro-inbox.service
systemctl restart scanpro-inbox.service
systemctl enable --now scanpro-samba-reload.path

nginx -t
systemctl reload nginx

testparm -s >/dev/null
systemctl enable --now smbd
systemctl reload smbd

echo "ScanPro läuft über http://<server>/"
echo "SMB-Freigaben: \\<server>\ScanPro-Inbox und \\<server>\ScanPro-Jobs"
echo "Profilbezogene SMB-Freigaben können optional im Webinterface aktiviert werden."
echo "Einmalig Samba-Passwort setzen mit: sudo smbpasswd -a scanpro"

if command -v naps2 >/dev/null 2>&1; then
  echo "NAPS2 gefunden: $(naps2 --version 2>/dev/null || true)"
else
  echo "WARNUNG: NAPS2 ist noch nicht installiert. Scanner-Erkennung und Scannen funktionieren erst nach der NAPS2-Installation."
fi
