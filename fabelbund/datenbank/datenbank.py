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
                    inventar_json TEXT NOT NULL DEFAULT '{}',
                    ruf_json TEXT NOT NULL,
                    lizenzen_json TEXT NOT NULL,
                    tutorialstatus TEXT NOT NULL DEFAULT 'neu',
                    tutorialschritt TEXT NOT NULL DEFAULT 'registrierung',
                    tutorialpfad TEXT,
                    offizielles_mitglied INTEGER NOT NULL DEFAULT 0,
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
                    kategorie TEXT NOT NULL DEFAULT 'pflege',
                    intensität TEXT NOT NULL DEFAULT 'mittel',
                    braucht_spieler INTEGER NOT NULL,
                    abbrechbar INTEGER NOT NULL DEFAULT 1,
                    status TEXT NOT NULL,
                    effekte_json TEXT NOT NULL,
                    wettbewerb_effekte_json TEXT NOT NULL DEFAULT '{}',
                    sport_effekte_json TEXT NOT NULL DEFAULT '{}',
                    abbruch_effekte_json TEXT NOT NULL DEFAULT '{}',
                    folgeaktionen_json TEXT NOT NULL DEFAULT '[]',
                    gestartet_am TEXT NOT NULL,
                    endet_am TEXT NOT NULL,
                    beendet_am TEXT
                );

                CREATE TABLE IF NOT EXISTS server_konfigurationen (
                    guild_id TEXT PRIMARY KEY,
                    kategorie_id TEXT NOT NULL,
                    aufträge_kanal_id TEXT NOT NULL,
                    chronik_kanal_id TEXT NOT NULL,
                    events_kanal_id TEXT NOT NULL,
                    auftragswand_nachricht_id TEXT,
                    eingerichtet_am TEXT NOT NULL,
                    aktualisiert_am TEXT NOT NULL
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
            if "inventar_json" not in spalten:
                verbindung.execute("ALTER TABLE spieler ADD COLUMN inventar_json TEXT NOT NULL DEFAULT '{}'")
            if "tutorialstatus" not in spalten:
                verbindung.execute("ALTER TABLE spieler ADD COLUMN tutorialstatus TEXT NOT NULL DEFAULT 'neu'")
            if "tutorialschritt" not in spalten:
                verbindung.execute("ALTER TABLE spieler ADD COLUMN tutorialschritt TEXT NOT NULL DEFAULT 'registrierung'")
            if "tutorialpfad" not in spalten:
                verbindung.execute("ALTER TABLE spieler ADD COLUMN tutorialpfad TEXT")
            if "offizielles_mitglied" not in spalten:
                verbindung.execute("ALTER TABLE spieler ADD COLUMN offizielles_mitglied INTEGER NOT NULL DEFAULT 0")
            aktivität_spalten = {
                zeile["name"]
                for zeile in verbindung.execute("PRAGMA table_info(aktivitäten)").fetchall()
            }
            if "abbrechbar" not in aktivität_spalten:
                verbindung.execute("ALTER TABLE aktivitäten ADD COLUMN abbrechbar INTEGER NOT NULL DEFAULT 1")
            if "kategorie" not in aktivität_spalten:
                verbindung.execute("ALTER TABLE aktivitäten ADD COLUMN kategorie TEXT NOT NULL DEFAULT 'pflege'")
            if "intensität" not in aktivität_spalten:
                verbindung.execute("ALTER TABLE aktivitäten ADD COLUMN intensität TEXT NOT NULL DEFAULT 'mittel'")
            if "wettbewerb_effekte_json" not in aktivität_spalten:
                verbindung.execute("ALTER TABLE aktivitäten ADD COLUMN wettbewerb_effekte_json TEXT NOT NULL DEFAULT '{}'")
            if "sport_effekte_json" not in aktivität_spalten:
                verbindung.execute("ALTER TABLE aktivitäten ADD COLUMN sport_effekte_json TEXT NOT NULL DEFAULT '{}'")
            if "abbruch_effekte_json" not in aktivität_spalten:
                verbindung.execute("ALTER TABLE aktivitäten ADD COLUMN abbruch_effekte_json TEXT NOT NULL DEFAULT '{}'")
            if "folgeaktionen_json" not in aktivität_spalten:
                verbindung.execute("ALTER TABLE aktivitäten ADD COLUMN folgeaktionen_json TEXT NOT NULL DEFAULT '[]'")
