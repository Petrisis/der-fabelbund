from __future__ import annotations

from datetime import datetime

from fabelbund.datenbank.datenbank import Datenbank
from fabelbund.modelle.laufzeit import Wettbewerb, WettbewerbAnmeldung


class WettbewerbSpeicher:
    def __init__(self, datenbank: Datenbank) -> None:
        self.datenbank = datenbank

    def speichern(self, wettbewerb: Wettbewerb) -> None:
        nutzlast = (
            wettbewerb.id,
            wettbewerb.guild_id,
            wettbewerb.status,
            wettbewerb.wert,
            wettbewerb.beginnt_am.isoformat(),
            wettbewerb.anmeldeschluss_am.isoformat(),
            wettbewerb.preisgeld,
            wettbewerb.nachricht_id,
            wettbewerb.discord_event_id,
            wettbewerb.erstellt_am.isoformat(),
        )
        with self.datenbank.verbinden() as verbindung:
            verbindung.execute(
                """
                INSERT INTO wettbewerbe (
                    id, guild_id, status, wert, beginnt_am, anmeldeschluss_am, preisgeld,
                    nachricht_id, discord_event_id, erstellt_am
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status = excluded.status,
                    wert = excluded.wert,
                    beginnt_am = excluded.beginnt_am,
                    anmeldeschluss_am = excluded.anmeldeschluss_am,
                    preisgeld = excluded.preisgeld,
                    nachricht_id = excluded.nachricht_id,
                    discord_event_id = excluded.discord_event_id
                """,
                nutzlast,
            )

    def holen(self, wettbewerb_id: str) -> Wettbewerb | None:
        with self.datenbank.verbinden() as verbindung:
            zeile = verbindung.execute("SELECT * FROM wettbewerbe WHERE id = ?", (wettbewerb_id,)).fetchone()
        return self._wettbewerb_aus_zeile(zeile) if zeile is not None else None

    def nächster_offener_für_guild(self, guild_id: str) -> Wettbewerb | None:
        with self.datenbank.verbinden() as verbindung:
            zeile = verbindung.execute(
                """
                SELECT * FROM wettbewerbe
                WHERE guild_id = ? AND status IN ('offen', 'läuft')
                ORDER BY beginnt_am
                LIMIT 1
                """,
                (guild_id,),
            ).fetchone()
        return self._wettbewerb_aus_zeile(zeile) if zeile is not None else None

    def fällige(self, jetzt: datetime) -> list[Wettbewerb]:
        with self.datenbank.verbinden() as verbindung:
            zeilen = verbindung.execute(
                """
                SELECT * FROM wettbewerbe
                WHERE status IN ('offen', 'läuft') AND beginnt_am <= ?
                ORDER BY beginnt_am
                """,
                (jetzt.isoformat(),),
            ).fetchall()
        return [self._wettbewerb_aus_zeile(zeile) for zeile in zeilen]

    def anmelden(self, anmeldung: WettbewerbAnmeldung) -> None:
        with self.datenbank.verbinden() as verbindung:
            verbindung.execute(
                """
                INSERT INTO wettbewerb_anmeldungen (wettbewerb_id, spieler_id, fabelwesen_id, angemeldet_am)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(wettbewerb_id, spieler_id) DO UPDATE SET
                    fabelwesen_id = excluded.fabelwesen_id,
                    angemeldet_am = excluded.angemeldet_am
                """,
                (
                    anmeldung.wettbewerb_id,
                    anmeldung.spieler_id,
                    anmeldung.fabelwesen_id,
                    anmeldung.angemeldet_am.isoformat(),
                ),
            )

    def anmeldungen(self, wettbewerb_id: str) -> list[WettbewerbAnmeldung]:
        with self.datenbank.verbinden() as verbindung:
            zeilen = verbindung.execute(
                """
                SELECT * FROM wettbewerb_anmeldungen
                WHERE wettbewerb_id = ?
                ORDER BY angemeldet_am
                """,
                (wettbewerb_id,),
            ).fetchall()
        return [
            WettbewerbAnmeldung(
                wettbewerb_id=zeile["wettbewerb_id"],
                spieler_id=zeile["spieler_id"],
                fabelwesen_id=zeile["fabelwesen_id"],
                angemeldet_am=zeile["angemeldet_am"],
            )
            for zeile in zeilen
        ]

    def _wettbewerb_aus_zeile(self, zeile) -> Wettbewerb:
        return Wettbewerb(
            id=zeile["id"],
            guild_id=zeile["guild_id"],
            status=zeile["status"],
            wert=zeile["wert"],
            beginnt_am=zeile["beginnt_am"],
            anmeldeschluss_am=zeile["anmeldeschluss_am"],
            preisgeld=zeile["preisgeld"],
            nachricht_id=zeile["nachricht_id"],
            discord_event_id=zeile["discord_event_id"],
            erstellt_am=zeile["erstellt_am"],
        )
