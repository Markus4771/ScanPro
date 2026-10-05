# ScanPro – Neuer Chat

## Projekt

Repository: `Markus4771/ScanPro`

Aktueller Stand: **0.1.2-dev**

## Erfolgreich getestet

- Brother ADS-2600We über NAPS2/SANE
- Scanner-Erkennung
- Scanner-Import
- Testscan über ScanPro-API
- PDF-Ausgabe unter `/var/lib/scanpro/jobs/`
- Dienstbenutzer `scanpro` mit Home `/var/lib/scanpro`

## In 0.1.2-dev umgesetzt

- erste Weboberfläche unter `/`
- Scanner erkennen über SANE/eSCL
- Scanner per Klick übernehmen
- gespeicherte Scanner anzeigen
- Testscan im Browser
- Auswahl 150/200/300/600 dpi
- Farbe, Graustufen, Schwarzweiß
- Einseitig oder Duplex
- letzte ScanJobs anzeigen
- PDF-Datei eines Jobs über `/api/jobs/{job_id}/file`
- Version auf 0.1.2-dev angehoben

## Update auf dem Testsystem

```bash
cd ~/ScanPro
git pull
sudo bash scripts/install-dev.sh
```

Danach:

```bash
curl http://127.0.0.1:8100/health
```

und im Browser:

```text
http://IP-DES-SCANPRO-SERVERS/
```

## Nächster Entwicklungsschritt

Als nächstes:

1. Weboberfläche weiter ausbauen
2. Scanner Online/Offline-Status
3. PDF-Link/Vorschau direkt in der Jobliste
4. Scanprofile im Webinterface
5. danach SMB-Inbox und konfigurierbare Scanziele
6. anschließend optionale Dokumenttrennung

## Weiterhin geplant

- mehrere Scanner
- Scanprofile
- Scanziele
- Workflows
- SMB-Eingang
- Patch-T
- QR-Code
- Barcode
- Leerseite
- manuelle Trennung
- OCR
- Seitenbearbeitung
- Paperless-ngx

## Einstieg in einem neuen Chat

```text
Lies bitte die Datei NEUER-CHAT.md aus meinem GitHub-Projekt Markus4771/ScanPro und führe die Entwicklung ab dem dort dokumentierten Stand weiter.
```
