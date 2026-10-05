# ScanPro – Neuer Chat

## Projekt

Repository: `Markus4771/ScanPro`

Aktueller Stand: **0.2.0-dev**

## Erfolgreich vorhanden

- Brother ADS-2600We über NAPS2/SANE
- Scanner-Erkennung und Scannerverwaltung
- Scan über Weboberfläche
- ScanJobs mit PDF-Ausgabe
- Scanprofile
- OCR-/Trennoptionen im Profil konfigurierbar
- Scanziele im Webinterface

## Neu in 0.2.0-dev

### Scanziele

Unterstützte Typen:

- `local`
- `smb`

Funktionen:

- Scanziel anlegen
- bearbeiten
- aktivieren/deaktivieren
- löschen
- Verbindung testen
- doppelte Namen verhindern
- Schutz vor Löschen, wenn ein Workflow das Ziel verwendet

### Lokale Ziele

Konfiguration:

- Pfad

Verbindungstest:

- Ordner wird bei Bedarf angelegt
- temporäre Datei wird geschrieben und wieder gelöscht

### SMB-Ziele

Konfiguration:

- Server/IP
- Freigabe
- Unterordner optional
- Benutzer
- Passwort
- Domäne optional

Verbindungstest:

- über `smbclient`
- Passwort wird in API-Ausgaben maskiert

## Installation

`scripts/install-dev.sh` installiert jetzt zusätzlich:

```text
smbclient
```

Update:

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
{"status":"ok","version":"0.2.0-dev"}
```

## Wichtig

Noch nicht umgesetzt:

- automatische Weiterleitung eines ScanJobs an ein Ziel
- SMB-Inbox für Scan-to-Network
- Workflow-Ausführung
- tatsächliche OCR
- tatsächliche Dokumenttrennung

## Nächster Entwicklungsschritt

**0.2.1-dev – Workflows und Weiterleitung**

Geplant:

1. Scanner + Scanprofil + Scanziel im Webinterface zu Workflow verbinden
2. Workflow aktivieren/deaktivieren
3. Scan direkt über Workflow starten
4. lokale Ziele automatisch beschicken
5. SMB-Ziele automatisch beschicken
6. Jobstatus um Weiterleitungsstatus erweitern
7. danach SMB-Inbox

## Einstieg in einem neuen Chat

```text
Lies bitte die Datei NEUER-CHAT.md aus meinem GitHub-Projekt Markus4771/ScanPro und führe die Entwicklung ab dem dort dokumentierten Stand weiter.
```
