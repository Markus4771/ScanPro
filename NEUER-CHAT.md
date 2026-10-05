# ScanPro – Neuer Chat

## Projekt

Repository: `Markus4771/ScanPro`

Aktueller Stand: **0.5.1-dev**

## Neu in 0.5.1-dev

Dateinamenregeln und Dokumentmetadaten sind umgesetzt.

## Dateinamensvorlage pro Profil

Standard:

```text
{date}_{profile}_{job}_{document}
```

Unterstützte Variablen:

```text
{date}
{time}
{datetime}
{profile}
{job}
{document}
{code}
{code_type}
{ocr_first_line}
```

## Beispiele

Normale Ablage:

```text
{date}_{profile}_{job}_{document}
```

QR-/Barcode-basiert:

```text
{date}_{profile}_{code}_{document}
```

OCR-basiert:

```text
{date}_{ocr_first_line}_{document}
```

## Technische Umsetzung

Neue Tabellen:

```text
profile_naming_settings
job_document_metadata
```

### profile_naming_settings

- profile_id
- filename_template
- use_ocr_first_line

### job_document_metadata

- scan_job_id
- document_id
- final_filename
- metadata_json
- created_at

Neue Datei:

```text
scanpro/services/naming.py
```

## Verhalten

Die internen Arbeits-PDFs werden nicht umbenannt.

Der finale Dateiname wird unmittelbar vor der Weiterleitung erzeugt und an:

- lokale Ziele
- SMB-Ziele

übergeben.

Damit bleiben OCR, Trennung und interne Jobpfade stabil.

## Metadaten

Pro Dokument speichert ScanPro:

- Profil
- Job-ID
- Dokumentnummer
- Codeinhalt
- Codetyp
- OCR-Erstzeile
- Quelldateiname
- finaler Dateiname

## API

```text
GET /api/profile-naming-settings
PUT /api/profiles/{profile_id}/naming-settings
GET /api/job-documents/{document_id}/metadata
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
{"status":"ok","version":"0.5.1-dev"}
```

## Nächster Entwicklungsschritt

Vor dem weiteren Funktionsausbau empfohlen:

**0.5.2-dev – Datenbank und Produktionshärtung**

- SQLite nach `/var/lib/scanpro/scanpro.db`
- bestehende Daten automatisch migrieren
- SQLite WAL
- Foreign Keys aktivieren
- Schema-Migrationen einführen
- robustere Transaktionen

Danach:

- Paperless-ngx
- Foto-/Bildscan JPEG/PNG
- VPN-/Remote-Scanner

## Backlog

- Paperless-ngx
- Bilder/Fotos scannen
- Scanner über VPN
- Patch-T Praxistest
- weitere Dateinamen-/Metadatenregeln
- Dokumentklassifikation aus OCR

## Einstieg in einem neuen Chat

```text
Lies bitte die Datei NEUER-CHAT.md aus meinem GitHub-Projekt Markus4771/ScanPro und führe die Entwicklung ab dem dort dokumentierten Stand weiter.
```
