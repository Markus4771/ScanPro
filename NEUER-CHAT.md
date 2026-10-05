# ScanPro – Neuer Chat

## Projekt

Repository: `Markus4771/ScanPro`

Aktueller Stand: **0.2.2-dev**

## Neu in 0.2.2-dev

Jedes Scanprofil kann optional eine eigene SMB-Freigabe auf dem ScanPro-Server erhalten.

### Beispiel

```text
Profil: Rechnungen
Freigabe: \\SCANPRO-SERVER\Rechnungen
```

Interner Pfad:

```text
/var/lib/scanpro/profile-inbox/<PROFIL-ID>
```

## Umsetzung

Neue Tabelle:

```text
profile_shares
```

Sie enthält:

- profile_id
- enabled
- share_name
- path

Neue API:

```text
GET /api/profile-shares
PUT /api/profiles/{profile_id}/share
```

Im Webinterface gibt es im Scanprofil:

- Checkbox **Eigene SMB-Freigabe auf ScanPro**
- Feld **Freigabename**

Die Freigabe kann unabhängig vom Profil aktiviert/deaktiviert werden.

## Samba

Statische ScanPro-Freigaben:

```text
ScanPro-Inbox
ScanPro-Jobs
```

Dynamische Profilfreigaben werden erzeugt in:

```text
/var/lib/scanpro/samba-profile-shares.conf
```

Diese Datei wird über:

```text
include = /var/lib/scanpro/samba-profile-shares.conf
```

in Samba eingebunden.

Ein systemd Path-Service:

```text
scanpro-samba-reload.path
```

überwacht Änderungen und lädt Samba automatisch neu.

## Installation / Update

```bash
cd ~/ScanPro
git pull
sudo bash scripts/install-dev.sh
```

Einmalig Samba-Passwort:

```bash
sudo smbpasswd -a scanpro
```

Danach prüfen:

```bash
curl http://127.0.0.1:8100/health
smbclient -L localhost -U scanpro
```

Erwartete Version:

```json
{"status":"ok","version":"0.2.2-dev"}
```

## Noch nicht umgesetzt

- automatische Verarbeitung von Dateien aus den profilbezogenen SMB-Freigaben
- Workflow-Ausführung
- automatische Weiterleitung
- echte OCR
- echte Dokumenttrennung

## Nächster Entwicklungsschritt

**Profil-SMB-Inbox-Verarbeitung**

Neue Dateien in einer Profilfreigabe sollen automatisch:

1. erkannt werden
2. dem richtigen Scanprofil zugeordnet werden
3. als ScanJob angelegt werden
4. anschließend an das konfigurierte Scanziel weiterlaufen

## Einstieg in einem neuen Chat

```text
Lies bitte die Datei NEUER-CHAT.md aus meinem GitHub-Projekt Markus4771/ScanPro und führe die Entwicklung ab dem dort dokumentierten Stand weiter.
```
