# ScanPro – Neuer Chat

## Projekt

Repository: `Markus4771/ScanPro`

Aktueller Stand: **0.1.1-dev**

ScanPro wird als neue Linux-ScanStation von Grund auf entwickelt. Das frühere OpenScanStation-Projekt wird nicht als Codebasis verwendet.

## Aktuell erfolgreich getestet

Der Brother ADS-2600We wird auf Debian über NAPS2/SANE erkannt:

```text
Brother ADS-2600We (airscan:ip=192.168.0.172)
```

Der Samsung C48x Series wird ebenfalls erkannt.

eSCL liefert auf dem aktuellen System keine Geräte, SANE/airscan funktioniert jedoch.

Ein direkter NAPS2-ADF-Testscan mit dem Brother war erfolgreich:

```bash
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

## In 0.1.1-dev umgesetzt

- NAPS2-Aufruf unter Linux auf `naps2 console` korrigiert
- Scanner-Erkennung über API
- SANE/eSCL als wählbare Discovery-Treiber
- Parser für NAPS2-Geräteliste
- Scanner-Import/Speicherung
- Testscan-Endpunkt
- ScanJob-Status:
  - queued
  - scanning
  - finished
  - error
- Testscan-Ausgabe unter `/var/lib/scanpro/jobs/`
- Job-Abfrage über API
- Installationsskript legt Job-Verzeichnis und Rechte an
- Parser-Test für reale Brother-/Samsung-Ausgabe

## Relevante API-Endpunkte

```text
GET  /api/scanners/discover?driver=sane
GET  /api/scanners
POST /api/scanners/import
POST /api/scanners/{scanner_id}/testscan
GET  /api/jobs
GET  /api/jobs/{job_id}
```

## Nach Update auf dem Testsystem prüfen

```bash
cd ~/ScanPro
git pull
sudo bash scripts/install-dev.sh
```

Dann:

```bash
curl http://127.0.0.1:8100/health
curl "http://127.0.0.1:8100/api/scanners/discover?driver=sane"
```

Danach Brother importieren, Blatt einlegen und Testscan über ScanPro starten.

## Weiterhin geplante Grundfunktionen

- mehrere Scanner konfigurierbar
- Scanprofile konfigurierbar
- Scanziele konfigurierbar
- Workflows
- SMB-Eingang
- optionale Dokumenttrennung
- Patch-T
- QR-Code
- Barcode
- Leerseite
- manuelle Trennung
- OCR
- Vorschau und Seitenbearbeitung
- Paperless-ngx
- weitere Ziel-Adapter

## Nächster Entwicklungsschritt

Nach erfolgreichem 0.1.1-Test auf dem Server:

**0.1.2-dev – erste Weboberfläche für Scannerverwaltung**

Geplant:

1. erkannte Scanner anzeigen
2. Scanner per Klick übernehmen
3. gespeicherte Scanner anzeigen
4. Online/Offline-Status
5. Testscan per Button
6. ScanJob-Ergebnis anzeigen

Danach folgen SMB-Inbox und Trennfunktion.

## Einstieg in einem neuen Chat

```text
Lies bitte die Datei NEUER-CHAT.md aus meinem GitHub-Projekt Markus4771/ScanPro und führe die Entwicklung ab dem dort dokumentierten Stand weiter.
```
