# ScanPro

ScanPro ist eine modulare Linux-ScanStation für Dokumenten- und Netzwerkscanner.

**Aktueller Entwicklungsstand: 0.9.1-dev**  
**Datenbankschema: 7**

Der Brother ADS-2600We ist das erste reale Testgerät. ScanPro bleibt herstellerunabhängig und unterstützt mehrere Scanner, lokale Netze und entfernte Standorte.

## Dokumentation

- [Benutzerhandbuch](BENUTZERHANDBUCH.md)
- [Installationsanleitung](INSTALLATION.md)
- [Architektur](docs/ARCHITECTURE.md)
- [Entwicklungsübergabe / NEUER-CHAT](NEUER-CHAT.md)

## Aktuell umgesetzt

### Scanner

- NAPS2 als Scan-Engine
- SANE und eSCL
- Scanner-Erkennung
- mehrere gespeicherte Scanner
- Aktivieren/Deaktivieren
- Online-/Offline-Status
- Testscan
- Standorte
- lokale und VPN-Scanner
- Timeout und Retry pro Scanner
- statische SANE/eSCL-Ziele
- sane-airscan ohne mDNS
- Reachability-Test
- Fehlerklassen `network`, `discovery`, `scan`

### Scanner-Menüprofile

ScanPro-Profile können einem physischen Scanner als Menüprofil zugeordnet werden.

ScanPro erzeugt dafür automatisch eine profilbezogene SMB-Inbox.

Beispiel:

```text
Scanner: Brother ADS-2600We
Profil: Rechnungen
Anzeigename: Rechnung

SMB:
\\SCANPRO\Rechnungen

Benutzer:
scanpro
```

Der Brother verwaltet seine Display-Einträge selbst. Der von ScanPro erzeugte SMB-Pfad wird einmalig als Scan-to-Network-Profil im Brother-Webinterface eingetragen.

Danach kann der Benutzer direkt am Scanner beispielsweise `Rechnung`, `Lieferschein` oder `Archiv` auswählen.

API:

```text
GET /api/scanner-menu
PUT /api/scanners/{scanner_id}/menu-profile/{profile_id}
```

### Scanprofile

Profile speichern unter anderem:

- DPI
- Farbmodus
- Simplex/Duplex
- OCR
- OCR-Sprache
- Leerseitenbehandlung
- Dokumenttrennung
- Bildoptimierung
- Dateinamensregeln
- Foto-/Bildmodus
- Paperless-Regeln
- optionale Profil-SMB-Inbox

### Dokumenttrennung

Unterstützte Methoden:

- Patch-T
- QR-Code
- Barcode
- Leerseite
- manuell

Erkannte QR-/Barcode-Marker werden mit Seite, Typ und Wert gespeichert.

### Bildoptimierung

Optional pro Profil:

- automatische Rotation
- Deskew
- Auto-Crop
- Scanner-Ränder entfernen

### OCR

OCR wird mit OCRmyPDF und Tesseract ausgeführt.

Unterstützte Sprachen:

- Deutsch
- Englisch
- Deutsch + Englisch

OCR-Ergebnisse werden als durchsuchbare PDFs erzeugt und der erkannte Text wird zusätzlich gespeichert.

### Foto-/Bildscan

Profilmodus:

```text
document
photo
```

Ausgabeformate:

```text
PDF
JPEG
PNG
```

JPEG-Qualität ist konfigurierbar. Für JPEG/PNG werden OCR und Dokumenttrennung automatisch deaktiviert.

### Scanziele

Unterstützte Ziele:

- lokaler Ordner
- SMB
- Paperless-ngx

### Paperless-ngx

Unterstützt:

- API-Upload
- Korrespondent
- Dokumenttyp
- Speicherpfad
- Tags
- Taskstatus
- QR-/Barcode-Regeln
- OCR-basierte Regeln
- dynamische Titel

### Workflows

Ein Workflow verbindet:

```text
Quelle
  ↓
Scanprofil
  ↓
Scanziel
```

Als Quelle sind möglich:

- Scanner
- Profil-SMB-Inbox

Beispiel:

```text
Brother ADS-2600We
        ↓
Rechnungen
        ↓
Paperless
```

oder:

```text
Brother Display: "Rechnung"
        ↓
\\SCANPRO\Rechnungen
        ↓
Profil Rechnungen
        ↓
Paperless
```

### Secret Store

SMB-Passwörter und Paperless-API-Tokens werden nicht im Klartext in SQLite gespeichert.

Ablage:

```text
/var/lib/scanpro/secrets/
```

Verwendet wird `cryptography/Fernet`.

Dateien:

```text
master.key
destination-<ID>-smb-password.secret
destination-<ID>-paperless-token.secret
```

SQLite enthält nur interne Secret-Referenzen. Diese Referenzen werden über die öffentliche API nicht ausgegeben.

Wichtig: Datenbank und Secret Store müssen gemeinsam gesichert werden.

### Datenbank

SQLite liegt dauerhaft unter:

```text
/var/lib/scanpro/scanpro.db
```

Aktiv:

- WAL
- Foreign Keys
- Busy Timeout
- `synchronous=NORMAL`
- interne Schema-Versionierung
- Integritätsprüfung beim Update
- automatische Backups

Backups:

```text
/var/lib/scanpro/backups/
```

## Verarbeitungsablauf

```text
Scanner / Profil-SMB-Inbox
        ↓
ScanJob
        ↓
Leerseiten
        ↓
Dokumenttrennung
        ↓
Bildoptimierung
        ↓
PDF oder JPEG/PNG
        ↓
OCR bei PDF
        ↓
Dateiname / Metadaten
        ↓
Workflow
        ↓
lokal / SMB / Paperless
```

## Getestete Hardware

### Brother ADS-2600We

Erkannt und getestet über:

```text
SANE / sane-airscan
airscan:ip=192.168.0.172
```

Direkte ADF-Scans über NAPS2 wurden erfolgreich erzeugt.

### Samsung C48x Series

Wird ebenfalls über SANE/airscan erkannt.

## Wichtige API-Endpunkte

### System

```text
GET /health
GET /api/system/database
```

### Scanner

```text
GET    /api/scanners
GET    /api/scanners/status
GET    /api/scanners/discover
POST   /api/scanners/import
PATCH  /api/scanners/{scanner_id}
DELETE /api/scanners/{scanner_id}
POST   /api/scanners/{scanner_id}/testscan
POST   /api/scanners/{scanner_id}/reachability
```

Remote-/VPN-Einstellungen:

```text
GET /api/scanner-connection-settings
PUT /api/scanners/{scanner_id}/connection-settings

GET /api/scanner-static-targets
PUT /api/scanners/{scanner_id}/static-target
```

Scanner-Menüprofile:

```text
GET /api/scanner-menu
PUT /api/scanners/{scanner_id}/menu-profile/{profile_id}
```

### Profile

```text
GET /api/profiles
GET /api/profile-shares
GET /api/profile-processing
GET /api/profile-image-processing
GET /api/profile-ocr-settings
GET /api/profile-naming-settings
GET /api/profile-output-settings
GET /api/profile-paperless-rules
```

### Ziele und Workflows

```text
GET /api/destinations
GET /api/workflows
GET /api/jobs
```

## Installation / Update

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
{"status":"ok","version":"0.9.1-dev","schema_version":7}
```

## Projektpfade

```text
/opt/scanpro/                         Anwendung
/var/lib/scanpro/scanpro.db          SQLite-Datenbank
/var/lib/scanpro/jobs/               ScanJobs
/var/lib/scanpro/profile-inbox/      profilbezogene SMB-Inboxen
/var/lib/scanpro/secrets/            verschlüsselte Secrets
/var/lib/scanpro/backups/            Datenbank-/Secret-Backups
```

## Nächste Entwicklungsschritte

### 0.9.2-dev – Cleanup / Retention

Geplant:

- Aufbewahrungsregeln für ScanJobs
- temporäre PDFs und Bilder bereinigen
- unterschiedliche Regeln für erfolgreiche und fehlerhafte Jobs
- manuelle Bereinigung im Webinterface
- Schutz noch benötigter Dateien

Danach:

- Paperless Custom Fields
- automatische Dokumentklassifikation
- Remote Collector
- Stabilisierung und Tests Richtung 1.0
