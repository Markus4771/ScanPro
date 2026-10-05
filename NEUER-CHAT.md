# ScanPro – Neuer Chat

## Projekt

Repository: `Markus4771/ScanPro`

Aktueller Stand: **0.1.0-dev**

ScanPro wird als neue Linux-ScanStation von Grund auf entwickelt. Das frühere OpenScanStation-Projekt wird nicht als Codebasis verwendet.

## Ziel

Eine stabile, modular aufgebaute ScanStation für Linux mit mehreren konfigurierbaren Scannern, Scanprofilen, Scanzielen und Workflows.

## Anforderungen

- Debian als Zielsystem
- NAPS2 als Scan-Engine
- mehrere Scanner konfigurierbar
- erster Testscanner: Brother ADS-2600We
- eSCL und SANE als erste Scanner-Anbindungen
- zusätzlicher SMB-Eingang für Scan-to-Network-Geräte
- Scanprofile konfigurierbar
- Scanziele konfigurierbar
- Workflows konfigurierbar
- Dokumenttrennung optional
- Trennung je Profil bzw. Workflow aktivierbar
- geplante Trennmethoden:
  - Patch-T
  - QR-Code
  - Barcode
  - Leerseite
  - manuell
- später OCR
- Vorschau und Seitenbearbeitung
- Paperless-ngx
- weitere Ziel-Adapter

## Architekturentscheidung

Scanner, Scanprofile, Scanziele und Workflows bleiben voneinander getrennt.

Ein Scanner ist nicht fest an ein Ziel gebunden. Ein Scanprofil kann später von mehreren Scannern verwendet werden.

## Bereits vorhanden

- `README.md`
- `INSTALLATION.md`
- `NEUER-CHAT.md`
- `docs/ARCHITECTURE.md`
- `pyproject.toml`
- `scanpro/main.py`
- `scanpro/db.py`
- `scanpro/models.py`
- `scanpro/schemas.py`
- `scanpro/services/naps2.py`
- `scanpro/services/separation.py`
- `tests/test_health.py`
- `scripts/install-dev.sh`
- systemd- und Nginx-Vorlagen

## Bereits im Datenmodell

- Scanner
- ScanProfile
- Destination
- Workflow
- ScanJob

## Aktuelle Trennmethoden im Modell

- `none`
- `patch-t`
- `qr`
- `barcode`
- `blank-page`
- `manual`

## Nächster Entwicklungsschritt

**0.1.1-dev – Scanner-Erkennung und Testscan**

1. NAPS2-Geräte über eSCL erkennen
2. NAPS2-Geräte über SANE erkennen
3. erkannte Scanner über die API anzeigen
4. Scanner in ScanPro übernehmen und speichern
5. Testscan mit gespeichertem Scanner auslösen
6. ScanJob anlegen
7. Status und Fehler speichern
8. PDF in ScanPro-Arbeitsverzeichnis ablegen

Danach:

- erste Weboberfläche für Scannerverwaltung
- SMB-Inbox
- Patch-T-Trennung

## Einstieg in einem neuen Chat

Den nächsten Chat mit folgendem Auftrag starten:

```text
Lies bitte die Datei NEUER-CHAT.md aus meinem GitHub-Projekt Markus4771/ScanPro und führe die Entwicklung ab dem dort dokumentierten Stand weiter.
```
