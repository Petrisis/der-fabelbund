from __future__ import annotations

import asyncio
import logging

import discord

from fabelbund.anwendung import Anwendungskontext
from fabelbund.discord.auftragswand import auftragswand_erstellen_oder_aktualisieren
from fabelbund.discord.eventmarkt import eventmarkt_aktualisieren
from fabelbund_bot.konfiguration import lade_konfiguration


log = logging.getLogger(__name__)


class KanalNeuaufbauClient(discord.Client):
    def __init__(self, kontext: Anwendungskontext) -> None:
        super().__init__(intents=discord.Intents.default())
        self.kontext = kontext

    async def on_ready(self) -> None:
        try:
            for guild in self.guilds:
                await self._guild_neu_aufbauen(guild)
        finally:
            await self.close()

    async def _guild_neu_aufbauen(self, guild: discord.Guild) -> None:
        konfiguration = self.kontext.server.holen(str(guild.id))
        if konfiguration is None or not konfiguration.eingerichtet:
            log.info("Server ohne Einrichtung übersprungen: %s (%s)", guild.name, guild.id)
            return

        for kanal_id in (konfiguration.aufträge_kanal_id, konfiguration.events_kanal_id):
            if not kanal_id:
                continue
            kanal = guild.get_channel(int(kanal_id))
            if isinstance(kanal, discord.TextChannel):
                await kanal.purge(limit=None, reason="Fabelbund-Nachrichten neu generieren")
                log.info("Kanal geleert: #%s in %s", kanal.name, guild.name)

        self.kontext.server.speichern(
            konfiguration.model_copy(update={"einstieg_nachricht_id": None, "auftragswand_nachricht_id": None})
        )
        await auftragswand_erstellen_oder_aktualisieren(self.kontext, guild)
        await eventmarkt_aktualisieren(self.kontext, guild)
        log.info("Fabelbund-Nachrichten neu aufgebaut: %s (%s)", guild.name, guild.id)


async def neu_aufbauen() -> None:
    konfiguration = lade_konfiguration()
    if not konfiguration.token:
        raise RuntimeError("DISCORD_TOKEN wird benötigt.")
    kontext = Anwendungskontext.aus_pfaden(
        konfiguration.daten_ordner,
        konfiguration.datenbank_pfad,
        zeitfaktor=konfiguration.zeitfaktor,
    )
    client = KanalNeuaufbauClient(kontext)
    await client.start(konfiguration.token)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(neu_aufbauen())


if __name__ == "__main__":
    main()
