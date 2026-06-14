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
                "freigeschaltete_ställe": zeile["freigeschaltete_ställe"],
                "stalltypen": json.loads(zeile["stalltypen_json"]),
                "inventar": json.loads(zeile["inventar_json"]),
                "ruf": json.loads(zeile["ruf_json"]),
                "lizenzen": json.loads(zeile["lizenzen_json"]),
                "tutorialstatus": zeile["tutorialstatus"],
                "tutorialschritt": zeile["tutorialschritt"],
                "tutorialpfad": zeile["tutorialpfad"],
                "offizielles_mitglied": bool(zeile["offizielles_mitglied"]),
                "erstellt_am": zeile["erstellt_am"],
            }
        )

    def speichern(self, spieler: SpielerProfil) -> None:
        nutzlast = (
            spieler.nutzer_id,
            spieler.geld,
            spieler.freigeschaltete_ställe,
            json.dumps(spieler.stalltypen, sort_keys=True),
            json.dumps(spieler.inventar, sort_keys=True),
            json.dumps(spieler.ruf, sort_keys=True),
            json.dumps(spieler.lizenzen),
            spieler.tutorialstatus,
            spieler.tutorialschritt,
            spieler.tutorialpfad,
            1 if spieler.offizielles_mitglied else 0,
            spieler.erstellt_am.isoformat(),
        )
        with self.datenbank.verbinden() as verbindung:
            verbindung.execute(
                """
                INSERT INTO spieler (
                    nutzer_id, geld, freigeschaltete_ställe, stalltypen_json, inventar_json, ruf_json,
                    lizenzen_json, tutorialstatus, tutorialschritt, tutorialpfad, offizielles_mitglied, erstellt_am
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(nutzer_id) DO UPDATE SET
                    geld = excluded.geld,
                    freigeschaltete_ställe = excluded.freigeschaltete_ställe,
                    stalltypen_json = excluded.stalltypen_json,
                    inventar_json = excluded.inventar_json,
                    ruf_json = excluded.ruf_json,
                    lizenzen_json = excluded.lizenzen_json,
                    tutorialstatus = excluded.tutorialstatus,
                    tutorialschritt = excluded.tutorialschritt,
                    tutorialpfad = excluded.tutorialpfad,
                    offizielles_mitglied = excluded.offizielles_mitglied
                """,
                nutzlast,
            )

    def löschen(self, nutzer_id: str) -> None:
        with self.datenbank.verbinden() as verbindung:
            verbindung.execute("DELETE FROM spieler WHERE nutzer_id = ?", (nutzer_id,))
