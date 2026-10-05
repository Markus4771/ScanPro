# ScanPro – Neuer Chat

## Projekt

Repository: `Markus4771/ScanPro`

Aktueller Stand: **0.2.3-dev**

## Neu in 0.2.3-dev

Profilbezogene SMB-Freigaben werden jetzt automatisch überwacht.

Beispiel:

```text
Profil: Rechnungen
Freigabe: \\SCANPRO-SERVER\Rechnungen
```

Wenn dort eine PDF abgelegt wird:

1. ScanPro erkennt die Datei.
2. ScanPro wartet auf eine stabile Dateigröße.
3. Die Datei wird dem Scanprofil zugeordnet.
4. Ein ScanJob wird erzeugt.
5. Die Datei wird nach `/var/lib/scanpro/jobs/inbox/<PROFIL-ID>/` verschoben.
6. Der Job erhält Status `imported`.
7. Profilname und Quelle `profile-smb` werden in der API ausgegeben.
8. Die PDF kann in der Weboberfläche geöffnet werden.

## Neue Komponenten

```text
scanpro/inbox_worker.py
deploy/scanpro-inbox.service
```

Neue Tabelle:

```text
inbox_imports
```

Sie speichert:

- profile_id
- scan_job_id
- source_path
- imported_path
- created_at

Neue API:

```text
GET /api/inbox-imports
```

Die bestehende Job-API liefert zusätzlich:

- profile_id
- profile_name
- source

## Worker

Systemd-Dienst:

```text
scanpro-inbox.service
```

Prüfen:

```bash
systemctl status scanpro-inbox --no-pager
journalctl -u scanpro-inbox -f
```

## Update

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
{"status":"ok","version":"0.2.3-dev"}
```

## Aktuelle Einschränkung

Der Profil-Inbox-Worker verarbeitet zunächst nur PDF-Dateien.

Noch nicht umgesetzt:

- automatische Weiterleitung an Scanziele
- Workflow-Ausführung
- OCR
- Dokumenttrennung

## Nächster Entwicklungsschritt

**0.2.4-dev – Workflows und automatische Weiterleitung**

Geplant:

1. Scanner oder Profil-SMB-Inbox als Quelle
2. Scanprofil
3. Scanziel
4. Workflow im Webinterface
5. automatische Weiterleitung an lokale Ziele
6. automatische Weiterleitung an SMB-Ziele
7. Status der Weiterleitung im ScanJob

## Einstieg in einem neuen Chat

```text
Lies bitte die Datei NEUER-CHAT.md aus meinem GitHub-Projekt Markus4771/ScanPro und führe die Entwicklung ab dem dort dokumentierten Stand weiter.
```
