# ScanPro – Übergabe für neuen Chat

## Projekt

Repository: `Markus4771/ScanPro`

Aktueller Stand: **0.1.0-dev**

ScanPro wird als neue Linux-ScanStation von Grund auf entwickelt. Das frühere OpenScanStation-Projekt soll nicht als Codebasis verwendet werden.

## Anforderungen

- Linux/Debian als Zielsystem
- NAPS2 als Scan-Engine
- mehrere Scanner konfigurierbar
- erster Testscanner: Brother ADS-2600We
- Scanner möglichst über eSCL/SANE, zusätzlich SMB-Eingang
- Scanprofile konfigurierbar
- Scanziele konfigurierbar
- Workflows konfigurierbar
- Dokumenttrennung optional
- Trennung kann über Profil/Scanziel bzw. Workflow aktiviert werden
- geplante Trennmethoden:
  - Patch-T
  - QR-Code
  - Barcode
  - Leerseite
  - manuell
- später OCR, Vorschau, Seitenbearbeitung und Paperless-ngx

## Architekturentscheidung

Scanner, Scanprofile, Scanziele und Workflows sind voneinander getrennt.

Ein Scanner ist nicht fest an ein Ziel gebunden. Ein Scanprofil kann von mehreren Scannern verwendet werden.

## Bereits angelegt

- `scanpro/main.py`
- `scanpro/db.py`
- `scanpro/models.py`
- `scanpro/schemas.py`
- `scanpro/services/naps2.py`
- `scanpro/services/separation.py`
- `tests/test_health.py`
- `docs/ARCHITECTURE.md`
- `pyproject.toml`

## Nächster Entwicklungsschritt

**0.1.1-dev: Scanner-Erkennung und Testscan**

Ziele:

1. verfügbare NAPS2-Scanner über eSCL und SANE ermitteln
2. erkannte Geräte in der Web-API anzeigen
3. Scanner übernehmen/speichern
4. Testscan mit gespeichertem Scanner durchführen
5. ScanJob anlegen und Status/Fehler speichern
6. Ausgabe in einem lokalen ScanPro-Arbeitsverzeichnis ablegen

Erst danach SMB-Inbox und Web-GUI ausbauen.
