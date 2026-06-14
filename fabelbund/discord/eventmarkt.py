from __future__ import annotations

import logging

import discord

from fabelbund.anwendung import Anwendungskontext
from fabelbund.discord.darstellung import siegel, siegel_übrig
from fabelbund.modelle.inhalte import ArtDefinition


log = logging.getLogger(__name__)
EVENTMARKT_SCAN_LIMIT = 80


class EventmarktAngebotAnsicht(discord.ui.View):
    def __init__(self, kontext: Anwendungskontext, art_id: str) -> None:
        super().__init__(timeout=None)
        self.kontext = kontext
        self.art_id = art_id
        button = discord.ui.Button(
            label="Fabling kaufen",
            style=discord.ButtonStyle.success,
            custom_id=f"eventmarkt:kaufen:{art_id}",
        )
        button.callback = self._kaufen
        self.add_item(button)

    async def _kaufen(self, interaction: discord.Interaction) -> None:
        nutzer_id = str(interaction.user.id)
        try:
            ergebnis = self.kontext.spiel.fabelwesen_kaufen(nutzer_id, self.art_id)
        except ValueError as fehler:
            await interaction.response.send_message(str(fehler), ephemeral=True)
            return

        embed = discord.Embed(title="Fabling gekauft", color=discord.Color.green())
        embed.add_field(name="Fabling", value=ergebnis.fabelwesen.spitzname, inline=True)
        embed.add_field(name="Preis", value=siegel(ergebnis.preis), inline=True)
        embed.add_field(name="Kontostand", value=siegel_übrig(ergebnis.spieler.geld), inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)


def eventmarkt_angebot_einbettung(kontext: Anwendungskontext, art: ArtDefinition) -> discord.Embed:
    preis = kontext.spiel.fabelwesen_preis(art.art_id)
    embed = discord.Embed(title=art.name, color=discord.Color.gold())
    embed.add_field(name="Preis", value=siegel(preis), inline=False)
    embed.set_footer(text=f"fabling:{art.art_id}")
    return embed


async def eventmarkt_aktualisieren(kontext: Anwendungskontext, guild: discord.Guild | None) -> None:
    if guild is None:
        return
    konfiguration = kontext.server.holen(str(guild.id))
    if konfiguration is None or not konfiguration.events_kanal_id:
        return
    kanal = guild.get_channel(int(konfiguration.events_kanal_id))
    if not isinstance(kanal, discord.TextChannel):
        log.warning("Gespeicherter Eventkanal existiert nicht mehr: %s (%s)", guild.name, guild.id)
        return

    vorhandene = await _eventmarkt_nachrichten(kanal)
    for art in _marktarten(kontext):
        embed = eventmarkt_angebot_einbettung(kontext, art)
        view = EventmarktAngebotAnsicht(kontext, art.art_id)
        nachricht = vorhandene.get(art.art_id)
        if nachricht is None:
            await kanal.send(embed=embed, view=view)
        else:
            await nachricht.edit(embed=embed, view=view)


def eventmarkt_ansichten(kontext: Anwendungskontext) -> list[EventmarktAngebotAnsicht]:
    return [EventmarktAngebotAnsicht(kontext, art.art_id) for art in _marktarten(kontext)]


def _marktarten(kontext: Anwendungskontext) -> list[ArtDefinition]:
    return sorted(
        kontext.spiel.inhalte.arten.values(),
        key=lambda art: (kontext.spiel.fabelwesen_preis(art.art_id), art.name),
    )


async def _eventmarkt_nachrichten(kanal: discord.TextChannel) -> dict[str, discord.Message]:
    nachrichten: dict[str, discord.Message] = {}
    bot_mitglied = kanal.guild.me
    async for nachricht in kanal.history(limit=EVENTMARKT_SCAN_LIMIT):
        if bot_mitglied is not None and nachricht.author.id != bot_mitglied.id:
            continue
        for embed in nachricht.embeds:
            footer = embed.footer.text or ""
            if footer.startswith("fabling:"):
                nachrichten[footer.split(":", 1)[1]] = nachricht
    return nachrichten
