# ScanPro

ScanPro ist eine modulare Linux-ScanStation für Dokumentenscanner.

## Zielbild

- mehrere Scanner verwalten (NAPS2/eSCL/SANE, später weitere Backends)
- Scanprofile zentral konfigurieren
- Scan-Ziele frei konfigurieren
- optionale Dokumenttrennung je Profil/Workflow
- SMB-Eingänge für Scan-to-Network-Geräte
- OCR, Vorschau und Weiterleitung als nachgelagerte Verarbeitung
- Paperless-ngx und weitere Ziele über erweiterbare Destination-Adapter

## Entwicklungsstand

Aktuell: **0.1.0-dev**

Die erste Entwicklungsstufe legt Architektur, Datenmodell und Web-API fest. Der Brother ADS-2600We ist das erste Testgerät, ScanPro selbst bleibt jedoch herstellerunabhängig.

## Kernobjekte

- **Scanner** – physisches oder logisches Eingabegerät
- **Scanprofil** – DPI, Farbe, Duplex, Quelle und Verarbeitung
- **Scanziel** – lokaler Ordner, SMB, Paperless usw.
- **Workflow** – verbindet Eingabe, Trennung, OCR und Ziel
- **Scanjob** – ein konkreter Scan-/Importvorgang

## Geplanter Ausbau

- 0.1.x: Grundsystem, Scannerverwaltung, NAPS2-Anbindung
- 0.2.x: SMB-Eingänge
- 0.3.x: Patch-T und manuelle Dokumenttrennung
- 0.4.x: QR-/Barcode-Trennung
- 0.5.x: OCR und Seitenbearbeitung
- 0.6.x: Paperless-ngx und weitere Ziele

Siehe `NEUER-CHAT.md` und `docs/ARCHITECTURE.md`.
