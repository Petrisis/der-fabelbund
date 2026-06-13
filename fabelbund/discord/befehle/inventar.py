from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from fabelbund.anwendung import Anwendungskontext
from fabelbund.discord.darstellung import fütterung_einbettung


class InventarBefehle(commands.Cog):
    def __init__(self, kontext: Anwendungskontext) -> None:
        self.kontext = kontext

    @app_commands.command(name="inventar", description="Zeigt deine Gegenstände.")
    async def inventar(self, interaction: discord.Interaction) -> None:
        nutzer_id = str(interaction.user.id)
        inventar = self.kontext.spiel.inventar(nutzer_id)
        embed = discord.Embed(title="Inventar", color=discord.Color.green())
        if inventar:
            embed.description = inventar_text(self.kontext, inventar)
        else:
            embed.description = "Dein Inventar ist leer."
        await interaction.response.send_message(embed=embed, view=InventarAnsicht(self.kontext, nutzer_id), ephemeral=True)


class InventarAnsicht(discord.ui.View):
    def __init__(self, kontext: Anwendungskontext, nutzer_id: str) -> None:
        super().__init__(timeout=180)
        self.kontext = kontext
        self.nutzer_id = nutzer_id
        inventar = kontext.spiel.inventar(nutzer_id)
        for gegenstand_id, anzahl in inventar.items():
            gegenstand = kontext.spiel.inhalte.gegenstände.get(gegenstand_id)
            if gegenstand is None or gegenstand.kategorie != "futter":
                continue
            button = discord.ui.Button(
                label=f"{gegenstand.name} geben ({anzahl})",
                style=discord.ButtonStyle.success,
                custom_id=f"inventar:futter:{gegenstand_id}",
            )
            button.callback = self._füttern_callback(gegenstand_id)
            self.add_item(button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) == self.nutzer_id:
            return True
        await interaction.response.send_message("Dieses Inventar gehört einem anderen Spieler.", ephemeral=True)
        return False

    def _füttern_callback(self, gegenstand_id: str):
        async def callback(interaction: discord.Interaction) -> None:
            try:
                ergebnis = self.kontext.spiel.futter_geben(self.nutzer_id, gegenstand_id)
            except ValueError as fehler:
                await interaction.response.send_message(str(fehler), ephemeral=True)
                return
            await interaction.response.edit_message(embed=fütterung_einbettung(ergebnis), view=InventarAnsicht(self.kontext, self.nutzer_id))

        return callback


def inventar_text(kontext: Anwendungskontext, inventar: dict[str, int]) -> str:
    zeilen = []
    for gegenstand_id, anzahl in inventar.items():
        gegenstand = kontext.spiel.inhalte.gegenstände.get(gegenstand_id)
        name = gegenstand.name if gegenstand else gegenstand_id
        zeilen.append(f"{anzahl}x {name}")
    return "\n".join(zeilen)
