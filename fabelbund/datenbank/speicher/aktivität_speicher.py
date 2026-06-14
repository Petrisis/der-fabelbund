from __future__ import annotations

import json

from fabelbund.datenbank.datenbank import Datenbank
from fabelbund.modelle.laufzeit import Aktivität


class AktivitätSpeicher:
    def __init__(self, datenbank: Datenbank) -> None:
        self.datenbank = datenbank

    def laufende_für_spieler_holen(self, spieler_id: str) -> list[Aktivität]:
        with self.datenbank.verbinden() as verbindung:
            zeilen = verbindung.execute(
                """
                SELECT * FROM aktivitäten
                WHERE spieler_id = ? AND status = 'läuft'
                ORDER BY endet_am, gestartet_am
                """,
                (spieler_id,),
            ).fetchall()
        return [self._aus_zeile(zeile) for zeile in zeilen]

    def laufende_aktive_für_spieler_holen(self, spieler_id: str) -> Aktivität | None:
        with self.datenbank.verbinden() as verbindung:
            zeile = verbindung.execute(
                """
                SELECT * FROM aktivitäten
                WHERE spieler_id = ? AND status = 'läuft' AND braucht_spieler = 1
                ORDER BY endet_am, gestartet_am
                LIMIT 1
                """,
                (spieler_id,),
            ).fetchone()
        if zeile is None:
            return None
        return self._aus_zeile(zeile)

    def laufende_für_fabelwesen_holen(self, fabelwesen_id: str) -> Aktivität | None:
        with self.datenbank.verbinden() as verbindung:
            zeile = verbindung.execute(
                """
                SELECT * FROM aktivitäten
                WHERE fabelwesen_id = ? AND status = 'läuft'
                ORDER BY gestartet_am DESC
                LIMIT 1
                """,
                (fabelwesen_id,),
            ).fetchone()
        if zeile is None:
            return None
        return self._aus_zeile(zeile)

    def holen(self, aktivität_id: str) -> Aktivität | None:
        with self.datenbank.verbinden() as verbindung:
            zeile = verbindung.execute("SELECT * FROM aktivitäten WHERE id = ?", (aktivität_id,)).fetchone()
        if zeile is None:
            return None
        return self._aus_zeile(zeile)

    def speichern(self, aktivität: Aktivität) -> None:
        nutzlast = (
            aktivität.id,
            aktivität.spieler_id,
            aktivität.fabelwesen_id,
            aktivität.art,
            aktivität.aktion_id,
            aktivität.name,
            aktivität.kategorie,
            aktivität.intensität,
            1 if aktivität.braucht_spieler else 0,
            1 if aktivität.abbrechbar else 0,
            aktivität.status,
            json.dumps(aktivität.effekte, sort_keys=True),
            json.dumps(aktivität.wettbewerb_effekte, sort_keys=True),
            json.dumps(aktivität.sport_effekte, sort_keys=True),
            json.dumps(aktivität.abbruch_effekte, sort_keys=True),
            json.dumps(aktivität.folgeaktionen),
            aktivität.gestartet_am.isoformat(),
            aktivität.endet_am.isoformat(),
            aktivität.beendet_am.isoformat() if aktivität.beendet_am else None,
        )
        with self.datenbank.verbinden() as verbindung:
            verbindung.execute(
                """
                INSERT INTO aktivitäten (
                    id, spieler_id, fabelwesen_id, art, aktion_id, name, kategorie, intensität,
                    braucht_spieler, abbrechbar, status, effekte_json, wettbewerb_effekte_json,
                    sport_effekte_json, abbruch_effekte_json, folgeaktionen_json, gestartet_am, endet_am, beendet_am
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    kategorie = excluded.kategorie,
                    intensität = excluded.intensität,
                    status = excluded.status,
                    effekte_json = excluded.effekte_json,
                    wettbewerb_effekte_json = excluded.wettbewerb_effekte_json,
                    sport_effekte_json = excluded.sport_effekte_json,
                    abbruch_effekte_json = excluded.abbruch_effekte_json,
                    folgeaktionen_json = excluded.folgeaktionen_json,
                    endet_am = excluded.endet_am,
                    beendet_am = excluded.beendet_am
                """,
                nutzlast,
            )

    def für_spieler_löschen(self, spieler_id: str) -> None:
        with self.datenbank.verbinden() as verbindung:
            verbindung.execute("DELETE FROM aktivitäten WHERE spieler_id = ?", (spieler_id,))

    @staticmethod
    def _aus_zeile(zeile) -> Aktivität:
        return Aktivität.model_validate(
            {
                "id": zeile["id"],
                "spieler_id": zeile["spieler_id"],
                "fabelwesen_id": zeile["fabelwesen_id"],
                "art": zeile["art"],
                "aktion_id": zeile["aktion_id"],
                "name": zeile["name"],
                "kategorie": zeile["kategorie"],
                "intensität": zeile["intensität"],
                "braucht_spieler": bool(zeile["braucht_spieler"]),
                "abbrechbar": bool(zeile["abbrechbar"]),
                "status": zeile["status"],
                "effekte": json.loads(zeile["effekte_json"]),
                "wettbewerb_effekte": json.loads(zeile["wettbewerb_effekte_json"]),
                "sport_effekte": json.loads(zeile["sport_effekte_json"]),
                "abbruch_effekte": json.loads(zeile["abbruch_effekte_json"]),
                "folgeaktionen": json.loads(zeile["folgeaktionen_json"]),
                "gestartet_am": zeile["gestartet_am"],
                "endet_am": zeile["endet_am"],
                "beendet_am": zeile["beendet_am"],
            }
        )
