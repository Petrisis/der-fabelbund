from __future__ import annotations

import json

from fabelbund.datenbank.datenbank import Datenbank
from fabelbund.modelle.laufzeit import AktiverAuftrag


class AuftragSpeicher:
    def __init__(self, datenbank: Datenbank) -> None:
        self.datenbank = datenbank

    def aktiven_holen(self, spieler_id: str) -> AktiverAuftrag | None:
        with self.datenbank.verbinden() as verbindung:
            zeile = verbindung.execute(
                """
                SELECT * FROM aktive_aufträge
                WHERE spieler_id = ? AND status = 'aktiv'
                ORDER BY gestartet_am DESC
                LIMIT 1
                """,
                (spieler_id,),
            ).fetchone()
        if zeile is None:
            return None
        return self._aus_zeile(zeile)

    def aktive_auflisten(self) -> list[AktiverAuftrag]:
        with self.datenbank.verbinden() as verbindung:
            zeilen = verbindung.execute(
                """
                SELECT * FROM aktive_aufträge
                WHERE status = 'aktiv'
                ORDER BY gestartet_am DESC
                """
            ).fetchall()
        return [self._aus_zeile(zeile) for zeile in zeilen]

    def speichern(self, auftrag: AktiverAuftrag) -> None:
        nutzlast = (
            auftrag.id,
            auftrag.spieler_id,
            auftrag.auftrag_id,
            auftrag.fabelwesen_id,
            auftrag.status,
            json.dumps(auftrag.fortschritt, sort_keys=True),
            auftrag.gestartet_am.isoformat(),
            auftrag.abgeschlossen_am.isoformat() if auftrag.abgeschlossen_am else None,
        )
        with self.datenbank.verbinden() as verbindung:
            verbindung.execute(
                """
                INSERT INTO aktive_aufträge (
                    id, spieler_id, auftrag_id, fabelwesen_id, status, fortschritt_json, gestartet_am, abgeschlossen_am
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status = excluded.status,
                    fortschritt_json = excluded.fortschritt_json,
                    abgeschlossen_am = excluded.abgeschlossen_am
                """,
                nutzlast,
            )

    def für_spieler_löschen(self, spieler_id: str) -> None:
        with self.datenbank.verbinden() as verbindung:
            verbindung.execute("DELETE FROM aktive_aufträge WHERE spieler_id = ?", (spieler_id,))

    @staticmethod
    def _aus_zeile(zeile) -> AktiverAuftrag:
        return AktiverAuftrag.model_validate(
            {
                "id": zeile["id"],
                "spieler_id": zeile["spieler_id"],
                "auftrag_id": zeile["auftrag_id"],
                "fabelwesen_id": zeile["fabelwesen_id"],
                "status": zeile["status"],
                "fortschritt": json.loads(zeile["fortschritt_json"]),
                "gestartet_am": zeile["gestartet_am"],
                "abgeschlossen_am": zeile["abgeschlossen_am"],
            }
        )
