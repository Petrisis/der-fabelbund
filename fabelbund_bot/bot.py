from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands

from fabelbund.anwendung import Anwendungskontext
from fabelbund.discord.auftragswand import AuftragsnavigationAnsicht, AuftragswandAnsicht, TutorialEinstiegAnsicht, auftragswand_aktualisieren
from fabelbund.discord.befehle.auftrag import AuftragBefehle
from fabelbund.discord.befehle.inventar import InventarBefehle
from fabelbund.discord.befehle.laden import LadenBefehle
from fabelbund.discord.befehle.profil import ProfilBefehle
from fabelbund.discord.befehle.sammlung import SammlungBefehle
from fabelbund.discord.befehle.stall import StallBefehle
from fabelbund.discord.eventmarkt import eventmarkt_ansichten, eventmarkt_aktualisieren
from fabelbund.discord.server_einrichtung import ServerEinrichtungDienst, guild_ids_für_nachholeinrichtung
from fabelbund_bot.konfiguration import lade_konfiguration


log = logging.getLogger(__name__)


class FabelbundBot(commands.Bot):
    def __init__(self, kontext: Anwendungskontext, befehle_synchronisieren: bool, testserver_id: int | None) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents, activity=discord.Game(name="Der Fabelbund"))
        self.kontext = kontext
        self.befehle_synchronisieren = befehle_synchronisieren
        self.testserver_id = testserver_id
        self.server_einrichtung = ServerEinrichtungDienst(kontext, self)
        self.server_einrichtung_geprüft = False
        self.auftragswand_task: asyncio.Task[None] | None = None
        self.eventmarkt_task: asyncio.Task[None] | None = None

    async def setup_hook(self) -> None:
        for ansicht in eventmarkt_ansichten(self.kontext):
            self.add_view(ansicht)
        for server in self.kontext.server.auflisten():
            if server.eingerichtet:
                self.add_view(TutorialEinstiegAnsicht(self.kontext))
                self.add_view(AuftragsnavigationAnsicht(self.kontext))
                self.add_view(AuftragswandAnsicht(self.kontext, server.guild_id))
        await self.add_cog(ProfilBefehle(self.kontext))
        await self.add_cog(SammlungBefehle(self.kontext))
        await self.add_cog(StallBefehle(self.kontext))
        await self.add_cog(AuftragBefehle(self.kontext))
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
        if self.server_einrichtung_geprüft:
            return
        self.server_einrichtung_geprüft = True
        nachzuholen = guild_ids_für_nachholeinrichtung(self.kontext.server, list(self.guilds))
        for guild in self.guilds:
            if str(guild.id) in nachzuholen:
                await self.server_einrichtung.guild_sicherstellen(guild)
            else:
                await auftragswand_aktualisieren(self.kontext, guild)
                await eventmarkt_aktualisieren(self.kontext, guild)
        if self.auftragswand_task is None or self.auftragswand_task.done():
            self.auftragswand_task = asyncio.create_task(self._auftragswand_regelmäßig_aktualisieren())
        if self.eventmarkt_task is None or self.eventmarkt_task.done():
            self.eventmarkt_task = asyncio.create_task(self._eventmarkt_regelmäßig_aktualisieren())

    async def on_guild_join(self, guild: discord.Guild) -> None:
        await self.server_einrichtung.guild_sicherstellen(guild)

    async def _auftragswand_regelmäßig_aktualisieren(self) -> None:
        while not self.is_closed():
            await asyncio.sleep(7 * 60)
            for guild in list(self.guilds):
                try:
                    await auftragswand_aktualisieren(self.kontext, guild)
                except Exception:
                    log.exception("Auftragswand konnte nicht automatisch aktualisiert werden: %s (%s)", guild.name, guild.id)

    async def _eventmarkt_regelmäßig_aktualisieren(self) -> None:
        while not self.is_closed():
            await asyncio.sleep(30 * 60)
            for guild in list(self.guilds):
                try:
                    await eventmarkt_aktualisieren(self.kontext, guild)
                except Exception:
                    log.exception("Eventmarkt konnte nicht automatisch aktualisiert werden: %s (%s)", guild.name, guild.id)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    konfiguration = lade_konfiguration()
    if not konfiguration.token:
        raise RuntimeError("DISCORD_TOKEN wird benötigt.")
    log.info("Zeitfaktor: %sx", konfiguration.zeitfaktor)

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
