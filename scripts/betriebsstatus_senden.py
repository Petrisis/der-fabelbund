from __future__ import annotations

import asyncio
import logging
from pathlib import Path
import sys

import discord

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fabelbund.anwendung import Anwendungskontext
from fabelbund.discord.betriebsstatus import betriebsstatus_senden
from fabelbund_bot.konfiguration import lade_konfiguration


log = logging.getLogger(__name__)


class BetriebsstatusClient(discord.Client):
    def __init__(self, kontext: Anwendungskontext, text: str) -> None:
        super().__init__(intents=discord.Intents.default())
        self.kontext = kontext
        self.text = text

    async def on_ready(self) -> None:
        try:
            for guild in self.guilds:
                await betriebsstatus_senden(self.kontext, guild, self.text)
                log.info("Betriebsstatus gesendet: %s (%s)", guild.name, guild.id)
        finally:
            await self.close()


async def senden(text: str) -> None:
    konfiguration = lade_konfiguration()
    if not konfiguration.token:
        raise RuntimeError("DISCORD_TOKEN wird benötigt.")
    kontext = Anwendungskontext.aus_pfaden(
        konfiguration.daten_ordner,
        konfiguration.datenbank_pfad,
        zeitfaktor=konfiguration.zeitfaktor,
    )
    client = BetriebsstatusClient(kontext, text)
    await client.start(konfiguration.token)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Aufruf: python scripts/betriebsstatus_senden.py <Text>")
        return 1
    logging.basicConfig(level=logging.INFO)
    asyncio.run(senden(" ".join(argv[1:])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
