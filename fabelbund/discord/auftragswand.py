from __future__ import annotations

import logging

import discord

from fabelbund.anwendung import Anwendungskontext
from fabelbund.discord.darstellung import auftrag_einbettung, auftragswand_einbettung


log = logging.getLogger(__name__)


class TutorialEinstiegAnsicht(discord.ui.View):
    def __init__(self, kontext: Anwendungskontext) -> None:
        super().__init__(timeout=None)
        self.kontext = kontext
        einstieg = discord.ui.Button(
            label="Los geht's!",
            style=discord.ButtonStyle.success,
            custom_id="auftragswand:einstieg",
        )
        einstieg.callback = self._einstieg
        self.add_item(einstieg)

    async def _einstieg(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="Neu beim Fabelbund",
            description=(
                "Der Fabelbund sucht verlässliche Betreuer. Am Anfang arbeitest du mit Fablingen, "
                "die dir für konkrete Aufträge anvertraut werden. So verdienst du Geld, baust Ruf auf "
                "und lernst, worauf unterschiedliche Fabelwesen reagieren, bevor du deine eigene Zucht aufbaust."
            ),
            color=discord.Color.green(),
        )
        await interaction.response.send_message(
            embed=embed,
            view=TutorialStartAnsicht(self.kontext),
            ephemeral=True,
        )


class AuftragswandAnsicht(discord.ui.View):
    def __init__(self, kontext: Anwendungskontext, guild_id: str) -> None:
        super().__init__(timeout=None)
        self.kontext = kontext
        self.guild_id = guild_id
        for auftrag in self.kontext.spiel.öffentliche_aufträge():
            button = discord.ui.Button(
                label=f"Annehmen: {auftrag.name}"[:80],
                style=discord.ButtonStyle.primary,
                custom_id=f"auftragswand:annehmen:{auftrag.auftrag_id}",
            )
            button.callback = self._annehmen
            self.add_item(button)

    async def _annehmen(self, interaction: discord.Interaction) -> None:
        custom_id = interaction.data.get("custom_id") if isinstance(interaction.data, dict) else None
        auftrag_id = str(custom_id).split(":")[-1] if custom_id else ""
        nutzer_id = str(interaction.user.id)
        try:
            aktiver_auftrag = self.kontext.spiel.öffentlichen_auftrag_annehmen(nutzer_id, auftrag_id, self.guild_id)
        except ValueError as fehler:
            await interaction.response.send_message(str(fehler), ephemeral=True)
            return

        auftrag = self.kontext.spiel.inhalte.aufträge[aktiver_auftrag.auftrag_id]
        fabelwesen = self.kontext.spiel.fabelwesen.holen(aktiver_auftrag.fabelwesen_id)
        embed = auftrag_einbettung(aktiver_auftrag, auftrag, fabelwesen, self.kontext.spiel.auftrag_fablinge(aktiver_auftrag))
        await interaction.response.send_message(
            "Auftrag angenommen. Der Leih-Fabling wartet jetzt in deinem Stall.",
            embed=embed,
            ephemeral=True,
        )
        await chronik_senden(
            self.kontext,
            interaction.guild,
            f"{interaction.user.mention} hat **{auftrag.name}** angenommen.",
        )
        await auftragswand_aktualisieren(self.kontext, interaction.guild)


class TutorialStartAnsicht(discord.ui.View):
    def __init__(self, kontext: Anwendungskontext) -> None:
        super().__init__(timeout=12 * 60 * 60)
        self.kontext = kontext
        button = discord.ui.Button(label="Ich bin bereit.", style=discord.ButtonStyle.success, custom_id="tutorial:start")
        button.callback = self._starten
        self.add_item(button)

    async def _starten(self, interaction: discord.Interaction) -> None:
        spieler = self.kontext.spiel.tutorial_starten(str(interaction.user.id))
        embed = discord.Embed(
            title="Einführung begonnen",
            description="Mira wartet mit deinem ersten Probeauftrag. Wenn du bereit bist, nimm ihn direkt hier an.",
            color=discord.Color.green(),
        )
        embed.add_field(name="Status", value=spieler.tutorialschritt.replace("_", " "), inline=True)
        await interaction.response.edit_message(embed=embed, view=TutorialErsterAuftragAnsicht(self.kontext, str(interaction.user.id)))


class TutorialErsterAuftragAnsicht(discord.ui.View):
    def __init__(self, kontext: Anwendungskontext, nutzer_id: str) -> None:
        super().__init__(timeout=12 * 60 * 60)
        self.kontext = kontext
        self.nutzer_id = nutzer_id
        button = discord.ui.Button(label="Annehmen: Miras erste Probe", style=discord.ButtonStyle.success, custom_id="tutorial:erster_auftrag")
        button.callback = self._annehmen
        self.add_item(button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) == self.nutzer_id:
            return True
        await interaction.response.send_message("Diese Einführung gehört einem anderen Spieler.", ephemeral=True)
        return False

    async def _annehmen(self, interaction: discord.Interaction) -> None:
        from fabelbund.discord.befehle.auftrag import AuftragAnsicht, auftragsziel_text

        try:
            aktiver_auftrag = self.kontext.spiel.pflegeauftrag_starten(self.nutzer_id)
        except ValueError as fehler:
            await interaction.response.send_message(str(fehler), ephemeral=True)
            return
        auftrag = self.kontext.spiel.inhalte.aufträge[aktiver_auftrag.auftrag_id]
        fabelwesen = self.kontext.spiel.fabelwesen.holen(aktiver_auftrag.fabelwesen_id)
        embed = auftrag_einbettung(aktiver_auftrag, auftrag, fabelwesen, self.kontext.spiel.auftrag_fablinge(aktiver_auftrag))
        embed.add_field(name="Aufgabe", value=auftragsziel_text(auftrag.ziele), inline=False)
        await interaction.response.edit_message(embed=embed, view=AuftragAnsicht(self.kontext, self.nutzer_id))


async def auftragswand_erstellen_oder_aktualisieren(kontext: Anwendungskontext, guild: discord.Guild) -> discord.Message | None:
    konfiguration = kontext.server.holen(str(guild.id))
    if konfiguration is None or not konfiguration.aufträge_kanal_id:
        log.warning("Auftragswand ohne gespeicherten Auftragskanal angefordert: %s (%s)", guild.name, guild.id)
        return None
    kanal = guild.get_channel(int(konfiguration.aufträge_kanal_id))
    if not isinstance(kanal, discord.TextChannel):
        log.warning("Gespeicherter Auftragskanal existiert nicht mehr: %s (%s)", guild.name, guild.id)
        return None

    if not konfiguration.einstieg_nachricht_id:
        await kanal.purge(limit=100, reason="Fabelbund-Auftragskanal neu strukturieren")
        konfiguration = kontext.server.speichern(
            konfiguration.model_copy(update={"einstieg_nachricht_id": None, "auftragswand_nachricht_id": None})
        )

    einstieg_embed = discord.Embed(
        title="Neu hier? Willst du mitmachen?",
        description="Der Fabelbund sucht Betreuer, die Verantwortung für Fablinge übernehmen wollen.",
        color=discord.Color.green(),
    )
    einstieg_nachricht = None
    if konfiguration.einstieg_nachricht_id:
        try:
            einstieg_nachricht = await kanal.fetch_message(int(konfiguration.einstieg_nachricht_id))
        except discord.NotFound:
            einstieg_nachricht = None
    if einstieg_nachricht is None:
        einstieg_nachricht = await kanal.send(embed=einstieg_embed, view=TutorialEinstiegAnsicht(kontext))
    else:
        await einstieg_nachricht.edit(embed=einstieg_embed, view=TutorialEinstiegAnsicht(kontext))

    embed = auftragswand_einbettung(kontext.spiel.öffentliche_aufträge())
    view = AuftragswandAnsicht(kontext, str(guild.id))
    nachricht = None
    if konfiguration.auftragswand_nachricht_id:
        try:
            nachricht = await kanal.fetch_message(int(konfiguration.auftragswand_nachricht_id))
        except discord.NotFound:
            log.warning("Gespeicherte Auftragswand-Nachricht existiert nicht mehr: %s (%s)", guild.name, guild.id)
            nachricht = None
        except discord.Forbidden as fehler:
            log.exception("Keine Leserechte für die Auftragswand in %s (%s): %s", guild.name, guild.id, fehler)
            return None
    if nachricht is None:
        nachricht = await kanal.send(embed=embed, view=view)
    else:
        await nachricht.edit(embed=embed, view=view)

    kontext.server.speichern(
        konfiguration.model_copy(
            update={
                "einstieg_nachricht_id": str(einstieg_nachricht.id),
                "auftragswand_nachricht_id": str(nachricht.id),
            }
        )
    )
    return nachricht


async def auftragswand_aktualisieren(kontext: Anwendungskontext, guild: discord.Guild | None) -> None:
    if guild is None:
        return
    await auftragswand_erstellen_oder_aktualisieren(kontext, guild)


async def chronik_senden(kontext: Anwendungskontext, guild: discord.Guild | None, text: str) -> None:
    if guild is None:
        return
    konfiguration = kontext.server.holen(str(guild.id))
    if konfiguration is None or not konfiguration.chronik_kanal_id:
        return
    kanal = guild.get_channel(int(konfiguration.chronik_kanal_id))
    if isinstance(kanal, discord.TextChannel):
        await kanal.send(text)
