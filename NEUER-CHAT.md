# ScanPro – Neuer Chat

## Projekt

Repository: `Markus4771/ScanPro`

Aktueller Stand: **0.4.0-dev**

## Neu in 0.4.0-dev

Die Bildoptimierung ist umgesetzt.

## Profiloptionen

Jedes Scanprofil kann optional aktivieren:

- automatische Rotation
- Deskew / schiefe Seiten begradigen
- Auto-Crop
- Scanner-Ränder entfernen

## Verarbeitungskette

```text
Scan / SMB-Eingang
→ Leerseiten-Verarbeitung
→ Dokumenttrennung
→ Bildoptimierung
→ später OCR
→ Weiterleitung
```

Die Bildoptimierung läuft sowohl für:

- Scanner-Workflows
- Profil-SMB-Inbox-Workflows
- getrennte Teildokumente
- ungetrennte PDFs

## Technische Umsetzung

Neue Datei:

```text
scanpro/services/image_processing.py
```

Verwendet:

- OpenCV
- PyMuPDF
- Tesseract OSD
- pytesseract

## Neue Tabellen

```text
profile_image_processing
job_image_processing
```

### profile_image_processing

- profile_id
- auto_rotate
- deskew
- auto_crop
- remove_borders

### job_image_processing

- scan_job_id
- document_id
- pages_processed
- pages_rotated
- pages_deskewed
- pages_cropped
- pages_border_cleaned

## API

```text
GET /api/profile-image-processing
PUT /api/profiles/{profile_id}/image-processing
```

## Webinterface

Die vier Bildoptionen sind direkt im Scanprofil konfigurierbar.

Die Jobliste zeigt erkannte Optimierungen wie:

```text
gedreht: 1
begradigt: 2
zugeschnitten: 2
```

## Update

```bash
cd ~/ScanPro
git pull
sudo bash scripts/install-dev.sh
```

Danach:

```bash
curl http://127.0.0.1:8100/health
```

Erwartet:

```json
{"status":"ok","version":"0.4.0-dev"}
```

## Nächster Entwicklungsschritt

Empfohlen:

**0.5.0-dev – OCR**

- OCR wirklich ausführen
- OCR-Sprache pro Profil
- durchsuchbare PDF
- OCR-Text speichern
- später Metadaten/Dateinamen aus OCR und QR-/Barcode-Inhalten

## Backlog

Weiterhin geplant:

- Bilder/Fotos scannen mit JPEG/PNG
- Scanner über VPN / entfernte Standorte
- Patch-T Praxistest mit Brother ADS-2600We
- Paperless-ngx
- Dateinamen-/Metadatenregeln

## Einstieg in einem neuen Chat

```text
Lies bitte die Datei NEUER-CHAT.md aus meinem GitHub-Projekt Markus4771/ScanPro und führe die Entwicklung ab dem dort dokumentierten Stand weiter.
```
