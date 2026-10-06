# ScanPro – Benutzungsanleitung

**Version:** 0.9.0-dev

ScanPro ist eine zentrale Scan- und Dokumentenverarbeitungslösung für Linux/Debian. Scanner können lokal oder über VPN angebunden werden. ScanPro kann Dokumente automatisch verarbeiten, trennen, per OCR erkennen, umbenennen und anschließend beispielsweise auf ein SMB-Ziel oder nach Paperless-ngx übertragen.

## 1. ScanPro öffnen

ScanPro wird im Browser geöffnet.

Beispiel:

```text
http://IP-DES-SCANPRO-SERVERS/
```

Wenn ScanPro beispielsweise die IP-Adresse `192.168.0.50` besitzt:

```text
http://192.168.0.50/
```

Die Oberfläche zeigt die installierte ScanPro-Version an.

## 2. Grundprinzip

Ein vollständiger Scanvorgang besteht normalerweise aus drei Komponenten:

```text
Scanner
   ↓
Scanprofil
   ↓
Scanziel
```

Diese drei Komponenten werden in einem **Workflow** verbunden.

Beispiel:

```text
Brother ADS-2600We
        ↓
Profil Rechnungen
        ↓
Paperless-ngx
```

Ein Workflow kann anschließend mit einem Klick gestartet werden.

## 3. Scanner einrichten

Im Bereich **Scanner erkennen** stehen zwei Möglichkeiten zur Verfügung:

```text
SANE suchen
eSCL suchen
```

Für Netzwerkgeräte wie den Brother ADS-2600We ist normalerweise **SANE suchen** ausreichend.

ScanPro zeigt anschließend alle erkannten Scanner an.

Beispiel:

```text
Brother ADS-2600We
192.168.0.172
sane
```

Mit **Übernehmen** wird der Scanner dauerhaft gespeichert.

## 4. Gespeicherte Scanner

Im Bereich **Gespeicherte Scanner** werden alle konfigurierten Geräte angezeigt.

ScanPro zeigt unter anderem:

```text
Scannername
IP-Adresse
Driver
Online / Offline
Standort
LOCAL / VPN
Netzwerkstatus
```

Mögliche Zustände sind:

```text
OK
Netzwerk
Discovery
Scanfehler
```

### OK

Der Scanner ist erreichbar und kann verwendet werden.

### Netzwerk

Der Scanner ist über das Netzwerk nicht erreichbar.

Mögliche Ursachen:

- Scanner ausgeschaltet
- falsche IP-Adresse
- VPN nicht verbunden
- Firewall blockiert Zugriff
- Routingproblem

### Discovery

Der Scanner ist grundsätzlich erreichbar, wurde aber nicht über die automatische Scannererkennung gefunden.

Dies kommt besonders häufig bei VPN-Verbindungen vor.

### Scanfehler

Der Scanner wurde erreicht, aber der eigentliche Scanvorgang ist fehlgeschlagen.

## 5. Scanner bearbeiten

Über **Bearbeiten** können die Einstellungen eines Scanners geändert werden.

Konfigurierbar sind:

```text
Scannername
IP-Adresse
Standort
Verbindungstyp
Timeout
Wiederholungen
statisches Remote-Ziel
```

## 6. Standorte

Jeder Scanner kann einem Standort zugeordnet werden.

Beispiele:

```text
Büro
Werkstatt
Außenstelle Augsburg
Homeoffice
Lager
```

Über den **Standortfilter** können nur die Scanner eines bestimmten Standortes angezeigt werden.

## 7. Lokaler Scanner oder VPN-Scanner

Als Verbindungstyp stehen zur Verfügung:

```text
local
vpn
```

Für einen Scanner im lokalen Netzwerk:

```text
Verbindungstyp: local
Timeout: 60
Retries: 1
```

Für einen Scanner über WireGuard oder ein anderes VPN beispielsweise:

```text
Verbindungstyp: vpn
Timeout: 120
Retries: 2
```

ScanPro versucht den Scan bei einem temporären Fehler automatisch erneut.

## 8. Erreichbarkeit eines Scanners testen

Bei jedem gespeicherten Scanner befindet sich die Funktion:

```text
Erreichbarkeit testen
```

ScanPro prüft dabei typische Netzwerkdienste des Scanners.

Unter anderem werden folgende Ports geprüft:

```text
80
443
631
6566
```

Dadurch funktioniert der Test auch dann, wenn ICMP/Ping im Netzwerk blockiert ist.

## 9. Statischen VPN-Scanner einrichten

Bei gerouteten VPN-Verbindungen funktioniert die automatische mDNS-Erkennung häufig nicht.

Dafür kann ScanPro einen Scanner statisch ansprechen.

Beim Bearbeiten des Scanners:

```text
Statisches Remote-Ziel verwenden: Ja
```

Danach beispielsweise:

```text
Driver: sane
Gerätename: Brother Außenstelle
Adresse: 10.20.30.40
```

ScanPro erzeugt daraus intern eine direkte AirScan/eSCL-Verbindung.

Sinngemäß:

```text
http://10.20.30.40/eSCL
```

Alternativ kann direkt eine vollständige URL eingetragen werden:

```text
http://10.20.30.40:8080/eSCL
```

Damit ist keine mDNS-Erkennung erforderlich.

## 10. Scanprofile

Scanprofile bestimmen, **wie ein Dokument gescannt und verarbeitet wird**.

Beispiele:

```text
Rechnung
Lieferschein
Brief
Archiv
Foto
Personaldokument
```

Ein Scanprofil enthält unter anderem:

```text
Auflösung
Farbmodus
Duplex
OCR
Dokumenttrennung
Bildoptimierung
Dateinamensregeln
Paperless-Regeln
```

## 11. Auflösung

Typische Einstellungen:

```text
150 dpi
200 dpi
300 dpi
600 dpi
1200 dpi
```

Empfehlung:

```text
Normale Dokumente: 300 dpi
kleine Schrift:     300–600 dpi
Fotos:              600 dpi
Archivfotos:        bis 1200 dpi
```

1200 dpi sollte nur verwendet werden, wenn der Scanner diese Auflösung unterstützt.

## 12. Farbmodus

Verfügbar sind:

```text
Farbe
Graustufen
Schwarzweiß
```

Für normale Geschäftsdokumente ist meistens Farbe oder Graustufen sinnvoll.

## 13. Duplex

Bei aktiviertem Duplex werden Vorder- und Rückseite gescannt.

Beispiel:

```text
Duplex: Ja
```

## 14. Leerseiten entfernen

Die Option:

```text
Leere Seiten aussortieren
```

entfernt automatisch leere Seiten aus einem Scan.

Das ist besonders bei Duplex-Scans sinnvoll.

## 15. Automatische Bildoptimierung

ScanPro kann Dokumente automatisch korrigieren.

Verfügbar sind:

```text
Automatische Rotation
Schiefe Seiten begradigen
Automatisch zuschneiden
Scanner-Ränder entfernen
```

Für normale Dokumente ist beispielsweise sinnvoll:

```text
Automatische Rotation: Ja
Deskew:                Ja
Auto-Crop:             optional
Ränder entfernen:      optional
```

## 16. OCR

OCR macht den Text eines gescannten Dokuments durchsuchbar.

Im Profil:

```text
OCR aktivieren
```

Danach Sprache auswählen:

```text
Deutsch
Englisch
Deutsch + Englisch
```

Ein gescanntes PDF kann anschließend beispielsweise in Paperless oder einem PDF-Reader durchsucht werden.

## 17. Dokumenttrennung

Mehrere Dokumente können in einem einzigen Stapel gescannt und anschließend automatisch getrennt werden.

ScanPro unterstützt:

```text
Patch-T
QR-Code
Barcode
Leerseite
manuell
```

## 18. Trennung mit Leerseite

Beispielstapel:

```text
Dokument 1
Leerseite
Dokument 2
Leerseite
Dokument 3
```

ScanPro erzeugt daraus:

```text
Dokument 1
Dokument 2
Dokument 3
```

Die Leerseiten werden als Trenner verwendet.

## 19. QR-Code als Dokumenttrenner

Ein spezielles QR-Blatt kann zwischen Dokumente gelegt werden.

Beispiel:

```text
QR: RECHNUNG
Dokument 1

QR: LIEFERSCHEIN
Dokument 2
```

Der Inhalt des QR-Codes kann später auch zur Dateibenennung oder Paperless-Zuordnung verwendet werden.

## 20. Barcode als Dokumenttrenner

Dasselbe Prinzip funktioniert mit Barcodes.

Unterstützt werden unter anderem:

```text
CODE128
CODE39
EAN13
EAN8
UPC
CODABAR
I25
```

## 21. Dateinamen automatisch erzeugen

ScanPro kann Dateinamen automatisch aufbauen.

Standard:

```text
{date}_{profile}_{job}_{document}
```

Beispiel:

```text
2026-10-05_Rechnung_125_001.pdf
```

Verfügbare Variablen sind:

```text
{date}
{time}
{datetime}
{profile}
{job}
{document}
{code}
{code_type}
{ocr_first_line}
```

Beispiel mit QR-Code:

```text
{date}_{profile}_{code}_{document}
```

ergibt beispielsweise:

```text
2026-10-05_Rechnung_KUNDE4711_001.pdf
```

## 22. OCR für Dateinamen verwenden

Die erste erkannte OCR-Zeile kann Bestandteil des Dateinamens werden.

Beispiel:

```text
{date}_{ocr_first_line}_{document}
```

Dazu muss aktiviert werden:

```text
OCR-Erstzeile für Dateinamen verwenden
```

## 23. Scanziele

Ein Scanziel bestimmt, wohin das fertige Dokument übertragen wird.

Unterstützt werden:

```text
Lokaler Ordner
SMB-Freigabe
Paperless-ngx
```

## 24. Lokales Ziel

Beispiel:

```text
/srv/scans/rechnungen
```

Mit **Verbindung testen** kann geprüft werden, ob ScanPro in den Ordner schreiben kann.

## 25. SMB-Ziel

Beispiel:

```text
Server:      192.168.0.20
Freigabe:    Dokumente
Unterordner: Rechnungen
Benutzer:    scanpro
Passwort:    ********
```

ScanPro kann anschließend Dateien beispielsweise nach:

```text
\\192.168.0.20\Dokumente\Rechnungen
```

übertragen.

Vor Verwendung sollte immer **Verbindung testen** ausgeführt werden.

## 26. Paperless-ngx

Paperless-ngx kann direkt als Scanziel verwendet werden.

Benötigt werden:

```text
Paperless-URL
API-Token
```

Beispiel:

```text
https://paperless.meinedomain.de
```

Zusätzlich können optional festgelegt werden:

```text
Korrespondent
Dokumenttyp
Speicherpfad
Tags
Titel
```

## 27. Paperless-Werte laden

Nach dem Speichern eines Paperless-Ziels kann:

```text
Paperless-Werte laden
```

verwendet werden.

ScanPro liest dann unter anderem folgende Informationen aus Paperless:

```text
Korrespondenten
Dokumenttypen
Speicherpfade
Tags
```

## 28. Automatische Paperless-Regeln

Ein Scanprofil kann Paperless-Metadaten automatisch setzen.

Beispiel für einen QR-Code:

```text
RECHNUNG
```

Mapping:

```json
{"RECHNUNG":3}
```

Damit kann beispielsweise automatisch der Paperless-Dokumenttyp mit ID `3` gesetzt werden.

## 29. OCR-basierte Paperless-Regel

Beispiel:

```json
[
  {
    "contains": "Telekom",
    "correspondent": 4,
    "document_type": 3,
    "tags": [2]
  }
]
```

Enthält der OCR-Text `Deutsche Telekom`, kann ScanPro automatisch passende Paperless-Metadaten setzen.

## 30. Paperless-Status

Nach dem Upload zeigt ScanPro eine Paperless-Task-ID.

Über:

```text
Paperless-Status
```

kann geprüft werden, ob Paperless das Dokument bereits verarbeitet hat.

## 31. Foto-/Bildscan

ScanPro kann neben Dokumenten auch Bilder und Fotos scannen.

Im Profil:

```text
Profilmodus: Foto / Bild
```

Ausgabeformate:

```text
JPEG
PNG
PDF
```

## 32. Empfohlenes Fotoprofil

Beispiel:

```text
Name: Foto 600
Profilmodus: Foto / Bild
Format: JPEG
Qualität: 92
Auflösung: 600 dpi
Farbe: Farbe
OCR: Aus
Dokumenttrennung: Aus
Auto-Crop: Ein
```

Bei JPEG/PNG deaktiviert ScanPro OCR und Dokumenttrennung automatisch.

## 33. Workflows

Ein Workflow verbindet:

```text
Quelle
   ↓
Scanprofil
   ↓
Scanziel
```

Beispiel:

```text
Brother ADS-2600We
        ↓
Rechnungen
        ↓
Paperless
```

Ein Workflow kann über **Workflow starten** ausgeführt werden.

## 34. Workflow mit SMB-Inbox

Neben einem Scanner kann auch eine SMB-Freigabe als Quelle dienen.

Beispiel:

```text
\\SCANPRO\Rechnungen
        ↓
Profil Rechnungen
        ↓
Paperless
```

Wird eine PDF in die Freigabe gelegt, startet die Verarbeitung automatisch.

## 35. Typischer Rechnungsworkflow

Empfohlene Konfiguration:

```text
Profil: Rechnungen
300 dpi
Duplex
Leerseiten entfernen
Deskew
OCR Deutsch
QR-Trennung
Dateiname:
{date}_{profile}_{code}_{document}
```

Ziel:

```text
Paperless-ngx
```

Ablauf:

```text
Dokumente in Scanner legen
        ↓
Workflow starten
        ↓
Scannen
        ↓
Dokumente trennen
        ↓
Bild korrigieren
        ↓
OCR
        ↓
Dateiname erzeugen
        ↓
Paperless-Metadaten bestimmen
        ↓
Paperless-Upload
```

## 36. ScanJobs

Im unteren Bereich zeigt ScanPro die letzten ScanJobs.

Dort sieht man unter anderem:

```text
Job-ID
Status
Profil
Dokumentanzahl
OCR-Ergebnis
Bildkorrekturen
Dateinamen
Versandstatus
Paperless-Status
Fehler
```

## 37. Typische Jobstatus

Beispiele:

```text
scanning
finished
separated
delivered
delivery_error
processing_error
network_error
discovery_error
scan_error
```

## 38. Netzwerkfehler

```text
network_error
```

bedeutet beispielsweise:

```text
VPN getrennt
Scanner ausgeschaltet
Routingproblem
Timeout
```

## 39. Discovery-Fehler

```text
discovery_error
```

bedeutet:

```text
Netzwerk funktioniert
aber Scanner wurde nicht automatisch gefunden
```

Bei VPN-Verbindungen sollte dann ein statisches Scannerziel verwendet werden.

## 40. Scanfehler

```text
scan_error
```

kann beispielsweise bedeuten:

```text
kein Papier
Papierstau
Scanner beschäftigt
ADF offen
Gerätefehler
```

## 41. Empfohlene Profile

### Rechnung

```text
300 dpi
Farbe
Duplex
Leerseiten entfernen
Deskew
OCR Deutsch
QR-/Leerseitentrennung
PDF
Paperless
```

### Allgemeine Dokumente

```text
300 dpi
Farbe
Duplex
Leerseiten entfernen
Deskew
OCR Deutsch
PDF
SMB oder Paperless
```

### Archiv

```text
300–600 dpi
Farbe
Duplex
OCR
PDF
SMB
```

### Foto

```text
600 dpi
Farbe
JPEG
Qualität 92–95
Auto-Crop
OCR aus
Trennung aus
```

## 42. Empfohlene Vorgehensweise im Alltag

Für einen normalen Scanvorgang sind nur wenige Schritte erforderlich:

```text
1. Dokumente einlegen
2. passenden Workflow wählen
3. Workflow starten
4. ScanJob kontrollieren
```

Die restliche Verarbeitung läuft automatisch.

## 43. Administratorfunktionen

Ein Administrator richtet normalerweise einmalig ein:

```text
Scanner
Standorte
VPN-Einstellungen
Scanprofile
SMB-Ziele
Paperless
Workflows
Dateinamensregeln
OCR-Regeln
```

Der normale Benutzer braucht anschließend überwiegend nur noch die fertigen Workflows.

## 44. Empfohlene Struktur

Für einen kleinen Betrieb könnte beispielsweise folgende Struktur eingerichtet werden:

Scanner:

```text
Brother Büro
Brother Werkstatt
Brother Außenstelle
```

Profile:

```text
Rechnung
Lieferschein
Allgemein
Archiv
Foto
```

Ziele:

```text
Paperless
NAS Dokumente
NAS Archiv
Foto-Archiv
```

Workflows:

```text
Rechnung → Paperless
Lieferschein → Paperless
Allgemein → NAS
Archiv → NAS Archiv
Foto → Foto-Archiv
```

Damit muss ein Benutzer nicht mehr wissen, wie OCR, SMB oder Paperless technisch funktionieren.

Er wählt lediglich den passenden Workflow.


## 45. Zugangsdaten und Secret Store

SMB-Passwörter und Paperless-API-Tokens werden ab ScanPro 0.9.0-dev verschlüsselt auf dem ScanPro-Server gespeichert.

Im Webinterface ändert sich die Bedienung nicht. Bereits gespeicherte Zugangsdaten werden weiterhin als:

```text
********
```

angezeigt.

Beim Ändern eines Scanziels kann ein neues Passwort bzw. Token eingegeben werden. Wird `********` unverändert übernommen, bleibt das vorhandene Secret erhalten.

Die verschlüsselte Ablage befindet sich unter:

```text
/var/lib/scanpro/secrets/
```

Dieser Bereich ist eine Administratorfunktion und sollte nicht für normale Benutzer freigegeben werden.

**Wichtig für Backups:** Die ScanPro-Datenbank und der Secret Store müssen immer gemeinsam gesichert werden. Ohne den zugehörigen `master.key` können vorhandene Zugangsdaten nicht wiederhergestellt werden.
