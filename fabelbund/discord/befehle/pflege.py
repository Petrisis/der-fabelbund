from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from fabelbund.anwendung import Anwendungskontext
from fabelbund.discord.ansichten.pflege_ansicht import PflegeAnsicht
from fabelbund.discord.darstellung import aktivität_einbettung, fabelwesen_einbettung


class PflegeBefehle(commands.Cog):
    def __init__(self, kontext: Anwendungskontext) -> None:
        self.kontext = kontext

    @app_commands.command(name="pflege", description="Öffnet Betreuung und Aktivitäten für deinen aktuellen Auftrag.")
    async def pflege(self, interaction: discord.Interaction) -> None:
        nutzer_id = str(interaction.user.id)
        spieler = self.kontext.spiel.stelle_spieler_sicher(nutzer_id)
        aktiver_auftrag = self.kontext.spiel.aktiver_auftrag(nutzer_id)
        if aktiver_auftrag is None and spieler.offizielles_mitglied:
            kanalhinweis = "in #aufträge"
            if interaction.guild is not None:
                konfiguration = self.kontext.server.holen(str(interaction.guild.id))
                if konfiguration is not None:
                    kanal = interaction.guild.get_channel(int(konfiguration.aufträge_kanal_id))
                    if isinstance(kanal, discord.TextChannel):
                        kanalhinweis = kanal.mention
            await interaction.response.send_message(
                f"Du hast keinen aktiven Auftrag. Öffentliche Aufträge findest du {kanalhinweis}.",
                ephemeral=True,
            )
            return
        try:
            aktiver_auftrag = aktiver_auftrag or self.kontext.spiel.pflegeauftrag_starten(nutzer_id)
        except ValueError as fehler:
            await interaction.response.send_message(str(fehler), ephemeral=True)
            return
        fabelwesen = self.kontext.spiel.fabelwesen.holen(aktiver_auftrag.fabelwesen_id)
        if fabelwesen is None:
            await interaction.response.send_message("Das Auftrags-Fabelwesen wurde nicht gefunden.", ephemeral=True)
            return
        laufende_aktivität = self.kontext.spiel.laufende_aktive_spieleraktivität(nutzer_id)
        if laufende_aktivität is None:
            laufende_aktivität = self.kontext.spiel.laufende_aktivität_für_fabelwesen(fabelwesen.id)
        if laufende_aktivität is not None:
            await interaction.response.send_message(
                embed=aktivität_einbettung(laufende_aktivität),
                view=PflegeAnsicht(self.kontext.spiel, nutzer_id),
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            embed=fabelwesen_einbettung(fabelwesen, titel="Betreuung"),
            view=PflegeAnsicht(self.kontext.spiel, nutzer_id),
            ephemeral=True,
        )
