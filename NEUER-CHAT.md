# ScanPro – Neuer Chat

## Projekt

Repository: `Markus4771/ScanPro`

Aktueller Stand: **0.5.0-dev**

## Neu in 0.5.0-dev

OCR ist jetzt vollständig in die Verarbeitung integriert.

## OCR-Profiloptionen

OCR kann pro Scanprofil aktiviert werden.

Sprachen:

- `deu`
- `eng`
- `deu+eng`

## Verarbeitungskette

```text
Scan / SMB-Eingang
→ Leerseiten-Verarbeitung
→ Dokumenttrennung
→ Bildoptimierung
→ OCR
→ Weiterleitung
```

OCR läuft sowohl für Scanner-Workflows als auch Profil-SMB-Inboxen.

## Technische Umsetzung

Neue Datei:

```text
scanpro/services/ocr.py
```

Verwendet:

- OCRmyPDF
- Tesseract

OCRmyPDF erzeugt eine durchsuchbare PDF und zusätzlich Sidecar-Text.

## Neue Tabellen

```text
profile_ocr_settings
job_ocr_results
```

## API

```text
GET /api/profile-ocr-settings
PUT /api/profiles/{profile_id}/ocr-settings
GET /api/job-documents/{document_id}/ocr
```

## Webinterface

Im Profil:

```text
OCR aktivieren
OCR-Sprache
```

Verfügbare Sprachen:

```text
Deutsch
Englisch
Deutsch + Englisch
```

## Installation

Das Installationsskript installiert zusätzlich:

```text
ocrmypdf
tesseract-ocr-deu
tesseract-ocr-eng
```

## Update

```bash
cd ~/ScanPro
git pull
sudo bash scripts/install-dev.sh
```

Prüfen:

```bash
curl http://127.0.0.1:8100/health
```

Erwartet:

```json
{"status":"ok","version":"0.5.0-dev"}
```

## Nächster Entwicklungsschritt

**0.5.1-dev – Dateinamen und Metadaten**

Geplant:

- Dateinamenregeln pro Profil
- Datum/Uhrzeit/Profilname
- QR-/Barcode-Inhalt als Variable
- OCR-Inhalt als Variable
- Dokumentnummern
- saubere Dateinamen für lokale und SMB-Ziele

Danach:

- Paperless-ngx
- Foto-/Bildscan JPEG/PNG
- VPN-/Remote-Scanner

## Backlog

Weiterhin geplant:

- Bilder/Fotos scannen
- Scanner über VPN / entfernte Standorte
- Patch-T Praxistest mit Brother ADS-2600We
- Paperless-ngx
- Datenbank nach `/var/lib/scanpro/` verlagern und Migrationen einführen

## Einstieg in einem neuen Chat

```text
Lies bitte die Datei NEUER-CHAT.md aus meinem GitHub-Projekt Markus4771/ScanPro und führe die Entwicklung ab dem dort dokumentierten Stand weiter.
```
