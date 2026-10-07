# ScanPro 1.1-dev – Installation

ScanPro 1.1 führt WebGUI-Benutzer und persönliche SMB-Freigaben ein.

## Update / Installation

Vor jedem Update legt der Installer automatisch ein Backup der SQLite-Datenbank unter
`/var/lib/scanpro-v1/backups/` an.

```bash
cd ~/ScanPro
git pull
sudo bash scripts/install-dev.sh
```

Installiert werden u. a.:

- Python 3
- Nginx
- Samba / smbclient
- SQLite
- sudo für den eingeschränkten ScanPro-Samba-Helfer
- OCRmyPDF
- Tesseract Deutsch/Englisch

## Dienste prüfen

```bash
systemctl status scanpro --no-pager
systemctl status scanpro-inbox --no-pager
systemctl status scanpro-samba-reload.path --no-pager
```

## Health-Test

```bash
curl http://127.0.0.1:8100/health
```

Erwartet:

```json
{"status":"ok","version":"1.1.0-dev","schema_version":2}
```

## Erster Aufruf

Im Browser:

```text
http://IP-DES-SCANPRO-SERVERS/
```

Beim ersten Aufruf wird der erste Administrator angelegt.

Dabei werden zwei getrennte Kennwörter vergeben:

1. **WebGUI-Passwort** – wird nur gehasht gespeichert und ist später nicht auslesbar.
2. **SMB-Passwort** – wird für den Scanner benötigt und darf im angemeldeten Benutzerbereich sichtbar sein.

Bestehende Profile, Ziele, Scan-Eingänge und ScanJobs ohne Eigentümer werden beim Anlegen
des ersten Administrators diesem Benutzer zugeordnet.

## Benutzer und SMB

Jeder ScanPro-Benutzer erhält automatisch einen eigenen Samba-Benutzer, zum Beispiel:

```text
scanpro_u1
scanpro_u2
scanpro_u3
```

Der Administrator muss diese Linux-/Samba-Konten nicht manuell anlegen.

Ein Scan-Eingang wird in Samba beispielsweise so eingeschränkt:

```text
[Rechnungen-Markus]
    path = /var/lib/scanpro-v1/inputs/1
    read only = no
    guest ok = no
    valid users = scanpro_u1
    force user = scanpro
```

Damit kann nur der Eigentümer mit seinen persönlichen SMB-Zugangsdaten in diese Freigabe scannen.

## WebGUI-Benutzerverwaltung

Administratoren können weitere Benutzer anlegen. Für jeden Benutzer werden festgelegt:

- Benutzername
- Anzeigename
- WebGUI-Passwort
- SMB-Passwort
- Administrator ja/nein

Der Benutzer sieht nach seiner Anmeldung nur:

- seine Verarbeitungsprofile
- seine Scanziele
- seine Scan-Eingänge / SMB-Freigaben
- seine ScanJobs
- seine eigenen SMB-Zugangsdaten

## Brother-Scanner

Für einen persönlichen Scan-Eingang zeigt ScanPro beispielsweise:

```text
\\192.168.0.240\Rechnungen-Markus
Benutzer: scanpro_u1
Passwort: <sichtbares SMB-Passwort>
```

Diese drei Angaben werden am Brother als Scan-to-Network-/SMB-Profil hinterlegt.

## Datenbank

```text
/var/lib/scanpro-v1/scanpro-v1.db
```

Die SMB-Passwörter werden absichtlich lesbar in der ScanPro-Datenbank gespeichert, damit der
angemeldete Benutzer sie für die Scanner-Konfiguration anzeigen kann. Das Datenverzeichnis ist
auf dem Server entsprechend restriktiv berechtigt.
