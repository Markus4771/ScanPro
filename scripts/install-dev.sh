#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Bitte als root ausführen."
  exit 1
fi

apt-get update
apt-get install -y python3 python3-venv nginx git

id scanpro >/dev/null 2>&1 || useradd --system --home /opt/scanpro --shell /usr/sbin/nologin scanpro

mkdir -p /opt/scanpro
cp -a . /opt/scanpro/
python3 -m venv /opt/scanpro/.venv
/opt/scanpro/.venv/bin/pip install --upgrade pip
/opt/scanpro/.venv/bin/pip install /opt/scanpro

chown -R scanpro:scanpro /opt/scanpro

cp /opt/scanpro/deploy/scanpro.service /etc/systemd/system/scanpro.service
cp /opt/scanpro/deploy/nginx.conf /etc/nginx/sites-available/scanpro
ln -sf /etc/nginx/sites-available/scanpro /etc/nginx/sites-enabled/scanpro
rm -f /etc/nginx/sites-enabled/default

systemctl daemon-reload
systemctl enable --now scanpro
nginx -t
systemctl reload nginx

echo "ScanPro läuft über http://<server>/"
echo "Hinweis: NAPS2 wird bewusst separat installiert und in 0.1.1-dev geprüft."
