# ScanPro – Neuer Chat

## Projekt

Repository: `Markus4771/ScanPro`

Aktueller Stand: **0.8.1-dev**

## Neu in 0.8.1-dev

Remote-Scanner-Härtung ist umgesetzt.

## Statische Scannerziele

Neue Tabelle:

```text
scanner_static_targets
```

Felder:

- scanner_id
- enabled
- driver
- device_name
- device_id
- address

API:

```text
GET /api/scanner-static-targets
PUT /api/scanners/{scanner_id}/static-target
```

## sane-airscan ohne mDNS

Bei aktiviertem statischem SANE-Ziel setzt ScanPro für den Scanprozess:

```text
SANE_AIRSCAN_DEVICE=escl:<NAME>:<URL>
```

Wird nur eine IP gespeichert, erzeugt ScanPro:

```text
http://<IP>/eSCL
```

Eine vollständige http/https-eSCL-URL kann ebenfalls angegeben werden.

## Fehlerklassifikation

NAPS2-/Scannerfehler werden kategorisiert:

```text
network
discovery
scan
```

Jobs können entsprechend folgende Stati erhalten:

```text
network_error
discovery_error
scan_error
```

## Scannerstatus

Die Scannerliste zeigt:

- Online/Offline
- Netzwerk/Discovery/OK
- Standort
- LOCAL/VPN
- Reachability-Details

Statisch konfigurierte, erreichbare Scanner gelten nicht als Discovery-Fehler.

## Standortfilter

Im Webinterface gibt es jetzt:

```text
Standortfilter
```

Damit können Scanner z. B. nach Hauptstandort und Außenstellen gefiltert werden.

## Schema-Version

```text
5
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
{"status":"ok","version":"0.8.1-dev","schema_version":5}
```

## Nächster Entwicklungsschritt

Empfohlen:

**0.9.0-dev – Secret Store**

- SMB-Passwörter nicht mehr im Klartext
- Paperless-Tokens nicht mehr im Klartext
- verschlüsselte lokale Secret-Ablage
- Maskierung bleibt im Webinterface

Danach:

- Remote Collector
- Paperless Custom Fields
- Dokumentklassifikation
- Cleanup/Retention

## Einstieg in einem neuen Chat

```text
Lies bitte die Datei NEUER-CHAT.md aus meinem GitHub-Projekt Markus4771/ScanPro und führe die Entwicklung ab dem dort dokumentierten Stand weiter.
```
