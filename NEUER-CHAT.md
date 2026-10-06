# ScanPro – Neuer Chat

## Projekt

Repository: `Markus4771/ScanPro`

Aktueller Stand: **0.9.0-dev**

## Neu in 0.9.0-dev

Ein verschlüsselter lokaler Secret Store ist umgesetzt.

## Geschützte Werte

Aktuell:

- SMB-Passwörter
- Paperless-API-Tokens

## Ablage

```text
/var/lib/scanpro/secrets/
```

Dateien:

```text
master.key
destination-<ID>-smb-password.secret
destination-<ID>-paperless-token.secret
```

Verschlüsselung:

```text
cryptography / Fernet
```

## SQLite

In `destinations.config_json` liegen keine Klartext-Secrets mehr.

Stattdessen intern:

```json
{"password_secret_ref":"destination-1-smb-password"}
```

oder:

```json
{"token_secret_ref":"destination-2-paperless-token"}
```

Diese Referenzen werden über die öffentliche API nicht ausgegeben.

Das Webinterface erhält weiterhin nur:

```text
********
```

## Migration

Beim Update von älteren Versionen werden vorhandene Klartext-Passwörter/-Tokens automatisch verschlüsselt ausgelagert und aus SQLite entfernt.

Der Installer führt diese Migration vor dem Start der Dienste aus.

## Rechte

```text
secrets/    0700
master.key  0600
*.secret    0600
```

## Backup

Beim Update:

```text
/var/lib/scanpro/backups/scanpro-<ZEITSTEMPEL>.db
/var/lib/scanpro/backups/scanpro-secrets-<ZEITSTEMPEL>.tar.gz
```

Datenbank und Secret Store müssen gemeinsam gesichert/wiederhergestellt werden.

## Schema-Version

```text
6
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
{"status":"ok","version":"0.9.0-dev","schema_version":6}
```

Secret Store:

```bash
sudo ls -lah /var/lib/scanpro/secrets
sudo -u scanpro sqlite3 /var/lib/scanpro/scanpro.db "SELECT id,name,type,config_json FROM destinations;"
```

## Nächster Entwicklungsschritt

Empfohlen:

**0.9.1-dev – Cleanup / Retention**

- Aufbewahrungsregeln für Jobs
- temporäre PDFs/Bilder bereinigen
- erfolgreiche/fehlerhafte Jobs unterschiedlich behandeln
- manuelle Bereinigung im Webinterface
- Schutz noch benötigter Dateien

Danach:

- Paperless Custom Fields
- automatische Dokumentklassifikation
- Remote Collector
- Stabilisierung Richtung 1.0

## Einstieg in einem neuen Chat

```text
Lies bitte die Datei NEUER-CHAT.md aus meinem GitHub-Projekt Markus4771/ScanPro und führe die Entwicklung ab dem dort dokumentierten Stand weiter.
```
