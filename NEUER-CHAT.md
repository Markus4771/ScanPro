# ScanPro – Neuer Chat

## Projekt

Repository: `Markus4771/ScanPro`

Aktueller Stand: **0.2.1-dev**

## Neu in 0.2.1-dev

ScanPro stellt nun selbst SMB-Freigaben bereit.

### Freigaben

```text
ScanPro-Inbox
ScanPro-Jobs
```

Pfade:

```text
/var/lib/scanpro/inbox
/var/lib/scanpro/jobs
```

Netzwerkzugriff:

```text
\\SCANPRO-SERVER\ScanPro-Inbox
\\SCANPRO-SERVER\ScanPro-Jobs
```

### Rechte

- `ScanPro-Inbox`: schreibbar
- `ScanPro-Jobs`: nur lesbar
- gültiger Samba-Benutzer: `scanpro`

Einmalig:

```bash
sudo smbpasswd -a scanpro
```

Das Installationsskript:

- installiert Samba und smbclient
- legt Inbox und Jobs an
- setzt Rechte
- installiert `/etc/samba/scanpro.conf`
- bindet die Datei in `/etc/samba/smb.conf` ein
- prüft Samba mit `testparm`
- aktiviert `smbd`

## Externe SMB-Ziele

Weiterhin vorhanden:

- lokale Scanziele
- externe SMB-Scanziele
- Verbindungstest über smbclient

## Noch nicht umgesetzt

- automatische Verarbeitung von Dateien aus ScanPro-Inbox
- Workflow-Ausführung
- automatische Weiterleitung
- echte OCR
- echte Dokumenttrennung

## Nächster Entwicklungsschritt

**0.2.2-dev – SMB-Inbox-Verarbeitung und Workflows**

Geplant:

1. ScanPro-Inbox überwachen
2. neue PDFs automatisch als ScanJob übernehmen
3. Eingangsprofil zuordnen
4. Scanner-/Profil-/Ziel-Workflow im Webinterface
5. lokale und SMB-Weiterleitung
6. danach Dokumenttrennung

## Update

```bash
cd ~/ScanPro
git pull
sudo bash scripts/install-dev.sh
sudo smbpasswd -a scanpro
```

Danach prüfen:

```bash
smbclient -L localhost -U scanpro
```

## Einstieg in einem neuen Chat

```text
Lies bitte die Datei NEUER-CHAT.md aus meinem GitHub-Projekt Markus4771/ScanPro und führe die Entwicklung ab dem dort dokumentierten Stand weiter.
```
