# ScanPro Architektur

## Grundprinzip

ScanPro trennt Hardware, Scanparameter, Verarbeitung und Ausgabe voneinander.

```text
Scanner / SMB-Inbox
        |
        v
     ScanJob
        |
        v
    ScanProfile
        |
        +--> optionale Trennung
        +--> OCR (später)
        +--> Seitenbearbeitung (später)
        |
        v
      Workflow
        |
        v
   Destination
```

## Scanner

Ein Scanner ist ein konfigurierbares Gerät oder ein logischer Eingang.

Geplante Backends:

- NAPS2 + eSCL
- NAPS2 + SANE
- USB/SANE
- SMB-Inbox
- weitere Adapter später

Der Brother ADS-2600We ist das erste Testgerät, aber nicht fest im Kern verdrahtet.

## Scanprofile

Ein Profil enthält geräteunabhängige Scan- und Verarbeitungsparameter:

- DPI
- Farbe/Graustufe
- Duplex
- OCR an/aus
- Dokumenttrennung an/aus
- Trennmethode

Trennmethoden im Datenmodell:

- none
- patch-t
- qr
- barcode
- blank-page
- manual

## Scanziele

Ziele werden dynamisch gespeichert. Der typabhängige Teil liegt in `config_json`.

Vorgesehene Zieltypen:

- local
- smb
- paperless
- sftp
- webdav
- später E-Mail/DATEV-Adapter

## Workflows

Ein Workflow verbindet:

- optional einen Scanner
- ein Scanprofil
- ein Scanziel

Damit kann ein Profil scannerübergreifend wiederverwendet werden.

## Sicherheitsprinzipien

- Passwörter/API-Tokens nicht im Klartext in Repository-Dateien ablegen.
- Ziel-Credentials später über Secret Store/verschlüsselte Konfiguration verwalten.
- Scan-Jobs bekommen Zustände und Fehlerprotokollierung.
- Eingehende Dateien werden zunächst in einem kontrollierten Arbeitsbereich verarbeitet.

## 0.1.0-dev

Aktuell umgesetzt:

- FastAPI-Grundsystem
- SQLite/SQLAlchemy
- Scanner-CRUD-Basis
- Scanprofile
- Scanziele
- Workflows
- optionale Trennkonfiguration
- NAPS2-Servicegrundlage
- Health-Endpunkt

Als Nächstes:

1. Scanner-Erkennung über NAPS2
2. Testscan-Endpunkt
3. Weboberfläche
4. SMB-Inbox
5. Patch-T-Verarbeitung
