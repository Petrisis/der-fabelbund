from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from fabelbund.anwendung import Anwendungskontext
from fabelbund.discord.darstellung import profil_einbettung


class ProfilBefehle(commands.Cog):
    def __init__(self, kontext: Anwendungskontext) -> None:
        self.kontext = kontext

    @app_commands.command(name="profil", description="Registriert dich bei Der Fabelbund und zeigt dein Profil.")
    async def profil(self, interaction: discord.Interaction) -> None:
        spieler = self.kontext.spiel.stelle_spieler_sicher(str(interaction.user.id))
        embed = profil_einbettung(spieler)
        if spieler.tutorialstatus == "aktiv" and spieler.tutorialschritt == "ruhe_starten":
            embed.add_field(
                name="Einführung",
                value=(
                    "Mira vom Fabelbund begrüßt dich zur Probezeit. Die ersten Fablinge werden dir auftragsweise anvertraut; "
                    "beginne mit `/auftrag` und lass den zugeteilten Fabling eine kontrollierte Ruhe abschließen."
                ),
                inline=False,
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)
