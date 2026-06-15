from __future__ import annotations

import logging

import discord

from fabelbund.anwendung import Anwendungskontext


log = logging.getLogger(__name__)


async def betriebsstatus_senden(kontext: Anwendungskontext, guild: discord.Guild | None, text: str) -> None:
    if guild is None:
        return
    konfiguration = kontext.server.holen(str(guild.id))
    if konfiguration is None or not konfiguration.events_kanal_id:
        return
    kanal = guild.get_channel(int(konfiguration.events_kanal_id))
    if not isinstance(kanal, discord.TextChannel):
        log.warning("Gespeicherter Eventkanal existiert nicht mehr: %s (%s)", guild.name, guild.id)
        return
    await kanal.send(text, silent=True)
