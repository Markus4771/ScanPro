# ScanPro – Neuer Chat

## Projekt

Repository: `Markus4771/ScanPro`

Aktueller Stand: **0.6.0-dev**

## Neu in 0.6.0-dev

Paperless-ngx ist als eigener Scanziel-Typ integriert.

## Zieltyp

```text
paperless
```

## Konfiguration

- `base_url`
- `token`
- `title`
- `correspondent`
- `document_type`
- `storage_path`
- `tags`
- `verify_ssl`

## Authentifizierung

ScanPro verwendet:

```text
Authorization: Token <TOKEN>
Accept: application/json; version=10
```

## Verbindungstest

Der Zieltest führt einen authentifizierten Request auf:

```text
GET /api/documents/?page_size=1
```

aus.

## Upload

PDFs werden hochgeladen über:

```text
POST /api/documents/post_document/
```

als Multipart-Feld:

```text
document
```

Optional werden übergeben:

- title
- correspondent
- document_type
- storage_path
- tags

Wenn kein fester Titel konfiguriert ist, wird der von ScanPro erzeugte Dateiname ohne PDF-Endung verwendet.

## Async-Verarbeitung

Paperless gibt beim Upload eine Consumption-Task-ID zurück.

ScanPro speichert:

```text
paperless-task:<UUID>
```

in `job_deliveries.target_path`.

## Webinterface

Unter **Scanziele** steht nun zur Auswahl:

```text
Lokaler Ordner
SMB-Freigabe
Paperless-ngx
```

Paperless-Felder:

- URL
- API-Token
- Titel
- Korrespondent-ID
- Dokumenttyp-ID
- Speicherpfad-ID
- Tag-IDs
- TLS-Prüfung

## Sicherheit

Der API-Token wird im Web/API maskiert.

Im aktuellen Entwicklungsstand liegt er noch im SQLite-Konfigurationsfeld. Später sollte ein Secret Store eingeführt werden.

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
{"status":"ok","version":"0.6.0-dev","schema_version":1}
```

## Nächster Entwicklungsschritt

Empfohlen:

**0.6.1-dev – Paperless-Metadatenregeln**

- QR-/Barcode-Werte auf Paperless-Felder abbilden
- OCR-Ergebnisse auf Titel/Korrespondent/Dokumenttyp/Tags abbilden
- Consumption-Task-Status nachverfolgen
- Paperless-IDs komfortabel aus der API laden statt manuell einzutragen

Danach:

- Foto-/Bildscan JPEG/PNG
- VPN-/Remote-Scanner

## Weiterer Backlog

- Secret Store für Tokens und Passwörter
- Patch-T Praxistest
- Dokumentklassifikation
- Cleanup-Regeln für Jobdateien

## Einstieg in einem neuen Chat

```text
Lies bitte die Datei NEUER-CHAT.md aus meinem GitHub-Projekt Markus4771/ScanPro und führe die Entwicklung ab dem dort dokumentierten Stand weiter.
```
