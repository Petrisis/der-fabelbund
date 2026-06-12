from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from fabelbund.anwendung import Anwendungskontext
from fabelbund.discord.darstellung import auftrag_einbettung


class AuftragBefehle(commands.Cog):
    def __init__(self, kontext: Anwendungskontext) -> None:
        self.kontext = kontext

    @app_commands.command(name="auftrag", description="Startet oder zeigt deinen aktuellen Pflegeauftrag.")
    async def auftrag(self, interaction: discord.Interaction) -> None:
        try:
            aktiver_auftrag = self.kontext.spiel.pflegeauftrag_starten(str(interaction.user.id))
        except ValueError as fehler:
            await interaction.response.send_message(str(fehler), ephemeral=True)
            return
        auftrag = self.kontext.spiel.inhalte.aufträge[aktiver_auftrag.auftrag_id]
        embed = auftrag_einbettung(aktiver_auftrag, auftrag.name)
        embed.add_field(
            name="Ziele",
            value="\n".join(
                [
                    f"Gesundheit >= {auftrag.ziele.get('gesundheit_mindestens')}",
                    f"Stimmung >= {auftrag.ziele.get('stimmung_mindestens')}",
                    f"Stress <= {auftrag.ziele.get('stress_höchstens')}",
                    f"Fellpflege >= {auftrag.ziele.get('fellpflege_mindestens')}",
                ]
            ),
            inline=False,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
