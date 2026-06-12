from __future__ import annotations

import discord

from fabelbund.dienste.spiel_dienst import SpielDienst
from fabelbund.discord.darstellung import fabelwesen_einbettung


class PflegeAnsicht(discord.ui.View):
    def __init__(self, spiel: SpielDienst, nutzer_id: str) -> None:
        super().__init__(timeout=180)
        self.spiel = spiel
        self.nutzer_id = nutzer_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) == self.nutzer_id:
            return True
        await interaction.response.send_message("Diese Pflegeansicht gehoert einem anderen Spieler.", ephemeral=True)
        return False

    @discord.ui.button(label="Sanfte Fellpflege", style=discord.ButtonStyle.primary, custom_id="pflege:sanfte_fellpflege")
    async def sanfte_fellpflege(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        ergebnis = self.spiel.pflege_anwenden(self.nutzer_id, "sanfte_fellpflege")
        embed = fabelwesen_einbettung(ergebnis.fabelwesen, titel="Pflege abgeschlossen")
        if ergebnis.auftrag_abgeschlossen:
            ruf = ", ".join(f"{schluessel} +{wert}" for schluessel, wert in ergebnis.ruf_erhalten.items())
            embed.add_field(
                name="Auftrag abgeschlossen",
                value=f"+{ergebnis.geld_erhalten} Credits\n{ruf or 'Ruf unveraendert'}",
                inline=False,
            )
            button.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Kontrollierte Ruhe", style=discord.ButtonStyle.secondary, custom_id="pflege:kontrollierte_ruhe")
    async def kontrollierte_ruhe(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        ergebnis = self.spiel.pflege_anwenden(self.nutzer_id, "kontrollierte_ruhe")
        embed = fabelwesen_einbettung(ergebnis.fabelwesen, titel="Ruhe abgeschlossen")
        if ergebnis.auftrag_abgeschlossen:
            ruf = ", ".join(f"{schluessel} +{wert}" for schluessel, wert in ergebnis.ruf_erhalten.items())
            embed.add_field(
                name="Auftrag abgeschlossen",
                value=f"+{ergebnis.geld_erhalten} Credits\n{ruf or 'Ruf unveraendert'}",
                inline=False,
            )
            for element in self.children:
                if isinstance(element, discord.ui.Button):
                    element.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)
