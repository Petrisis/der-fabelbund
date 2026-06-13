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
        if spieler.tutorialstatus == "neu":
            await interaction.response.send_message(
                "Beginne über die Auftragswand mit `Los geht's!`.",
                ephemeral=True,
            )
            return
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
        embed = auftrag_einbettung(aktiver_auftrag, auftrag, fabelwesen, self.kontext.spiel.auftrag_fablinge(aktiver_auftrag))
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
        fablinge = discord.ui.Button(label="Deine Fablinge", style=discord.ButtonStyle.primary, custom_id="auftrag:fablinge")
        fablinge.callback = self._fablinge
        self.add_item(fablinge)
        laden = discord.ui.Button(label="Laden", style=discord.ButtonStyle.primary, custom_id="auftrag:laden")
        laden.callback = self._laden
        self.add_item(laden)
        inventar = discord.ui.Button(label="Inventar", style=discord.ButtonStyle.primary, custom_id="auftrag:inventar")
        inventar.callback = self._inventar
        self.add_item(inventar)

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
            if spieler is not None and not spieler.offizielles_mitglied and spieler.tutorialschritt in {
                "ruhe_starten",
                "pflege_und_ausrüstung",
                "aktiv_passiv",
                "futterauftrag",
                "betreuungszeit",
                "wettbewerb_vorbereitung",
            }:
                view = NächsterAuftragAnsicht(self.kontext, self.nutzer_id)
            elif spieler is not None and spieler.tutorialstatus == "aktiv" and spieler.tutorialschritt == "stall_ausbauen":
                view = TutorialZwischenschrittAnsicht(self.kontext, self.nutzer_id)
            elif spieler is not None and spieler.tutorialstatus == "aktiv" and spieler.tutorialschritt == "starter_wählen":
                view = StarterWahlAnsicht(self.kontext, self.nutzer_id)
        else:
            auftrag = self.kontext.spiel.inhalte.aufträge[ergebnis.auftrag.auftrag_id]
            fabelwesen = self.kontext.spiel.fabelwesen.holen(ergebnis.auftrag.fabelwesen_id)
            embed = auftrag_einbettung(
                ergebnis.auftrag,
                auftrag,
                fabelwesen,
                self.kontext.spiel.auftrag_fablinge(ergebnis.auftrag),
            )
            embed.add_field(name="Aufgabe", value=f"❌ {auftragsziel_text(auftrag.ziele)}", inline=False)
            embed.add_field(name="Einschätzung", value=ergebnis.hinweis, inline=False)
            await interaction.response.edit_message(embed=embed, view=AuftragAnsicht(self.kontext, self.nutzer_id))
            return
        await interaction.response.edit_message(embed=auftrag_abgabe_einbettung(ergebnis), view=view)
        if ergebnis.erfolgreich and ergebnis.auftrag.fortschritt.get("quelle") == "auftragswand":
            auftrag = self.kontext.spiel.inhalte.aufträge[ergebnis.auftrag.auftrag_id]
            await chronik_senden(
                self.kontext,
                interaction.guild,
                f"<@{self.nutzer_id}> hat **{auftrag.name}** abgeschlossen und den Leih-Fabling zurückgegeben.",
            )
            await auftragswand_aktualisieren(self.kontext, interaction.guild)

    async def _fablinge(self, interaction: discord.Interaction) -> None:
        from fabelbund.discord.ansichten.stall_ansicht import StallAnsicht, stallübersicht_einbettung

        fabelwesen = self.kontext.spiel.sammlung(self.nutzer_id)
        kapazität = self.kontext.spiel.stall_kapazität(self.nutzer_id)
        await interaction.response.edit_message(
            embed=stallübersicht_einbettung(self.kontext.spiel, self.nutzer_id, fabelwesen, kapazität),
            view=StallAnsicht(self.kontext.spiel, self.nutzer_id, fabelwesen, kapazität, kontext=self.kontext),
        )

    async def _laden(self, interaction: discord.Interaction) -> None:
        from fabelbund.discord.befehle.laden import LadenAnsicht, laden_einbettung

        await interaction.response.edit_message(
            embed=laden_einbettung(self.kontext, self.nutzer_id),
            view=LadenAnsicht(self.kontext, self.nutzer_id),
        )

    async def _inventar(self, interaction: discord.Interaction) -> None:
        from fabelbund.discord.befehle.inventar import InventarAnsicht, inventar_einbettung

        await interaction.response.edit_message(
            embed=inventar_einbettung(self.kontext, self.nutzer_id),
            view=InventarAnsicht(self.kontext, self.nutzer_id),
        )


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
        embed = auftrag_einbettung(aktiver_auftrag, auftrag, fabelwesen, self.kontext.spiel.auftrag_fablinge(aktiver_auftrag))
        embed.add_field(name="Aufgabe", value=auftragsziel_text(auftrag.ziele), inline=False)
        await interaction.response.edit_message(embed=embed, view=AuftragAnsicht(self.kontext, self.nutzer_id))


class TutorialZwischenschrittAnsicht(discord.ui.View):
    def __init__(self, kontext: Anwendungskontext, nutzer_id: str) -> None:
        super().__init__(timeout=EPHEMERE_ANSICHT_TIMEOUT_SEKUNDEN)
        self.kontext = kontext
        self.nutzer_id = nutzer_id
        button = discord.ui.Button(label="Zum Stall", style=discord.ButtonStyle.primary, custom_id="tutorial:stall")
        button.callback = self._zum_stall
        self.add_item(button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) == self.nutzer_id:
            return True
        await interaction.response.send_message("Diese Ansicht gehört einem anderen Spieler.", ephemeral=True)
        return False

    async def _zum_stall(self, interaction: discord.Interaction) -> None:
        from fabelbund.discord.ansichten.stall_ansicht import StallAnsicht, stallübersicht_einbettung

        embed = discord.Embed(
            title="Mehr Platz im Stall",
            description=(
                "Mira sagt: „Wenn du später mehrere Fablinge gleichzeitig betreust, brauchst du genug Stallplätze. "
                "Geh zu deinen Fablingen und baue einen weiteren neutralen Platz aus.“"
            ),
            color=discord.Color.green(),
        )
        fabelwesen = self.kontext.spiel.sammlung(self.nutzer_id)
        kapazität = self.kontext.spiel.stall_kapazität(self.nutzer_id)
        stall_embed = stallübersicht_einbettung(self.kontext.spiel, self.nutzer_id, fabelwesen, kapazität)
        stall_embed.description = embed.description
        await interaction.response.edit_message(
            embed=stall_embed,
            view=StallAnsicht(self.kontext.spiel, self.nutzer_id, fabelwesen, kapazität, kontext=self.kontext),
        )


def auftragsziel_text(ziele: dict[str, object]) -> str:
    if ziele.get("energie_mindestens") is not None and ziele.get("stress_höchstens") is not None:
        return "Ruhe: Angeleitete Ruhe. Der Fabling soll danach ausgeruht genug und deutlich ruhiger wirken."
    if ziele.get("abgeschlossene_aktion") == "kontrollierte_ruhe":
        return "Kontrollierte Ruhe. Der Fabling soll danach wieder ausgeruht genug wirken."
    if ziele.get("abgeschlossene_aktion") == "sanfte_fellpflege":
        return "Moosbürste kaufen. Danach: Pflege: Sanfte Fellpflege."
    if ziele.get("abgeschlossene_aktion") == "ausdruck_üben":
        return "Training: Ausdruck üben."
    if ziele.get("abgeschlossene_aktionen"):
        aktionen = ziele.get("abgeschlossene_aktionen")
        if aktionen == ["kontrollierte_ruhe", "gemeinsames_spiel"]:
            return "Quellfink: Kontrollierte Ruhe. Gluthase: Gemeinsames Spiel."
        if aktionen == ["gemeinsames_spiel", "kurze_pause"]:
            return "Gemeinsames Spiel und danach eine Kurze Pause. Insgesamt 30 Minuten Betreuung."
        return "Erfülle die genannten Betreuungen bei den zugeteilten Fablingen."
    if ziele.get("gefüttert"):
        return "Gib dem zugeteilten Fabling passendes Futter und gib den Auftrag danach ab."
    if ziele.get("futter_priorität"):
        return "Setze die passende Futterpräferenz beim zugeteilten Fabling."
    if ziele.get("betreuungsdauer_sekunden"):
        return "Betreue den Fabling über die geforderte Zeit und achte auf sinnvolle Pausen."

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


class StarterWahlAnsicht(discord.ui.View):
    def __init__(self, kontext: Anwendungskontext, nutzer_id: str) -> None:
        super().__init__(timeout=EPHEMERE_ANSICHT_TIMEOUT_SEKUNDEN)
        self.kontext = kontext
        self.nutzer_id = nutzer_id
        for art_id in ("gluthase", "moosluchs", "quellfink"):
            art = kontext.spiel.inhalte.arten.get(art_id)
            if art is None:
                continue
            button = discord.ui.Button(label=art.name, style=discord.ButtonStyle.success, custom_id=f"starter:{art_id}")
            button.callback = self._wählen(art_id)
            self.add_item(button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) == self.nutzer_id:
            return True
        await interaction.response.send_message("Diese Starterwahl gehört einem anderen Spieler.", ephemeral=True)
        return False

    def _wählen(self, art_id: str):
        async def callback(interaction: discord.Interaction) -> None:
            try:
                starter = self.kontext.spiel.tutorial_starter_wählen(self.nutzer_id, art_id)
            except ValueError as fehler:
                await interaction.response.send_message(str(fehler), ephemeral=True)
                return
            embed = discord.Embed(
                title="Willkommen im Fabelbund",
                description=(
                    f"{starter.spitzname} gehört jetzt zu dir. Du bist offiziell Teil des Fabelbunds. "
                    "Beachte die Regeln, nimm weiter Aufträge an und lerne die Fablinge schätzen."
                ),
                color=discord.Color.green(),
            )
            await interaction.response.edit_message(embed=embed, view=None)

        return callback
