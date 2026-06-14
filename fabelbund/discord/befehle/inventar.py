from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from fabelbund.anwendung import Anwendungskontext
from fabelbund.discord.zeitlimits import EPHEMERE_ANSICHT_TIMEOUT_SEKUNDEN


class InventarBefehle(commands.Cog):
    def __init__(self, kontext: Anwendungskontext) -> None:
        self.kontext = kontext

    @app_commands.command(name="inventar", description="Zeigt deine Gegenstände.")
    async def inventar(self, interaction: discord.Interaction) -> None:
        nutzer_id = str(interaction.user.id)
        await interaction.response.send_message(embed=inventar_einbettung(self.kontext, nutzer_id), view=InventarAnsicht(self.kontext, nutzer_id), ephemeral=True)


class InventarAnsicht(discord.ui.View):
    def __init__(self, kontext: Anwendungskontext, nutzer_id: str) -> None:
        super().__init__(timeout=EPHEMERE_ANSICHT_TIMEOUT_SEKUNDEN)
        self.kontext = kontext
        self.nutzer_id = nutzer_id
        self.add_item(self._navigation_button("Profil", "inventar:profil", self._profil_öffnen))
        self.add_item(self._navigation_button("Fablinge", "inventar:fablinge", self._fablinge_öffnen))
        self.add_item(self._navigation_button("Laden", "inventar:laden", self._laden_öffnen))
        self.add_item(self._navigation_button("Aufträge", "inventar:aufträge", self._aufträge_öffnen))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) == self.nutzer_id:
            return True
        await interaction.response.send_message("Dieses Inventar gehört einem anderen Spieler.", ephemeral=True)
        return False

    def _navigation_button(self, label: str, custom_id: str, callback) -> discord.ui.Button:
        button = discord.ui.Button(label=label, style=discord.ButtonStyle.primary, custom_id=custom_id, row=4)
        button.callback = callback
        return button

    async def _profil_öffnen(self, interaction: discord.Interaction) -> None:
        from fabelbund.discord.befehle.profil import ProfilAnsicht, profil_einbettung_mit_inventar

        await interaction.response.edit_message(
            embed=profil_einbettung_mit_inventar(self.kontext, self.nutzer_id),
            view=ProfilAnsicht(self.kontext, self.nutzer_id),
        )

    async def _fablinge_öffnen(self, interaction: discord.Interaction) -> None:
        from fabelbund.discord.ansichten.stall_ansicht import StallAnsicht, stallübersicht_einbettung

        fabelwesen = self.kontext.spiel.sammlung(self.nutzer_id)
        kapazität = self.kontext.spiel.stall_kapazität(self.nutzer_id)
        await interaction.response.edit_message(
            embed=stallübersicht_einbettung(self.kontext.spiel, self.nutzer_id, fabelwesen, kapazität),
            view=StallAnsicht(self.kontext.spiel, self.nutzer_id, fabelwesen, kapazität, kontext=self.kontext),
        )

    async def _laden_öffnen(self, interaction: discord.Interaction) -> None:
        from fabelbund.discord.befehle.laden import LadenAnsicht, laden_einbettung

        await interaction.response.edit_message(
            embed=laden_einbettung(self.kontext, self.nutzer_id),
            view=LadenAnsicht(self.kontext, self.nutzer_id),
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


def inventar_einbettung(kontext: Anwendungskontext, nutzer_id: str) -> discord.Embed:
    inventar = kontext.spiel.inventar(nutzer_id)
    embed = discord.Embed(title="Inventar", color=discord.Color.green())
    if inventar:
        embed.description = f"{inventar_text(kontext, inventar)}\n\nFutter wird von deinen Fablingen automatisch aus dem Vorrat genommen."
    else:
        embed.description = "Dein Inventar ist leer."
    return embed


def inventar_text(kontext: Anwendungskontext, inventar: dict[str, object]) -> str:
    zeilen = []
    for gegenstand_id, eintrag in inventar.items():
        gegenstand = kontext.spiel.inhalte.gegenstände.get(gegenstand_id)
        name = gegenstand.name if gegenstand else gegenstand_id
        zusatz = ""
        if isinstance(eintrag, dict) and isinstance(eintrag.get("haltbarkeit"), list):
            haltbarkeit = ", ".join(str(wert) for wert in eintrag["haltbarkeit"])
            zusatz = f" ({haltbarkeit}/20)"
        zeilen.append(f"{inventar_anzahl(eintrag)}x {name}{zusatz}")
    return "\n".join(zeilen)


def inventar_anzahl(eintrag: object) -> int:
    if isinstance(eintrag, dict):
        return int(eintrag.get("anzahl", 0))
    return int(eintrag)
