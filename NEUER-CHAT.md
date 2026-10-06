# ScanPro – Neuer Chat

## Aktueller Stand

Repository:

```text
Markus4771/ScanPro
```

Version:

```text
1.0.0-dev
```

ScanPro wurde nach 0.9.2 fachlich komplett neu gestartet.

Alter Stand:

```text
archive/scanpro-0.9.2
```

## Neue Architektur

```text
Scanner
  ↓
SMB-Freigabe
  ↓
ScanInput
  ↓
ProcessingProfile
  ↓
Destination
```

Keine Scannerverwaltung und kein NAPS2 mehr im Kern.

## Neue Datenbank

```text
/var/lib/scanpro-v1/scanpro-v1.db
```

Tabellen:

- processing_profiles
- destinations
- scan_inputs
- scan_jobs
- job_documents
- job_deliveries

Schema-Version: 1.

## Aktuell umgesetzt

- Profil-CRUD-Basis
- Ziel-CRUD-Basis
- Scan-Eingänge mit dynamischen Samba-Freigaben
- Inbox-Worker
- OCR für PDF
- Dateinamen
- Local/SMB/Paperless Delivery
- Jobanzeige

## Nächster Schritt

Die gespeicherten Profiloptionen für:

- Leerseiten
- Rotation
- Deskew
- Auto-Crop
- QR/Barcode-Trennung

müssen als echte Verarbeitungspipeline neu implementiert und getestet werden.

Danach Secret Store und Retention.

## Einstieg

```text
Lies bitte NEUER-CHAT.md aus Markus4771/ScanPro und entwickle ScanPro 1.0-dev ab diesem Stand weiter.
```
