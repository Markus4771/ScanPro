# ScanPro – Neuer Chat

## Projekt

Repository: `Markus4771/ScanPro`

Aktueller Stand: **0.1.4-dev**

## Erfolgreich getestet

- Brother ADS-2600We über NAPS2/SANE
- Scanner-Erkennung und Import
- Scan über Weboberfläche
- PDF-Erzeugung unter `/var/lib/scanpro/jobs/`
- Scannerstatus online/offline
- Scannerverwaltung
- PDF direkt aus Jobliste öffnen

## In 0.1.4-dev umgesetzt

- Scanprofile im Webinterface anzeigen
- Scanprofile anlegen
- Scanprofile bearbeiten
- Scanprofile löschen
- doppelte Profilnamen verhindern
- Schutz vor Löschen eines Profils, das in einem Workflow verwendet wird
- DPI speichern
- Farbmodus speichern
- Einseitig/Duplex speichern
- OCR an/aus speichern
- Trennung an/aus speichern
- Trennmethode speichern
- Profil im Testscan auswählen
- DPI/Farbe/Duplex automatisch aus Profil übernehmen

## Trennmethoden im Profil

- `patch-t`
- `qr`
- `barcode`
- `blank-page`
- `manual`

## Wichtig

OCR und Dokumenttrennung werden in **0.1.4-dev nur konfiguriert und gespeichert**.

Die tatsächliche OCR-Verarbeitung und Dokumenttrennung ist noch nicht aktiv.

## Relevante Profil-API

```text
GET    /api/profiles
POST   /api/profiles
PATCH  /api/profiles/{profile_id}
DELETE /api/profiles/{profile_id}
```

## Update auf dem Testsystem

```bash
cd ~/ScanPro
git pull
sudo bash scripts/install-dev.sh
```

Danach im Browser neu laden:

```text
http://IP-DES-SCANPRO-SERVERS/
```

## Nächster Entwicklungsschritt

**0.2.0-dev – konfigurierbare Scanziele und SMB**

Geplant:

1. Scanziele im Webinterface
2. lokale Ordner
3. SMB-Ziele
4. Verbindung testen
5. Ziel aktivieren/deaktivieren
6. Scanprofil + Scanziel zusammenführen
7. SMB-Inbox für Scan-to-Network-Geräte

Danach:

- automatische Weiterleitung
- Patch-T-Verarbeitung
- OCR
- QR-/Barcode-Trennung

## Einstieg in einem neuen Chat

```text
Lies bitte die Datei NEUER-CHAT.md aus meinem GitHub-Projekt Markus4771/ScanPro und führe die Entwicklung ab dem dort dokumentierten Stand weiter.
```
