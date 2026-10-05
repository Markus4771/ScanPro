# ScanPro – Neuer Chat

## Projekt

Repository: `Markus4771/ScanPro`

Aktueller Stand: **0.8.0-dev**

## Neu in 0.8.0-dev

VPN-/Remote-Scanner-Unterstützung ist als erste Stufe umgesetzt.

## Scanner-Verbindungseinstellungen

Neue Tabelle:

```text
scanner_connection_settings
```

Felder:

- scanner_id
- location
- connection_type
- timeout_seconds
- retries

## Verbindungstypen

```text
local
vpn
```

## API

```text
GET /api/scanner-connection-settings
PUT /api/scanners/{scanner_id}/connection-settings
POST /api/scanners/{scanner_id}/reachability
```

## Reachability

ScanPro verwendet keinen ICMP-Ping, sondern TCP-Verbindungsversuche.

Getestete Ports:

```text
443
80
631
6566
```

Dadurch funktioniert der Test auch in Netzen, in denen ICMP geblockt ist.

## Timeout / Retry

NAPS2-Scans unterstützen jetzt:

- konfigurierbaren Timeout
- Retry bei Fehler/Timeout
- kurze Pause zwischen Versuchen

Diese Einstellungen gelten für:

- Testscan
- Scanner-Workflow

Beispiel VPN-Scanner:

```text
Standort: Außenstelle
connection_type: vpn
timeout_seconds: 120
retries: 2
```

## Webinterface

Gespeicherte Scanner zeigen:

- Standort
- LOCAL/VPN
- Erreichbarkeitsstatus

Zusätzlich:

```text
Erreichbarkeit testen
```

Beim Bearbeiten können Standort, Verbindungstyp, Timeout und Retry-Anzahl gesetzt werden.

## Wichtige technische Grenze

mDNS wird über geroutete VPNs normalerweise nicht übertragen.

Ein erreichbarer Scanner kann daher trotzdem von NAPS2/SANE nicht automatisch gefunden werden.

Für solche Standorte braucht es aktuell entweder:

- statische sane-airscan/eSCL-Konfiguration
- oder später einen ScanPro Remote Collector

## Schema-Version

```text
4
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
{"status":"ok","version":"0.8.0-dev","schema_version":4}
```

## Nächster Entwicklungsschritt

Empfohlen:

**0.8.1-dev – Remote-Scanner-Härtung**

- statische eSCL/SANE-Ziele komfortabler verwalten
- Remote-Scanner ohne mDNS besser erkennen
- Fehlerzustände getrennt anzeigen: Netzwerk / Discovery / Scan
- Standortfilter im UI

Danach:

**0.9.0-dev – Secret Store**

- Paperless-Token
- SMB-Passwörter
- verschlüsselte Ablage

Später:

- Remote Collector
- Paperless Custom Fields
- automatische Dokumentklassifikation
- Cleanup/Retention

## Einstieg in einem neuen Chat

```text
Lies bitte die Datei NEUER-CHAT.md aus meinem GitHub-Projekt Markus4771/ScanPro und führe die Entwicklung ab dem dort dokumentierten Stand weiter.
```
