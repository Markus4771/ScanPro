# ScanPro – Neuer Chat

## Projekt

Repository: `Markus4771/ScanPro`

Aktueller Stand: **0.2.4-dev**

## Neu in 0.2.4-dev

Workflows und automatische Weiterleitung sind umgesetzt.

## Workflow-Modell

```text
Quelle → Scanprofil → Scanziel
```

Quellen:

- Scanner
- Profil-SMB-Inbox

Ziele:

- lokaler Ordner
- SMB-Freigabe

## Scanner-Workflow

Ein Workflow mit `scanner_id` kann im Webinterface über **Workflow starten** ausgeführt werden.

Ablauf:

1. Scanner starten
2. Profilwerte verwenden
3. PDF erzeugen
4. PDF an Ziel weiterleiten
5. Delivery speichern
6. Jobstatus setzen

## SMB-Inbox-Workflow

Ein Workflow ohne `scanner_id` gilt als Profil-SMB-Inbox-Workflow.

Ablauf:

1. PDF kommt in Profilfreigabe an
2. Inbox-Worker importiert PDF
3. passende aktive Workflows für das Profil werden gesucht
4. PDF wird automatisch an die konfigurierten Ziele weitergeleitet
5. jeder Versand wird protokolliert

## Neue Delivery-Tabelle

```text
job_deliveries
```

Felder:

- scan_job_id
- workflow_id
- destination_id
- status
- target_path
- error
- created_at

## Workflow-API

```text
GET    /api/workflows
POST   /api/workflows
PATCH  /api/workflows/{workflow_id}
DELETE /api/workflows/{workflow_id}
POST   /api/workflows/{workflow_id}/run
```

## Status

Weiterleitungsstatus:

```text
delivered
delivery_error
```

## Update

```bash
cd ~/ScanPro
git pull
sudo bash scripts/install-dev.sh
```

Prüfen:

```bash
curl http://127.0.0.1:8100/health
systemctl status scanpro --no-pager
systemctl status scanpro-inbox --no-pager
```

Erwartet:

```json
{"status":"ok","version":"0.2.4-dev"}
```

## Noch nicht umgesetzt

- OCR-Ausführung
- Dokumenttrennung
- QR-/Barcode-Erkennung
- Dateinamenregeln und Metadaten
- Paperless-ngx

## Nächster Entwicklungsschritt

**0.3.0-dev – Dokumenttrennung**

Geplant:

1. Leerseiten-Trennung
2. Patch-T-Erkennung
3. mehrere Dokumente aus einem ScanJob
4. Trennung abhängig vom Scanprofil
5. danach QR-/Barcode-Trennung
6. anschließend OCR

## Einstieg in einem neuen Chat

```text
Lies bitte die Datei NEUER-CHAT.md aus meinem GitHub-Projekt Markus4771/ScanPro und führe die Entwicklung ab dem dort dokumentierten Stand weiter.
```
