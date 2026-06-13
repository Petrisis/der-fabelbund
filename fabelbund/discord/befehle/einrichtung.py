from __future__ import annotations

from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from fabelbund.anwendung import Anwendungskontext
from fabelbund.discord.auftragswand import auftragswand_erstellen_oder_aktualisieren
from fabelbund.modelle.laufzeit import ServerKonfiguration


class EinrichtungBefehle(commands.Cog):
    def __init__(self, kontext: Anwendungskontext) -> None:
        self.kontext = kontext

    @app_commands.command(name="fabelbund_einrichten", description="Richtet die Fabelbund-Kanäle und die Auftragswand ein.")
    async def fabelbund_einrichten(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message("Dieser Befehl funktioniert nur auf einem Server.", ephemeral=True)
            return
        rechte = getattr(interaction.user, "guild_permissions", None)
        if rechte is None or not rechte.administrator:
            await interaction.response.send_message("Dafür brauchst du Administratorrechte.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        guild = interaction.guild
        kategorie = await self._kategorie_holen_oder_erstellen(guild)
        aufträge = await self._kanal_holen_oder_erstellen(guild, kategorie, "aufträge", auftragskanal=True)
        chronik = await self._kanal_holen_oder_erstellen(guild, kategorie, "chronik")
        events = await self._kanal_holen_oder_erstellen(guild, kategorie, "events", langsam=30)

        bestehend = self.kontext.server.holen(str(guild.id))
        eingerichtet_am = bestehend.eingerichtet_am if bestehend is not None else datetime.now(timezone.utc)
        konfiguration = ServerKonfiguration(
            guild_id=str(guild.id),
            kategorie_id=str(kategorie.id),
            aufträge_kanal_id=str(aufträge.id),
            chronik_kanal_id=str(chronik.id),
            events_kanal_id=str(events.id),
            auftragswand_nachricht_id=bestehend.auftragswand_nachricht_id if bestehend else None,
            eingerichtet_am=eingerichtet_am,
        )
        self.kontext.server.speichern(konfiguration)
        nachricht = await auftragswand_erstellen_oder_aktualisieren(self.kontext, guild)

        await interaction.followup.send(
            "\n".join(
                [
                    "Fabelbund-Serverstruktur ist eingerichtet.",
                    f"Kategorie: {kategorie.mention}",
                    f"Auftragswand: {aufträge.mention}",
                    f"Chronik: {chronik.mention}",
                    f"Events: {events.mention}",
                    f"Auftragswand-Nachricht: {nachricht.jump_url if nachricht else 'nicht erstellt'}",
                ]
            ),
            ephemeral=True,
        )

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
        kanal = discord.utils.get(kategorie.text_channels, name=name)
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
            ),
        }
        await kanal.edit(
            category=kategorie,
            overwrites=überschreibungen,
            slowmode_delay=langsam,
            reason="Fabelbund-Einrichtung",
        )
        return kanal
