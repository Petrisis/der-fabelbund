from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Iterator
import sqlite3
from pathlib import Path


class Datenbank:
    def __init__(self, pfad: Path | str) -> None:
        self.pfad = Path(pfad)

    @contextmanager
    def verbinden(self) -> Iterator[sqlite3.Connection]:
        self.pfad.parent.mkdir(parents=True, exist_ok=True)
        verbindung = sqlite3.connect(self.pfad)
        verbindung.row_factory = sqlite3.Row
        verbindung.execute("PRAGMA foreign_keys = ON")
        try:
            yield verbindung
            verbindung.commit()
        finally:
            verbindung.close()

    def migrieren(self) -> None:
        with self.verbinden() as verbindung:
            verbindung.executescript(
                """
                CREATE TABLE IF NOT EXISTS spieler (
                    nutzer_id TEXT PRIMARY KEY,
                    geld INTEGER NOT NULL,
                    freigeschaltete_ställe INTEGER NOT NULL DEFAULT 1,
                    stalltypen_json TEXT NOT NULL DEFAULT '{"neutral": 1}',
                    ruf_json TEXT NOT NULL,
                    lizenzen_json TEXT NOT NULL,
                    erstellt_am TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS fabelwesen (
                    id TEXT PRIMARY KEY,
                    besitzer_id TEXT NOT NULL,
                    art_id TEXT NOT NULL,
                    spitzname TEXT NOT NULL,
                    seltenheit TEXT NOT NULL,
                    daten_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS aktive_aufträge (
                    id TEXT PRIMARY KEY,
                    spieler_id TEXT NOT NULL,
                    auftrag_id TEXT NOT NULL,
                    fabelwesen_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    fortschritt_json TEXT NOT NULL,
                    gestartet_am TEXT NOT NULL,
                    abgeschlossen_am TEXT
                );

                CREATE TABLE IF NOT EXISTS aktivitäten (
                    id TEXT PRIMARY KEY,
                    spieler_id TEXT NOT NULL,
                    fabelwesen_id TEXT NOT NULL,
                    art TEXT NOT NULL,
                    aktion_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    braucht_spieler INTEGER NOT NULL,
                    abbrechbar INTEGER NOT NULL DEFAULT 1,
                    status TEXT NOT NULL,
                    effekte_json TEXT NOT NULL,
                    gestartet_am TEXT NOT NULL,
                    endet_am TEXT NOT NULL,
                    beendet_am TEXT
                );
                """
            )
            spalten = {
                zeile["name"]
                for zeile in verbindung.execute("PRAGMA table_info(spieler)").fetchall()
            }
            if "freigeschaltete_ställe" not in spalten:
                verbindung.execute("ALTER TABLE spieler ADD COLUMN freigeschaltete_ställe INTEGER NOT NULL DEFAULT 1")
            if "stalltypen_json" not in spalten:
                verbindung.execute("ALTER TABLE spieler ADD COLUMN stalltypen_json TEXT NOT NULL DEFAULT '{\"neutral\": 1}'")
            aktivität_spalten = {
                zeile["name"]
                for zeile in verbindung.execute("PRAGMA table_info(aktivitäten)").fetchall()
            }
            if "abbrechbar" not in aktivität_spalten:
                verbindung.execute("ALTER TABLE aktivitäten ADD COLUMN abbrechbar INTEGER NOT NULL DEFAULT 1")
