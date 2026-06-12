from __future__ import annotations

import logging

import discord
from discord.ext import commands

from fabelbund.anwendung import Anwendungskontext
from fabelbund.discord.befehle.auftrag import AuftragBefehle
from fabelbund.discord.befehle.pflege import PflegeBefehle
from fabelbund.discord.befehle.profil import ProfilBefehle
from fabelbund.discord.befehle.sammlung import SammlungBefehle
from fabelbund_bot.konfiguration import lade_konfiguration


log = logging.getLogger(__name__)


class FabelbundBot(commands.Bot):
    def __init__(self, kontext: Anwendungskontext, befehle_synchronisieren: bool) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents, activity=discord.Game(name="Der Fabelbund"))
        self.kontext = kontext
        self.befehle_synchronisieren = befehle_synchronisieren

    async def setup_hook(self) -> None:
        await self.add_cog(ProfilBefehle(self.kontext))
        await self.add_cog(SammlungBefehle(self.kontext))
        await self.add_cog(AuftragBefehle(self.kontext))
        await self.add_cog(PflegeBefehle(self.kontext))
        if self.befehle_synchronisieren:
            synchronisierte_befehle = await self.tree.sync()
            log.info("%s Discord-Befehle synchronisiert.", len(synchronisierte_befehle))


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    konfiguration = lade_konfiguration()
    if not konfiguration.token:
        raise RuntimeError("DISCORD_TOKEN wird benoetigt.")

    kontext = Anwendungskontext.aus_pfaden(konfiguration.daten_ordner, konfiguration.datenbank_pfad)
    bot = FabelbundBot(kontext, befehle_synchronisieren=konfiguration.befehle_synchronisieren)
    bot.run(konfiguration.token)


if __name__ == "__main__":
    main()
