# ScanPro

ScanPro ist eine modulare Linux-ScanStation für Dokumentenscanner.

## Entwicklungsstand

Aktuell: **0.1.0-dev**

Der Brother ADS-2600We ist das erste Testgerät. ScanPro wird jedoch von Anfang an herstellerunabhängig und für mehrere Scanner entwickelt.

## Zielbild

- mehrere Scanner verwalten
- NAPS2 als Scan-Engine
- eSCL und SANE als erste Scanner-Backends
- Scanprofile zentral konfigurieren
- Scanziele frei konfigurieren
- Workflows zwischen Scanner, Verarbeitung und Ziel
- optionale Dokumenttrennung
- SMB-Eingänge für Scan-to-Network-Geräte
- OCR, Vorschau und Seitenbearbeitung
- Paperless-ngx und weitere Ziele über Adapter

## Dokumenttrennung

Die Trennung soll je Profil bzw. Workflow optional aktivierbar sein.

Geplante Methoden:

- Patch-T
- QR-Code
- Barcode
- Leerseite
- manuelle Trennung

## Kernobjekte

- **Scanner** – physisches oder logisches Eingabegerät
- **Scanprofil** – DPI, Farbe, Duplex, OCR und Trennoptionen
- **Scanziel** – lokaler Ordner, SMB, Paperless usw.
- **Workflow** – verbindet Scanner, Profil und Ziel
- **Scanjob** – konkreter Scan- oder Importvorgang

## Dokumentation

- [Installation](INSTALLATION.md)
- [Übergabe für einen neuen Chat](NEUER-CHAT.md)
- [Architektur](docs/ARCHITECTURE.md)

## Geplanter Ausbau

- **0.1.x** Grundsystem, Scannerverwaltung und NAPS2-Anbindung
- **0.2.x** SMB-Eingänge
- **0.3.x** Patch-T und manuelle Dokumenttrennung
- **0.4.x** QR-/Barcode-Trennung
- **0.5.x** OCR und Seitenbearbeitung
- **0.6.x** Paperless-ngx und weitere Scanziele
