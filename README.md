# ScanPro

ScanPro ist eine modulare Linux-ScanStation für Dokumentenscanner.

## Entwicklungsstand

Aktuell: **0.1.1-dev**

Der Brother ADS-2600We ist das erste reale Testgerät. ScanPro bleibt herstellerunabhängig und ist von Anfang an für mehrere Scanner ausgelegt.

## Bereits umgesetzt

- FastAPI-Grundsystem
- SQLite/SQLAlchemy
- Scannerverwaltung
- NAPS2-Anbindung unter Linux
- Scanner-Erkennung über SANE und eSCL
- erkannte Scanner über API anzeigen
- erkannte Scanner in ScanPro übernehmen
- Testscan aus ScanPro starten
- ScanJob mit Status und Fehler speichern
- Testscan-PDF unter `/var/lib/scanpro/jobs/`
- Scanprofile
- Scanziele
- Workflows
- optionale Dokumenttrennung im Datenmodell

## Getestete Hardware

### Brother ADS-2600We

Erkannt über:

```text
SANE / sane-airscan
Brother ADS-2600We
IP: 192.168.0.172
```

Ein direkter NAPS2-ADF-Scan wurde erfolgreich als PDF gespeichert.

### Samsung C48x Series

Wird ebenfalls über SANE/airscan erkannt.

## Zielbild

- mehrere Scanner verwalten
- NAPS2 als Scan-Engine
- eSCL und SANE als Scanner-Backends
- Scanprofile zentral konfigurieren
- Scanziele frei konfigurieren
- Workflows zwischen Scanner, Verarbeitung und Ziel
- optionale Dokumenttrennung
- SMB-Eingänge für Scan-to-Network-Geräte
- OCR, Vorschau und Seitenbearbeitung
- Paperless-ngx und weitere Ziele über Adapter

## API für Scanner

Scanner suchen:

```text
GET /api/scanners/discover?driver=sane
```

Gespeicherte Scanner:

```text
GET /api/scanners
```

Scanner übernehmen:

```text
POST /api/scanners/import
```

Testscan:

```text
POST /api/scanners/{scanner_id}/testscan
```

ScanJobs:

```text
GET /api/jobs
GET /api/jobs/{job_id}
```

## Dokumenttrennung

Die Trennung ist je Profil bzw. Workflow optional vorgesehen.

Geplante Methoden:

- Patch-T
- QR-Code
- Barcode
- Leerseite
- manuelle Trennung

## Dokumentation

- [Installation](INSTALLATION.md)
- [Übergabe für einen neuen Chat](NEUER-CHAT.md)
- [Architektur](docs/ARCHITECTURE.md)

## Geplanter Ausbau

- **0.1.x** Grundsystem, Scannerverwaltung und NAPS2-Anbindung
- **0.2.x** Weboberfläche und SMB-Eingänge
- **0.3.x** Patch-T und manuelle Dokumenttrennung
- **0.4.x** QR-/Barcode-Trennung
- **0.5.x** OCR und Seitenbearbeitung
- **0.6.x** Paperless-ngx und weitere Scanziele
