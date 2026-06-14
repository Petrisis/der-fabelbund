from __future__ import annotations

import json

from fabelbund.datenbank.datenbank import Datenbank
from fabelbund.modelle.laufzeit import Fabelwesen


class FabelwesenSpeicher:
    def __init__(self, datenbank: Datenbank) -> None:
        self.datenbank = datenbank

    def holen(self, fabelwesen_id: str) -> Fabelwesen | None:
        with self.datenbank.verbinden() as verbindung:
            zeile = verbindung.execute("SELECT daten_json FROM fabelwesen WHERE id = ?", (fabelwesen_id,)).fetchone()
        if zeile is None:
            return None
        return Fabelwesen.model_validate(json.loads(zeile["daten_json"]))

    def für_besitzer_auflisten(self, besitzer_id: str) -> list[Fabelwesen]:
        with self.datenbank.verbinden() as verbindung:
            zeilen = verbindung.execute(
                "SELECT daten_json FROM fabelwesen WHERE besitzer_id = ? ORDER BY spitzname, id",
                (besitzer_id,),
            ).fetchall()
        return [Fabelwesen.model_validate(json.loads(zeile["daten_json"])) for zeile in zeilen]

    def speichern(self, fabelwesen: Fabelwesen) -> None:
        nutzlast = (
            fabelwesen.id,
            fabelwesen.besitzer_id,
            fabelwesen.art_id,
            fabelwesen.spitzname,
            fabelwesen.seltenheit,
            fabelwesen.model_dump_json(),
        )
        with self.datenbank.verbinden() as verbindung:
            verbindung.execute(
                """
                INSERT INTO fabelwesen (id, besitzer_id, art_id, spitzname, seltenheit, daten_json)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    spitzname = excluded.spitzname,
                    seltenheit = excluded.seltenheit,
                    daten_json = excluded.daten_json
                """,
                nutzlast,
            )

    def löschen(self, fabelwesen_id: str) -> None:
        with self.datenbank.verbinden() as verbindung:
            verbindung.execute("DELETE FROM fabelwesen WHERE id = ?", (fabelwesen_id,))

    def für_besitzer_löschen(self, besitzer_id: str) -> None:
        with self.datenbank.verbinden() as verbindung:
            verbindung.execute("DELETE FROM fabelwesen WHERE besitzer_id = ?", (besitzer_id,))
