# ScanPro

ScanPro ist ein scannerunabhängiger Scan-Verarbeitungsserver.

**Aktueller Stand: 1.0.0-dev**

## Grundprinzip

```text
Scanner
  ↓
SMB-Freigabe
  ↓
Scan-Eingang
  ↓
Verarbeitungsprofil
  ↓
Scanziel
```

Der Scanner wird von ScanPro nicht aktiv gesteuert. Er muss lediglich Scan-to-SMB unterstützen.

Beispiel:

```text
Brother: "Rechnung"
  ↓
\\SCANPRO\Rechnungen
  ↓
Profil "Rechnungen"
  ↓
OCR / Dateiname
  ↓
Paperless
```

## Kernobjekte

- **Verarbeitungsprofil** – bestimmt die Verarbeitung
- **Scanziel** – Local, SMB oder Paperless
- **Scan-Eingang** – SMB-Freigabe + Profil + Ziel
- **ScanJob** – verarbeitet eine eingehende Datei

## Datenverzeichnis

```text
/var/lib/scanpro-v1/
├── scanpro-v1.db
├── inputs/
├── jobs/
├── backups/
└── samba-inputs.conf
```

Die alte 0.9.2-Version bleibt im Branch:

```text
archive/scanpro-0.9.2
```

## Installation

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
{"status":"ok","version":"1.0.0-dev","schema_version":1}
```

Einmalig Samba-Passwort setzen:

```bash
sudo smbpasswd -a scanpro
```

## Erster Test

1. Verarbeitungsprofil anlegen.
2. Scanziel anlegen.
3. Scan-Eingang anlegen.
4. Den angezeigten SMB-Pfad am Scanner als Scan-to-Network-Ziel eintragen.
5. Eine PDF scannen.
6. ScanJob im Webinterface kontrollieren.

## Aktuell umgesetzt

- neue Datenbank ohne 0.x-Migrationen
- dynamische SMB-Freigaben pro Scan-Eingang
- automatischer Inbox-Worker
- OCR für PDF über OCRmyPDF/Tesseract
- Dateinamensvorlage
- lokale Ziele
- SMB-Ziele
- Paperless-Upload
- Job- und Delivery-Protokoll
- neue reduzierte Weboberfläche
- automatische Reparatur einer leeren, veralteten `scan_jobs`-Tabelle aus frühen 1.0-dev Builds
- eindeutige Platzhalter in Profil-/Scanziel-Auswahl, solange noch nichts angelegt wurde

## Nächste Schritte

- Leerseiten wirklich verarbeiten
- Deskew/Rotation/Auto-Crop wieder sauber integrieren
- QR-/Barcode-Trennung
- verschlüsselter Secret Store
- Retention/Cleanup
- Paperless-Metadaten
- Tests und Stabilisierung
