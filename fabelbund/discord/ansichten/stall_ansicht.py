from __future__ import annotations

import discord

from fabelbund.dienste.spiel_dienst import MAXIMALE_FABLINGE_PRO_SPIELER, SpielDienst
from fabelbund.discord.darstellung import fabelwesen_einbettung, unixzeit
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
    ) -> None:
        super().__init__(timeout=180)
        self.spiel = spiel
        self.nutzer_id = nutzer_id
        self.kapazität = kapazität
        self.ausgewählt_id = ausgewählt_id
        self.fabelwesen_nach_id = {fabling.id: fabling for fabling in fabelwesen[:MAXIMALE_STALL_BUTTONS]}
        for index, fabling in enumerate(self.fabelwesen_nach_id.values()):
            self.add_item(self._fabling_button(fabling, index))
        if kapazität < MAXIMALE_STALL_BUTTONS:
            self.add_item(self._erweitern_button(len(self.fabelwesen_nach_id)))
        if ausgewählt_id is not None and ausgewählt_id in self.fabelwesen_nach_id:
            self.add_item(StallPrioritätAuswahl(spiel, nutzer_id, ausgewählt_id))

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
            fabelwesen = self.spiel.sammlung(self.nutzer_id)
            kapazität = self.spiel.stall_kapazität(self.nutzer_id)
            await interaction.response.edit_message(
                embed=embed,
                view=StallAnsicht(self.spiel, self.nutzer_id, fabelwesen, kapazität, aktueller_fabling.id),
            )

        button.callback = callback
        return button

    def _erweitern_button(self, index: int) -> discord.ui.Button:
        button = discord.ui.Button(
            label="Erweitern...",
            style=discord.ButtonStyle.secondary,
            custom_id="stall:erweitern",
            row=min(index // 5, 4),
        )

        async def callback(interaction: discord.Interaction) -> None:
            await interaction.response.send_message(
                "Stallerweiterungen sind vorbereitet, aber noch nicht kaufbar.",
                ephemeral=True,
            )

        button.callback = callback
        return button


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
    def __init__(self, spiel: SpielDienst, nutzer_id: str, fabelwesen_id: str) -> None:
        self.spiel = spiel
        self.nutzer_id = nutzer_id
        self.fabelwesen_id = fabelwesen_id
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
            row=4,
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
            view=StallAnsicht(self.spiel, self.nutzer_id, fabelwesen_liste, kapazität, fabelwesen.id),
        )


def stalltyp_label(stalltyp: str | None) -> str:
    if stalltyp is None:
        return "Automatisch"
    if stalltyp == "neutral":
        return "Neutraler Stall"
    return f"{element_emoji(stalltyp)} {stalltyp[:1].upper() + stalltyp[1:]}stall"
