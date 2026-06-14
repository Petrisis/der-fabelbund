from __future__ import annotations

from pathlib import Path
import sqlite3
import sys


ZU_LÖSCHENDE_TABELLEN = ("aktivitäten", "aktive_aufträge", "fabelwesen", "spieler")


def spielerdaten_zurücksetzen(datenbank_pfad: Path) -> int:
    if not datenbank_pfad.exists():
        print(f"Datenbank nicht gefunden: {datenbank_pfad}")
        return 1

    with sqlite3.connect(datenbank_pfad) as verbindung:
        verbindung.execute("PRAGMA foreign_keys = ON")
        for tabelle in ZU_LÖSCHENDE_TABELLEN:
            verbindung.execute(f'DELETE FROM "{tabelle}"')

    print("Spielerdaten zurückgesetzt. Server-Konfigurationen wurden nicht verändert.")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Aufruf: python scripts/spieler_reset.py <datenbankpfad>")
        return 1

    return spielerdaten_zurücksetzen(Path(argv[1]))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
