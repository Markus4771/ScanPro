# ScanPro – Installation

## Status

Diese Anleitung gilt für **ScanPro 0.1.3-dev** auf Debian 13.

## Voraussetzungen

- Debian 13
- Root- oder sudo-Zugriff
- Netzwerkzugriff auf die Scanner
- Internetzugang
- Python 3.11 oder neuer
- Git
- Nginx
- SANE-Werkzeuge
- NAPS2 für Linux

## System vorbereiten

```bash
sudo apt update
sudo apt install -y \
  git \
  curl \
  wget \
  ca-certificates \
  python3 \
  python3-venv \
  python3-pip \
  nginx \
  samba \
  sane-utils
```

## NAPS2 installieren

NAPS2 wird als Scan-Engine verwendet und muss aktuell noch separat installiert werden.

Danach prüfen:

```bash
naps2 --version
```

Scanner über SANE suchen:

```bash
naps2 console --listdevices --driver sane
```

Scanner über eSCL suchen:

```bash
naps2 console --listdevices --driver escl
```

Wichtig: Unter Linux verwendet ScanPro den Befehl `naps2 console`, nicht `naps2.console`.

## Scanner-Verbindung prüfen

```bash
scanimage -L
```

Beim Brother ADS-2600We wurde erfolgreich getestet:

```text
Brother ADS-2600We (airscan:ip=192.168.0.172)
```

Direkter Testscan:

```bash
mkdir -p ~/scantest

naps2 console \
  -o ~/scantest/testscan.pdf \
  --noprofile \
  --driver sane \
  --device "Brother ADS-2600We" \
  --source feeder \
  --dpi 300 \
  --bitdepth color \
  --pagesize a4 \
  -v
```

## Repository klonen

```bash
git clone https://github.com/Markus4771/ScanPro.git
cd ScanPro
```

## Entwicklungsinstallation

```bash
sudo bash scripts/install-dev.sh
```

Das Skript:

- installiert die ScanPro-Grundabhängigkeiten
- legt den Systembenutzer `scanpro` an
- kopiert ScanPro nach `/opt/scanpro`
- erstellt eine Python-Virtualenv
- installiert die Python-Abhängigkeiten
- legt `/var/lib/scanpro/jobs` an
- setzt die benötigten Rechte
- installiert den systemd-Dienst
- richtet Nginx auf Port 80 ein
- startet bzw. aktualisiert ScanPro
- prüft, ob NAPS2 vorhanden ist

NAPS2 selbst wird derzeit noch nicht automatisch installiert.

## ScanPro prüfen

```bash
systemctl status scanpro --no-pager
```

```bash
curl http://127.0.0.1:8100/health
```

Erwartete Antwort:

```json
{"status":"ok","version":"0.1.3-dev"}
```

## Scanner über ScanPro suchen

```bash
curl "http://127.0.0.1:8100/api/scanners/discover?driver=sane"
```

Die Antwort sollte den Brother ADS-2600We und weitere von NAPS2 erkannte SANE-Geräte enthalten.

## Scanner speichern

Beispiel für den Brother:

```bash
curl -X POST http://127.0.0.1:8100/api/scanners/import \
  -H "Content-Type: application/json" \
  -d '{
    "name":"Brother ADS-2600We",
    "driver":"sane",
    "address":"192.168.0.172",
    "device_id":"airscan:ip=192.168.0.172"
  }'
```

Danach gespeicherte Scanner anzeigen:

```bash
curl http://127.0.0.1:8100/api/scanners
```

## Testscan über ScanPro

Zuerst die Scanner-ID aus `/api/scanners` ermitteln.

Beispiel mit Scanner-ID 1:

```bash
curl -X POST http://127.0.0.1:8100/api/scanners/1/testscan \
  -H "Content-Type: application/json" \
  -d '{
    "dpi":300,
    "duplex":false,
    "color_mode":"color"
  }'
```

Vor dem Aufruf ein Blatt in den ADF legen.

Erfolgreiche Testscans werden gespeichert unter:

```text
/var/lib/scanpro/jobs/
```

Jobs anzeigen:

```bash
curl http://127.0.0.1:8100/api/jobs
```

## Nginx

ScanPro sollte zusätzlich über Port 80 erreichbar sein:

```text
http://<IP-DES-SCANPRO-SERVERS>/
```

## Update

```bash
cd ~/ScanPro
git pull
sudo bash scripts/install-dev.sh
```

## Logs

```bash
journalctl -u scanpro -f
```

## Verzeichnisstruktur

```text
/opt/scanpro/           Anwendung
/var/lib/scanpro/jobs/  erzeugte ScanJobs/PDFs
```

Die SQLite-Datenbank liegt im aktuellen Entwicklungsstand weiterhin im ScanPro-Arbeitsverzeichnis. Eine Verlagerung nach `/var/lib/scanpro/` folgt vor dem produktiven Einsatz.

## Nächster Entwicklungsschritt

Nach erfolgreichem API-Testscan:

1. Weboberfläche für Scanner-Erkennung und Scannerverwaltung
2. Testscan-Button im Webinterface
3. SMB-Inbox
4. Patch-T-Trennung


## Weboberfläche

Nach dem Update ist ScanPro direkt im Browser erreichbar:

```text
http://<IP-DES-SCANPRO-SERVERS>/
```

Die Weboberfläche bietet aktuell:

- Scanner über SANE oder eSCL suchen
- erkannte Scanner übernehmen
- gespeicherte Scanner anzeigen
- Testscan starten
- DPI wählen
- Farbe/Graustufen/Schwarzweiß wählen
- Einseitig/Duplex wählen
- letzte ScanJobs anzeigen

## Update auf 0.1.3-dev

```bash
cd ~/ScanPro
git pull
sudo bash scripts/install-dev.sh
```

Danach Browser neu laden.


## Neue Funktionen in 0.1.3-dev

- Online-/Offline-Status gespeicherter Scanner
- Scanner bearbeiten
- Scanner aktivieren/deaktivieren
- Scanner löschen
- kompakte Scan-Ergebnisanzeige
- PDF direkt aus der Jobliste öffnen
- verbesserte ScanJob-Liste
