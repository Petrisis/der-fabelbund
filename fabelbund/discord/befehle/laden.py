from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from fabelbund.anwendung import Anwendungskontext
from fabelbund.discord.darstellung import kauf_einbettung, siegel
from fabelbund.discord.zeitlimits import EPHEMERE_ANSICHT_TIMEOUT_SEKUNDEN


class LadenBefehle(commands.Cog):
    def __init__(self, kontext: Anwendungskontext) -> None:
        self.kontext = kontext

    @app_commands.command(name="laden", description="Öffnet den Fabelbund-Laden.")
    async def laden(self, interaction: discord.Interaction) -> None:
        nutzer_id = str(interaction.user.id)
        await interaction.response.send_message(
            embed=laden_einbettung(self.kontext, nutzer_id),
            view=LadenAnsicht(self.kontext, nutzer_id),
            ephemeral=True,
        )


class LadenAnsicht(discord.ui.View):
    def __init__(self, kontext: Anwendungskontext, nutzer_id: str, kategorie: str | None = None) -> None:
        super().__init__(timeout=EPHEMERE_ANSICHT_TIMEOUT_SEKUNDEN)
        self.kontext = kontext
        self.nutzer_id = nutzer_id
        self.kategorie = kategorie
        if kategorie == "leckerli":
            self._leckerli_buttons_anlegen()
        else:
            self._hauptsortiment_buttons_anlegen()
        self.add_item(self._navigation_button("Fablinge", "laden:fablinge", self._fablinge_öffnen))
        self.add_item(self._navigation_button("Inventar", "laden:inventar", self._inventar_öffnen))
        self.add_item(self._navigation_button("Aufträge", "laden:aufträge", self._aufträge_öffnen))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) == self.nutzer_id:
            return True
        await interaction.response.send_message("Dieser Ladenbesuch gehört einem anderen Spieler.", ephemeral=True)
        return False

    def _hauptsortiment_buttons_anlegen(self) -> None:
        leckerli_button = discord.ui.Button(label="🍬 Leckerlis", style=discord.ButtonStyle.primary, custom_id="laden:kategorie:leckerli", row=0)

        async def leckerli_callback(interaction: discord.Interaction) -> None:
            await interaction.response.edit_message(
                embed=laden_einbettung(self.kontext, self.nutzer_id, "leckerli"),
                view=LadenAnsicht(self.kontext, self.nutzer_id, "leckerli"),
            )

        leckerli_button.callback = leckerli_callback
        self.add_item(leckerli_button)
        gegenstände = [
            gegenstand
            for gegenstand in self.kontext.spiel.inhalte.gegenstände.values()
            if "leckerli" not in gegenstand.markierungen
        ]
        for index, gegenstand in enumerate(sorted(gegenstände, key=lambda eintrag: (eintrag.preis, eintrag.name)), start=1):
            button = discord.ui.Button(
                label=f"{gegenstand.name} ({siegel(gegenstand.preis)})",
                style=discord.ButtonStyle.secondary,
                custom_id=f"laden:kaufen:{gegenstand.gegenstand_id}",
                row=index // 5,
            )
            button.callback = self._kaufen_callback(gegenstand.gegenstand_id)
            self.add_item(button)

    def _leckerli_buttons_anlegen(self) -> None:
        leckerlis = self._leckerli_sortiment()
        for index, gegenstand in enumerate(sorted(leckerlis, key=lambda eintrag: (eintrag.preis, eintrag.name))[:21]):
            button = discord.ui.Button(
                label=f"{leckerli_emoji(gegenstand.gegenstand_id)} {gegenstand.name} ({siegel(gegenstand.preis)})",
                style=discord.ButtonStyle.secondary,
                custom_id=f"laden:kaufen:{gegenstand.gegenstand_id}",
                row=index // 5,
            )
            button.callback = self._kaufen_callback(gegenstand.gegenstand_id)
            self.add_item(button)

        zurück_button = discord.ui.Button(label="Zurück", style=discord.ButtonStyle.primary, custom_id="laden:zurück", row=4)

        async def zurück_callback(interaction: discord.Interaction) -> None:
            await interaction.response.edit_message(
                embed=laden_einbettung(self.kontext, self.nutzer_id),
                view=LadenAnsicht(self.kontext, self.nutzer_id),
            )

        zurück_button.callback = zurück_callback
        self.add_item(zurück_button)

    def _kaufen_callback(self, gegenstand_id: str):
        async def callback(interaction: discord.Interaction) -> None:
            try:
                ergebnis = self.kontext.spiel.gegenstand_kaufen(self.nutzer_id, gegenstand_id)
            except ValueError as fehler:
                await interaction.response.send_message(str(fehler), ephemeral=True)
                return
            await interaction.response.edit_message(
                embed=kauf_einbettung(ergebnis),
                view=LadenAnsicht(self.kontext, self.nutzer_id, self.kategorie),
            )

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


    def _leckerli_sortiment(self):
        leckerlis = [
            gegenstand
            for gegenstand in self.kontext.spiel.inhalte.gegenstände.values()
            if "leckerli" in gegenstand.markierungen
        ]
        tutorial_ids = self._tutorial_leckerli_ids(leckerlis)
        if tutorial_ids:
            nach_id = {gegenstand.gegenstand_id: gegenstand for gegenstand in leckerlis}
            return [nach_id[gegenstand_id] for gegenstand_id in tutorial_ids if gegenstand_id in nach_id]
        return leckerlis

    def _tutorial_leckerli_ids(self, leckerlis) -> list[str]:
        aktiver_auftrag = self.kontext.spiel.aktiver_auftrag(self.nutzer_id)
        if aktiver_auftrag is None or aktiver_auftrag.auftrag_id != "tutorial_futter_004":
            return []
        fablinge = self.kontext.spiel.auftrag_fablinge(aktiver_auftrag)
        liebling = None
        for fabling in fablinge:
            wert = fabling.persönlichkeit.get("lieblingsfutter")
            if isinstance(wert, str):
                liebling = wert
                break
        if liebling is None:
            return []
        günstige = [
            gegenstand.gegenstand_id
            for gegenstand in sorted(leckerlis, key=lambda eintrag: (eintrag.preis, eintrag.name))
            if gegenstand.gegenstand_id != liebling
        ][:2]
        auswahl = [liebling, *günstige]
        return [
            gegenstand_id
            for gegenstand_id in sorted(auswahl, key=lambda eintrag: self.kontext.spiel.inhalte.gegenstände[eintrag].preis)
        ]


def laden_einbettung(kontext: Anwendungskontext, nutzer_id: str, kategorie: str | None = None) -> discord.Embed:
    spieler = kontext.spiel.stelle_spieler_sicher(nutzer_id)
    titel = "Fabelbund-Laden: Leckerlis" if kategorie == "leckerli" else "Fabelbund-Laden"
    embed = discord.Embed(title=titel, color=discord.Color.green())
    embed.add_field(name="Bundsiegel", value=siegel(spieler.geld), inline=True)
    return embed


def sortiment_text(kontext: Anwendungskontext, nutzer_id: str | None = None, kategorie: str | None = None) -> str:
    gegenstände = list(kontext.spiel.inhalte.gegenstände.values())
    if kategorie == "leckerli":
        gegenstände = [gegenstand for gegenstand in gegenstände if "leckerli" in gegenstand.markierungen]
        if nutzer_id is not None:
            gegenstände = tutorial_leckerli_sortiment(kontext, nutzer_id, gegenstände) or gegenstände
    else:
        gegenstände = [gegenstand for gegenstand in gegenstände if "leckerli" not in gegenstand.markierungen]
    zeilen = []
    for gegenstand in sorted(gegenstände, key=lambda eintrag: (eintrag.preis, eintrag.name)):
        name = f"{leckerli_emoji(gegenstand.gegenstand_id)} {gegenstand.name}" if "leckerli" in gegenstand.markierungen else gegenstand.name
        zeilen.append(f"{name}: {siegel(gegenstand.preis)}")
    return "\n".join(zeilen)


def tutorial_leckerli_sortiment(kontext: Anwendungskontext, nutzer_id: str, leckerlis) -> list:
    aktiver_auftrag = kontext.spiel.aktiver_auftrag(nutzer_id)
    if aktiver_auftrag is None or aktiver_auftrag.auftrag_id != "tutorial_futter_004":
        return []
    fablinge = kontext.spiel.auftrag_fablinge(aktiver_auftrag)
    liebling = None
    for fabling in fablinge:
        wert = fabling.persönlichkeit.get("lieblingsfutter")
        if isinstance(wert, str):
            liebling = wert
            break
    if liebling is None:
        return []
    nach_id = {gegenstand.gegenstand_id: gegenstand for gegenstand in leckerlis}
    günstige = [
        gegenstand.gegenstand_id
        for gegenstand in sorted(leckerlis, key=lambda eintrag: (eintrag.preis, eintrag.name))
        if gegenstand.gegenstand_id != liebling
    ][:2]
    auswahl = [liebling, *günstige]
    return [
        nach_id[gegenstand_id]
        for gegenstand_id in sorted(auswahl, key=lambda eintrag: nach_id[eintrag].preis)
        if gegenstand_id in nach_id
    ]


def leckerli_emoji(gegenstand_id: str) -> str:
    return {
        "apfelstücke": "🍎",
        "honigbeeren": "🍯",
        "kräuterheu": "🌿",
        "farnspitzen": "🌱",
        "erdknollen": "🥔",
        "rauchbeeren": "🫐",
        "geröstete_nüsse": "🌰",
        "geröstete_wurzeln": "🍠",
        "warme_samen": "🌻",
        "waldbeeren": "🍓",
        "weiche_wurzeln": "🥕",
        "bachlarven": "🐛",
        "weiche_algen": "🪸",
        "herbe_beeren": "🍇",
        "dornensamen": "🌵",
        "glanzkörner": "✨",
        "moorbeeren": "🫐",
        "nachtkörner": "🌙",
        "schilfsprossen": "🎋",
        "wasserkräuter": "💧",
    }.get(gegenstand_id, "🍬")
