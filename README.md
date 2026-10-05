# ScanPro

ScanPro ist eine modulare Linux-ScanStation für Dokumentenscanner.

## Entwicklungsstand

Aktuell: **0.3.0-dev**

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
