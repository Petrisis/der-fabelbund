from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Protocol

import discord

from fabelbund.anwendung import Anwendungskontext
from fabelbund.discord.auftragswand import AuftragswandAnsicht, auftragswand_erstellen_oder_aktualisieren
from fabelbund.discord.eventmarkt import eventmarkt_aktualisieren
from fabelbund.datenbank.speicher.server_speicher import ServerSpeicher
from fabelbund.modelle.laufzeit import ServerKonfiguration


log = logging.getLogger(__name__)


class GuildMitId(Protocol):
    id: int


def server_braucht_einrichtung(speicher: ServerSpeicher, guild_id: str) -> bool:
    konfiguration = speicher.holen(guild_id)
    return konfiguration is None or not konfiguration.eingerichtet


def guild_ids_für_nachholeinrichtung(speicher: ServerSpeicher, guilds: list[GuildMitId]) -> list[str]:
    return [str(guild.id) for guild in guilds if server_braucht_einrichtung(speicher, str(guild.id))]


class ServerEinrichtungDienst:
    def __init__(self, kontext: Anwendungskontext, bot: discord.Client) -> None:
        self.kontext = kontext
        self.bot = bot

    async def guild_sicherstellen(self, guild: discord.Guild) -> ServerKonfiguration | None:
        try:
            bestehend = self.kontext.server.holen(str(guild.id))
            kategorie = await self._kategorie_holen_oder_erstellen(guild)
            aufträge = await self._kanal_holen_oder_erstellen(guild, kategorie, "aufträge", auftragskanal=True)
            chronik = await self._kanal_holen_oder_erstellen(guild, kategorie, "chronik")
            events = await self._kanal_holen_oder_erstellen(guild, kategorie, "events", langsam=30)

            eingerichtet_am = bestehend.eingerichtet_am if bestehend is not None else datetime.now(timezone.utc)
            konfiguration = ServerKonfiguration(
                guild_id=str(guild.id),
                eingerichtet=True,
                kategorie_id=str(kategorie.id),
                aufträge_kanal_id=str(aufträge.id),
                chronik_kanal_id=str(chronik.id),
                events_kanal_id=str(events.id),
                auftragswand_nachricht_id=bestehend.auftragswand_nachricht_id if bestehend else None,
                eingerichtet_am=eingerichtet_am,
            )
            self.kontext.server.speichern(konfiguration)
            nachricht = await auftragswand_erstellen_oder_aktualisieren(self.kontext, guild)
            await eventmarkt_aktualisieren(self.kontext, guild)
            self.bot.add_view(AuftragswandAnsicht(self.kontext, str(guild.id)))
            log.info(
                "Server eingerichtet: %s (%s), Auftragswand-Nachricht: %s",
                guild.name,
                guild.id,
                nachricht.id if nachricht else "nicht erstellt",
            )
            return self.kontext.server.holen(str(guild.id))
        except discord.Forbidden as fehler:
            log.exception("Server-Einrichtung fehlgeschlagen: fehlende Rechte in %s (%s): %s", guild.name, guild.id, fehler)
        except discord.HTTPException as fehler:
            log.exception("Server-Einrichtung fehlgeschlagen in %s (%s): %s", guild.name, guild.id, fehler)
        return None

    async def _kategorie_holen_oder_erstellen(self, guild: discord.Guild) -> discord.CategoryChannel:
        for kanal in guild.categories:
            if kanal.name == "Der Fabelbund":
                return kanal
        return await guild.create_category("Der Fabelbund", reason="Fabelbund-Einrichtung")

    async def _kanal_holen_oder_erstellen(
        self,
        guild: discord.Guild,
        kategorie: discord.CategoryChannel,
        name: str,
        *,
        auftragskanal: bool = False,
        langsam: int = 0,
    ) -> discord.TextChannel:
        kanal = discord.utils.get(guild.text_channels, name=name)
        if kanal is None:
            kanal = await guild.create_text_channel(name, category=kategorie, reason="Fabelbund-Einrichtung")
        überschreibungen = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=True,
                read_message_history=True,
                send_messages=not auftragskanal,
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                read_message_history=True,
                send_messages=True,
                manage_messages=True,
                embed_links=True,
            ),
        }
        await kanal.edit(
            category=kategorie,
            overwrites=überschreibungen,
            slowmode_delay=langsam,
            reason="Fabelbund-Einrichtung",
        )
        return kanal
