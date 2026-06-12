from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from fabelbund.anwendung import Anwendungskontext
from fabelbund.discord.ansichten.stall_ansicht import MAXIMALE_STALL_BUTTONS, StallAnsicht, stalltyp_label


class StallBefehle(commands.Cog):
    def __init__(self, kontext: Anwendungskontext) -> None:
        self.kontext = kontext

    @app_commands.command(name="stall", description="Öffnet deine Stallübersicht.")
    async def stall(self, interaction: discord.Interaction) -> None:
        nutzer_id = str(interaction.user.id)
        fabelwesen = self.kontext.spiel.sammlung(nutzer_id)
        kapazität = self.kontext.spiel.stall_kapazität(nutzer_id)

        embed = discord.Embed(title="Stall", color=discord.Color.blurple())
        embed.description = "Wähle einen Fabling aus, um seinen Zustand einzuschätzen."
        if not fabelwesen:
            embed.description = "Dein Stall ist noch leer. Das Tutorial wird dir den ersten Fabling anvertrauen."
        embed.add_field(name="Fablinge", value=f"{len(fabelwesen)}/{kapazität}", inline=True)
        embed.add_field(name="Maximal möglich", value=str(MAXIMALE_STALL_BUTTONS), inline=True)
        belegung = self.kontext.spiel.stallbelegung(nutzer_id)
        if belegung:
            embed.add_field(
                name="Ställe",
                value="\n".join(f"{stalltyp_label(eintrag.stalltyp)}: {eintrag.belegt}/{eintrag.kapazität}" for eintrag in belegung),
                inline=False,
            )
        await interaction.response.send_message(
            embed=embed,
            view=StallAnsicht(self.kontext.spiel, nutzer_id, fabelwesen, kapazität),
            ephemeral=True,
        )
