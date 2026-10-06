# ScanPro – Installation

## Status

Diese Anleitung gilt für **ScanPro 0.9.2-dev** auf Debian 13.

## Voraussetzungen

- Debian 13
- Root- oder sudo-Zugriff
- Netzwerkzugriff auf die Scanner
- Internetzugang
- Python 3.11 oder neuer
- Git
- Nginx
- SANE-Werkzeuge
- NAPS2 für Linux

## System vorbereiten

```bash
sudo apt update
sudo apt install -y \
  git \
  curl \
  wget \
  ca-certificates \
  python3 \
  python3-venv \
  python3-pip \
  nginx \
  samba \
  sane-utils
```

## NAPS2 installieren

NAPS2 wird als Scan-Engine verwendet und muss aktuell noch separat installiert werden.

Danach prüfen:

```bash
naps2 --version
```

Scanner über SANE suchen:

```bash
naps2 console --listdevices --driver sane
```

Scanner über eSCL suchen:

```bash
naps2 console --listdevices --driver escl
```

Wichtig: Unter Linux verwendet ScanPro den Befehl `naps2 console`, nicht `naps2.console`.

## Scanner-Verbindung prüfen

```bash
scanimage -L
```

Beim Brother ADS-2600We wurde erfolgreich getestet:

```text
Brother ADS-2600We (airscan:ip=192.168.0.172)
```

Direkter Testscan:

```bash
mkdir -p ~/scantest

naps2 console \
  -o ~/scantest/testscan.pdf \
  --noprofile \
  --driver sane \
  --device "Brother ADS-2600We" \
  --source feeder \
  --dpi 300 \
  --bitdepth color \
  --pagesize a4 \
  -v
```

## Repository klonen

```bash
git clone https://github.com/Markus4771/ScanPro.git
cd ScanPro
```

## Entwicklungsinstallation

```bash
sudo bash scripts/install-dev.sh
```

Das Skript:

- installiert die ScanPro-Grundabhängigkeiten
- legt den Systembenutzer `scanpro` an
- kopiert ScanPro nach `/opt/scanpro`
- erstellt eine Python-Virtualenv
- installiert die Python-Abhängigkeiten
- legt `/var/lib/scanpro/jobs` an
- setzt die benötigten Rechte
- installiert den systemd-Dienst
- richtet Nginx auf Port 80 ein
- startet bzw. aktualisiert ScanPro
- prüft, ob NAPS2 vorhanden ist

NAPS2 selbst wird derzeit noch nicht automatisch installiert.

## ScanPro prüfen

```bash
systemctl status scanpro --no-pager
```

```bash
curl http://127.0.0.1:8100/health
```

Erwartete Antwort:

```json
{"status":"ok","version":"0.9.2-dev","schema_version":8}
```

## Scanner über ScanPro suchen

```bash
curl "http://127.0.0.1:8100/api/scanners/discover?driver=sane"
```

Die Antwort sollte den Brother ADS-2600We und weitere von NAPS2 erkannte SANE-Geräte enthalten.

## Scanner speichern

Beispiel für den Brother:

```bash
curl -X POST http://127.0.0.1:8100/api/scanners/import \
  -H "Content-Type: application/json" \
  -d '{
    "name":"Brother ADS-2600We",
    "driver":"sane",
    "address":"192.168.0.172",
    "device_id":"airscan:ip=192.168.0.172"
  }'
```

Danach gespeicherte Scanner anzeigen:

```bash
curl http://127.0.0.1:8100/api/scanners
```

## Testscan über ScanPro

Zuerst die Scanner-ID aus `/api/scanners` ermitteln.

Beispiel mit Scanner-ID 1:

```bash
curl -X POST http://127.0.0.1:8100/api/scanners/1/testscan \
  -H "Content-Type: application/json" \
  -d '{
    "dpi":300,
    "duplex":false,
    "color_mode":"color"
  }'
```

Vor dem Aufruf ein Blatt in den ADF legen.

Erfolgreiche Testscans werden gespeichert unter:

```text
/var/lib/scanpro/jobs/
```

Jobs anzeigen:

```bash
curl http://127.0.0.1:8100/api/jobs
```

## Nginx

ScanPro sollte zusätzlich über Port 80 erreichbar sein:

```text
http://<IP-DES-SCANPRO-SERVERS>/
```

## Update

```bash
cd ~/ScanPro
git pull
sudo bash scripts/install-dev.sh
```

## Logs

```bash
journalctl -u scanpro -f
```

## Verzeichnisstruktur

```text
/opt/scanpro/           Anwendung
/var/lib/scanpro/jobs/  erzeugte ScanJobs/PDFs
```

Die SQLite-Datenbank liegt ab 0.5.2-dev unter `/var/lib/scanpro/scanpro.db`. Vor Updates erstellt das Installationsskript automatisch eine Sicherung unter `/var/lib/scanpro/backups/`.

## Aktueller Funktionsstand

ScanPro 0.9.1-dev enthält bereits Scannerverwaltung, Weboberfläche, SMB-Inboxen, Workflows, Dokumenttrennung, Bildoptimierung, OCR, Paperless-Integration, Foto-/Bildscan, Remote-/VPN-Scanner, Secret Store und Scanner-Menüprofile.

Der nächste geplante Entwicklungsschritt ist **0.9.3-dev – Cleanup / Retention**.


## Weboberfläche

Nach dem Update ist ScanPro direkt im Browser erreichbar:

```text
http://<IP-DES-SCANPRO-SERVERS>/
```

Die Weboberfläche bietet aktuell:

- Scanner über SANE oder eSCL suchen
- erkannte Scanner übernehmen
- gespeicherte Scanner anzeigen
- Testscan starten
- DPI wählen
- Farbe/Graustufen/Schwarzweiß wählen
- Einseitig/Duplex wählen
- letzte ScanJobs anzeigen

## Update auf 0.2.3-dev

```bash
cd ~/ScanPro
git pull
sudo bash scripts/install-dev.sh
```

Danach Browser neu laden.


## Neue Funktionen in 0.1.3-dev

- Online-/Offline-Status gespeicherter Scanner
- Scanner bearbeiten
- Scanner aktivieren/deaktivieren
- Scanner löschen
- kompakte Scan-Ergebnisanzeige
- PDF direkt aus der Jobliste öffnen
- verbesserte ScanJob-Liste


## Scanprofile in 0.1.4-dev

Im Webinterface können jetzt Scanprofile angelegt und verwaltet werden.

Ein Profil speichert:

- DPI
- Farbmodus
- Einseitig/Duplex
- OCR an/aus
- Trennung an/aus
- Trennmethode

Das Profil kann anschließend im Bereich **Testscan** ausgewählt werden. DPI, Farbmodus und Einzug werden automatisch übernommen.

OCR und Dokumenttrennung sind in 0.1.4-dev zunächst Konfigurationswerte. Die eigentliche Verarbeitung folgt in späteren Entwicklungsstufen.


## Scanziele in 0.2.0-dev

Das Installationsskript installiert zusätzlich:

```text
smbclient
```

Dadurch kann ScanPro SMB-Ziele direkt testen.

### Lokales Ziel

Beispiel:

```text
/srv/scans/archiv
```

Der Verbindungstest prüft, ob der Ordner angelegt und beschrieben werden kann.

### SMB-Ziel

Beispiel:

```text
Server: 192.168.0.20
Freigabe: Scans
Unterordner: Eingang
Benutzer: scanpro
```

Die Verbindung kann direkt im Webinterface über **Verbindung testen** geprüft werden.

Hinweis: Die automatische Weiterleitung eines Scans an das Ziel ist in 0.2.0-dev noch nicht aktiv.


## SMB-Freigaben auf dem ScanPro-Server

Ab 0.2.1-dev richtet das Installationsskript Samba automatisch ein.

Es werden folgende Verzeichnisse angelegt:

```text
/var/lib/scanpro/inbox
/var/lib/scanpro/jobs
```

und folgende Freigaben bereitgestellt:

```text
\\SCANPRO-SERVER\ScanPro-Inbox
\\SCANPRO-SERVER\ScanPro-Jobs
```

### Einmalig Samba-Passwort setzen

Nach Installation oder Update:

```bash
sudo smbpasswd -a scanpro
```

Danach Samba prüfen:

```bash
sudo testparm -s
sudo systemctl status smbd --no-pager
```

Freigaben lokal anzeigen:

```bash
smbclient -L localhost -U scanpro
```

### Rechte

`ScanPro-Inbox` ist schreibbar.

`ScanPro-Jobs` ist nur lesbar.

Damit kann ein Netzwerk-Scanner direkt nach:

```text
\\IP-DES-SCANPRO-SERVERS\ScanPro-Inbox
```

scannen.


## Optionale SMB-Freigabe je Scanprofil

Ab 0.2.2-dev kann jedes Scanprofil eine eigene SMB-Freigabe bekommen.

Beispiel:

```text
Scanprofil: Rechnungen
SMB-Freigabe: Rechnungen
Netzwerkpfad: \\IP-DES-SCANPRO-SERVERS\Rechnungen
```

Im Webinterface beim Scanprofil:

1. **Eigene SMB-Freigabe auf ScanPro** aktivieren
2. Freigabenamen eintragen
3. Profil speichern

ScanPro erzeugt dann automatisch den Profilordner unter:

```text
/var/lib/scanpro/profile-inbox/<PROFIL-ID>
```

Die dynamische Samba-Konfiguration liegt unter:

```text
/var/lib/scanpro/samba-profile-shares.conf
```

Ein systemd Path-Service überwacht diese Datei und lädt Samba bei Änderungen automatisch neu.

Prüfen:

```bash
systemctl status scanpro-samba-reload.path --no-pager
sudo testparm -s
smbclient -L localhost -U scanpro
```


## Profil-SMB-Inbox-Worker

Ab 0.2.3-dev läuft zusätzlich:

```text
scanpro-inbox.service
```

Status prüfen:

```bash
systemctl status scanpro-inbox --no-pager
```

Logs:

```bash
journalctl -u scanpro-inbox -f
```

### Funktion testen

1. Im Webinterface ein Scanprofil mit eigener SMB-Freigabe anlegen.
2. Freigaben prüfen:

```bash
smbclient -L localhost -U scanpro
```

3. Eine PDF in die Profilfreigabe kopieren, z. B.:

```text
\\IP-DES-SCANPRO-SERVERS\Rechnungen
```

4. Nach wenigen Sekunden im Webinterface die ScanJob-Liste aktualisieren.

Der neue Job sollte den Status:

```text
imported
```

und den Profilnamen anzeigen.

Die importierte Datei liegt anschließend unter:

```text
/var/lib/scanpro/jobs/inbox/<PROFIL-ID>/
```

Der Worker verarbeitet aktuell PDF-Dateien.


## Workflows in 0.2.4-dev

Im Webinterface steht jetzt der Bereich **Workflows** zur Verfügung.

Ein Workflow verbindet:

```text
Quelle → Scanprofil → Scanziel
```

### Scanner als Quelle

Beispiel:

```text
Brother ADS-2600We → Rechnung → NAS-Rechnungen
```

Der Workflow kann über **Workflow starten** ausgelöst werden.

### Profil-SMB-Inbox als Quelle

Beispiel:

```text
\\SCANPRO\Rechnungen → Profil Rechnung → NAS-Rechnungen
```

Dieser Workflow startet automatisch, sobald eine PDF in der Profilfreigabe angekommen ist.

### Weiterleitungsstatus

Die Jobliste zeigt zusätzlich den Versandstatus an.

Mögliche Zustände:

```text
delivered
delivery_error
```

Bei lokalen Zielen wird die PDF kopiert. Bei SMB-Zielen erfolgt die Übertragung mit `smbclient put`.


## Leere Seiten automatisch entfernen

Ab 0.2.5-dev gibt es im Scanprofil die Option:

```text
Leere Seiten aussortieren
```

Ist sie aktiviert, verarbeitet ScanPro die PDF vor der Weiterleitung.

Unterstützt werden:

- Scans aus Scanner-Workflows
- PDFs aus Profil-SMB-Inboxen

Die PDF-Verarbeitung verwendet PyMuPDF.

Nach einem verarbeiteten Job zeigt die Jobliste an, wie viele Leerseiten entfernt wurden.


## Dokumenttrennung testen

### Leerseite als Trenner

Im Scanprofil einstellen:

```text
Trennung aktivieren: ja
Trennmethode: Leerseite
```

Dann einen Teststapel scannen:

```text
Dokument 1
Leerseite
Dokument 2
Leerseite
Dokument 3
```

In der Jobliste sollten anschließend mehrere Dokumente erscheinen:

```text
Dok. 1
Dok. 2
Dok. 3
```

### Patch-T

Im Profil:

```text
Trennung aktivieren: ja
Trennmethode: Patch-T
```

Für Patch-T möglichst mit mindestens 300 dpi scannen.

Patch-T wird über NAPS2 `--splitpatcht` verarbeitet und muss unter Linux/SANE praktisch geprüft werden.

Die erzeugten Dokumente liegen unter:

```text
/var/lib/scanpro/jobs/documents/<JOB-ID>/
```


## QR-/Barcode-Trennung testen

Im Scanprofil:

```text
Trennung aktivieren: ja
Trennmethode: QR-Code
```

oder:

```text
Trennung aktivieren: ja
Trennmethode: Barcode
```

Ein Teststapel kann beispielsweise so aussehen:

```text
Dokument 1
QR-Trennblatt
Dokument 2
QR-Trennblatt
Dokument 3
```

Die Trennerseiten selbst werden verworfen.

Die Jobliste zeigt:

- Anzahl erzeugter Dokumente
- erkannte Trenner
- Seite des Trenners
- Typ und Inhalt des Codes

Das Installationsskript installiert dafür zusätzlich:

```text
libzbar0
```


## Bildoptimierung testen

Ab 0.4.0-dev stehen im Scanprofil folgende Optionen zur Verfügung:

```text
Automatische Rotation
Schiefe Seiten begradigen
Automatisch zuschneiden
Scanner-Ränder entfernen
```

Die Installation bringt dafür zusätzlich mit:

```text
tesseract-ocr
tesseract-ocr-osd
opencv-python-headless
pytesseract
```

Empfohlener Test:

1. Scanprofil öffnen.
2. **Schiefe Seiten begradigen** aktivieren.
3. Eine leicht schief eingelegte Seite scannen.
4. Jobliste prüfen.
5. Dort sollte bei erkannter Korrektur z. B. `begradigt: 1` erscheinen.

Für die automatische Rotation sollte eine Seite testweise um 90° verdreht eingelegt werden.


## OCR testen

Ab 0.5.0-dev kann OCR direkt im Scanprofil aktiviert werden.

```text
OCR aktivieren: ja
OCR-Sprache: Deutsch
```

Installierte Komponenten:

```text
ocrmypdf
tesseract-ocr
tesseract-ocr-deu
tesseract-ocr-eng
```

Empfohlener Test:

1. Profil mit OCR aktivieren.
2. Sprache `Deutsch` wählen.
3. Textdokument scannen.
4. PDF öffnen.
5. Text im PDF markieren oder suchen.
6. Jobliste prüfen.

OCR-Text kann zusätzlich über:

```text
/api/job-documents/<DOKUMENT-ID>/ocr
```

abgerufen werden.


## Dateinamensregeln testen

Ab 0.5.1-dev kann jedes Scanprofil eine Dateinamensvorlage verwenden.

Standard:

```text
{date}_{profile}_{job}_{document}
```

Weitere Variablen:

```text
{time}
{datetime}
{code}
{code_type}
{ocr_first_line}
```

Beispiel für QR-Trennung:

```text
{date}_{profile}_{code}_{document}
```

Beispiel mit OCR:

```text
{date}_{ocr_first_line}_{document}
```

Dafür im Profil zusätzlich aktivieren:

```text
OCR-Erstzeile für {ocr_first_line} verwenden
```

Die finalen Dateinamen werden beim Versand an lokale oder SMB-Ziele angewendet.

Metadaten eines erzeugten Dokuments:

```text
/api/job-documents/<DOKUMENT-ID>/metadata
```


## Datenbank nach Update prüfen

Ab 0.5.2-dev:

```bash
curl http://127.0.0.1:8100/api/system/database
```

Erwartet ungefähr:

```json
{
  "database_url":"sqlite:////var/lib/scanpro/scanpro.db",
  "path":"/var/lib/scanpro/scanpro.db",
  "schema_version":1,
  "target_schema_version":1,
  "journal_mode":"wal",
  "foreign_keys":true
}
```

Datei prüfen:

```bash
ls -lh /var/lib/scanpro/scanpro.db
ls -lh /var/lib/scanpro/backups/
```

SQLite direkt prüfen:

```bash
sudo -u scanpro sqlite3 /var/lib/scanpro/scanpro.db 'PRAGMA integrity_check;'
sudo -u scanpro sqlite3 /var/lib/scanpro/scanpro.db 'PRAGMA journal_mode;'
```

Erwartet:

```text
ok
wal
```

Beim ersten Update von einer älteren Version wird eine vorhandene Datenbank aus:

```text
/opt/scanpro/scanpro.db
```

automatisch übernommen.


## Paperless-ngx als Scanziel

Ab 0.6.0-dev kann Paperless-ngx direkt als Scanziel verwendet werden.

Im Webinterface:

1. **Scanziele**
2. **Neues Ziel**
3. Typ **Paperless-ngx**
4. Paperless-URL eintragen
5. API-Token eintragen
6. Ziel speichern
7. **Verbindung testen**

Beispiel:

```text
Name: Paperless Archiv
Typ: Paperless-ngx
URL: https://paperless.example.local
API-Token: <TOKEN>
TLS-Zertifikat prüfen: ja
```

Optional können Paperless-interne IDs gesetzt werden:

```text
Korrespondent-ID
Dokumenttyp-ID
Speicherpfad-ID
Tag-IDs
```

Tag-IDs werden kommasepariert eingegeben:

```text
2,5,9
```

Danach kann das Paperless-Ziel wie ein lokales oder SMB-Ziel in einem Workflow ausgewählt werden.

Der Upload wird von Paperless asynchron verarbeitet. Ein erfolgreicher HTTP-Upload bedeutet, dass Paperless die Verarbeitung gestartet hat; die zurückgegebene Task-ID wird von ScanPro gespeichert.


## Paperless-Regeln testen

Ab 0.6.1-dev können Paperless-Metadaten pro Scanprofil geregelt werden.

Im Profil stehen zur Verfügung:

```text
Paperless-Titelvorlage
QR-/Barcode → Korrespondent
QR-/Barcode → Dokumenttyp
QR-/Barcode → Tags
OCR-Enthält-Regeln
```

Beispiel Titel:

```text
{profile}_{code}_{document}
```

Beispiel Dokumenttyp-Mapping:

```json
{"RECHNUNG":3}
```

Beispiel OCR-Regel:

```json
[{"contains":"Telekom","correspondent":4,"document_type":3,"tags":[2]}]
```

Beim Paperless-Ziel kann nach dem Speichern über **Paperless-Werte laden** auf Korrespondenten, Dokumenttypen und Speicherpfade zugegriffen werden.

Nach einem Upload kann in der Jobliste über **Paperless-Status** der Consumption-Task geprüft werden.


## Foto-/Bildscan testen

Ab 0.7.0-dev:

1. Neues Scanprofil anlegen.
2. Profilmodus **Foto / Bild** wählen.
3. Ausgabeformat **JPEG** oder **PNG** wählen.
4. Auflösung z. B. 600 dpi wählen.
5. Optional Auto-Crop oder Randentfernung aktivieren.
6. Profil speichern.
7. Workflow mit lokalem oder SMB-Ziel starten.

Bei JPEG kann zusätzlich die Qualität eingestellt werden, z. B.:

```text
92
```

Bei JPEG/PNG werden OCR und Dokumenttrennung automatisch deaktiviert.

Mehrseitige Scans werden zu:

```text
..._001.jpg
..._002.jpg
..._003.jpg
```

bzw. PNG-Dateien.

Hinweis: 1200 dpi funktioniert nur, wenn der verwendete Scanner diese Auflösung über SANE/eSCL tatsächlich unterstützt.


## VPN-/Remote-Scanner testen

Ab 0.8.0-dev kann jeder Scanner einem Standort und Verbindungstyp zugeordnet werden.

Im Webinterface beim Scanner auf **Bearbeiten**:

```text
Standort: Außenstelle
Verbindungstyp: vpn
Scan-Timeout: 120
Wiederholungen: 2
```

Danach **Erreichbarkeit testen** verwenden.

Alternativ per API:

```bash
curl -X PUT http://127.0.0.1:8100/api/scanners/1/connection-settings \
  -H "Content-Type: application/json" \
  -d '{
    "location":"Außenstelle",
    "connection_type":"vpn",
    "timeout_seconds":120,
    "retries":2
  }'
```

Reachability:

```bash
curl -X POST http://127.0.0.1:8100/api/scanners/1/reachability
```

Hinweis zu VPN und mDNS:

Geroutete WireGuard-/IPsec-Verbindungen übertragen mDNS normalerweise nicht. Wenn ein AirScan/eSCL-Gerät deshalb nicht automatisch gefunden wird, muss der Scanner über eine statische SANE/eSCL-Konfiguration erreichbar gemacht werden.

Der Erreichbarkeitstest ersetzt diese Scanner-Konfiguration nicht; er prüft nur, ob das entfernte Gerät über typische TCP-Ports erreichbar ist.


## Statischen Remote-Scanner konfigurieren

Ab 0.8.1-dev kann ein Scanner ohne mDNS als statisches Ziel hinterlegt werden.

Im Webinterface:

1. Scanner **Bearbeiten**
2. Standort und VPN-Einstellungen setzen
3. **Statisches Remote-Ziel verwenden** bestätigen
4. Driver `sane`
5. Gerätename setzen
6. IP oder vollständige eSCL-URL eintragen

Beispiel IP:

```text
10.20.30.40
```

ScanPro erzeugt daraus intern:

```text
http://10.20.30.40/eSCL
```

Oder direkt:

```text
http://10.20.30.40:8080/eSCL
```

API-Beispiel:

```bash
curl -X PUT http://127.0.0.1:8100/api/scanners/1/static-target \
  -H "Content-Type: application/json" \
  -d '{
    "enabled":true,
    "driver":"sane",
    "device_name":"Brother Außenstelle",
    "device_id":"",
    "address":"10.20.30.40"
  }'
```

Fehlerzustände werden getrennt ausgewiesen:

```text
network
discovery
scan
```

Die Scannerliste kann nach Standort gefiltert werden.


## Secret Store prüfen

Ab 0.9.0-dev werden SMB-Passwörter und Paperless-Tokens verschlüsselt gespeichert.

Verzeichnis prüfen:

```bash
sudo ls -lah /var/lib/scanpro/secrets
```

Erwartet nach dem ersten gespeicherten Secret:

```text
master.key
destination-1-smb-password.secret
```

oder:

```text
destination-2-paperless-token.secret
```

Rechte prüfen:

```bash
sudo stat -c '%a %U:%G %n' /var/lib/scanpro/secrets /var/lib/scanpro/secrets/master.key
```

Erwartet:

```text
700 scanpro:scanpro /var/lib/scanpro/secrets
600 scanpro:scanpro /var/lib/scanpro/secrets/master.key
```

Prüfen, dass keine Klartext-Secrets mehr in SQLite liegen:

```bash
sudo -u scanpro sqlite3 /var/lib/scanpro/scanpro.db \
  "SELECT id,name,type,config_json FROM destinations;"
```

Bei SMB/Paperless sollte dort nur noch eine Secret-Referenz stehen, nicht Passwort oder Token.

### Backup

Der Installer legt beim Update eine Sicherung an:

```text
/var/lib/scanpro/backups/scanpro-secrets-<ZEITSTEMPEL>.tar.gz
```

Für eine Wiederherstellung müssen **Datenbank und Secret Store zusammen** zurückgespielt werden.

Ohne `master.key` können bestehende Secret-Dateien nicht entschlüsselt werden.


## Scanner-Menüprofile / Brother Scan-to-Network

Ab 0.9.1-dev können ScanPro-Profile für einen Scanner als Menüprofil vorbereitet werden.

Im ScanPro-Webinterface:

1. **Scanner-Menüprofile** öffnen.
2. Scanner auswählen.
3. Scanprofil auswählen.
4. Anzeigenamen festlegen, z. B. `Rechnung`.
5. **Am Scanner anzeigen** wählen.

ScanPro aktiviert automatisch eine eigene SMB-Inbox für dieses Profil.

Danach zeigt ScanPro z. B.:

```text
\\scanpro\Rechnungen
Benutzer: scanpro
```

Diesen Pfad einmalig im Brother ADS-2600We als Scan-to-Network-/Netzwerk-Profil hinterlegen.

Wichtig: Das Samba-Passwort des Benutzers `scanpro` muss gesetzt sein:

```bash
sudo smbpasswd -a scanpro
```

Danach kann der Benutzer das Profil direkt am Scanner auswählen. Die eingehende PDF wird von ScanPro automatisch dem zugehörigen Scanprofil zugeordnet und weiterverarbeitet.


## Prüfung Scanner-Menüprofile nach dem Update

Scanner-Menüprofile anzeigen:

```bash
curl http://127.0.0.1:8100/api/scanner-menu
```

Profil-SMB-Freigaben prüfen:

```bash
curl http://127.0.0.1:8100/api/profile-shares
```

Samba-Konfiguration prüfen:

```bash
sudo testparm -s
smbclient -L localhost -U scanpro
```

Für einen Brother ADS-2600We wird der von ScanPro angezeigte SMB-Pfad anschließend einmalig als Scan-to-Network-Profil am Gerät hinterlegt.

## Nächster Entwicklungsschritt

**0.9.2-dev – Cleanup / Retention**

Geplant:

- Aufbewahrungsregeln für Jobs
- automatische Bereinigung temporärer PDFs/Bilder
- unterschiedliche Regeln für erfolgreiche und fehlerhafte Jobs
- manuelle Bereinigung im Webinterface
- Schutz noch benötigter Dateien

Danach folgen Paperless Custom Fields, automatische Dokumentklassifikation, Remote Collector und Stabilisierung Richtung 1.0.


## Mehrere Brother-Menüprofile mit unterschiedlichen Zielen

Im Bereich **Scanner-Menüprofile** werden ab 0.9.2-dev vier Werte gewählt:

```text
Scanner
Scanprofil
Scanziel
Anzeigename am Scanner
```

Beispiel:

```text
Brother ADS-2600We
Profil: Rechnungen
Ziel: Paperless
Anzeigename: Rechnung
```

Danach **Am Scanner anzeigen**.

ScanPro erzeugt automatisch die passende Profil-SMB-Inbox und einen aktiven Inbox-Workflow zum gewählten Scanziel.

Für weitere Einträge werden weitere Scanprofile verwendet, z. B.:

```text
Rechnungen → Paperless
Lieferscheine → NAS
Archiv → SMB-Archiv
Foto → Foto-Archiv
```

Dasselbe Scanprofil kann technisch nicht gleichzeitig auf unterschiedliche Ziele zeigen, weil seine SMB-Inbox den absendenden Scanner nicht unterscheiden kann.
