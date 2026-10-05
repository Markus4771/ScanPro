# ScanPro – Neuer Chat

## Projekt

Repository: `Markus4771/ScanPro`

Aktueller Stand: **0.7.0-dev**

## Neu in 0.7.0-dev

Foto-/Bildscan ist umgesetzt.

## Profilmodus

Neue Profil-Ausgabeeinstellungen:

```text
mode: document | photo
output_format: pdf | jpeg | png
jpeg_quality: 1..100
```

Neue Tabelle:

```text
profile_output_settings
```

## API

```text
GET /api/profile-output-settings
PUT /api/profiles/{profile_id}/output-settings
```

## Foto-Modus

Im Webinterface:

```text
Profilmodus: Foto / Bild
Ausgabeformat: JPEG oder PNG
JPEG-Qualität
Auflösung bis 1200 dpi
```

Für JPEG/PNG setzt ScanPro automatisch:

- OCR aus
- Trennung aus
- Farbe

## Verarbeitung

ScanPro verwendet weiterhin NAPS2 mit PDF als robustem Zwischenformat:

```text
Scanner
→ NAPS2 PDF
→ Bildoptimierung
→ JPEG/PNG
→ Dateinamensregeln
→ Ziel
```

Mehrseitige PDFs werden in einzelne Bilddateien zerlegt.

Bilddateien liegen intern unter:

```text
/var/lib/scanpro/jobs/images/<JOB-ID>/
```

## Bildoptimierung

Rotation, Deskew, Auto-Crop und Randentfernung können auch für Foto-Profile genutzt werden.

Die Verarbeitung rendert jetzt mit der DPI des Profils statt fest mit 300 dpi.

## Dateinamen

Die Namensengine übernimmt automatisch die Dateiendung des erzeugten Formats.

Beispiele:

```text
2026-10-05_Fotos_120_001.jpg
2026-10-05_Fotos_120_002.jpg
```

## Ziele

Unterstützt:

- lokaler Ordner
- SMB
- Paperless technisch weiterhin möglich

Für Foto-/Bildprofile sind lokale und SMB-Ziele der primäre Anwendungsfall.

## Schema-Version

```text
3
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
{"status":"ok","version":"0.7.0-dev","schema_version":3}
```

## Nächster Entwicklungsschritt

Empfohlen:

**0.8.0-dev – VPN-/Remote-Scanner**

- Standort pro Scanner
- lokal/VPN
- Reachability-Test
- längere Timeouts
- Retry bei temporären VPN-Problemen
- Gruppierung nach Standort
- Vorbereitung für Remote Collector

Danach:

- Secret Store
- Paperless Custom Fields
- automatische Dokumentklassifikation
- Cleanup/Retention

## Einstieg in einem neuen Chat

```text
Lies bitte die Datei NEUER-CHAT.md aus meinem GitHub-Projekt Markus4771/ScanPro und führe die Entwicklung ab dem dort dokumentierten Stand weiter.
```
