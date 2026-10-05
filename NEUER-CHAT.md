# ScanPro – Neuer Chat

## Projekt

Repository: `Markus4771/ScanPro`

Aktueller Stand: **0.6.1-dev**

## Neu in 0.6.1-dev

Paperless-Metadatenregeln und API-Komfortfunktionen sind umgesetzt.

## Paperless-Auswahllisten

Endpoint:

```text
GET /api/destinations/{destination_id}/paperless/choices
```

Geladen werden:

- correspondents
- document_types
- storage_paths
- tags

Im Webinterface:

```text
Paperless-Werte laden
```

## Paperless-Taskstatus

Upload-Task-ID wird weiterhin in `job_deliveries.target_path` gespeichert.

Status:

```text
GET /api/deliveries/{delivery_id}/paperless-task
```

Intern:

```text
GET /api/tasks/?task_id=<UUID>
```

Im Webinterface:

```text
Paperless-Status
```

## Profilbezogene Regeln

Neue Tabelle:

```text
profile_paperless_rules
```

Felder:

- profile_id
- title_template
- correspondent_map_json
- document_type_map_json
- tags_map_json
- ocr_contains_rules_json

API:

```text
GET /api/profile-paperless-rules
PUT /api/profiles/{profile_id}/paperless-rules
```

## Titelvariablen

```text
{filename}
{profile}
{job}
{document}
{code}
{ocr_first_line}
```

## QR-/Barcode-Mapping

Beispiel Korrespondent:

```json
{"KUNDE4711":12}
```

Beispiel Dokumenttyp:

```json
{"RECHNUNG":3}
```

Beispiel Tags:

```json
{"RECHNUNG":[2,5]}
```

## OCR-Enthält-Regeln

Beispiel:

```json
[
  {
    "contains":"Telekom",
    "correspondent":4,
    "document_type":3,
    "tags":[2]
  }
]
```

Regeln werden pro erzeugtem Dokument angewendet.

## Priorität

- Zielkonfiguration liefert Standardwerte.
- Profilregel kann sie pro Dokument überschreiben.
- QR-/Barcode-Regeln werden vor OCR-Regeln angewendet.
- OCR-Regeln können Korrespondent, Dokumenttyp und Tags ergänzen/überschreiben.

## Schema-Version

```text
2
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
```

Erwartet:

```json
{"status":"ok","version":"0.6.1-dev","schema_version":2}
```

## Nächster Entwicklungsschritt

Empfohlen:

**0.7.0-dev – Foto-/Bildscan**

- JPEG/PNG-Ausgabe
- eigener Profilmodus
- 600/1200 dpi
- kein OCR als Standard
- kein Split als Standard
- Auto-Crop/Bildoptimierung
- lokale/SMB-Ziele

Danach:

- VPN-/Remote-Scanner
- Secret Store
- Paperless Custom Fields
- automatische Dokumentklassifikation

## Einstieg in einem neuen Chat

```text
Lies bitte die Datei NEUER-CHAT.md aus meinem GitHub-Projekt Markus4771/ScanPro und führe die Entwicklung ab dem dort dokumentierten Stand weiter.
```
