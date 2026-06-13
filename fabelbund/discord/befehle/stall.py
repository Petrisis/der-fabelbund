from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from fabelbund.anwendung import Anwendungskontext
from fabelbund.discord.ansichten.stall_ansicht import StallAnsicht, stallübersicht_einbettung


class StallBefehle(commands.Cog):
    def __init__(self, kontext: Anwendungskontext) -> None:
        self.kontext = kontext

    @app_commands.command(name="fablinge", description="Öffnet deine Fablinge, Ställe und Betreuung.")
    async def fablinge(self, interaction: discord.Interaction) -> None:
        nutzer_id = str(interaction.user.id)
        fabelwesen = self.kontext.spiel.sammlung(nutzer_id)
        kapazität = self.kontext.spiel.stall_kapazität(nutzer_id)
        await interaction.response.send_message(
            embed=stallübersicht_einbettung(self.kontext.spiel, nutzer_id, fabelwesen, kapazität),
            view=StallAnsicht(self.kontext.spiel, nutzer_id, fabelwesen, kapazität),
            ephemeral=True,
        )
