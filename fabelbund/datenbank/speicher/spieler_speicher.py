from __future__ import annotations

import json

from fabelbund.datenbank.datenbank import Datenbank
from fabelbund.modelle.laufzeit import SpielerProfil


class SpielerSpeicher:
    def __init__(self, datenbank: Datenbank) -> None:
        self.datenbank = datenbank

    def holen(self, nutzer_id: str) -> SpielerProfil | None:
        with self.datenbank.verbinden() as verbindung:
            zeile = verbindung.execute("SELECT * FROM spieler WHERE nutzer_id = ?", (nutzer_id,)).fetchone()
        if zeile is None:
            return None
        return SpielerProfil.model_validate(
            {
                "nutzer_id": zeile["nutzer_id"],
                "geld": zeile["geld"],
                "ruf": json.loads(zeile["ruf_json"]),
                "lizenzen": json.loads(zeile["lizenzen_json"]),
                "erstellt_am": zeile["erstellt_am"],
            }
        )

    def speichern(self, spieler: SpielerProfil) -> None:
        nutzlast = (
            spieler.nutzer_id,
            spieler.geld,
            json.dumps(spieler.ruf, sort_keys=True),
            json.dumps(spieler.lizenzen),
            spieler.erstellt_am.isoformat(),
        )
        with self.datenbank.verbinden() as verbindung:
            verbindung.execute(
                """
                INSERT INTO spieler (nutzer_id, geld, ruf_json, lizenzen_json, erstellt_am)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(nutzer_id) DO UPDATE SET
                    geld = excluded.geld,
                    ruf_json = excluded.ruf_json,
                    lizenzen_json = excluded.lizenzen_json
                """,
                nutzlast,
            )
