# ScanPro – Neuer Chat

## Projekt

Repository: `Markus4771/ScanPro`

Aktueller Stand: **0.3.0-dev**

## Neu in 0.3.0-dev

Echte Dokumenttrennung ist umgesetzt.

## Unterstützte Methoden

### Leerseite als Trenner

Produktiv implementiert in ScanPro.

Ablauf:

1. PDF-Seiten analysieren
2. Leerseite erkennen
3. Dokument an dieser Stelle beenden
4. Trennseite verwerfen
5. nächstes Dokument beginnen
6. mehrere PDFs erzeugen

### Patch-T

Über NAPS2 CLI:

```text
--splitpatcht
```

Die Ausgabedateien werden nummeriert erzeugt.

Patch-T ist technisch integriert, unter Linux/SANE aber noch praktisch mit dem Brother ADS-2600We zu testen.

## Neue Tabelle

```text
job_documents
```

Felder:

- scan_job_id
- sequence
- path
- split_method
- created_at

## Verarbeitung

Die erzeugten Teildokumente werden:

1. im Job gespeichert
2. in der Weboberfläche einzeln angezeigt
3. einzeln an das Workflow-Ziel übertragen

## Weboberfläche

In der Jobliste erscheinen bei getrennten Jobs Buttons wie:

```text
Dok. 1
Dok. 2
Dok. 3
```

## Zusammenspiel mit Leerseiten-Entfernung

Diese zwei Funktionen bleiben getrennt:

```text
Leere Seiten aussortieren
Leerseite als Dokumenttrenner
```

Bei aktiver Leerseiten-Trennung werden die Trennseiten nicht vorher entfernt.

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
{"status":"ok","version":"0.3.0-dev"}
```

## Nächster Entwicklungsschritt

**0.3.1-dev**

Geplant:

- Patch-T Praxistest und Feinabstimmung
- QR-Code-Trennung
- Barcode-Trennung
- Trennfehler besser im Webinterface anzeigen
- automatische Begradigung schiefer Scans (Deskew)
- danach OCR

## Einstieg in einem neuen Chat

```text
Lies bitte die Datei NEUER-CHAT.md aus meinem GitHub-Projekt Markus4771/ScanPro und führe die Entwicklung ab dem dort dokumentierten Stand weiter.
```


## Backlog: Deskew / automatische Begradigung

Geplant als optionale Profilfunktion:

```text
Schiefe Seiten automatisch begradigen
```

Vorgesehene Position in der Verarbeitung:

```text
Scan / SMB-Eingang
→ Leerseiten / Dokumenttrennung
→ Deskew / Begradigen
→ OCR
→ Weiterleitung
```

Die Funktion soll sowohl für Scanner-Workflows als auch für Profil-SMB-Inboxen gelten.
