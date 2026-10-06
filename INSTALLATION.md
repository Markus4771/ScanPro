# ScanPro 1.0-dev – Installation

Diese Anleitung gilt für den kompletten Neustart von ScanPro.

## Bestehende 0.x-Installation

Die alte Datenbank unter:

```text
/var/lib/scanpro/
```

wird nicht gelöscht.

ScanPro 1.0 verwendet stattdessen:

```text
/var/lib/scanpro-v1/
```

Der alte Quellstand ist zusätzlich im Git-Branch:

```text
archive/scanpro-0.9.2
```

gesichert.

## Update / Installation

```bash
cd ~/ScanPro
git pull
sudo bash scripts/install-dev.sh
```

Installiert werden u. a.:

- Python 3
- Nginx
- Samba
- smbclient
- SQLite
- OCRmyPDF
- Tesseract Deutsch/Englisch

## Dienste

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
{"status":"ok","version":"1.0.0-dev","schema_version":1}
```

## Samba

Einmalig Passwort für den Systembenutzer setzen:

```bash
sudo smbpasswd -a scanpro
```

Freigaben anzeigen:

```bash
smbclient -L localhost -U scanpro
```

ScanPro erzeugt die Freigaben dynamisch aus den **Scan-Eingängen**.

## Datenbank

```text
/var/lib/scanpro-v1/scanpro-v1.db
```

## Typischer Einstieg

Im Webinterface zuerst:

1. Profil `Rechnungen`
2. Ziel `Paperless`
3. Eingang `Rechnungen`

Danach erscheint z. B.:

```text
\\192.168.0.240\Rechnungen
Benutzer: scanpro
```

Diesen Pfad am Brother als Scan-to-Network-Profil hinterlegen.
