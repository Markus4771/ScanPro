# ScanPro 1.0-dev – Benutzerhandbuch

## Grundidee

ScanPro arbeitet nur noch mit Freigaben.

Der Scanner wird einmalig so eingerichtet, dass er in eine SMB-Freigabe von ScanPro scannt.

```text
Scanner → Freigabe → Profil → Ziel
```

## 1. Verarbeitungsprofil anlegen

Beispiel:

```text
Name: Rechnungen
OCR: Ja
Sprache: Deutsch
Dateiname: {date}_{input}_{job}_{document}
```

Das Profil beschreibt die Verarbeitung nach dem Scan.

## 2. Scanziel anlegen

Unterstützte Zieltypen:

- Lokaler Ordner
- SMB
- Paperless-ngx

Beispiel Paperless:

```text
Name: Paperless
URL: https://paperless.example.local
API-Token: ...
```

## 3. Scan-Eingang anlegen

Beispiel:

```text
Name: Rechnungen
Freigabe: Rechnungen
Profil: Rechnungen
Ziel: Paperless
```

ScanPro zeigt anschließend:

```text
\\SCANPRO\Rechnungen
Benutzer: scanpro
```

## 4. Scanner einrichten

Im Brother ADS-2600We wird ein Scan-to-Network-Profil angelegt:

```text
Profilname: Rechnung
Server: IP des ScanPro-Servers
Freigabe: Rechnungen
Benutzer: scanpro
Passwort: Samba-Passwort
```

Weitere Eingänge können genauso angelegt werden:

```text
Rechnung      → \\SCANPRO\Rechnungen
Lieferschein  → \\SCANPRO\Lieferscheine
Archiv        → \\SCANPRO\Archiv
Foto          → \\SCANPRO\Fotos
```

## 5. Alltag

```text
Dokument einlegen
→ Profil am Scanner auswählen
→ Scan starten
→ Datei landet in SMB-Freigabe
→ ScanPro startet automatisch
→ Verarbeitung
→ Ziel
```

Es muss kein Browser geöffnet sein.

## 6. ScanJobs

Die Weboberfläche zeigt:

- Eingang
- Profil
- Ziel
- Status
- Fehler
- fertige Dokumente

Status `delivered` bedeutet, dass das Dokument erfolgreich an das Ziel übertragen wurde.

## Hinweise

ScanPro 1.0-dev ist der neue Entwicklungszweig. Erweiterte Bildverarbeitung und Dokumenttrennung werden im nächsten Schritt neu implementiert.
