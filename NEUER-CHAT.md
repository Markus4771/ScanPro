# ScanPro – Neuer Chat

## Projekt

Repository: `Markus4771/ScanPro`

Aktueller Stand: **0.3.1-dev**

## Neu in 0.3.1-dev

QR- und Barcode-Trennung sind umgesetzt.

## Unterstützte Trennmethoden

- Leerseite
- Patch-T
- QR-Code
- Barcode

## QR-/Barcode-Verarbeitung

PDF-Seiten werden gerendert und über `pyzbar` / `zbar` analysiert.

Wenn ein passender Code erkannt wird:

1. aktuelle Dokumentgruppe wird beendet
2. Trennerseite wird verworfen
3. neuer Dokumentabschnitt beginnt
4. Code-Marker wird gespeichert

## Marker

Neue Tabelle:

```text
job_separation_markers
```

Felder:

- scan_job_id
- page
- marker_type
- value
- created_at

Die Job-API liefert jetzt:

```text
separation_markers
```

Diese Daten können später für Dateinamen und Metadaten genutzt werden.

## Webinterface

Die Jobliste zeigt:

- Anzahl getrennter Dokumente
- Anzahl erkannter Trenner
- Seite des Trenners
- Codetyp
- Codeinhalt
- verständlichere Trennfehler

## Abhängigkeiten

Neu:

```text
libzbar0
Pillow
pyzbar
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
{"status":"ok","version":"0.3.1-dev"}
```

## Nächster Entwicklungsschritt

Empfohlen:

**0.4.0-dev – Bildoptimierung**

- automatische Rotation
- Deskew / Begradigen
- Auto-Crop
- Randentfernung

Danach:

- OCR
- Dateinamen-/Metadatenregeln
- Paperless-ngx

## Backlog

Weiterhin geplant:

- Bilder/Fotos scannen
- Scanner über VPN / entfernte Standorte
- Patch-T Praxistest mit Brother ADS-2600We

## Einstieg in einem neuen Chat

```text
Lies bitte die Datei NEUER-CHAT.md aus meinem GitHub-Projekt Markus4771/ScanPro und führe die Entwicklung ab dem dort dokumentierten Stand weiter.
```
