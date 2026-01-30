# Apka Portfelik

Lokalna aplikacja desktopowa do śledzenia portfela akcji. Dane są przechowywane w SQLite, a notowania pobierane z darmowego CSV Stooq (bez API key).

## Wymagania
- Python 3.11+ (najlepiej 3.12)
- Windows / Linux / macOS

## Instalacja (Windows)
```bash
cd C:\sciezka\do\folderu\z\projektem
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python main.py
```

## Dane i cache
- Domyślny plik bazy danych: `data/portfolio.db`.
- Limity pobrań i folder danych można zmienić w zakładce **Ustawienia**.

## Budowanie instalatora EXE (Windows)
```bash
build.bat
```
Po zakończeniu w folderze `dist/` pojawią się:
- `ApkaPortfelik.exe` – wersja przenośna (uruchamiana bez instalacji),
- `ApkaPortfelik-Setup.exe` – instalator do uruchomienia jednym kliknięciem na docelowym komputerze.

> Jeśli nie masz zainstalowanego **Inno Setup 6**, skrypt zbuduje tylko wersję przenośną i poinformuje, że brakuje narzędzia do tworzenia instalatora.

## Źródło notowań
- Stooq CSV: `https://stooq.com/q/d/l/?s={SYMBOL}&i=d`

## Testy
```bash
pytest
```
