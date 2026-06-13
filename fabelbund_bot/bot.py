from __future__ import annotations

import logging

import discord
from discord.ext import commands

from fabelbund.anwendung import Anwendungskontext
from fabelbund.discord.auftragswand import AuftragswandAnsicht
from fabelbund.discord.befehle.auftrag import AuftragBefehle
from fabelbund.discord.befehle.einrichtung import EinrichtungBefehle
from fabelbund.discord.befehle.inventar import InventarBefehle
from fabelbund.discord.befehle.laden import LadenBefehle
from fabelbund.discord.befehle.pflege import PflegeBefehle
from fabelbund.discord.befehle.profil import ProfilBefehle
from fabelbund.discord.befehle.sammlung import SammlungBefehle
from fabelbund.discord.befehle.stall import StallBefehle
from fabelbund_bot.konfiguration import lade_konfiguration


log = logging.getLogger(__name__)


class FabelbundBot(commands.Bot):
    def __init__(self, kontext: Anwendungskontext, befehle_synchronisieren: bool, testserver_id: int | None) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents, activity=discord.Game(name="Der Fabelbund"))
        self.kontext = kontext
        self.befehle_synchronisieren = befehle_synchronisieren
        self.testserver_id = testserver_id

    async def setup_hook(self) -> None:
        for server in self.kontext.server.auflisten():
            self.add_view(AuftragswandAnsicht(self.kontext, server.guild_id))
        await self.add_cog(EinrichtungBefehle(self.kontext))
        await self.add_cog(ProfilBefehle(self.kontext))
        await self.add_cog(SammlungBefehle(self.kontext))
        await self.add_cog(StallBefehle(self.kontext))
        await self.add_cog(AuftragBefehle(self.kontext))
        await self.add_cog(PflegeBefehle(self.kontext))
        await self.add_cog(LadenBefehle(self.kontext))
        await self.add_cog(InventarBefehle(self.kontext))
        if self.befehle_synchronisieren:
            if self.testserver_id is not None:
                testserver = discord.Object(id=self.testserver_id)
                self.tree.copy_global_to(guild=testserver)
                synchronisierte_befehle = await self.tree.sync(guild=testserver)
                log.info("%s Discord-Befehle für Testserver %s synchronisiert.", len(synchronisierte_befehle), self.testserver_id)
            else:
                synchronisierte_befehle = await self.tree.sync()
                log.info("%s globale Discord-Befehle synchronisiert.", len(synchronisierte_befehle))

    async def on_ready(self) -> None:
        assert self.user is not None
        log.info("Angemeldet als %s (%s).", self.user, self.user.id)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    konfiguration = lade_konfiguration()
    if not konfiguration.token:
        raise RuntimeError("DISCORD_TOKEN wird benötigt.")

    kontext = Anwendungskontext.aus_pfaden(
        konfiguration.daten_ordner,
        konfiguration.datenbank_pfad,
        zeitfaktor=konfiguration.zeitfaktor,
    )
    bot = FabelbundBot(
        kontext,
        befehle_synchronisieren=konfiguration.befehle_synchronisieren,
        testserver_id=konfiguration.testserver_id,
    )
    bot.run(konfiguration.token)


if __name__ == "__main__":
    main()
