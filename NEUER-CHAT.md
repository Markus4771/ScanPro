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

## Samba-Reparaturen (9. Oktober 2026)

Zwei Fehler, die auf dem Debian-Server festgestellt wurden, sind im GitHub-Code behoben:

1. `scripts/install-dev.sh` schreibt `include = /var/lib/scanpro-v1/samba-inputs.conf` nun in `[global]` statt ans Dateiende unter `[print$]`. Alte doppelte Zeilen werden entfernt; zuvor wird `smb.conf` gesichert.
2. `scripts/scanpro-samba-user` setzt für **Ein- und Ausgang** je Samba-Benutzer ein ACL-Durchquerungsrecht (`--x`) am privaten `/var/lib/scanpro-v1`. Der Installer stellt dieses Recht auch bei bestehenden Konten wieder her. ACL-Paket wird installiert.

Zusätzlich schützt der Installer die root-eigenen Samba-Konto-Markierungsdateien nach rekursiver Datenverzeichnis-Eigentümerkorrrektur vor versehentlicher Freigabe an den Dienst.

Der Anwender bestätigte, dass die manuell korrigierte Freigabe wieder funktioniert. **Der geänderte Installer wurde noch nicht auf dem Zielserver ausgeführt oder dort getestet.**

### SMB-Eingang: Korrektur vom 9. Oktober 2026

Auf dem Zielserver war die Samba-Anmeldung als `scanpro_s1` erfolgreich, jedoch scheiterte `cd PDF` mit `NT_STATUS_ACCESS_DENIED`. Ursache: Durchquerungsrecht des SMB-Kontos auf `/var/lib/scanpro-v1` fehlte. Der Samba-Helper setzt inzwischen `setfacl -m u:<konto>:--x` für Eingänge und Ausgänge. Zusätzlich ruft der Installer bei jedem Update `sync_samba_config` auf, um Besitzrechte, Freigabe-Konfiguration und Zugriffsrechte aller aktiven Eingangs- und Ausgangsziele erneut herzustellen (Commit `c9a6387`). Änderung noch nicht auf dem Zielserver getestet.

## Scan-Eingänge: frei wählbarer Samba-Benutzer (9. Oktober 2026)

- Scan-Eingangsformular unterstützt nun `SMB-Benutzer` zusätzlich zum Passwort.
- Leer gelassen: bisheriger automatisch generierter Name `scanpro_s<ID>`; andernfalls frei wählbarer Name wie `scannerpdf` (3–31 Zeichen, Kleinbuchstaben, Zahlen, `_` und `-`).
- Bei selbst gewähltem Namen wird gegen andere Eingänge, lokale SMB-Ziele sowie vorhandene Linux-/Samba-Konten geprüft; vorhandene Konten werden nicht übernommen.
- Benutzername und Passwort werden wie bisher im angemeldeten Scan-Eingangsbereich angezeigt. Bestehende Eingänge werden nicht umbenannt.
- Änderungen an Schema, API und WebGUI sind auf GitHub committed, aber ein Test auf dem Zielserver steht aus.

## Scan-Verarbeitung: Berechtigungsfehler (9. Oktober 2026)

ScanJob 1 zeigte `InputFileError: [Errno 13] Permission denied` beim Lesen einer PDF unter `/var/lib/scanpro-v1/Verarbeitung/jobs/1`. Die Samba-Share-Konfiguration setzt jetzt für Eingänge/Ausgänge `force create mode = 0660`, `force directory mode = 0770` und `force group = scanpro`, damit zukünftige Dateien für den ScanPro-Worker lesbar bleiben (Commit `c9cc109`). Der bereits fehlgeschlagene Job wird **nicht** automatisch erneut gestartet; Datei und Rechte vor einem erneuten Import überprüfen. Änderung auf dem Zielserver noch nicht getestet.

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

## Fehlerkorrekturen vom 9. Oktober 2026: Live-Test Brother SMB / Datenbank

- Brother → `Eingang/PDF` funktioniert. Frühere Dateien wurden als `scanpro_s1:scanpro_s1` statt `scanpro_s1:scanpro` abgelegt; Samba-Eingang erzwingt nun die Gruppe `scanpro` und Dateimodus 0660.
- `job_documents` aus einer früheren Datenbank benötigt `split_method` und `created_at`; der aktuelle Code benötigt außerdem `final_name`. ORM und Migration wurden kompatibel gemacht.
- `job_deliveries` aus früherer Datenbank hatte keine Spalte `target`; Migration ergänzt bei Bedarf `target`, `error` und `created_at`, ohne Datensätze zu löschen (Commit `ded1c16`).
- Worker setzt nach DB-Fehler die Transaktion mit `rollback()` zurück statt mit `PendingRollbackError` abzustürzen; Fehlermeldungen werden nun im Journal protokolliert (Commit `438bde1`).
- Regressionstest für alte DB-Schemata unter `tests/test_legacy_migrations.py` (Commit `15f14ce`); **auf Zielserver noch nicht ausgeführt**.
- Samba-`include` muss **am Ende** von `[global]` stehen; damit verschwinden `Global parameter ... found in service section`-Warnungen (Commit `1c83985`).
- Live-Datenbank: Job 1 `error` wegen Zugriffsrechten, Job 2 `processing` nach altem DB-Absturz, Jobs 3 und 4 `error` wegen fehlender Spalte `target`. Fertige PDF(s) liegen teilweise schon im Ausgang. **Nicht pauschal neu starten, um Duplikate zu vermeiden.** Neue ScanJobs mit aktualisiertem Code testen und ausgegebene Dateien gesondert prüfen.


## Verarbeitungsprofile nachträglich bearbeiten (9.10.2026)

- API `PUT /api/profiles/{profile_id}` aktualisiert alle Profilfelder unter Eigentümerprüfung, inklusive OCR, Dateinamen, Unterordnern und Trennmethoden. Bestehende Profil-ID und Verknüpfungen zu Scan-Eingängen bleiben erhalten.
- WebGUI zeigt bei jedem Profil `Bearbeiten`; das Formular wird mit bestehenden Werten befüllt und bietet `Änderungen speichern` / `Abbrechen`.
- Commits: `f7b1835`, `6faab4a`.
- Noch nicht auf dem Zielserver funktional getestet.

## Ausgang mit Datenbank synchronisieren (9. Oktober 2026)

- `JobDocument.file_present` markiert, ob die bekannte lokale Ausgabedatei vorhanden ist; Migration ergänzt die Spalte bei älteren SQLite-Datenbanken.
- `scanpro/services/output_sync.py` gleicht nur vorhandene Dokumenteinträge innerhalb des lokalen Ausgangs ab. Keine Dateilöschungen, keine neuen Jobs, keine Manipulation von ScanJob-/Delivery-Historie.
- Abgleich beim Start des Inbox-Workers und alle 300 Sekunden. `POST /api/output/sync` ermöglicht Administratoren sofortigen Abgleich.
- Fehlende PDFs erscheinen in der WebGUI mit Hinweis statt ungültigem Downloadlink. Werden sie wiederhergestellt, erscheint der Link beim nächsten Abgleich erneut.
- `queued`/`processing` werden zum Schutz vor unfertigen Dateien ausgelassen. Insbesondere historischer Job 2 (noch `processing`) wird dadurch nicht korrigiert; gesonderte Job-Wiederherstellung bleibt offen.
- Änderungen noch nicht live getestet.

## Projektstand am 9. Oktober 2026 – GitHub-Abgleich

- **Praxistest bestätigt:** ScanJob 5 hatte `delivered`, Zustellung `delivered`, Ausgabedatei `/var/lib/scanpro-v1/Ausgang/PDF/2026-10-09_PDF_5_001.pdf` (601 KB). Damit ist die Strecke Brother → SMB-Eingang → Verarbeitung → lokaler Ausgang grundsätzlich funktionsfähig.
- **Neu im Repository:** automatische Bestandsprüfung der in der Datenbank referenzierten Ausgangsdateien beim Worker-Start und alle fünf Minuten; manueller Admin-Button „Ausgang jetzt synchronisieren“; Dateistatus `file_present` und ausgeblendete Downloadlinks bei fehlenden Dateien. Die automatische Funktion muss auf dem Zielserver noch per Update und Lösch-/Wiederherstellungstest verifiziert werden.
- **Historische Daten:** Jobs 1–4 nicht blind erneut starten oder löschen; ältere Ausgabedateien können schon existieren. Job 2 steht historisch auf `processing`.
- **Update-Hinweis:** Vor Installation DB-Backup; `git status --short`, `git pull --ff-only`, `sudo bash scripts/install-dev.sh`; anschließend Weboberfläche hart aktualisieren.

## OCR-Auto-Rotation für PDFs mit bestehender Textebene (10. Oktober 2026)

- Bei aktivierter Auto-Rotation nutzt `ocr_pdf` nun `--redo-ocr` statt `--skip-text`; letzteres konnte bereits mit OCR versehene Seiten und somit deren Orientierungsprüfung überspringen.
- Hinzu kommen `--rotate-pages --rotate-pages-threshold 2.0` und OCRmyPDF-Logausgaben im Dienstjournal. Ohne Auto-Rotation bleibt `--skip-text` wie zuvor.
- Anlass: PDF `2026-10-09_PDF_2_001.pdf` mit nahezu leerer erster und um 180 Grad gedrehter zweiter Seite. Nach Änderung vollständigen Test mit diesem Dokument auf dem Zielserver durchführen; automatisierte Tests `tests/test_auto_rotation.py` prüfen die Befehlsparameter, nicht die tatsächliche Drehqualität.
- OCR durch `--redo-ocr` kann langsamer sein. Änderungen auf GitHub, noch nicht auf dem Server getestet.

## Leerseitenerkennung mit Scanner-Rand (10. Oktober 2026)

- Anwender-PDF `2026-10-09_PDF_2_001.pdf`: Seite 1 ist optisch leer, hat aber dunkle Scan-Ränder; bisheriger Weißanteil bei 50 DPI nur 98,71 % und somit unter dem Grenzwert 99 %. Ohne 6 px Rand beträgt er 99,996 %. Seite 2 enthält Inhalt und soll erhalten bleiben.
- `remove_blank_pdf_pages()` ignoriert jetzt die äußeren 1,5 % der gerenderten Seite bei der Weißanteilsmessung. Zusätzlich wird der Weißanteil je Seite ins Journal geschrieben (Commit `ae5017c`).
- Regressionstest `tests/test_blank_page_border.py` mit schwarzem Scanrand und einer Inhaltsseite (Commit `755fa0c`).
- **Noch nicht auf dem ScanPro-Server ausgeführt und mit echtem Scanner nachgetestet.** Im Profil muss die Option `Leerseiten entfernen` aktiviert sein.

## QR-Trennseiten nach Inhalt filtern (10. Oktober 2026)

- Neue Profiloption `qr_marker_content` (Datenbankmigration, ORM, API, WebGUI). Nur wenn Trennung = QR-Code ausgewählt ist, erscheint das Eingabefeld. Bestehende Profile erhalten `''`, sodass weiterhin jeder QR-Code als Trennmarker gilt.
- Für nicht leeren Inhalt erfolgt ein exakter Vergleich mit dem decodierten QR-Text, inklusive Groß-/Kleinschreibung. Nicht passende QR-Codes im Dokument lösen keine Trennung aus. Marker-Seiten werden wie bisher entfernt.
- Regressionstest `tests/test_qr_marker_content.py`; Änderungen auf GitHub, Praxistest auf ScanPro-Server noch offen.

## OCRmyPDF Auto-Rotation + Deskew korrigiert (10. Oktober 2026)

- Jobs 10/11 scheiterten mit `--redo-ocr is not currently compatible with --deskew, --clean-final, and --remove-background`; deshalb erschienen keine neuen Dateien im Ausgang.
- ScanPro verwendet bei aktivierter Auto-Rotation jetzt `--force-ocr` statt `--redo-ocr`, damit `--deskew` kombinierbar ist. Ohne Auto-Rotation bleibt `--skip-text`; `--force-ocr` rastert bestehende PDF-Seiten und kann deren Vektor-/Textebene verändern.
- Regressionstest `tests/test_auto_rotation.py` ergänzt für gleichzeitige Aktivierung von Auto-Rotation und Deskew. Auf ScanPro-Server noch nicht getestet. Jobs 10/11 bleiben Fehlerhistorie; neuen Testscan durchführen.
