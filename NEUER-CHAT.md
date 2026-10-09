# ScanPro – Neuer Chat

## Aktueller Entwicklungsstand (8. Oktober 2026)

Repository: `Markus4771/ScanPro`

Version laut pyproject.toml: **1.6.0.dev0**; `/health` meldet im aktuellen Code Schema **4**. README hat einen älteren Stand.

Die alte Version 0.9.2 liegt im Branch `archive/scanpro-0.9.2`.

## Architektur

```text
Scanner → SMB-Scan-Eingang → Verarbeitungsprofil → Scanziel
```

ScanPro arbeitet scannerunabhängig, ohne NAPS2 und ohne Scannerverwaltung im Kern.

Datenbank: `/var/lib/scanpro-v1/scanpro-v1.db`

## Bereits im Code vorhanden (nicht zwingend auf dem Server getestet)

- WebGUI mit Anmeldung, Benutzerverwaltung und eigener Passwortänderung
- Benutzerbezogene Profile, Ziele und Scan-Eingänge
- Dynamische SMB-Eingänge und Inbox-Worker
- OCR/PDF-A, Auto-Rotation und Deskew über OCRmyPDF
- Entfernen von PDF-Leerseiten über Bildanalyse
- Farbmodus, DPI und A4-Normalisierung
- Lokale Ziele, lokale SMB-Ziele, externe SMB-Ziele und Paperless-Upload
- Optionale Unterordner mit Vorlagen wie `{year}/{month}` (leere Vorlage = kein Unterordner)
- Handgezeichnetes Dreieck als PDF-Trennzeichen: Position, Mindestgröße und Entfernen der Trennseite einstellbar
- Job- und Delivery-Protokoll

## Änderung: lokales Samba-Scanziel (8.10.2026)

- Bei `local_smb` kann im Formular ein individueller Samba-Benutzer angegeben werden (`scanpro_d...`), andernfalls vergibt ScanPro weiterhin automatisch `scanpro_d<ID>`.
- Benutzername und Passwort werden weiterhin über die nur für den angemeldeten Eigentümer erreichbare Scanziel-Verbindungsansicht angezeigt.
- Beim Anlegen wird der SMB-Benutzer mit dem eingegebenen Passwort über den vorhandenen Samba-Helper eingerichtet.
- Vor der Inbetriebnahme die Funktion auf dem Linux-Server testen; kein erfolgreicher Laufzeittest ausgeführt.

## Frei wählbare lokale SMB-Benutzer (9. Oktober 2026)

- Lokale SMB-Scanziele akzeptieren Benutzernamen wie `markus` (3–31 Zeichen, Kleinbuchstaben, Zahlen, Bindestrich, Unterstrich; erster Buchstabe bzw. Unterstrich).
- Vor dem Anlegen erfolgt ein Konfliktcheck gegen Linux-/Samba-Konten, andere Scanziele und Scan-Eingänge.
- Vom aktualisierten Samba-Helper neu angelegte Konten werden durch root-geschützte Markierungsdateien unter `/var/lib/scanpro-v1/samba-managed-users/` registriert. Nur markierte Konten dürfen durch den Helper gelöscht werden.
- Benutzername und Passwort sind weiterhin nach Anmeldung über die vorhandene Scanziel-Verbindungsansicht sichtbar.
- **Noch auf Debian testen:** Anlage, Rechte, SMB-Login, Passwortwechsel und Löschung; keine Laufzeittests durchgeführt. Alte vor dieser Änderung angelegte Konten ohne Markierungsdatei werden beim Löschen absichtlich nicht automatisch entfernt.
- Bei einem bereits existierenden Linux- oder Samba-Konto `markus` muss ein anderer, noch freier SMB-Benutzername verwendet werden. Fremde Konten werden nicht übernommen.

## Offen / noch zu prüfen

1. **Auto-Crop**: Profiloption ist vorhanden, im eingesehenen `processor.py` aber noch nicht in die Verarbeitung eingebunden.
2. **Leerseite / QR / Barcode als Trennzeichen**: am 8.10.2026 im Worker ergänzt (`split_marker_pdf`), `zxing-cpp` als Abhängigkeit aufgenommen; ein Regressionstest liegt unter `tests/test_separator_split.py`. Noch kein erfolgreicher Testlauf gegen die tatsächliche Serverumgebung erfolgt. Trennseiten werden dabei entfernt. Bei QR/Barcode löst aktuell jeder erkannte Code des ausgewählten Typs eine Trennung aus; explizite Markerwerte wären als weitere Absicherung sinnvoll.
3. **SMB-Zielverhalten**: Unterordner und Zielpfade mit echten SMB-Freigaben testen, Fehlerbehandlung und sicheres Anlegen von Zielordnern überprüfen.
4. **Dreieck-Trennung**: Erkennung an echten Scans testen (handgezeichnet, gedruckt, Falschpositive, erste/letzte Seite).
5. **Benutzerverwaltung und eigene Passwortänderung**: WebGUI und Backend sind vorhanden, Funktion auf dem installierten Server prüfen.
6. Secret Store, Retention/Cleanup, Paperless-Metadaten und umfassende automatisierte Tests.
7. Tatsächliche Version des installierten Servers mit `/health` gegen GitHub abgleichen.

## Empfehlung für den nächsten Entwicklungsschritt

Die neu implementierten Trennverfahren mit realen Scans und `pytest -q tests/test_separator_split.py` testen; danach Markerwerte für QR/Barcode konfigurieren und Auto-Crop implementieren. Bestehende Dreieck-Trennung und optionale Unterordner dabei unverändert erhalten.

## Deployment / Test

```bash
cd ~/ScanPro
git pull
sudo bash scripts/install-dev.sh
curl http://127.0.0.1:8100/health
```

Vor Updates an produktionsnahen Daten stets eine Sicherung der Datenbank und Konfiguration erstellen.

**Aktuelle GitHub-Änderungen:** `4adaed9` (Trennlogik), `b80837d` (zxing-cpp), `c68d271` (Regressionstest). Da die Testumgebung GitHub nicht klonen konnte, wurden die Tests nicht lokal ausgeführt.

## Einstieg in einen neuen Chat

Lies `NEUER-CHAT.md` im Repository `Markus4771/ScanPro` und führe die Entwicklung ab dem dokumentierten Stand weiter.
