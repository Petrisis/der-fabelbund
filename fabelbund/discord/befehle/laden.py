from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from fabelbund.anwendung import Anwendungskontext
from fabelbund.discord.darstellung import kauf_einbettung


class LadenBefehle(commands.Cog):
    def __init__(self, kontext: Anwendungskontext) -> None:
        self.kontext = kontext

    @app_commands.command(name="laden", description="Öffnet den Fabelbund-Laden.")
    async def laden(self, interaction: discord.Interaction) -> None:
        nutzer_id = str(interaction.user.id)
        spieler = self.kontext.spiel.stelle_spieler_sicher(nutzer_id)
        embed = discord.Embed(title="Fabelbund-Laden", color=discord.Color.green())
        embed.add_field(name="Geld", value=f"{spieler.geld} Credits", inline=True)
        embed.add_field(name="Sortiment", value=sortiment_text(self.kontext), inline=False)
        await interaction.response.send_message(embed=embed, view=LadenAnsicht(self.kontext, nutzer_id), ephemeral=True)


class LadenAnsicht(discord.ui.View):
    def __init__(self, kontext: Anwendungskontext, nutzer_id: str) -> None:
        super().__init__(timeout=180)
        self.kontext = kontext
        self.nutzer_id = nutzer_id
        for gegenstand in kontext.spiel.inhalte.gegenstände.values():
            button = discord.ui.Button(
                label=f"{gegenstand.name} ({gegenstand.preis})",
                style=discord.ButtonStyle.secondary,
                custom_id=f"laden:kaufen:{gegenstand.gegenstand_id}",
            )
            button.callback = self._kaufen_callback(gegenstand.gegenstand_id)
            self.add_item(button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) == self.nutzer_id:
            return True
        await interaction.response.send_message("Dieser Ladenbesuch gehört einem anderen Spieler.", ephemeral=True)
        return False

    def _kaufen_callback(self, gegenstand_id: str):
        async def callback(interaction: discord.Interaction) -> None:
            try:
                ergebnis = self.kontext.spiel.gegenstand_kaufen(self.nutzer_id, gegenstand_id)
            except ValueError as fehler:
                await interaction.response.send_message(str(fehler), ephemeral=True)
                return
            await interaction.response.edit_message(embed=kauf_einbettung(ergebnis), view=LadenAnsicht(self.kontext, self.nutzer_id))

        return callback


def sortiment_text(kontext: Anwendungskontext) -> str:
    zeilen = []
    for gegenstand in kontext.spiel.inhalte.gegenstände.values():
        zeilen.append(f"{gegenstand.name}: {gegenstand.preis} Credits")
    return "\n".join(zeilen)
