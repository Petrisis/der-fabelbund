from __future__ import annotations

import discord

from fabelbund.dienste.spiel_dienst import SpielDienst
from fabelbund.discord.darstellung import aktivität_einbettung, aktivität_ergebnis_einbettung


class PflegeAnsicht(discord.ui.View):
    def __init__(self, spiel: SpielDienst, nutzer_id: str) -> None:
        super().__init__(timeout=180)
        self.spiel = spiel
        self.nutzer_id = nutzer_id
        if self.spiel.laufende_aktivität(nutzer_id) is None:
            self._start_buttons_anlegen()
        else:
            self._aktivitäts_buttons_anlegen()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) == self.nutzer_id:
            return True
        await interaction.response.send_message("Diese Pflegeansicht gehört einem anderen Spieler.", ephemeral=True)
        return False

    def _start_buttons_anlegen(self) -> None:
        self.add_item(self._start_button("sanfte_fellpflege", discord.ButtonStyle.primary))
        self.add_item(self._start_button("kontrollierte_ruhe", discord.ButtonStyle.secondary))

    def _aktivitäts_buttons_anlegen(self) -> None:
        abholen = discord.ui.Button(label="Abholen", style=discord.ButtonStyle.success, custom_id="pflege:abholen")
        abbrechen = discord.ui.Button(label="Abbrechen", style=discord.ButtonStyle.danger, custom_id="pflege:abbrechen")
        abholen.callback = self._abholen
        abbrechen.callback = self._abbrechen
        self.add_item(abholen)
        self.add_item(abbrechen)

    def _start_button(self, aktion_id: str, stil: discord.ButtonStyle) -> discord.ui.Button:
        aktion = self.spiel.inhalte.pflegeaktionen[aktion_id]
        button = discord.ui.Button(label=f"{aktion.name} ({dauer_kurz(aktion.dauer_sekunden)})", style=stil, custom_id=f"pflege:{aktion_id}")

        async def callback(interaction: discord.Interaction) -> None:
            aktivität = self.spiel.pflegeaktivität_starten(self.nutzer_id, aktion_id)
            await interaction.response.edit_message(embed=aktivität_einbettung(aktivität), view=PflegeAnsicht(self.spiel, self.nutzer_id))

        button.callback = callback
        return button

    async def _abholen(self, interaction: discord.Interaction) -> None:
        try:
            ergebnis = self.spiel.aktivität_abholen(self.nutzer_id)
        except ValueError as fehler:
            await interaction.response.send_message(str(fehler), ephemeral=True)
            return
        await interaction.response.edit_message(embed=aktivität_ergebnis_einbettung(ergebnis), view=PflegeAnsicht(self.spiel, self.nutzer_id))

    async def _abbrechen(self, interaction: discord.Interaction) -> None:
        try:
            ergebnis = self.spiel.aktivität_abbrechen(self.nutzer_id)
        except ValueError as fehler:
            await interaction.response.send_message(str(fehler), ephemeral=True)
            return
        await interaction.response.edit_message(embed=aktivität_ergebnis_einbettung(ergebnis), view=PflegeAnsicht(self.spiel, self.nutzer_id))


def dauer_kurz(sekunden: int) -> str:
    minuten = max(1, round(sekunden / 60))
    if minuten < 60:
        return f"{minuten}m"
    stunden, rest = divmod(minuten, 60)
    if rest == 0:
        return f"{stunden}h"
    return f"{stunden}h {rest}m"
