from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from fabelbund.anwendung import Anwendungskontext
from fabelbund.discord.auftragswand import chronik_senden, auftragswand_aktualisieren
from fabelbund.discord.darstellung import auftrag_abgabe_einbettung, auftrag_einbettung, tutorial_hinweis_text
from fabelbund.discord.zeitlimits import EPHEMERE_ANSICHT_TIMEOUT_SEKUNDEN


class AuftragBefehle(commands.Cog):
    def __init__(self, kontext: Anwendungskontext) -> None:
        self.kontext = kontext

    @app_commands.command(name="auftrag", description="Startet oder zeigt deinen aktuellen Auftrag.")
    async def auftrag(self, interaction: discord.Interaction) -> None:
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
            hinweis = tutorial_hinweis_text(spieler)
            text = str(fehler)
            if hinweis:
                text = f"{text}\n{hinweis}"
            await interaction.response.send_message(text, ephemeral=True)
            return
        auftrag = self.kontext.spiel.inhalte.aufträge[aktiver_auftrag.auftrag_id]
        fabelwesen = self.kontext.spiel.fabelwesen.holen(aktiver_auftrag.fabelwesen_id)
        embed = auftrag_einbettung(aktiver_auftrag, auftrag, fabelwesen)
        embed.add_field(name="Aufgabe", value=auftragsziel_text(auftrag.ziele), inline=False)
        await interaction.response.send_message(
            embed=embed,
            view=AuftragAnsicht(self.kontext, nutzer_id),
            ephemeral=True,
        )


class AuftragAnsicht(discord.ui.View):
    def __init__(self, kontext: Anwendungskontext, nutzer_id: str) -> None:
        super().__init__(timeout=EPHEMERE_ANSICHT_TIMEOUT_SEKUNDEN)
        self.kontext = kontext
        self.nutzer_id = nutzer_id
        button = discord.ui.Button(label="Abgeben", style=discord.ButtonStyle.success, custom_id="auftrag:abgeben")
        button.callback = self._abgeben
        self.add_item(button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) == self.nutzer_id:
            return True
        await interaction.response.send_message("Dieser Auftrag gehört einem anderen Spieler.", ephemeral=True)
        return False

    async def _abgeben(self, interaction: discord.Interaction) -> None:
        try:
            ergebnis = self.kontext.spiel.auftrag_abgeben(self.nutzer_id)
        except ValueError as fehler:
            await interaction.response.send_message(str(fehler), ephemeral=True)
            return
        view = None
        if ergebnis.erfolgreich:
            spieler = self.kontext.spiel.spieler.holen(self.nutzer_id)
            if spieler is not None and not spieler.offizielles_mitglied and spieler.tutorialschritt in {"ruhe_starten", "pflege_und_ausrüstung"}:
                view = NächsterAuftragAnsicht(self.kontext, self.nutzer_id)
        else:
            view = AuftragAnsicht(self.kontext, self.nutzer_id)
        await interaction.response.edit_message(embed=auftrag_abgabe_einbettung(ergebnis), view=view)
        if ergebnis.erfolgreich and ergebnis.auftrag.fortschritt.get("quelle") == "auftragswand":
            auftrag = self.kontext.spiel.inhalte.aufträge[ergebnis.auftrag.auftrag_id]
            await chronik_senden(
                self.kontext,
                interaction.guild,
                f"<@{self.nutzer_id}> hat **{auftrag.name}** abgeschlossen und den Leih-Fabling zurückgegeben.",
            )
            await auftragswand_aktualisieren(self.kontext, interaction.guild)


class NächsterAuftragAnsicht(discord.ui.View):
    def __init__(self, kontext: Anwendungskontext, nutzer_id: str) -> None:
        super().__init__(timeout=EPHEMERE_ANSICHT_TIMEOUT_SEKUNDEN)
        self.kontext = kontext
        self.nutzer_id = nutzer_id
        button = discord.ui.Button(label="Nächster Auftrag", style=discord.ButtonStyle.primary, custom_id="auftrag:nächster")
        button.callback = self._nächster_auftrag
        self.add_item(button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) == self.nutzer_id:
            return True
        await interaction.response.send_message("Diese Auftragsansicht gehört einem anderen Spieler.", ephemeral=True)
        return False

    async def _nächster_auftrag(self, interaction: discord.Interaction) -> None:
        try:
            aktiver_auftrag = self.kontext.spiel.pflegeauftrag_starten(self.nutzer_id)
        except ValueError as fehler:
            await interaction.response.send_message(str(fehler), ephemeral=True)
            return
        auftrag = self.kontext.spiel.inhalte.aufträge[aktiver_auftrag.auftrag_id]
        fabelwesen = self.kontext.spiel.fabelwesen.holen(aktiver_auftrag.fabelwesen_id)
        embed = auftrag_einbettung(aktiver_auftrag, auftrag, fabelwesen)
        embed.add_field(name="Aufgabe", value=auftragsziel_text(auftrag.ziele), inline=False)
        await interaction.response.edit_message(embed=embed, view=AuftragAnsicht(self.kontext, self.nutzer_id))


def auftragsziel_text(ziele: dict[str, object]) -> str:
    if ziele.get("abgeschlossene_aktion") == "kontrollierte_ruhe":
        return "Lass den zugeteilten Fabling eine vollständige kontrollierte Ruhe abschließen und gib den Auftrag danach ab."
    if ziele.get("abgeschlossene_aktion") == "sanfte_fellpflege":
        return "Pflege: Sanfte Fellpflege."
    if ziele.get("abgeschlossene_aktion") == "ausdruck_üben":
        return "Training: Ausdruck üben."
    if ziele.get("gefüttert"):
        return "Gib dem zugeteilten Fabling passendes Futter und gib den Auftrag danach ab."

    teile: list[str] = []
    if ziele.get("gesundheit_mindestens") is not None:
        teile.append("Der Fabling soll gesundheitlich stabil wirken.")
    if ziele.get("stimmung_mindestens") is not None:
        teile.append("Die Stimmung soll mindestens ausgeglichen sein.")
    if ziele.get("stress_höchstens") is not None:
        teile.append("Der Fabling soll nicht zu gestresst wirken.")
    if ziele.get("fellpflege_mindestens") is not None:
        teile.append("Das Fell soll ordentlich gepflegt sein.")
    return "\n".join(teile) or "Erfülle die Auftragsbedingungen und gib den Auftrag danach ab."
