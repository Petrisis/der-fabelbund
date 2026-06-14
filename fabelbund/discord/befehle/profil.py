from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from fabelbund.anwendung import Anwendungskontext
from fabelbund.discord.darstellung import profil_einbettung
from fabelbund.discord.zeitlimits import EPHEMERE_ANSICHT_TIMEOUT_SEKUNDEN


class ProfilBefehle(commands.Cog):
    def __init__(self, kontext: Anwendungskontext) -> None:
        self.kontext = kontext

    @app_commands.command(name="profil", description="Registriert dich bei Der Fabelbund und zeigt dein Profil.")
    async def profil(self, interaction: discord.Interaction) -> None:
        nutzer_id = str(interaction.user.id)
        embed = profil_einbettung_mit_inventar(self.kontext, nutzer_id)
        await interaction.response.send_message(embed=embed, view=ProfilAnsicht(self.kontext, nutzer_id), ephemeral=True)


class ProfilAnsicht(discord.ui.View):
    def __init__(self, kontext: Anwendungskontext, nutzer_id: str) -> None:
        super().__init__(timeout=EPHEMERE_ANSICHT_TIMEOUT_SEKUNDEN)
        self.kontext = kontext
        self.nutzer_id = nutzer_id
        inventar = discord.ui.Button(label="Inventar", style=discord.ButtonStyle.primary, custom_id="profil:inventar")
        inventar.callback = self._inventar_öffnen
        self.add_item(inventar)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) == self.nutzer_id:
            return True
        await interaction.response.send_message("Dieses Profil gehört einem anderen Spieler.", ephemeral=True)
        return False

    async def _inventar_öffnen(self, interaction: discord.Interaction) -> None:
        from fabelbund.discord.befehle.inventar import InventarAnsicht, inventar_einbettung

        await interaction.response.edit_message(
            embed=inventar_einbettung(self.kontext, self.nutzer_id),
            view=InventarAnsicht(self.kontext, self.nutzer_id),
        )


def profil_einbettung_mit_inventar(kontext: Anwendungskontext, nutzer_id: str) -> discord.Embed:
    spieler = kontext.spiel.stelle_spieler_sicher(nutzer_id)
    embed = profil_einbettung(spieler)
    embed.add_field(name="Inventar", value=inventar_kurztext(kontext, nutzer_id), inline=False)
    return embed


def inventar_kurztext(kontext: Anwendungskontext, nutzer_id: str) -> str:
    inventar = kontext.spiel.inventar(nutzer_id)
    if not inventar:
        return "leer"

    zeilen: list[str] = []
    for gegenstand_id, eintrag in list(inventar.items())[:3]:
        gegenstand = kontext.spiel.inhalte.gegenstände.get(gegenstand_id)
        name = gegenstand.name if gegenstand else gegenstand_id
        anzahl = int(eintrag.get("anzahl", 0)) if isinstance(eintrag, dict) else int(eintrag)
        zeilen.append(f"{anzahl}x {name}")
    rest = max(0, len(inventar) - len(zeilen))
    if rest:
        zeilen.append(f"+{rest} weitere")
    return "\n".join(zeilen)
