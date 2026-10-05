# ScanPro – Installation

## Status

Diese Anleitung gilt für **ScanPro 0.1.0-dev** auf Debian 13.

ScanPro befindet sich noch in Entwicklung. Der aktuelle Stand stellt die Basis für Scannerverwaltung, Scanprofile, Scanziele, Workflows und NAPS2-Anbindung bereit.

## Voraussetzungen

- Debian 13
- Root- oder sudo-Zugriff
- Netzwerkzugriff auf die Scanner
- Python 3.11 oder neuer
- Git
- Nginx
- NAPS2 für Linux

## Repository klonen

```bash
git clone https://github.com/Markus4771/ScanPro.git
cd ScanPro
```

## Entwicklungsinstallation

Im Repository liegt bereits ein Installationsskript:

```bash
sudo bash scripts/install-dev.sh
```

Das Skript:

- installiert Python, venv, Nginx und Git
- legt den Systembenutzer `scanpro` an
- kopiert ScanPro nach `/opt/scanpro`
- erstellt eine Python-Virtualenv
- installiert die Python-Abhängigkeiten
- installiert den systemd-Dienst
- richtet Nginx als Reverse Proxy auf Port 80 ein
- startet ScanPro

Danach sollte ScanPro erreichbar sein unter:

```text
http://<IP-DES-SCANPRO-SERVERS>/
```

Der interne FastAPI-Dienst läuft auf:

```text
127.0.0.1:8100
```

## Dienst prüfen

```bash
systemctl status scanpro
```

Logs anzeigen:

```bash
journalctl -u scanpro -f
```

Health-Check:

```bash
curl http://127.0.0.1:8100/health
```

Erwartete Antwort:

```json
{"status":"ok","version":"0.1.0-dev"}
```

## Nginx prüfen

```bash
nginx -t
systemctl status nginx
```

## NAPS2

NAPS2 wird als Scan-Engine verwendet.

Für die Entwicklung ist vorgesehen, Scanner über folgende Wege anzusprechen:

- eSCL
- SANE
- später USB/SANE und weitere Backends

Nach Installation von NAPS2 werden erkannte Geräte später über ScanPro abgefragt.

Direkter Test auf der Shell:

```bash
naps2.console --listdevices --driver escl
```

alternativ:

```bash
naps2.console --listdevices --driver sane
```

Der genaue Installationsweg von NAPS2 wird im nächsten Entwicklungsstand ergänzt und automatisiert.

## Verzeichnisstruktur

Geplanter Betriebsaufbau:

```text
/opt/scanpro/          Anwendung
/var/lib/scanpro/      Datenbank und Arbeitsdaten
/var/lib/scanpro/inbox Eingehende Scans
/var/lib/scanpro/jobs  Scan-Jobs
/var/log/scanpro/      optionale zusätzliche Logs
```

Im aktuellen Entwicklungsstand liegt die SQLite-Datenbank noch relativ zum Arbeitsverzeichnis als:

```text
scanpro.db
```

Das wird vor dem produktiven Einsatz auf `/var/lib/scanpro/` umgestellt.

## Update

Aktuell erfolgt ein Update noch manuell:

```bash
cd ScanPro
git pull
sudo bash scripts/install-dev.sh
```

Später soll ein eigenes Update-Verfahren ergänzt werden.

## Deinstallation des Entwicklungsstands

Dienst stoppen:

```bash
sudo systemctl disable --now scanpro
```

Dateien entfernen:

```bash
sudo rm -f /etc/systemd/system/scanpro.service
sudo rm -f /etc/nginx/sites-enabled/scanpro
sudo rm -f /etc/nginx/sites-available/scanpro
sudo rm -rf /opt/scanpro
sudo systemctl daemon-reload
sudo systemctl reload nginx
```

## Nächster Schritt

Für **0.1.1-dev** sind vorgesehen:

1. NAPS2-Scannererkennung über eSCL und SANE
2. Scanner in ScanPro speichern
3. Testscan auslösen
4. ScanJob mit Status und Fehlern speichern
5. Scan-PDF in einem lokalen Arbeitsverzeichnis ablegen
