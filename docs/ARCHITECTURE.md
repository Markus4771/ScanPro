# ScanPro Architektur

**Stand: ScanPro 0.9.2-dev**  
**Datenbankschema: 8**

## Grundprinzip

ScanPro trennt Scannerhardware, Scanparameter, Verarbeitung und Ausgabe voneinander.

```text
Scanner / Profil-SMB-Inbox
        ↓
      ScanJob
        ↓
     ScanProfile
        ↓
Leerseiten / Trennung
        ↓
Bildoptimierung
        ↓
PDF / JPEG / PNG
        ↓
OCR bei PDF
        ↓
Dateiname / Metadaten
        ↓
      Workflow
        ↓
    Destination
```

## Scanner

Ein Scanner ist ein gespeichertes physisches Gerät.

Unterstützte Anbindung:

- NAPS2
- SANE
- eSCL
- sane-airscan
- lokale Scanner
- Netzwerk-Scanner
- VPN-/Remote-Scanner
- statische Scannerziele ohne mDNS

Pro Scanner können gespeichert werden:

- Name
- Driver
- IP/Adresse
- Device-ID
- Standort
- Verbindungstyp `local` oder `vpn`
- Timeout
- Retry-Anzahl

Remote-Ziele können statisch hinterlegt werden. Für statische SANE/AirScan-Ziele kann ScanPro pro Scanprozess `SANE_AIRSCAN_DEVICE` setzen.

## Scanner-Menüprofile

Die Tabelle:

```text
scanner_menu_entries
```

verbindet einen physischen Scanner mit einem Scanprofil.

Beim Aktivieren eines Scanner-Menüprofils wird automatisch die profilbezogene SMB-Inbox aktiviert.

Beispiel:

```text
Brother ADS-2600We
        ↓
Anzeige "Rechnung"
        ↓
\\SCANPRO\Rechnungen
        ↓
Profil Rechnungen
```

Der physische Scanner verwaltet den sichtbaren Scan-to-Network-Eintrag selbst. ScanPro liefert dazu die SMB-Zieldaten.

## Profil-SMB-Inbox

Jedes Scanprofil kann eine eigene Samba-Freigabe erhalten.

Datenmodell:

```text
profile_shares
```

Dateisystem:

```text
/var/lib/scanpro/profile-inbox/<PROFIL-ID>/
```

Der Inbox-Worker überwacht eingehende PDFs, wartet bis die Datei stabil geschrieben wurde und überführt sie in einen ScanJob.

## Scanprofile

Ein Scanprofil enthält geräteunabhängige Scan- und Verarbeitungsparameter.

Kernwerte:

- DPI
- Farbe/Graustufen/Schwarzweiß
- Duplex
- OCR
- Dokumenttrennung

Erweiterte Profileinstellungen liegen in eigenen Tabellen:

- `profile_processing`
- `profile_image_processing`
- `profile_ocr_settings`
- `profile_naming_settings`
- `profile_output_settings`
- `profile_paperless_rules`
- `profile_shares`

## Dokumenttrennung

Unterstützte Methoden:

- `none`
- `patch-t`
- `qr`
- `barcode`
- `blank-page`
- `manual`

Teildokumente werden als `job_documents` gespeichert.

QR-/Barcode-Ergebnisse werden in `job_separation_markers` gespeichert.

## Bildverarbeitung

Die Bildverarbeitung verwendet PyMuPDF, Pillow, OpenCV und Tesseract OSD.

Optional:

- Rotation
- Deskew
- Auto-Crop
- Randentfernung

Verarbeitungsergebnisse werden pro Job/Dokument protokolliert.

## OCR

OCR erfolgt mit OCRmyPDF und Tesseract.

Ergebnis:

- durchsuchbares PDF
- OCR-Text in `job_ocr_results`

Der OCR-Text kann anschließend für Dateinamen und Paperless-Regeln verwendet werden.

## Foto-/Bildmodus

Profil-Ausgabe:

```text
mode: document | photo
output_format: pdf | jpeg | png
```

JPEG/PNG werden aus dem PDF-Zwischenformat gerendert.

Bei Bildausgabe werden OCR und Dokumenttrennung deaktiviert.

## Dateinamen und Metadaten

Die Namensengine erzeugt finale Dateinamen erst vor der Auslieferung.

Variablen:

- `{date}`
- `{time}`
- `{datetime}`
- `{profile}`
- `{job}`
- `{document}`
- `{code}`
- `{code_type}`
- `{ocr_first_line}`

Dokumentmetadaten werden in `job_document_metadata` gespeichert.

## Workflows

Ein Workflow verbindet:

- optional einen Scanner
- ein Scanprofil
- ein Scanziel

Scanner-Workflows starten einen echten Scan.

Workflows ohne `scanner_id` werden als Profil-SMB-Inbox-Workflows verwendet und können beim Dateieingang automatisch gestartet werden.

## Scanziele

Aktuell:

- `local`
- `smb`
- `paperless`

Der nicht geheime Teil der Zielkonfiguration liegt in `destinations.config_json`.

## Secret Store

SMB-Passwörter und Paperless-Tokens liegen nicht im Klartext in SQLite.

Ablage:

```text
/var/lib/scanpro/secrets/
```

Verschlüsselung:

```text
cryptography / Fernet
```

SQLite speichert nur Secret-Referenzen.

Die öffentliche API gibt weder Secret-Werte noch interne Secret-Referenzen zurück.

Datenbank und Secret Store müssen gemeinsam gesichert und wiederhergestellt werden.

## Paperless-ngx

Paperless ist ein eigener Destination-Typ.

Unterstützt:

- Dokumentupload
- Titel
- Korrespondent
- Dokumenttyp
- Speicherpfad
- Tags
- Consumption-Taskstatus
- profilbezogene QR-/Barcode-Regeln
- OCR-Regeln

## Datenbank

Persistenter Pfad:

```text
/var/lib/scanpro/scanpro.db
```

SQLite-Konfiguration:

- WAL
- Foreign Keys
- Busy Timeout
- `synchronous=NORMAL`

Schema-Version:

```text
8
```

Der Installer erstellt vor Updates Datenbank- und Secret-Backups.

## Dienste

Hauptdienst:

```text
scanpro.service
```

Inbox-Worker:

```text
scanpro-inbox.service
```

Samba-Konfigurationsreload:

```text
scanpro-samba-reload.path
scanpro-samba-reload.service
```

Nginx veröffentlicht ScanPro über Port 80 und leitet intern auf Uvicorn Port 8100 weiter.

## Dateisystem

```text
/opt/scanpro/                         Anwendung
/var/lib/scanpro/scanpro.db          Datenbank
/var/lib/scanpro/jobs/               Arbeits- und Ergebnisdateien
/var/lib/scanpro/profile-inbox/      profilbezogene SMB-Eingänge
/var/lib/scanpro/secrets/            verschlüsselte Secrets
/var/lib/scanpro/backups/            Backups
/var/lib/scanpro/samba-profile-shares.conf
```

## Nächster Architekturbaustein

0.9.3-dev soll Cleanup/Retention einführen:

- Retention-Regeln
- Job- und Dateibereinigung
- Schutz noch referenzierter Dateien
- unterschiedliche Behandlung erfolgreicher und fehlerhafter Jobs
- manuelle Bereinigung über die Weboberfläche

Danach folgen Paperless Custom Fields, automatische Klassifikation, Remote Collector und Stabilisierung Richtung 1.0.


## destination_id im Scanner-Menü

Ab 0.9.2-dev kann ein `scanner_menu_entries`-Datensatz zusätzlich ein `destination_id` enthalten.

Beim Aktivieren eines Menüeintrags sorgt ScanPro dafür, dass ein passender Workflow mit:

```text
scanner_id = NULL
profile_id = <Profil>
destination_id = <Ziel>
```

existiert und aktiviert ist.

Damit werden Scans aus der profilbezogenen SMB-Inbox automatisch zum gewählten Ziel ausgeliefert.

Da die Inbox profilbezogen ist, darf dasselbe Profil nicht gleichzeitig auf verschiedene Ziele zeigen.
