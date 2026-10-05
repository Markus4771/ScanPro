# ScanPro

ScanPro ist eine modulare Linux-ScanStation für Dokumentenscanner.

## Entwicklungsstand

Aktuell: **0.5.2-dev**

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
- erste Weboberfläche für Scanner-Erkennung, Übernahme und Testscan
- letzte ScanJobs im Browser anzeigen
- PDF direkt aus der Jobliste öffnen
- Scannerstatus online/offline anzeigen
- Scanner bearbeiten, aktivieren/deaktivieren und löschen
- Scanprofile im Webinterface anlegen, bearbeiten und löschen
- Scanprofil im Testscan auswählen und DPI/Farbe/Duplex übernehmen
- OCR- und Trennoptionen pro Profil speichern
- PDF-Datei eines Jobs über API bereitstellen
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
GET /api/scanners/status
```

Scanner übernehmen:

```text
POST /api/scanners/import
PATCH /api/scanners/{scanner_id}
DELETE /api/scanners/{scanner_id}
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
- **0.5.x** Bildoptimierung (Deskew/Begradigen), OCR und Seitenbearbeitung
- **0.6.x** Paperless-ngx und weitere Scanziele


## Scanprofile

Scanprofile können jetzt vollständig im Webinterface verwaltet werden.

Gespeicherte Werte:

- Profilname
- DPI
- Farbmodus
- Einseitig/Duplex
- OCR an/aus
- Trennung an/aus
- Trennmethode

Verfügbare Trennmethoden:

- Patch-T
- QR-Code
- Barcode
- Leerseite
- manuell

**Hinweis:** In 0.1.4-dev werden OCR- und Trenneinstellungen gespeichert und im Profil angezeigt. Die eigentliche OCR- bzw. Trennverarbeitung wird in späteren Versionen umgesetzt.


## Scanziele in 0.2.0-dev

Scanziele können jetzt im Webinterface angelegt, bearbeitet, aktiviert/deaktiviert, getestet und gelöscht werden.

Unterstützte Zieltypen:

- lokaler Ordner
- SMB-Freigabe

Für lokale Ziele wird ein echter Schreibtest durchgeführt.

Für SMB-Ziele werden gespeichert:

- Server/IP
- Freigabe
- optionaler Unterordner
- Benutzer
- Passwort
- optionale Domäne

Der Verbindungstest erfolgt mit `smbclient`.

**Wichtig:** Die automatische Weiterleitung eines fertigen Scans an ein Scanziel und die SMB-Inbox sind noch nicht aktiv. Diese folgen als nächster Entwicklungsschritt.


## SMB-Freigaben auf dem ScanPro-Server

ScanPro stellt jetzt selbst zwei Samba-Freigaben bereit:

```text
\\SCANPRO-SERVER\ScanPro-Inbox
\\SCANPRO-SERVER\ScanPro-Jobs
```

### ScanPro-Inbox

Pfad:

```text
/var/lib/scanpro/inbox
```

Die Freigabe ist schreibbar und dient später als Eingang für Scan-to-Network-Geräte.

### ScanPro-Jobs

Pfad:

```text
/var/lib/scanpro/jobs
```

Die Freigabe ist nur lesbar und ermöglicht Zugriff auf erzeugte PDF-Dateien.

Beide Freigaben verwenden den Samba-Benutzer `scanpro`. Das Samba-Passwort wird einmalig auf dem Server gesetzt:

```bash
sudo smbpasswd -a scanpro
```


## Optionale SMB-Freigabe pro Scanprofil

Jedes Scanprofil kann jetzt optional eine eigene SMB-Freigabe auf dem ScanPro-Server erhalten.

Beispiel:

```text
Profil: Rechnungen
Freigabe: \\SCANPRO-SERVER\Rechnungen
Pfad: /var/lib/scanpro/profile-inbox/<PROFIL-ID>
```

Die Option wird direkt im Scanprofil aktiviert:

- **Eigene SMB-Freigabe auf ScanPro**
- eigener Freigabename
- Freigabe kann jederzeit wieder deaktiviert werden

Die Freigabe ist schreibbar und verwendet den Samba-Benutzer `scanpro`.

Die Samba-Konfiguration wird automatisch aus den Profilen erzeugt und bei Änderungen neu geladen.


## Profil-SMB-Inbox-Verarbeitung in 0.2.3-dev

Profilbezogene SMB-Freigaben werden jetzt aktiv überwacht.

Beispiel:

```text
\\SCANPRO-SERVER\Rechnungen
```

Wird dort eine PDF abgelegt, passiert automatisch:

1. ScanPro wartet, bis die Datei stabil geschrieben wurde.
2. Die PDF wird dem zugehörigen Scanprofil zugeordnet.
3. Ein ScanJob wird angelegt.
4. Die PDF wird nach `/var/lib/scanpro/jobs/inbox/<PROFIL-ID>/` übernommen.
5. Der Job erhält den Status `imported`.
6. In der Weboberfläche erscheint Profilname + Hinweis `SMB-Inbox`.
7. Die PDF kann direkt aus der Jobliste geöffnet werden.

Aktuell werden über die Profil-Inbox zunächst PDF-Dateien verarbeitet.


## Workflows und automatische Weiterleitung in 0.2.4-dev

Workflows verbinden jetzt:

```text
Quelle → Scanprofil → Scanziel
```

Als Quelle stehen zur Verfügung:

- gespeicherter Scanner
- Profil-SMB-Inbox

Ein Scanner-Workflow kann direkt im Webinterface gestartet werden. Dabei verwendet ScanPro automatisch DPI, Farbmodus und Duplex aus dem gewählten Scanprofil.

Ein Profil-SMB-Inbox-Workflow wird automatisch gestartet, sobald eine neue PDF in der zugehörigen Profilfreigabe erkannt und importiert wurde.

Unterstützte Ziele:

- lokaler Ordner
- SMB-Freigabe

Jede Weiterleitung wird in `job_deliveries` protokolliert. Der ScanJob kann dadurch unter anderem die Status `delivered` oder `delivery_error` erhalten.


## Optionale Leerseiten-Entfernung in 0.2.5-dev

Jedes Scanprofil kann jetzt optional **Leere Seiten aussortieren** aktivieren.

Das gilt für:

- Scanner-Workflows
- profilbezogene SMB-Inboxen

ScanPro rendert die PDF-Seiten verkleinert in Graustufen und erkennt nahezu vollständig weiße Seiten. Erkannte Leerseiten werden vor der Weiterleitung aus der PDF entfernt.

Die Anzahl der entfernten Seiten wird pro ScanJob gespeichert und in der Jobliste angezeigt.

Wichtig: Die Leerseiten-Entfernung ist unabhängig von der Dokumenttrennung. Sie kann später z. B. gemeinsam mit Patch-T verwendet werden.


## Dokumenttrennung in 0.3.0-dev

ScanPro kann einen ScanJob jetzt in mehrere PDF-Dokumente zerlegen.

Unterstützte Methoden:

- **Leerseite als Trenner**
- **Patch-T** über NAPS2

Die erzeugten Teildokumente werden als eigene `job_documents` gespeichert und einzeln durch den Workflow weitergeleitet.

### Leerseite als Trenner

Bei aktiviertem Profil:

```text
Trennung aktivieren
Trennmethode: Leerseite
```

werden leere Seiten als Dokumentgrenze verwendet. Die Trennseiten selbst werden nicht in die Ausgabedokumente übernommen.

### Patch-T

Patch-T wird über NAPS2 CLI mit `--splitpatcht` ausgeführt.

Da NAPS2 Patch-Code-Unterstützung offiziell besonders für WIA/TWAIN dokumentiert, sollte Patch-T auf Linux/SANE mit dem Brother ADS-2600We praktisch getestet werden.

### Wichtig

`Leere Seiten aussortieren` und `Leerseite als Trenner` sind getrennte Funktionen.

Wenn Leerseite als Trenner aktiv ist, entfernt ScanPro die Leerseiten nicht vor der Trennung.


## Backlog: automatische Begradigung schiefer Scans

Geplant ist eine optionale **Deskew-Funktion** pro Scanprofil.

Ziel:

- schief eingezogene Seiten automatisch erkennen
- Seiten vor OCR automatisch begradigen
- optional aktivierbar pro Scanprofil
- sowohl für direkte Scanner-Workflows als auch SMB-Inbox-PDFs
- Verarbeitung nach Dokumenttrennung und vor OCR

Die Funktion soll später zusätzlich mit Seitenrotation und weiterer Bildoptimierung kombinierbar sein.


## Backlog: Bilder und Fotos scannen

ScanPro soll neben Dokumenten auch **Bilder/Fotos** als eigenen Scanmodus unterstützen.

Geplant als eigener Profiltyp bzw. Profiloption:

- Ausgabe als JPEG oder PNG
- optional weiterhin PDF
- höhere Auflösungen, z. B. 300 / 600 / 1200 dpi je nach Scanner
- Farbe als Standard
- keine Dokumenttrennung
- OCR standardmäßig aus
- optionale Bildoptimierung
- automatische Rotation
- Deskew / Begradigen
- Zuschneiden auf Bildinhalt
- optional Rand entfernen
- Dateinamenregeln für Fotos/Bilder
- direkte Ablage in lokale oder SMB-Ziele

Beispiel:

```text
Profil: Foto 600 dpi
Ausgabe: JPEG
Farbe: Farbe
Trennung: aus
OCR: aus
Deskew: optional
Ziel: \\NAS\Bilder\Scans
```


## Backlog: Scanner über VPN / entfernte Standorte

ScanPro soll Scanner unterstützen, die nicht im lokalen LAN stehen, sondern über VPN bzw. an entfernten Standorten erreichbar sind.

Geplant:

- Scanner mit Standort kennzeichnen
- Verbindungstyp `lokal` / `VPN`
- Erreichbarkeit und Online-/Offline-Status über VPN prüfen
- längere Timeouts für entfernte Scanner
- robuste Behandlung von Paketverlust und Verbindungsabbrüchen
- Retry-Logik bei temporären VPN-Problemen
- ScanJobs bei Abbruch sauber als Fehler markieren
- optional Standortname im Webinterface anzeigen
- Scanner nach Standort gruppieren
- Unterstützung für SANE/eSCL über geroutete VPN-Netze
- optional eigener Gateway-/Remote-Collector für Standorte, an denen direkte Scannerprotokolle über VPN nicht zuverlässig funktionieren

Beispiel:

```text
Scanner: Außenstelle
Standort: Filiale 1
Verbindung: VPN
IP: 192.168.50.20
Backend: SANE/eSCL
```


## QR- und Barcode-Trennung in 0.3.1-dev

ScanPro unterstützt jetzt zusätzlich:

- QR-Code als Dokumenttrenner
- Barcode als Dokumenttrenner

Die Trennerseite wird nicht in das Ausgabedokument übernommen.

Erkannte Marker werden gespeichert mit:

- Seitennummer
- Codetyp
- Codeinhalt

Diese Informationen können später für Dateinamen, Dokumenttypen oder Metadaten verwendet werden.

Technisch verwendet ScanPro `zbar` über `pyzbar`.

Unterstützte Barcode-Typen umfassen unter anderem:

- Code 128
- Code 39
- EAN-13
- EAN-8
- UPC-A
- UPC-E
- Codabar
- Interleaved 2 of 5

Die Jobliste zeigt erkannte Trenner und Fehler jetzt deutlicher an.


## Bildoptimierung in 0.4.0-dev

Scanprofile können jetzt optional folgende Bildoptimierungen aktivieren:

- **Automatische Rotation**
- **Schiefe Seiten begradigen (Deskew)**
- **Automatisch zuschneiden (Auto-Crop)**
- **Scanner-Ränder entfernen**

Die Verarbeitung erfolgt nach Leerseiten-/Dokumenttrennung und vor der Weiterleitung.

Ablauf:

```text
Scan / SMB-Eingang
→ Leerseiten-Verarbeitung
→ Dokumenttrennung
→ Rotation
→ Deskew
→ Randentfernung
→ Auto-Crop
→ später OCR
→ Scanziel
```

### Automatische Rotation

Tesseract OSD erkennt eine Seitenorientierung von 90°, 180° oder 270° und dreht die Seite automatisch.

### Deskew

OpenCV erkennt kleine Schräglagen und korrigiert sie. Extreme Winkel werden bewusst nicht automatisch korrigiert.

### Auto-Crop

ScanPro schneidet überflüssige Außenbereiche ab, verhindert aber ein aggressives Zuschneiden auf reine Textblöcke.

### Scanner-Ränder entfernen

Dunkle Scanner-/Einzugsränder am äußeren Seitenbereich können automatisch abgeschnitten werden.

Die Ergebnisse werden pro Job protokolliert, z. B. Anzahl gedrehter, begradigter oder zugeschnittener Seiten.


## OCR in 0.5.0-dev

ScanPro führt OCR jetzt tatsächlich aus und erzeugt durchsuchbare PDFs.

Pro Scanprofil kann die OCR aktiviert und die Sprache gewählt werden:

- Deutsch (`deu`)
- Englisch (`eng`)
- Deutsch + Englisch (`deu+eng`)

Die OCR läuft nach Dokumenttrennung und Bildoptimierung, aber vor der Weiterleitung an das Scanziel.

```text
Scan / SMB-Eingang
→ Leerseiten
→ Dokumenttrennung
→ Bildoptimierung
→ OCR
→ durchsuchbare PDF
→ Scanziel
```

Technisch verwendet ScanPro OCRmyPDF mit Tesseract.

Zusätzlich wird der erkannte Text pro Dokument gespeichert. Dadurch kann der OCR-Inhalt später für Dateinamen, Metadaten, Dokumentklassifikation oder Paperless-ngx verwendet werden.

OCR-Text eines Dokuments:

```text
GET /api/job-documents/{document_id}/ocr
```


## Dateinamen und Metadaten in 0.5.1-dev

ScanPro kann pro Scanprofil jetzt eine Dateinamensvorlage speichern und vor der Weiterleitung auflösen.

Standard:

```text
{date}_{profile}_{job}_{document}
```

Verfügbare Variablen:

- `{date}` – Datum
- `{time}` – Uhrzeit
- `{datetime}` – Datum + Uhrzeit
- `{profile}` – Scanprofil
- `{job}` – ScanJob-ID
- `{document}` – laufende Dokumentnummer
- `{code}` – erkannter QR-/Barcode-Inhalt
- `{code_type}` – Typ des Codes
- `{ocr_first_line}` – erste nichtleere OCR-Zeile

Beispiel:

```text
{date}_{profile}_{code}_{document}
```

kann zu:

```text
2026-10-05_Rechnungen_KUNDE4711_002.pdf
```

werden.

Die interne Arbeitsdatei bleibt unverändert. Der finale Name wird erst beim Versand an das lokale oder SMB-Ziel verwendet.

Zusätzlich speichert ScanPro pro Dokument Metadaten:

- Profil
- Job-ID
- Dokumentnummer
- QR-/Barcode-Inhalt
- QR-/Barcode-Typ
- OCR-Erstzeile
- Quelldateiname
- finaler Dateiname

API:

```text
GET /api/profile-naming-settings
PUT /api/profiles/{profile_id}/naming-settings
GET /api/job-documents/{document_id}/metadata
```

Die Jobliste zeigt den erzeugten Dateinamen an.


## Datenbank-Härtung in 0.5.2-dev

Die ScanPro-Datenbank liegt jetzt dauerhaft unter:

```text
/var/lib/scanpro/scanpro.db
```

Statt im Anwendungsverzeichnis `/opt/scanpro`.

Aktiviert sind:

- SQLite WAL-Modus
- Foreign Keys
- 30 Sekunden Busy Timeout
- `synchronous=NORMAL`
- persistenter Datenbankpfad per `SCANPRO_DATABASE_URL`
- Schema-Versionierung
- interne Migrations-Registry
- automatische Datenbanksicherung beim Update
- SQLite-Integritätsprüfung vor dem Start

Bestehende Installationen werden automatisch von:

```text
/opt/scanpro/scanpro.db
```

nach:

```text
/var/lib/scanpro/scanpro.db
```

übernommen.

Backups landen unter:

```text
/var/lib/scanpro/backups/
```

Datenbankstatus:

```text
GET /api/system/database
```
