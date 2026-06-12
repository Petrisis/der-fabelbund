from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from fabelbund.anwendung import Anwendungskontext
from fabelbund.discord.ansichten.pflege_ansicht import PflegeAnsicht
from fabelbund.discord.darstellung import fabelwesen_einbettung


class PflegeBefehle(commands.Cog):
    def __init__(self, kontext: Anwendungskontext) -> None:
        self.kontext = kontext

    @app_commands.command(name="pflege", description="Oeffnet Pflegeaktionen fuer deinen aktuellen Auftrag.")
    async def pflege(self, interaction: discord.Interaction) -> None:
        nutzer_id = str(interaction.user.id)
        aktiver_auftrag = self.kontext.spiel.pflegeauftrag_starten(nutzer_id)
        fabelwesen = self.kontext.spiel.fabelwesen.holen(aktiver_auftrag.fabelwesen_id)
        if fabelwesen is None:
            await interaction.response.send_message("Das Auftrags-Fabelwesen wurde nicht gefunden.", ephemeral=True)
            return
        await interaction.response.send_message(
            embed=fabelwesen_einbettung(fabelwesen, titel="Pflege"),
            view=PflegeAnsicht(self.kontext.spiel, nutzer_id),
            ephemeral=True,
        )
