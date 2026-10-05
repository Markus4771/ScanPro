# ScanPro – Neuer Chat

## Projekt

Repository: `Markus4771/ScanPro`

Aktueller Stand: **0.1.3-dev**

## Erfolgreich getestet

- Brother ADS-2600We über NAPS2/SANE
- Scanner-Erkennung und Import
- Scan über Weboberfläche
- PDF-Erzeugung unter `/var/lib/scanpro/jobs/`
- ScanPro als systemd-Dienst
- Weboberfläche über Nginx/Port 80

## In 0.1.3-dev umgesetzt

- Scannerstatus online/offline
- Scanner bearbeiten
- Scanner aktivieren/deaktivieren
- Scanner löschen
- Schutz vor Löschen eines Scanners, der noch in einem Workflow verwendet wird
- kompakte Testscan-Ergebnisanzeige
- PDF direkt nach erfolgreichem Scan öffnen
- PDF-Link in der Jobliste
- verbesserte Jobdarstellung
- Version auf 0.1.3-dev angehoben

## Relevante API-Endpunkte

```text
GET    /api/scanners/discover?driver=sane
GET    /api/scanners
GET    /api/scanners/status
POST   /api/scanners/import
PATCH  /api/scanners/{scanner_id}
DELETE /api/scanners/{scanner_id}
POST   /api/scanners/{scanner_id}/testscan
GET    /api/jobs
GET    /api/jobs/{job_id}
GET    /api/jobs/{job_id}/file
```

## Update auf dem Testsystem

```bash
cd ~/ScanPro
git pull
sudo bash scripts/install-dev.sh
```

Danach Browser neu laden.

## Nächster Entwicklungsschritt

**0.1.4-dev – Scanprofile im Webinterface**

Geplant:

1. Scanprofile anzeigen
2. Profile anlegen
3. DPI/Farbe/Duplex speichern
4. OCR an/aus
5. Trennung an/aus
6. Trennmethode wählen
7. Profil im Scanbereich auswählen

Danach:

- konfigurierbare Scanziele
- SMB-Ziele
- SMB-Inbox
- automatische Weiterleitung

## Einstieg in einem neuen Chat

```text
Lies bitte die Datei NEUER-CHAT.md aus meinem GitHub-Projekt Markus4771/ScanPro und führe die Entwicklung ab dem dort dokumentierten Stand weiter.
```
