# ScanPro 1.0-dev – Architektur

## Ziel

Scannerunabhängige Verarbeitung über SMB-Eingänge.

```text
Scanner/MFP
  ↓
SMB
  ↓
ScanInput
  ↓
ScanJob
  ↓
ProcessingProfile
  ↓
JobDocument
  ↓
Destination
  ↓
JobDelivery
```

## ScanInput

Ein ScanInput besitzt:

- Name
- SMB-Freigabename
- Dateisystempfad
- ProcessingProfile
- Destination
- enabled

Jeder aktive ScanInput erzeugt genau eine Samba-Freigabe.

## ProcessingProfile

Beschreibt ausschließlich die nachgelagerte Verarbeitung.

Scannerparameter wie DPI, Farbe und Duplex gehören nicht in ScanPro, wenn der Scanner selbst nach SMB scannt.

## Destination

Aktuell:

- local
- smb
- paperless

## Worker

`scanpro.inbox_worker` überwacht aktive Eingänge.

Eine Datei wird erst übernommen, wenn Größe und mtime in zwei Polling-Runden stabil sind.

## Datenbank

Neue Datenbank ohne Legacy-Migrationen:

```text
/var/lib/scanpro-v1/scanpro-v1.db
```

Schema 1.

## Samba

Generierte Konfiguration:

```text
/var/lib/scanpro-v1/samba-inputs.conf
```

Eine systemd Path Unit lädt Samba nach Änderungen neu.

## Altsystem

ScanPro 0.9.2 bleibt im Branch:

```text
archive/scanpro-0.9.2
```
