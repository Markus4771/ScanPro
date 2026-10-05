# ScanPro – Neuer Chat

## Projekt

Repository: `Markus4771/ScanPro`

Aktueller Stand: **0.2.5-dev**

## Neu in 0.2.5-dev

Scanprofile können optional leere Seiten automatisch entfernen.

Webinterface:

```text
Leere Seiten aussortieren
```

Die Option gilt für:

- Scanner-Workflows
- Profil-SMB-Inbox-Workflows

## Technische Umsetzung

Neue Tabelle:

```text
profile_processing
```

Aktuell enthalten:

- profile_id
- remove_blank_pages

Neue Tabelle:

```text
job_processing
```

Sie protokolliert:

- scan_job_id
- blank_pages_removed
- blank_pages_json

Neue API:

```text
GET /api/profile-processing
PUT /api/profiles/{profile_id}/processing
```

## Leerseitenerkennung

Datei:

```text
scanpro/services/blank_pages.py
```

Verwendet:

```text
PyMuPDF
```

Ablauf:

1. PDF-Seite verkleinert in Graustufen rendern
2. Weißanteil bestimmen
3. nahezu vollständig weiße Seiten markieren
4. PDF ohne diese Seiten neu schreiben
5. entfernte Seitennummern protokollieren
6. anschließend Workflow-Ziel beliefern

Wenn alle Seiten als leer erkannt werden, bleibt die Originaldatei erhalten und der Job erhält `processing_error`.

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
{"status":"ok","version":"0.2.5-dev"}
```

## Nächster Entwicklungsschritt

**0.3.0-dev – echte Dokumenttrennung**

Geplant:

1. Leerseite als Trennblatt
2. Patch-T
3. mehrere PDFs aus einem ScanJob
4. QR-/Barcode-Trennung
5. OCR

Wichtig: **Leere Seiten entfernen** und **Leerseite als Dokumenttrenner** bleiben zwei getrennte Profilfunktionen.

## Einstieg in einem neuen Chat

```text
Lies bitte die Datei NEUER-CHAT.md aus meinem GitHub-Projekt Markus4771/ScanPro und führe die Entwicklung ab dem dort dokumentierten Stand weiter.
```
