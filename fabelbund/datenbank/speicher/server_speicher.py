from __future__ import annotations

from datetime import datetime, timezone

from fabelbund.datenbank.datenbank import Datenbank
from fabelbund.modelle.laufzeit import ServerKonfiguration


class ServerSpeicher:
    def __init__(self, datenbank: Datenbank) -> None:
        self.datenbank = datenbank

    def holen(self, guild_id: str) -> ServerKonfiguration | None:
        with self.datenbank.verbinden() as verbindung:
            zeile = verbindung.execute(
                "SELECT * FROM server_konfigurationen WHERE guild_id = ?",
                (guild_id,),
            ).fetchone()
        if zeile is None:
            return None
        return ServerKonfiguration.model_validate(
            {
                "guild_id": zeile["guild_id"],
                "eingerichtet": bool(zeile["eingerichtet"]),
                "kategorie_id": zeile["kategorie_id"],
                "aufträge_kanal_id": zeile["aufträge_kanal_id"],
                "chronik_kanal_id": zeile["chronik_kanal_id"],
                "events_kanal_id": zeile["events_kanal_id"],
                "einstieg_nachricht_id": zeile["einstieg_nachricht_id"],
                "auftragswand_nachricht_id": zeile["auftragswand_nachricht_id"],
                "eingerichtet_am": zeile["eingerichtet_am"],
                "aktualisiert_am": zeile["aktualisiert_am"],
            }
        )

    def auflisten(self) -> list[ServerKonfiguration]:
        with self.datenbank.verbinden() as verbindung:
            zeilen = verbindung.execute("SELECT * FROM server_konfigurationen ORDER BY guild_id").fetchall()
        return [
            ServerKonfiguration.model_validate(
                {
                    "guild_id": zeile["guild_id"],
                    "eingerichtet": bool(zeile["eingerichtet"]),
                    "kategorie_id": zeile["kategorie_id"],
                    "aufträge_kanal_id": zeile["aufträge_kanal_id"],
                    "chronik_kanal_id": zeile["chronik_kanal_id"],
                    "events_kanal_id": zeile["events_kanal_id"],
                    "einstieg_nachricht_id": zeile["einstieg_nachricht_id"],
                    "auftragswand_nachricht_id": zeile["auftragswand_nachricht_id"],
                    "eingerichtet_am": zeile["eingerichtet_am"],
                    "aktualisiert_am": zeile["aktualisiert_am"],
                }
            )
            for zeile in zeilen
        ]

    def speichern(self, konfiguration: ServerKonfiguration) -> ServerKonfiguration:
        aktualisiert = konfiguration.model_copy(update={"aktualisiert_am": datetime.now(timezone.utc)})
        nutzlast = (
            aktualisiert.guild_id,
            int(aktualisiert.eingerichtet),
            aktualisiert.kategorie_id,
            aktualisiert.aufträge_kanal_id,
            aktualisiert.chronik_kanal_id,
            aktualisiert.events_kanal_id,
            aktualisiert.einstieg_nachricht_id,
            aktualisiert.auftragswand_nachricht_id,
            aktualisiert.eingerichtet_am.isoformat(),
            aktualisiert.aktualisiert_am.isoformat(),
        )
        with self.datenbank.verbinden() as verbindung:
            verbindung.execute(
                """
                INSERT INTO server_konfigurationen (
                    guild_id, eingerichtet, kategorie_id, aufträge_kanal_id, chronik_kanal_id, events_kanal_id,
                    einstieg_nachricht_id, auftragswand_nachricht_id, eingerichtet_am, aktualisiert_am
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET
                    eingerichtet = excluded.eingerichtet,
                    kategorie_id = excluded.kategorie_id,
                    aufträge_kanal_id = excluded.aufträge_kanal_id,
                    chronik_kanal_id = excluded.chronik_kanal_id,
                    events_kanal_id = excluded.events_kanal_id,
                    einstieg_nachricht_id = excluded.einstieg_nachricht_id,
                    auftragswand_nachricht_id = excluded.auftragswand_nachricht_id,
                    aktualisiert_am = excluded.aktualisiert_am
                """,
                nutzlast,
            )
        return aktualisiert
