# mesh_scanner_core – Mini-Shodan Scanner-Core

Ein kleiner, asynchroner Port- und Banner-Scanner:

- Eingabe: CIDR (z. B. `192.168.0.0/24`) + Ports
- Ausgabe: Scan-Ergebnisse in einer SQLite-Datenbank
- Features:
  - asyncio-basierter Port-Scan
  - HTTP- und Raw-Banner-Grab
  - CLI für Scan und Ergebnisanzeige

## Installation

```bash
cd mesh_scanner_core
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip
# keine externen Dependencies nötig


Nutzung
Scan starten
python -m mesh_scanner.cli scan \
  --cidr 192.168.0.0/24 \
  --ports 22,80,443 \
  --db mesh_scanner.sqlite3 \
  --max-hosts 64

Letzte Ergebnisse ansehen
python -m mesh_scanner.cli last \
  --db mesh_scanner.sqlite3 \
  --limit 20