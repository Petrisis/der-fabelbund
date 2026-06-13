from __future__ import annotations

from datetime import datetime, timezone

import discord

from fabelbund.dienste.spiel_dienst import SpielDienst
from fabelbund.discord.darstellung import aktivität_einbettung, aktivität_ergebnis_einbettung
from fabelbund.modelle.laufzeit import Aktivität


class PflegeAnsicht(discord.ui.View):
    def __init__(self, spiel: SpielDienst, nutzer_id: str) -> None:
        super().__init__(timeout=180)
        self.spiel = spiel
        self.nutzer_id = nutzer_id
        self.aktivität = self._angezeigte_aktivität()
        if self.aktivität is None:
            self._start_buttons_anlegen()
        else:
            self._aktivitäts_buttons_anlegen()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) == self.nutzer_id:
            return True
        await interaction.response.send_message("Diese Pflegeansicht gehört einem anderen Spieler.", ephemeral=True)
        return False

    def _start_buttons_anlegen(self) -> None:
        for aktion in self.spiel.inhalte.pflegeaktionen.values():
            if aktion.gesperrt:
                continue
            self.add_item(self._start_button(aktion.aktion_id, stil_für_kategorie(aktion.kategorie)))

    def _aktivitäts_buttons_anlegen(self) -> None:
        aktivität = self.aktivität
        abholen = discord.ui.Button(label="Abholen", style=discord.ButtonStyle.success, custom_id=f"pflege:abholen:{aktivität.id if aktivität else 'offen'}")
        abholen.callback = self._abholen
        self.add_item(abholen)
        if aktivität is not None and aktivität.abbrechbar:
            abbrechen = discord.ui.Button(label="Abbrechen", style=discord.ButtonStyle.danger, custom_id=f"pflege:abbrechen:{aktivität.id}")
            abbrechen.callback = self._abbrechen
            self.add_item(abbrechen)

    def _start_button(self, aktion_id: str, stil: discord.ButtonStyle) -> discord.ui.Button:
        aktion = self.spiel.inhalte.pflegeaktionen[aktion_id]
        button = discord.ui.Button(label=f"{aktion.name} ({dauer_kurz(aktion.dauer_sekunden)})", style=stil, custom_id=f"pflege:{aktion_id}")

        async def callback(interaction: discord.Interaction) -> None:
            try:
                aktivität = self.spiel.pflegeaktivität_starten(self.nutzer_id, aktion_id)
                if aktivität.endet_am <= datetime.now(timezone.utc):
                    ergebnis = self.spiel.aktivität_abholen(self.nutzer_id, aktivität.id)
                    await interaction.response.edit_message(
                        embed=aktivität_ergebnis_einbettung(ergebnis),
                        view=PflegeAnsicht(self.spiel, self.nutzer_id),
                    )
                    return
            except ValueError as fehler:
                await interaction.response.send_message(str(fehler), ephemeral=True)
                return
            await interaction.response.edit_message(embed=aktivität_einbettung(aktivität), view=PflegeAnsicht(self.spiel, self.nutzer_id))

        button.callback = callback
        return button

    async def _abholen(self, interaction: discord.Interaction) -> None:
        try:
            ergebnis = self.spiel.aktivität_abholen(self.nutzer_id, self.aktivität.id if self.aktivität else None)
        except ValueError as fehler:
            await interaction.response.send_message(str(fehler), ephemeral=True)
            return
        await interaction.response.edit_message(embed=aktivität_ergebnis_einbettung(ergebnis), view=PflegeAnsicht(self.spiel, self.nutzer_id))

    async def _abbrechen(self, interaction: discord.Interaction) -> None:
        try:
            ergebnis = self.spiel.aktivität_abbrechen(self.nutzer_id, self.aktivität.id if self.aktivität else None)
        except ValueError as fehler:
            await interaction.response.send_message(str(fehler), ephemeral=True)
            return
        await interaction.response.edit_message(embed=aktivität_ergebnis_einbettung(ergebnis), view=PflegeAnsicht(self.spiel, self.nutzer_id))

    def _angezeigte_aktivität(self) -> Aktivität | None:
        aktive_spieleraktivität = self.spiel.laufende_aktive_spieleraktivität(self.nutzer_id)
        if aktive_spieleraktivität is not None:
            return aktive_spieleraktivität

        aktiver_auftrag = self.spiel.aktiver_auftrag(self.nutzer_id)
        if aktiver_auftrag is None:
            return None
        return self.spiel.laufende_aktivität_für_fabelwesen(aktiver_auftrag.fabelwesen_id)


def dauer_kurz(sekunden: int) -> str:
    if sekunden <= 0:
        return "sofort"
    minuten = max(1, round(sekunden / 60))
    if minuten < 60:
        return f"{minuten}m"
    stunden, rest = divmod(minuten, 60)
    if rest == 0:
        return f"{stunden}h"
    return f"{stunden}h {rest}m"


def stil_für_kategorie(kategorie: str) -> discord.ButtonStyle:
    if kategorie == "spiel":
        return discord.ButtonStyle.success
    if kategorie == "ruhe":
        return discord.ButtonStyle.secondary
    if kategorie == "check":
        return discord.ButtonStyle.secondary
    if kategorie == "training":
        return discord.ButtonStyle.primary
    return discord.ButtonStyle.primary
