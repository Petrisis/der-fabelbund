from __future__ import annotations

import logging

import discord

from fabelbund.anwendung import Anwendungskontext
from fabelbund.discord.darstellung import auftrag_einbettung, auftragsaushang_einbettung, auftragswand_einbettung, tutorial_hinweis_text


log = logging.getLogger(__name__)
MAXIMALE_AUFTRAGSAUSHÄNGE = 3
AUFTRAGSAUSHANG_SCAN_LIMIT = 50


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
        reset = discord.ui.Button(
            label="Fortschritt zurücksetzen",
            style=discord.ButtonStyle.danger,
            custom_id="auftragswand:reset",
        )
        reset.callback = self._reset_starten
        self.add_item(reset)

    async def _einstieg(self, interaction: discord.Interaction) -> None:
        nutzer_id = str(interaction.user.id)
        spieler = self.kontext.spiel.stelle_spieler_sicher(nutzer_id)
        if spieler.tutorialstatus != "neu":
            await tutorial_fortsetzen_senden(interaction, self.kontext, nutzer_id)
            return

        embed = discord.Embed(
            title="Neu beim Fabelbund",
            description=(
                "Der Fabelbund sucht verlässliche Betreuer. Am Anfang arbeitest du mit Fablingen, "
                "die dir für konkrete Aufträge anvertraut werden. So verdienst du Bundsiegel, baust Ruf auf "
                "und lernst, worauf unterschiedliche Fabelwesen reagieren, bevor du deine eigene Zucht aufbaust."
            ),
            color=discord.Color.green(),
        )
        await interaction.response.send_message(
            embed=embed,
            view=TutorialStartAnsicht(self.kontext),
            ephemeral=True,
        )

    async def _reset_starten(self, interaction: discord.Interaction) -> None:
        nutzer_id = str(interaction.user.id)
        embed = discord.Embed(
            title="Fortschritt zurücksetzen",
            description=(
                "Das entfernt dein Spielerprofil, alle Fablinge, aktive und abgeschlossene Aufträge, "
                "laufende Aktivitäten, Inventar, Bundsiegel, Ruf, Lizenzen und Stallausbau."
            ),
            color=discord.Color.red(),
        )
        await interaction.response.send_message(
            embed=embed,
            view=ResetErsteBestätigungAnsicht(self.kontext, nutzer_id),
            ephemeral=True,
        )


class ResetErsteBestätigungAnsicht(discord.ui.View):
    def __init__(self, kontext: Anwendungskontext, nutzer_id: str) -> None:
        super().__init__(timeout=12 * 60 * 60)
        self.kontext = kontext
        self.nutzer_id = nutzer_id
        button = discord.ui.Button(label="Reset vorbereiten", style=discord.ButtonStyle.danger, custom_id="reset:vorbereiten")
        button.callback = self._vorbereiten
        self.add_item(button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) == self.nutzer_id:
            return True
        await interaction.response.send_message("Dieser Reset gehört einem anderen Spieler.", ephemeral=True)
        return False

    async def _vorbereiten(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="Endgültige Bestätigung",
            description=(
                "Dieser Schritt ist nicht rückgängig zu machen. Serverkanäle und Auftragswand bleiben erhalten, "
                "aber dein gesamter Spielfortschritt wird gelöscht."
            ),
            color=discord.Color.red(),
        )
        await interaction.response.edit_message(
            embed=embed,
            view=ResetEndgültigeBestätigungAnsicht(self.kontext, self.nutzer_id),
        )


class ResetEndgültigeBestätigungAnsicht(discord.ui.View):
    def __init__(self, kontext: Anwendungskontext, nutzer_id: str) -> None:
        super().__init__(timeout=12 * 60 * 60)
        self.kontext = kontext
        self.nutzer_id = nutzer_id
        button = discord.ui.Button(label="Endgültig zurücksetzen", style=discord.ButtonStyle.danger, custom_id="reset:endgültig")
        button.callback = self._zurücksetzen
        self.add_item(button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) == self.nutzer_id:
            return True
        await interaction.response.send_message("Dieser Reset gehört einem anderen Spieler.", ephemeral=True)
        return False

    async def _zurücksetzen(self, interaction: discord.Interaction) -> None:
        self.kontext.spiel.spielerfortschritt_zurücksetzen(self.nutzer_id)
        embed = discord.Embed(
            title="Fortschritt zurückgesetzt",
            description="Dein Fortschritt wurde vollständig zurückgesetzt. Du kannst über die Auftragswand neu beginnen.",
            color=discord.Color.green(),
        )
        await interaction.response.edit_message(embed=embed, view=None)
        await chronik_senden(
            self.kontext,
            interaction.guild,
            f"{interaction.user.mention} hat den eigenen Fortschritt zurückgesetzt und beginnt neu.",
        )


async def tutorial_fortsetzen_senden(
    interaction: discord.Interaction,
    kontext: Anwendungskontext,
    nutzer_id: str,
) -> None:
    spieler = kontext.spiel.stelle_spieler_sicher(nutzer_id)
    aktiver_auftrag = kontext.spiel.aktiver_auftrag(nutzer_id)
    if aktiver_auftrag is not None:
        from fabelbund.discord.befehle.auftrag import AuftragAnsicht, auftragsziel_text

        auftrag = kontext.spiel.inhalte.aufträge[aktiver_auftrag.auftrag_id]
        fabelwesen = kontext.spiel.fabelwesen.holen(aktiver_auftrag.fabelwesen_id)
        embed = auftrag_einbettung(aktiver_auftrag, auftrag, fabelwesen, kontext.spiel.auftrag_fablinge(aktiver_auftrag))
        embed.add_field(name="Aufgabe", value=auftragsziel_text(auftrag.ziele), inline=False)
        await interaction.response.send_message(
            embed=embed,
            view=AuftragAnsicht(kontext, nutzer_id),
            ephemeral=True,
        )
        return

    if spieler.tutorialstatus == "abgeschlossen" or spieler.offizielles_mitglied:
        embed = discord.Embed(
            title="Einführung abgeschlossen",
            description="Du bist offizielles Mitglied. Öffentliche Aufträge findest du an der Auftragswand.",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if spieler.tutorialschritt == "ruhe_starten":
        embed = discord.Embed(
            title="Einführung fortsetzen",
            description="Mira wartet mit deinem ersten Probeauftrag. Wenn du bereit bist, nimm ihn direkt hier an.",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(
            embed=embed,
            view=TutorialErsterAuftragAnsicht(kontext, nutzer_id),
            ephemeral=True,
        )
        return

    if spieler.tutorialschritt == "stall_ausbauen":
        from fabelbund.discord.ansichten.stall_ansicht import StallAnsicht, stallübersicht_einbettung

        fabelwesen = kontext.spiel.sammlung(nutzer_id)
        kapazität = kontext.spiel.stall_kapazität(nutzer_id)
        embed = stallübersicht_einbettung(kontext.spiel, nutzer_id, fabelwesen, kapazität)
        embed.description = (
            "Mira sagt: „Wenn du später mehrere Fablinge gleichzeitig betreust, brauchst du genug Stallplätze. "
            "Baue einen weiteren neutralen Platz aus.“"
        )
        await interaction.response.send_message(
            embed=embed,
            view=StallAnsicht(kontext.spiel, nutzer_id, fabelwesen, kapazität, kontext=kontext),
            ephemeral=True,
        )
        return

    if spieler.tutorialschritt == "starter_wählen":
        from fabelbund.discord.befehle.auftrag import StarterWahlAnsicht, starterwahl_einbettung

        await interaction.response.send_message(
            embed=starterwahl_einbettung(),
            view=StarterWahlAnsicht(kontext, nutzer_id),
            ephemeral=True,
        )
        return

    from fabelbund.discord.befehle.auftrag import NächsterAuftragAnsicht

    hinweis = tutorial_hinweis_text(spieler) or "Der nächste Probeauftrag ist bereit."
    embed = discord.Embed(
        title="Einführung fortsetzen",
        description=hinweis,
        color=discord.Color.green(),
    )
    await interaction.response.send_message(
        embed=embed,
        view=NächsterAuftragAnsicht(kontext, nutzer_id),
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
        if interaction.message is not None:
            embed = auftragsaushang_einbettung(auftrag)
            embed.title = f"{auftrag.name} - vergeben"
            embed.color = discord.Color.dark_grey()
            embed.add_field(name="Status", value=f"Angenommen von {interaction.user.mention}.", inline=False)
            embed.set_footer(text=f"vergeben:{auftrag.auftrag_id}")
            await interaction.message.edit(embed=embed, view=None)
        await auftragswand_aktualisieren(self.kontext, interaction.guild)


class AuftragsnavigationAnsicht(discord.ui.View):
    def __init__(self, kontext: Anwendungskontext) -> None:
        super().__init__(timeout=None)
        self.kontext = kontext
        auftrag = discord.ui.Button(label="Auftrag", style=discord.ButtonStyle.primary, custom_id="auftragswand:navigation:auftrag")
        auftrag.callback = self._auftrag_öffnen
        self.add_item(auftrag)
        fablinge = discord.ui.Button(label="Fablinge", style=discord.ButtonStyle.primary, custom_id="auftragswand:navigation:fablinge")
        fablinge.callback = self._fablinge_öffnen
        self.add_item(fablinge)
        inventar = discord.ui.Button(label="Inventar", style=discord.ButtonStyle.primary, custom_id="auftragswand:navigation:inventar")
        inventar.callback = self._inventar_öffnen
        self.add_item(inventar)

    async def _auftrag_öffnen(self, interaction: discord.Interaction) -> None:
        from fabelbund.discord.befehle.auftrag import AuftragAnsicht, auftragsziel_text

        nutzer_id = str(interaction.user.id)
        aktiver_auftrag = self.kontext.spiel.aktiver_auftrag(nutzer_id)
        if aktiver_auftrag is None:
            await interaction.response.send_message("Du hast gerade keinen aktiven Auftrag.", ephemeral=True)
            return
        auftrag = self.kontext.spiel.inhalte.aufträge[aktiver_auftrag.auftrag_id]
        fabelwesen = self.kontext.spiel.fabelwesen.holen(aktiver_auftrag.fabelwesen_id)
        embed = auftrag_einbettung(aktiver_auftrag, auftrag, fabelwesen, self.kontext.spiel.auftrag_fablinge(aktiver_auftrag))
        embed.add_field(name="Aufgabe", value=auftragsziel_text(auftrag.ziele), inline=False)
        await interaction.response.send_message(embed=embed, view=AuftragAnsicht(self.kontext, nutzer_id), ephemeral=True)

    async def _fablinge_öffnen(self, interaction: discord.Interaction) -> None:
        from fabelbund.discord.ansichten.stall_ansicht import StallAnsicht, stallübersicht_einbettung

        nutzer_id = str(interaction.user.id)
        fabelwesen = self.kontext.spiel.sammlung(nutzer_id)
        kapazität = self.kontext.spiel.stall_kapazität(nutzer_id)
        await interaction.response.send_message(
            embed=stallübersicht_einbettung(self.kontext.spiel, nutzer_id, fabelwesen, kapazität),
            view=StallAnsicht(self.kontext.spiel, nutzer_id, fabelwesen, kapazität, kontext=self.kontext),
            ephemeral=True,
        )

    async def _inventar_öffnen(self, interaction: discord.Interaction) -> None:
        from fabelbund.discord.befehle.inventar import InventarAnsicht, inventar_einbettung

        nutzer_id = str(interaction.user.id)
        await interaction.response.send_message(
            embed=inventar_einbettung(self.kontext, nutzer_id),
            view=InventarAnsicht(self.kontext, nutzer_id),
            ephemeral=True,
        )


class EinzelauftragAnsicht(discord.ui.View):
    def __init__(self, kontext: Anwendungskontext, guild_id: str, auftrag_id: str) -> None:
        super().__init__(timeout=None)
        self.kontext = kontext
        self.guild_id = guild_id
        button = discord.ui.Button(
            label="Auftrag annehmen",
            style=discord.ButtonStyle.success,
            custom_id=f"auftragswand:annehmen:{auftrag_id}",
        )
        button.callback = AuftragswandAnsicht(kontext, guild_id)._annehmen
        self.add_item(button)


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
        await chronik_senden(
            self.kontext,
            interaction.guild,
            f"{interaction.user.mention} beginnt die Einführung im Fabelbund.",
        )


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

    öffentliche_aufträge = kontext.spiel.öffentliche_aufträge(limit=MAXIMALE_AUFTRAGSAUSHÄNGE)
    embed = auftragswand_einbettung(öffentliche_aufträge)
    view = AuftragsnavigationAnsicht(kontext)
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

    vorhandene_aushänge = await _auftragsaushang_ids_im_kanal(kanal)
    for auftrag in öffentliche_aufträge:
        if auftrag.auftrag_id in vorhandene_aushänge:
            continue
        await kanal.send(
            embed=auftragsaushang_einbettung(auftrag),
            view=EinzelauftragAnsicht(kontext, str(guild.id), auftrag.auftrag_id),
        )
        vorhandene_aushänge.add(auftrag.auftrag_id)

    kontext.server.speichern(
        konfiguration.model_copy(
            update={
                "einstieg_nachricht_id": str(einstieg_nachricht.id),
                "auftragswand_nachricht_id": str(nachricht.id),
            }
        )
    )
    return nachricht


async def _auftragsaushang_ids_im_kanal(kanal: discord.TextChannel) -> set[str]:
    ids: set[str] = set()
    bot_mitglied = kanal.guild.me
    async for nachricht in kanal.history(limit=AUFTRAGSAUSHANG_SCAN_LIMIT):
        if bot_mitglied is not None and nachricht.author.id != bot_mitglied.id:
            continue
        for embed in nachricht.embeds:
            footer = embed.footer.text or ""
            if footer.startswith("auftrag:"):
                ids.add(footer.split(":", 1)[1])
    return ids


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
