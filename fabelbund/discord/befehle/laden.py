from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from fabelbund.anwendung import Anwendungskontext
from fabelbund.discord.darstellung import kauf_einbettung
from fabelbund.discord.zeitlimits import EPHEMERE_ANSICHT_TIMEOUT_SEKUNDEN


class LadenBefehle(commands.Cog):
    def __init__(self, kontext: Anwendungskontext) -> None:
        self.kontext = kontext

    @app_commands.command(name="laden", description="Öffnet den Fabelbund-Laden.")
    async def laden(self, interaction: discord.Interaction) -> None:
        nutzer_id = str(interaction.user.id)
        await interaction.response.send_message(embed=laden_einbettung(self.kontext, nutzer_id), view=LadenAnsicht(self.kontext, nutzer_id), ephemeral=True)


class LadenAnsicht(discord.ui.View):
    def __init__(self, kontext: Anwendungskontext, nutzer_id: str) -> None:
        super().__init__(timeout=EPHEMERE_ANSICHT_TIMEOUT_SEKUNDEN)
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
        self.add_item(self._navigation_button("Fablinge", "laden:fablinge", self._fablinge_öffnen))
        self.add_item(self._navigation_button("Inventar", "laden:inventar", self._inventar_öffnen))
        self.add_item(self._navigation_button("Aufträge", "laden:aufträge", self._aufträge_öffnen))

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

    def _navigation_button(self, label: str, custom_id: str, callback) -> discord.ui.Button:
        button = discord.ui.Button(label=label, style=discord.ButtonStyle.primary, custom_id=custom_id, row=4)
        button.callback = callback
        return button

    async def _fablinge_öffnen(self, interaction: discord.Interaction) -> None:
        from fabelbund.discord.ansichten.stall_ansicht import StallAnsicht, stallübersicht_einbettung

        fabelwesen = self.kontext.spiel.sammlung(self.nutzer_id)
        kapazität = self.kontext.spiel.stall_kapazität(self.nutzer_id)
        await interaction.response.edit_message(
            embed=stallübersicht_einbettung(self.kontext.spiel, self.nutzer_id, fabelwesen, kapazität),
            view=StallAnsicht(self.kontext.spiel, self.nutzer_id, fabelwesen, kapazität, kontext=self.kontext),
        )

    async def _inventar_öffnen(self, interaction: discord.Interaction) -> None:
        from fabelbund.discord.befehle.inventar import InventarAnsicht, inventar_einbettung

        await interaction.response.edit_message(
            embed=inventar_einbettung(self.kontext, self.nutzer_id),
            view=InventarAnsicht(self.kontext, self.nutzer_id),
        )

    async def _aufträge_öffnen(self, interaction: discord.Interaction) -> None:
        from fabelbund.discord.befehle.auftrag import AuftragAnsicht, auftragsziel_text
        from fabelbund.discord.darstellung import auftrag_einbettung

        aktiver_auftrag = self.kontext.spiel.aktiver_auftrag(self.nutzer_id)
        if aktiver_auftrag is None:
            await interaction.response.send_message("Du hast gerade keinen aktiven Auftrag.", ephemeral=True)
            return
        auftrag = self.kontext.spiel.inhalte.aufträge[aktiver_auftrag.auftrag_id]
        fabelwesen = self.kontext.spiel.fabelwesen.holen(aktiver_auftrag.fabelwesen_id)
        embed = auftrag_einbettung(aktiver_auftrag, auftrag, fabelwesen, self.kontext.spiel.auftrag_fablinge(aktiver_auftrag))
        embed.add_field(name="Aufgabe", value=auftragsziel_text(auftrag.ziele), inline=False)
        await interaction.response.edit_message(embed=embed, view=AuftragAnsicht(self.kontext, self.nutzer_id))


def laden_einbettung(kontext: Anwendungskontext, nutzer_id: str) -> discord.Embed:
    spieler = kontext.spiel.stelle_spieler_sicher(nutzer_id)
    embed = discord.Embed(title="Fabelbund-Laden", color=discord.Color.green())
    embed.add_field(name="Geld", value=f"{spieler.geld} Credits", inline=True)
    embed.add_field(name="Sortiment", value=sortiment_text(kontext), inline=False)
    return embed


def sortiment_text(kontext: Anwendungskontext) -> str:
    zeilen = []
    for gegenstand in kontext.spiel.inhalte.gegenstände.values():
        zeilen.append(f"{gegenstand.name}: {gegenstand.preis} Credits")
    return "\n".join(zeilen)
