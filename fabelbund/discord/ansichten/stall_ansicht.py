from __future__ import annotations

from datetime import datetime, timezone

import discord

from fabelbund.dienste.spiel_dienst import MAXIMALE_FABLINGE_PRO_SPIELER, SpielDienst
from fabelbund.anwendung import Anwendungskontext
from fabelbund.discord.darstellung import aktivität_einbettung, aktivität_ergebnis_einbettung, fabelwesen_einbettung, fütterung_einbettung, siegel, schlüssel_label, unixzeit
from fabelbund.discord.zeitlimits import EPHEMERE_ANSICHT_TIMEOUT_SEKUNDEN
from fabelbund.modelle.laufzeit import Fabelwesen


MAXIMALE_STALL_BUTTONS = MAXIMALE_FABLINGE_PRO_SPIELER


class StallAnsicht(discord.ui.View):
    def __init__(
        self,
        spiel: SpielDienst,
        nutzer_id: str,
        fabelwesen: list[Fabelwesen],
        kapazität: int,
        ausgewählt_id: str | None = None,
        kategorie: str | None = None,
        kontext: Anwendungskontext | None = None,
    ) -> None:
        super().__init__(timeout=EPHEMERE_ANSICHT_TIMEOUT_SEKUNDEN)
        self.spiel = spiel
        self.nutzer_id = nutzer_id
        self.kapazität = kapazität
        self.ausgewählt_id = ausgewählt_id
        self.kategorie = kategorie
        self.kontext = kontext
        self.fabelwesen_nach_id = {fabling.id: fabling for fabling in fabelwesen[:MAXIMALE_STALL_BUTTONS]}
        if ausgewählt_id is None:
            for index, fabling in enumerate(self.fabelwesen_nach_id.values()):
                self.add_item(self._fabling_button(fabling, index))
            if kapazität < MAXIMALE_STALL_BUTTONS:
                self.add_item(self._erweitern_button(len(self.fabelwesen_nach_id)))
            return

        if ausgewählt_id in self.fabelwesen_nach_id:
            aktivität = self._angezeigte_aktivität(ausgewählt_id)
            if aktivität is None and kategorie is None:
                if spiel.verfügbare_leckerli_ids(nutzer_id):
                    self.add_item(LeckerliAuswahl(spiel, nutzer_id, ausgewählt_id, kontext))
                self.add_item(StallPrioritätAuswahl(spiel, nutzer_id, ausgewählt_id, kontext))
            if aktivität is not None:
                self.add_item(self._abholen_button(aktivität.id))
                if aktivität.abbrechbar:
                    self.add_item(self._abbrechen_button(aktivität.id))
                if not aktivität.braucht_spieler:
                    self.add_item(self._zurück_button())
            elif kategorie is None:
                self._kategorie_buttons_anlegen()
                self.add_item(self._zurück_button())
            else:
                self._aktions_buttons_anlegen(kategorie, ausgewählt_id)
                self.add_item(self._zurück_button())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) == self.nutzer_id:
            return True
        await interaction.response.send_message("Diese Stallübersicht gehört einem anderen Spieler.", ephemeral=True)
        return False

    def _fabling_button(self, fabling: Fabelwesen, index: int) -> discord.ui.Button:
        button = discord.ui.Button(
            label=f"{element_emoji(fabling.element)} {fabling.spitzname}",
            style=discord.ButtonStyle.secondary,
            custom_id=f"stall:{fabling.id}",
            row=index // 5,
        )

        async def callback(interaction: discord.Interaction) -> None:
            aktueller_fabling = self.spiel.fabelwesen.holen(fabling.id)
            if aktueller_fabling is None:
                await interaction.response.send_message("Dieser Fabling wurde nicht gefunden.", ephemeral=True)
                return

            embed = fabelwesen_einbettung(aktueller_fabling)
            aktivität = self.spiel.laufende_aktivität_für_fabelwesen(aktueller_fabling.id)
            if aktivität is not None:
                embed.add_field(
                    name="Aktivität",
                    value=f"{aktivität.name}\nFertig <t:{unixzeit(aktivität.endet_am)}:R>",
                    inline=False,
                )
            futter = leckerli_text(self.spiel, aktueller_fabling)
            if futter:
                embed.add_field(name="Leckerlis", value=futter, inline=False)
            fabelwesen = self.spiel.sammlung(self.nutzer_id)
            kapazität = self.spiel.stall_kapazität(self.nutzer_id)
            await interaction.response.edit_message(
                embed=embed,
                view=StallAnsicht(self.spiel, self.nutzer_id, fabelwesen, kapazität, aktueller_fabling.id, kontext=self.kontext),
            )

        button.callback = callback
        return button

    def _abbrechen_button(self, aktivität_id: str) -> discord.ui.Button:
        button = discord.ui.Button(label="Abbrechen", style=discord.ButtonStyle.danger, custom_id=f"stall:abbrechen:{aktivität_id}")

        async def callback(interaction: discord.Interaction) -> None:
            try:
                ergebnis = self.spiel.aktivität_abbrechen(self.nutzer_id, aktivität_id)
            except ValueError as fehler:
                await interaction.response.send_message(str(fehler), ephemeral=True)
                return
            fabelwesen = self.spiel.sammlung(self.nutzer_id)
            kapazität = self.spiel.stall_kapazität(self.nutzer_id)
            await interaction.response.edit_message(
                embed=aktivität_ergebnis_einbettung(ergebnis),
                view=StallAnsicht(self.spiel, self.nutzer_id, fabelwesen, kapazität, ergebnis.fabelwesen.id, kontext=self.kontext),
            )

        button.callback = callback
        return button

    def _abholen_button(self, aktivität_id: str) -> discord.ui.Button:
        button = discord.ui.Button(label="Abholen", style=discord.ButtonStyle.success, custom_id=f"stall:abholen:{aktivität_id}")

        async def callback(interaction: discord.Interaction) -> None:
            try:
                ergebnis = self.spiel.aktivität_abholen(self.nutzer_id, aktivität_id)
            except ValueError as fehler:
                await interaction.response.send_message(str(fehler), ephemeral=True)
                return
            fabelwesen = self.spiel.sammlung(self.nutzer_id)
            kapazität = self.spiel.stall_kapazität(self.nutzer_id)
            await interaction.response.edit_message(
                embed=aktivität_ergebnis_einbettung(ergebnis),
                view=StallAnsicht(self.spiel, self.nutzer_id, fabelwesen, kapazität, ergebnis.fabelwesen.id, kontext=self.kontext),
            )

        button.callback = callback
        return button

    def _erweitern_button(self, index: int) -> discord.ui.Button:
        spieler = self.spiel.spieler.holen(self.nutzer_id)
        läuft = spieler is not None and isinstance(spieler.tutorialpfad, str) and spieler.tutorialpfad.startswith("stallausbau:")
        button = discord.ui.Button(
            label="Stall fertigstellen" if läuft else f"Neuer Stall ({siegel(180)}, 1m)",
            style=discord.ButtonStyle.success if läuft else discord.ButtonStyle.secondary,
            custom_id="stall:erweitern",
            row=min(index // 5, 4),
        )

        async def callback(interaction: discord.Interaction) -> None:
            spieler = self.spiel.spieler.holen(self.nutzer_id)
            try:
                if spieler is not None and isinstance(spieler.tutorialpfad, str) and spieler.tutorialpfad.startswith("stallausbau:"):
                    ergebnis = self.spiel.stallausbau_abholen(self.nutzer_id)
                else:
                    embed = discord.Embed(title="Neuer Stall", color=discord.Color.green())
                    embed.description = f"Kosten: {siegel(180)}. Der neue neutrale Stall ist nach 1 Minute fertig."
                    await interaction.response.edit_message(
                        embed=embed,
                        view=StallausbauBestätigung(self.spiel, self.nutzer_id, self.kontext),
                    )
                    return
            except ValueError as fehler:
                await interaction.response.send_message(str(fehler), ephemeral=True)
                return
            if ergebnis.status == "läuft":
                embed = discord.Embed(title="Stallausbau", color=discord.Color.green())
                embed.description = f"Der neue Stallplatz ist fertig <t:{unixzeit(ergebnis.endet_am)}:R>."
                await interaction.response.edit_message(embed=embed, view=StallAnsicht(self.spiel, self.nutzer_id, self.spiel.sammlung(self.nutzer_id), self.spiel.stall_kapazität(self.nutzer_id), kontext=self.kontext))
                return
            fabelwesen = self.spiel.sammlung(self.nutzer_id)
            kapazität = self.spiel.stall_kapazität(self.nutzer_id)
            spieler = self.spiel.spieler.holen(self.nutzer_id)
            if (
                self.kontext is not None
                and spieler is not None
                and spieler.tutorialstatus == "aktiv"
                and spieler.tutorialschritt == "aktiv_passiv"
            ):
                embed = discord.Embed(
                    title="Stall fertig",
                    description="Der neue Platz ist bereit. Mira hat den nächsten Probeauftrag vorbereitet.",
                    color=discord.Color.green(),
                )
                await interaction.response.edit_message(
                    embed=embed,
                    view=StallausbauWeiterAnsicht(self.kontext, self.nutzer_id),
                )
                return
            await interaction.response.edit_message(
                embed=stallübersicht_einbettung(self.spiel, self.nutzer_id, fabelwesen, kapazität),
                view=StallAnsicht(self.spiel, self.nutzer_id, fabelwesen, kapazität, kontext=self.kontext),
            )

        button.callback = callback
        return button

    def _kategorie_buttons_anlegen(self) -> None:
        vorhandene_kategorien = {
            aktion.kategorie
            for aktion in self.spiel.inhalte.pflegeaktionen.values()
            if not aktion.gesperrt
        }
        for kategorie in ("pflege", "ruhe", "spiel", "training", "check"):
            if kategorie not in vorhandene_kategorien:
                continue
            button = discord.ui.Button(
                label=kategorie_label(kategorie),
                style=discord.ButtonStyle.secondary,
                custom_id=f"stall:kategorie:{kategorie}",
                row=2,
            )
            button.callback = self._kategorie_callback(kategorie)
            self.add_item(button)
        if self.kontext is not None:
            self.add_item(self._menü_button("Aufträge", "stall:menü:aufträge", self._aufträge_öffnen, row=3))
            self.add_item(self._menü_button("Laden", "stall:menü:laden", self._laden_öffnen, row=3))
            self.add_item(self._menü_button("Inventar", "stall:menü:inventar", self._inventar_öffnen, row=3))

    def _menü_button(self, label: str, custom_id: str, callback, row: int) -> discord.ui.Button:
        button = discord.ui.Button(label=label, style=discord.ButtonStyle.primary, custom_id=custom_id, row=row)
        button.callback = callback
        return button

    async def _aufträge_öffnen(self, interaction: discord.Interaction) -> None:
        if self.kontext is None:
            return
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

    async def _laden_öffnen(self, interaction: discord.Interaction) -> None:
        if self.kontext is None:
            return
        from fabelbund.discord.befehle.laden import LadenAnsicht, laden_einbettung

        await interaction.response.edit_message(
            embed=laden_einbettung(self.kontext, self.nutzer_id),
            view=LadenAnsicht(self.kontext, self.nutzer_id),
        )

    async def _inventar_öffnen(self, interaction: discord.Interaction) -> None:
        if self.kontext is None:
            return
        from fabelbund.discord.befehle.inventar import InventarAnsicht, inventar_einbettung

        await interaction.response.edit_message(
            embed=inventar_einbettung(self.kontext, self.nutzer_id),
            view=InventarAnsicht(self.kontext, self.nutzer_id),
        )

    def _aktions_buttons_anlegen(self, kategorie: str, fabelwesen_id: str) -> None:
        if kategorie == "training":
            self._training_wert_buttons_anlegen()
            return
        if kategorie.startswith("training:"):
            self._training_stufen_buttons_anlegen(kategorie.split(":", 1)[1], fabelwesen_id)
            return
        aktionen = [
            aktion
            for aktion in self.spiel.inhalte.pflegeaktionen.values()
            if not aktion.gesperrt and aktion.kategorie == kategorie
            and not (kategorie == "check" and aktion.aktion_id == "kurzer_blick")
        ]
        for index, aktion in enumerate(aktionen):
            dauer_sekunden = self.spiel.aktionsdauer_sekunden(self.nutzer_id, aktion.aktion_id)
            label = f"{aktion.name} ({dauer_kurz(dauer_sekunden)})"
            if aktion.kosten:
                label = f"{aktion.name} ({dauer_kurz(dauer_sekunden)}, {siegel(aktion.kosten)})"
            button = discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.secondary,
                custom_id=f"stall:aktion:{aktion.aktion_id}",
                row=1 + min(index // 5, 2),
            )
            button.callback = self._aktion_callback(aktion.aktion_id, fabelwesen_id)
            self.add_item(button)

    def _training_wert_buttons_anlegen(self) -> None:
        werte = ("schönheit", "eleganz", "charme", "intelligenz", "ausdruck", "disziplin", "harmonie")
        for index, wert in enumerate(werte):
            button = discord.ui.Button(
                label=schlüssel_label(wert),
                style=discord.ButtonStyle.secondary,
                custom_id=f"stall:training:{wert}",
                row=1 + index // 5,
            )
            button.callback = self._kategorie_callback(f"training:{wert}")
            self.add_item(button)

    def _training_stufen_buttons_anlegen(self, wert: str, fabelwesen_id: str) -> None:
        reihenfolge = {"kurz": 0, "gründlich": 1, "ausgiebig": 2}
        aktionen = sorted(
            [
                aktion
                for aktion in self.spiel.inhalte.pflegeaktionen.values()
                if not aktion.gesperrt and aktion.kategorie == "training" and wert in aktion.markierungen
            ],
            key=lambda aktion: reihenfolge.get(aktion.intensität, 99),
        )
        for index, aktion in enumerate(aktionen):
            dauer_sekunden = self.spiel.aktionsdauer_sekunden(self.nutzer_id, aktion.aktion_id)
            label = f"{schlüssel_label(aktion.intensität)} ({dauer_kurz(dauer_sekunden)})"
            button = discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.danger if aktion.intensität == "ausgiebig" else discord.ButtonStyle.secondary,
                custom_id=f"stall:aktion:{aktion.aktion_id}",
                row=1,
            )
            button.callback = self._aktion_callback(aktion.aktion_id, fabelwesen_id)
            self.add_item(button)

    def _kategorie_callback(self, kategorie: str):
        async def callback(interaction: discord.Interaction) -> None:
            fabelwesen = self.spiel.sammlung(self.nutzer_id)
            kapazität = self.spiel.stall_kapazität(self.nutzer_id)
            ausgewählt = self.fabelwesen_nach_id.get(self.ausgewählt_id or "")
            embed = fabelwesen_detail_einbettung(self.spiel, ausgewählt) if ausgewählt else discord.Embed(title="Fabling")
            await interaction.response.edit_message(
                embed=embed,
                view=StallAnsicht(self.spiel, self.nutzer_id, fabelwesen, kapazität, self.ausgewählt_id, kategorie, kontext=self.kontext),
            )

        return callback

    def _aktion_callback(self, aktion_id: str, fabelwesen_id: str):
        async def callback(interaction: discord.Interaction) -> None:
            try:
                aktivität = self.spiel.pflegeaktivität_starten(self.nutzer_id, aktion_id, fabelwesen_id)
            except ValueError as fehler:
                await interaction.response.send_message(str(fehler), ephemeral=True)
                return
            if aktivität.endet_am <= datetime.now(timezone.utc):
                ergebnis = self.spiel.aktivität_abholen(self.nutzer_id, aktivität.id)
                fabelwesen = self.spiel.sammlung(self.nutzer_id)
                kapazität = self.spiel.stall_kapazität(self.nutzer_id)
                await interaction.response.edit_message(
                    embed=aktivität_ergebnis_einbettung(ergebnis),
                    view=StallAnsicht(self.spiel, self.nutzer_id, fabelwesen, kapazität, ergebnis.fabelwesen.id, kontext=self.kontext),
                )
                return
            fabelwesen = self.spiel.sammlung(self.nutzer_id)
            kapazität = self.spiel.stall_kapazität(self.nutzer_id)
            await interaction.response.edit_message(
                embed=aktivität_einbettung(aktivität),
                view=StallAnsicht(self.spiel, self.nutzer_id, fabelwesen, kapazität, fabelwesen_id, kontext=self.kontext),
            )

        return callback

    def _zurück_button(self) -> discord.ui.Button:
        button = discord.ui.Button(label="Zurück", style=discord.ButtonStyle.primary, custom_id="stall:zurück", row=4)

        async def callback(interaction: discord.Interaction) -> None:
            fabelwesen = self.spiel.sammlung(self.nutzer_id)
            kapazität = self.spiel.stall_kapazität(self.nutzer_id)
            if self.kategorie is not None and self.kategorie.startswith("training:"):
                ausgewählt = self.fabelwesen_nach_id.get(self.ausgewählt_id or "")
                embed = fabelwesen_detail_einbettung(self.spiel, ausgewählt) if ausgewählt else discord.Embed(title="Fabling")
                await interaction.response.edit_message(
                    embed=embed,
                    view=StallAnsicht(self.spiel, self.nutzer_id, fabelwesen, kapazität, self.ausgewählt_id, "training", kontext=self.kontext),
                )
                return
            if self.kategorie is not None:
                ausgewählt = self.fabelwesen_nach_id.get(self.ausgewählt_id or "")
                embed = fabelwesen_detail_einbettung(self.spiel, ausgewählt) if ausgewählt else discord.Embed(title="Fabling")
                await interaction.response.edit_message(
                    embed=embed,
                    view=StallAnsicht(self.spiel, self.nutzer_id, fabelwesen, kapazität, self.ausgewählt_id, kontext=self.kontext),
                )
                return
            await interaction.response.edit_message(
                embed=stallübersicht_einbettung(self.spiel, self.nutzer_id, fabelwesen, kapazität),
                view=StallAnsicht(self.spiel, self.nutzer_id, fabelwesen, kapazität, kontext=self.kontext),
            )

        button.callback = callback
        return button

    def _angezeigte_aktivität(self, fabelwesen_id: str):
        aktive_spieleraktivität = self.spiel.laufende_aktive_spieleraktivität(self.nutzer_id)
        if aktive_spieleraktivität is not None:
            return aktive_spieleraktivität
        return self.spiel.laufende_aktivität_für_fabelwesen(fabelwesen_id)


def stallübersicht_einbettung(spiel: SpielDienst, nutzer_id: str, fabelwesen: list[Fabelwesen], kapazität: int) -> discord.Embed:
    embed = discord.Embed(title="Fablinge", color=discord.Color.blurple())
    embed.description = "Wähle einen Fabling aus."
    if not fabelwesen:
        embed.description = "Dein Stall ist noch leer. Das Tutorial wird dir den ersten Fabling anvertrauen."
    embed.add_field(name="Fablinge", value=f"{len(fabelwesen)}/{kapazität}", inline=True)
    embed.add_field(name="Maximal möglich", value=str(MAXIMALE_STALL_BUTTONS), inline=True)
    belegung = spiel.stallbelegung(nutzer_id)
    if belegung:
        embed.add_field(
            name="Ställe",
            value="\n".join(f"{stalltyp_label(eintrag.stalltyp)}: {eintrag.belegt}/{eintrag.kapazität}" for eintrag in belegung),
            inline=False,
        )
    return embed


class StallausbauBestätigung(discord.ui.View):
    def __init__(self, spiel: SpielDienst, nutzer_id: str, kontext: Anwendungskontext | None) -> None:
        super().__init__(timeout=EPHEMERE_ANSICHT_TIMEOUT_SEKUNDEN)
        self.spiel = spiel
        self.nutzer_id = nutzer_id
        self.kontext = kontext
        bestätigen = discord.ui.Button(label="Bauen", style=discord.ButtonStyle.success, custom_id="stallausbau:bestätigen")
        bestätigen.callback = self._bestätigen
        zurück = discord.ui.Button(label="Zurück", style=discord.ButtonStyle.primary, custom_id="stallausbau:zurück")
        zurück.callback = self._zurück
        self.add_item(bestätigen)
        self.add_item(zurück)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) == self.nutzer_id:
            return True
        await interaction.response.send_message("Dieser Stallausbau gehört einem anderen Spieler.", ephemeral=True)
        return False

    async def _bestätigen(self, interaction: discord.Interaction) -> None:
        try:
            ergebnis = self.spiel.stallausbau_starten(self.nutzer_id)
        except ValueError as fehler:
            await interaction.response.send_message(str(fehler), ephemeral=True)
            return
        embed = discord.Embed(title="Stallausbau", color=discord.Color.green())
        embed.description = f"Der neue Stallplatz ist fertig <t:{unixzeit(ergebnis.endet_am)}:R>."
        fabelwesen = self.spiel.sammlung(self.nutzer_id)
        kapazität = self.spiel.stall_kapazität(self.nutzer_id)
        await interaction.response.edit_message(
            embed=embed,
            view=StallAnsicht(self.spiel, self.nutzer_id, fabelwesen, kapazität, kontext=self.kontext),
        )

    async def _zurück(self, interaction: discord.Interaction) -> None:
        fabelwesen = self.spiel.sammlung(self.nutzer_id)
        kapazität = self.spiel.stall_kapazität(self.nutzer_id)
        await interaction.response.edit_message(
            embed=stallübersicht_einbettung(self.spiel, self.nutzer_id, fabelwesen, kapazität),
            view=StallAnsicht(self.spiel, self.nutzer_id, fabelwesen, kapazität, kontext=self.kontext),
        )


class StallausbauWeiterAnsicht(discord.ui.View):
    def __init__(self, kontext: Anwendungskontext, nutzer_id: str) -> None:
        super().__init__(timeout=EPHEMERE_ANSICHT_TIMEOUT_SEKUNDEN)
        self.kontext = kontext
        self.nutzer_id = nutzer_id
        button = discord.ui.Button(label="Auftrag ansehen", style=discord.ButtonStyle.primary, custom_id="stallausbau:auftrag")
        button.callback = self._auftrag_öffnen
        self.add_item(button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) == self.nutzer_id:
            return True
        await interaction.response.send_message("Diese Ansicht gehört einem anderen Spieler.", ephemeral=True)
        return False

    async def _auftrag_öffnen(self, interaction: discord.Interaction) -> None:
        from fabelbund.discord.befehle.auftrag import AuftragAnsicht, auftragsziel_text
        from fabelbund.discord.darstellung import auftrag_einbettung

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


def fabelwesen_detail_einbettung(spiel: SpielDienst, fabelwesen: Fabelwesen | None) -> discord.Embed:
    if fabelwesen is None:
        return discord.Embed(title="Fabling", color=discord.Color.blurple())
    embed = fabelwesen_einbettung(fabelwesen)
    aktivität = spiel.laufende_aktivität_für_fabelwesen(fabelwesen.id)
    if aktivität is not None:
        embed.add_field(
            name="Aktivität",
            value=f"{aktivität.name}\nFertig <t:{unixzeit(aktivität.endet_am)}:R>",
            inline=False,
        )
    futter = leckerli_text(spiel, fabelwesen)
    if futter:
        embed.add_field(name="Leckerlis", value=futter, inline=False)
    return embed


def dauer_kurz(sekunden: int) -> str:
    if sekunden <= 0:
        return "sofort"
    minuten = max(1, round(sekunden / 60))
    if minuten < 60:
        return f"{minuten}m"
    stunden, rest = divmod(minuten, 60)
    if rest == 0:
        return f"{stunden}h"
    return f"{stunden}h {rest}m"


def kategorie_label(kategorie: str) -> str:
    return {
        "pflege": "Pflege",
        "ruhe": "Ruhe",
        "spiel": "Spiel",
        "training": "Training",
        "check": "Check",
    }.get(kategorie, kategorie[:1].upper() + kategorie[1:])


def element_emoji(element: str) -> str:
    return {
        "glut": "🔥",
        "feuer": "🔥",
        "wald": "🌿",
        "erde": "⛰️",
        "wasser": "💧",
        "eis": "❄️",
        "luft": "🌬️",
        "licht": "✨",
        "schatten": "🌑",
    }.get(element, "◇")


class StallPrioritätAuswahl(discord.ui.Select):
    def __init__(
        self,
        spiel: SpielDienst,
        nutzer_id: str,
        fabelwesen_id: str,
        kontext: Anwendungskontext | None,
    ) -> None:
        self.spiel = spiel
        self.nutzer_id = nutzer_id
        self.fabelwesen_id = fabelwesen_id
        self.kontext = kontext
        stalltypen = spiel.stalltypen(nutzer_id)
        optionen = [
            discord.SelectOption(label="Automatisch", value="automatisch", description="Passender Elementstall, danach neutral."),
        ]
        optionen.extend(
            discord.SelectOption(label=stalltyp_label(stalltyp), value=stalltyp)
            for stalltyp in stalltypen
            if stalltyp != "neutral"
        )
        if "neutral" in stalltypen:
            optionen.append(discord.SelectOption(label="Neutraler Stall", value="neutral"))
        super().__init__(
            placeholder="Stallpriorität wählen",
            min_values=1,
            max_values=1,
            options=optionen[:25],
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        wert = self.values[0]
        stalltyp = None if wert == "automatisch" else wert
        try:
            fabelwesen = self.spiel.stallpriorität_setzen(self.nutzer_id, self.fabelwesen_id, stalltyp)
        except ValueError as fehler:
            await interaction.response.send_message(str(fehler), ephemeral=True)
            return

        embed = fabelwesen_einbettung(fabelwesen)
        embed.add_field(name="Stallpriorität", value=stalltyp_label(stalltyp) if stalltyp else "Automatisch", inline=False)
        fabelwesen_liste = self.spiel.sammlung(self.nutzer_id)
        kapazität = self.spiel.stall_kapazität(self.nutzer_id)
        await interaction.response.edit_message(
            embed=embed,
            view=StallAnsicht(self.spiel, self.nutzer_id, fabelwesen_liste, kapazität, fabelwesen.id, kontext=self.kontext),
        )


class LeckerliAuswahl(discord.ui.Select):
    def __init__(
        self,
        spiel: SpielDienst,
        nutzer_id: str,
        fabelwesen_id: str,
        kontext: Anwendungskontext | None,
    ) -> None:
        self.spiel = spiel
        self.nutzer_id = nutzer_id
        self.fabelwesen_id = fabelwesen_id
        self.kontext = kontext
        leckerli_ids = spiel.verfügbare_leckerli_ids(nutzer_id)
        optionen = []
        optionen.extend(
            discord.SelectOption(label=gegenstand.name, value=gegenstand.gegenstand_id, description="Als Leckerli geben")
            for gegenstand_id in leckerli_ids
            if (gegenstand := spiel.inhalte.gegenstände.get(gegenstand_id)) is not None
        )
        super().__init__(
            placeholder="Leckerli geben",
            min_values=1,
            max_values=1,
            options=optionen[:25],
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        gegenstand_id = self.values[0]
        try:
            ergebnis = self.spiel.futter_geben(self.nutzer_id, gegenstand_id, self.fabelwesen_id)
        except ValueError as fehler:
            await interaction.response.send_message(str(fehler), ephemeral=True)
            return

        embed = fütterung_einbettung(ergebnis)
        fabelwesen_liste = self.spiel.sammlung(self.nutzer_id)
        kapazität = self.spiel.stall_kapazität(self.nutzer_id)
        await interaction.response.edit_message(
            embed=embed,
            view=StallAnsicht(self.spiel, self.nutzer_id, fabelwesen_liste, kapazität, ergebnis.fabelwesen.id, kontext=self.kontext),
        )


def stalltyp_label(stalltyp: str | None) -> str:
    if stalltyp is None:
        return "Automatisch"
    if stalltyp == "neutral":
        return "Neutraler Stall"
    return f"{element_emoji(stalltyp)} {stalltyp[:1].upper() + stalltyp[1:]}stall"


def leckerli_text(spiel: SpielDienst, fabelwesen: Fabelwesen) -> str:
    lieblingsfutter = fabelwesen.persönlichkeit.get("lieblingsfutter")
    gefunden = bool(fabelwesen.status.get("lieblingsleckerli_gefunden"))
    if gefunden and isinstance(lieblingsfutter, str):
        gegenstand = spiel.inhalte.gegenstände.get(lieblingsfutter)
        return f"Lieblingsleckerli erkannt: {gegenstand.name if gegenstand else lieblingsfutter}"
    letztes = fabelwesen.status.get("letztes_leckerli")
    if isinstance(letztes, str):
        gegenstand = spiel.inhalte.gegenstände.get(letztes)
        return f"Zuletzt probiert: {gegenstand.name if gegenstand else letztes}"
    return "Noch kein Leckerli ausprobiert."
