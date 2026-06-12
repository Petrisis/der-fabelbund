from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from fabelbund.anwendung import Anwendungskontext
from fabelbund.discord.darstellung import fabelwesen_einbettung


class SammlungBefehle(commands.Cog):
    def __init__(self, kontext: Anwendungskontext) -> None:
        self.kontext = kontext

    @app_commands.command(name="sammlung", description="Zeigt deine Fabelwesen-Sammlung.")
    async def sammlung(self, interaction: discord.Interaction) -> None:
        fabelwesen = self.kontext.spiel.sammlung(str(interaction.user.id))
        if not fabelwesen:
            await interaction.response.send_message("Du hast noch keine Fabelwesen.", ephemeral=True)
            return
        embed = fabelwesen_einbettung(fabelwesen[0], titel=f"Sammlung ({len(fabelwesen)})")
        if len(fabelwesen) > 1:
            embed.add_field(name="Weitere Fabelwesen", value="\n".join(d.spitzname for d in fabelwesen[1:10]), inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
