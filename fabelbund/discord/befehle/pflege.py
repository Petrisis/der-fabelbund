from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from fabelbund.anwendung import Anwendungskontext
from fabelbund.discord.ansichten.pflege_ansicht import PflegeAnsicht
from fabelbund.discord.darstellung import aktivität_einbettung, fabelwesen_einbettung


class PflegeBefehle(commands.Cog):
    def __init__(self, kontext: Anwendungskontext) -> None:
        self.kontext = kontext

    @app_commands.command(name="pflege", description="Öffnet Pflegeaktionen für deinen aktuellen Auftrag.")
    async def pflege(self, interaction: discord.Interaction) -> None:
        nutzer_id = str(interaction.user.id)
        try:
            aktiver_auftrag = self.kontext.spiel.pflegeauftrag_starten(nutzer_id)
        except ValueError as fehler:
            await interaction.response.send_message(str(fehler), ephemeral=True)
            return
        fabelwesen = self.kontext.spiel.fabelwesen.holen(aktiver_auftrag.fabelwesen_id)
        if fabelwesen is None:
            await interaction.response.send_message("Das Auftrags-Fabelwesen wurde nicht gefunden.", ephemeral=True)
            return
        laufende_aktivität = self.kontext.spiel.laufende_aktivität(nutzer_id)
        if laufende_aktivität is not None:
            await interaction.response.send_message(
                embed=aktivität_einbettung(laufende_aktivität),
                view=PflegeAnsicht(self.kontext.spiel, nutzer_id),
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            embed=fabelwesen_einbettung(fabelwesen, titel="Pflege"),
            view=PflegeAnsicht(self.kontext.spiel, nutzer_id),
            ephemeral=True,
        )
