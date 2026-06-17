from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import logging
import random

import discord

from fabelbund.anwendung import Anwendungskontext
from fabelbund.discord.darstellung import siegel
from fabelbund.dienste.wettbewerb_dienst import (
    WETTBEWERBSWERTE,
    folgetermin,
    leistungswert,
    nächster_wettbewerbstermin,
    wettbewerb_erstellen,
)
from fabelbund.modelle.laufzeit import Fabelwesen, Wettbewerb, WettbewerbAnmeldung


log = logging.getLogger(__name__)
WETTBEWERB_SCAN_LIMIT = 80
AUSWERTUNG_PAUSE_SEKUNDEN = 60
WETTBEWERB_ERWÄHNUNGEN = discord.AllowedMentions(everyone=False, users=True, roles=False)
WETTBEWERB_START_ERWÄHNUNGEN = discord.AllowedMentions(everyone=True, users=True, roles=False)
WERTNAMEN = {
    "schönheit": "Schönheit",
    "eleganz": "Eleganz",
    "charme": "Charme",
    "intelligenz": "Intelligenz",
    "ausdruck": "Ausdruck",
    "disziplin": "Disziplin",
    "harmonie": "Harmonie",
}


class WettbewerbAnsicht(discord.ui.View):
    def __init__(self, kontext: Anwendungskontext, wettbewerb_id: str) -> None:
        super().__init__(timeout=None)
        self.kontext = kontext
        self.wettbewerb_id = wettbewerb_id
        button = discord.ui.Button(
            label="Fabling anmelden",
            style=discord.ButtonStyle.primary,
            custom_id=f"wettbewerb:anmelden:{wettbewerb_id}",
        )
        button.callback = self._anmelden
        self.add_item(button)

    async def _anmelden(self, interaction: discord.Interaction) -> None:
        wettbewerb = self.kontext.wettbewerbe.holen(self.wettbewerb_id)
        if wettbewerb is None or wettbewerb.status != "offen":
            await interaction.response.send_message("Dieser Wettbewerb ist nicht mehr offen.", ephemeral=True)
            return
        if datetime.now(timezone.utc) >= wettbewerb.anmeldeschluss_am:
            await interaction.response.send_message("Der Anmeldeschluss ist bereits vorbei.", ephemeral=True)
            return

        nutzer_id = str(interaction.user.id)
        eigene_fablinge = [
            fabling
            for fabling in self.kontext.spiel.sammlung(nutzer_id)
            if fabling.besitzer_id == nutzer_id and not fabling.status.get("leih_fabling")
        ]
        if not eigene_fablinge:
            await interaction.response.send_message(
                "Du hast aktuell keinen eigenen Fabling, der antreten kann.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            embed=_anmeldung_einbettung(wettbewerb),
            view=WettbewerbAuswahlAnsicht(self.kontext, wettbewerb, eigene_fablinge),
            ephemeral=True,
        )


class WettbewerbAuswahlAnsicht(discord.ui.View):
    def __init__(self, kontext: Anwendungskontext, wettbewerb: Wettbewerb, fabelwesen: list[Fabelwesen]) -> None:
        super().__init__(timeout=15 * 60)
        self.add_item(WettbewerbAuswahl(kontext, wettbewerb, fabelwesen))


class WettbewerbAuswahl(discord.ui.Select):
    def __init__(self, kontext: Anwendungskontext, wettbewerb: Wettbewerb, fabelwesen: list[Fabelwesen]) -> None:
        self.kontext = kontext
        self.wettbewerb = wettbewerb
        optionen = [
            discord.SelectOption(
                label=fabling.spitzname[:100],
                value=fabling.id,
                description=f"{WERTNAMEN.get(wettbewerb.wert, wettbewerb.wert)}: {fabling.wettbewerbswerte.get(wettbewerb.wert, 0)}",
            )
            for fabling in fabelwesen[:25]
        ]
        super().__init__(
            placeholder="Wähle einen eigenen Fabling",
            min_values=1,
            max_values=1,
            options=optionen,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        nutzer_id = str(interaction.user.id)
        fabelwesen_id = self.values[0]
        wettbewerb = self.kontext.wettbewerbe.holen(self.wettbewerb.id)
        if wettbewerb is None or wettbewerb.status != "offen":
            await interaction.response.edit_message(content="Dieser Wettbewerb ist nicht mehr offen.", embed=None, view=None)
            return
        if datetime.now(timezone.utc) >= wettbewerb.anmeldeschluss_am:
            await interaction.response.edit_message(content="Der Anmeldeschluss ist bereits vorbei.", embed=None, view=None)
            return
        fabling = self.kontext.spiel.fabelwesen.holen(fabelwesen_id)
        if fabling is None or fabling.besitzer_id != nutzer_id or fabling.status.get("leih_fabling"):
            await interaction.response.edit_message(content="Dieser Fabling kann nicht angemeldet werden.", embed=None, view=None)
            return

        self.kontext.wettbewerbe.anmelden(
            WettbewerbAnmeldung(
                wettbewerb_id=wettbewerb.id,
                spieler_id=nutzer_id,
                fabelwesen_id=fabelwesen_id,
            )
        )
        await interaction.response.edit_message(
            content=f"{fabling.spitzname} ist für den Wettbewerb angemeldet.",
            embed=None,
            view=None,
        )
        if interaction.guild is not None:
            await wettbewerb_aktualisieren(self.kontext, interaction.guild)


async def wettbewerb_aktualisieren(kontext: Anwendungskontext, guild: discord.Guild | None) -> None:
    if guild is None:
        return
    kanal = _eventkanal(kontext, guild)
    if kanal is None:
        return
    wettbewerb = kontext.wettbewerbe.nächster_offener_für_guild(str(guild.id))
    if wettbewerb is None:
        wettbewerb = wettbewerb_erstellen(str(guild.id), nächster_wettbewerbstermin())
        kontext.wettbewerbe.speichern(wettbewerb)

    if wettbewerb.discord_event_id is None:
        discord_event_id = await _discord_event_anlegen(guild, wettbewerb)
        if discord_event_id is not None:
            wettbewerb = wettbewerb.model_copy(update={"discord_event_id": discord_event_id})
            kontext.wettbewerbe.speichern(wettbewerb)

    embed = wettbewerb_einbettung(kontext, wettbewerb)
    view = WettbewerbAnsicht(kontext, wettbewerb.id)
    nachricht = None
    if wettbewerb.nachricht_id:
        try:
            nachricht = await kanal.fetch_message(int(wettbewerb.nachricht_id))
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            nachricht = None
    if nachricht is None:
        vorhandene = await _wettbewerb_nachrichten(kanal)
        nachricht = vorhandene.get(wettbewerb.id)
    if nachricht is None:
        nachricht = await kanal.send(embed=embed, view=view)
    else:
        await nachricht.edit(embed=embed, view=view)
    if wettbewerb.nachricht_id != str(nachricht.id):
        kontext.wettbewerbe.speichern(wettbewerb.model_copy(update={"nachricht_id": str(nachricht.id)}))


async def wettbewerbe_prüfen(kontext: Anwendungskontext, guilds: list[discord.Guild]) -> None:
    jetzt = datetime.now(timezone.utc)
    guilds_nach_id = {str(guild.id): guild for guild in guilds}
    for wettbewerb in kontext.wettbewerbe.fällige(jetzt):
        guild = guilds_nach_id.get(wettbewerb.guild_id)
        if guild is None:
            continue
        await wettbewerb_auswerten(kontext, guild, wettbewerb)


async def wettbewerb_auswerten(kontext: Anwendungskontext, guild: discord.Guild, wettbewerb: Wettbewerb) -> None:
    kanal = _eventkanal(kontext, guild)
    if kanal is None:
        return
    kontext.wettbewerbe.speichern(wettbewerb.model_copy(update={"status": "läuft"}))
    anmeldungen = kontext.wettbewerbe.anmeldungen(wettbewerb.id)
    teilnehmer: list[tuple[WettbewerbAnmeldung, Fabelwesen]] = []
    for anmeldung in anmeldungen:
        fabling = kontext.spiel.fabelwesen.holen(anmeldung.fabelwesen_id)
        if fabling is None or fabling.besitzer_id != anmeldung.spieler_id or fabling.status.get("leih_fabling"):
            continue
        teilnehmer.append((anmeldung, fabling))

    wertname = WERTNAMEN.get(wettbewerb.wert, wettbewerb.wert)
    if not teilnehmer:
        await kanal.send(
            f"Der Wettbewerb um **{wertname}** fällt aus, weil keine Fablinge angemeldet wurden.",
            silent=True,
        )
        await _nächsten_wettbewerb_planen(kontext, guild, wettbewerb)
        return

    namen = ", ".join(_teilnehmer_label(anmeldung, fabling) for anmeldung, fabling in teilnehmer)
    await kanal.send(
        f"🏆✨ @everyone **Der Wettbewerb um {wertname} beginnt jetzt!** ✨🏆\n"
        f"🎺 Teilnehmende Fablinge: {namen}\n"
        "📣 Die Wertung läuft. Ergebnisse folgen gleich einzeln.",
        allowed_mentions=WETTBEWERB_START_ERWÄHNUNGEN,
    )
    await asyncio.sleep(AUSWERTUNG_PAUSE_SEKUNDEN)

    random.shuffle(teilnehmer)
    leistungen: list[tuple[WettbewerbAnmeldung, Fabelwesen, int]] = []
    for anmeldung, fabling in teilnehmer:
        punktzahl = leistungswert(fabling, wettbewerb.wert)
        leistungen.append((anmeldung, fabling, punktzahl))
        await kanal.send(
            f"🎯 {_teilnehmer_label(anmeldung, fabling)} erreicht **{punktzahl} Punkte**.",
            allowed_mentions=WETTBEWERB_ERWÄHNUNGEN,
        )
        await asyncio.sleep(AUSWERTUNG_PAUSE_SEKUNDEN)

    leistungen.sort(key=lambda eintrag: eintrag[2], reverse=True)
    sieger_anmeldung, sieger_fabling, _ = leistungen[0]
    spieler = kontext.spiel.spieler.holen(sieger_anmeldung.spieler_id)
    if spieler is not None:
        kontext.spiel.spieler.speichern(spieler.model_copy(update={"geld": spieler.geld + wettbewerb.preisgeld}))

    rangliste = "\n".join(
        f"{platz}. {_teilnehmer_label(anmeldung, fabling)}: {punktzahl} Punkte"
        for platz, (anmeldung, fabling, punktzahl) in enumerate(leistungen, start=1)
    )
    embed = discord.Embed(
        title="🏆 Wettbewerb entschieden",
        description=f"✨ {_teilnehmer_label(sieger_anmeldung, sieger_fabling)} gewinnt den Wettbewerb.",
        color=discord.Color.gold(),
    )
    embed.add_field(name="Preisgeld", value=siegel(wettbewerb.preisgeld), inline=True)
    embed.add_field(name="Rangliste", value=rangliste, inline=False)
    await kanal.send(embed=embed, allowed_mentions=WETTBEWERB_ERWÄHNUNGEN)
    await asyncio.sleep(AUSWERTUNG_PAUSE_SEKUNDEN)
    await _nächsten_wettbewerb_planen(kontext, guild, wettbewerb)


def wettbewerb_einbettung(kontext: Anwendungskontext, wettbewerb: Wettbewerb) -> discord.Embed:
    anmeldungen = kontext.wettbewerbe.anmeldungen(wettbewerb.id)
    wertname = WERTNAMEN.get(wettbewerb.wert, wettbewerb.wert)
    embed = discord.Embed(
        title=f"Wettbewerb: {wertname}",
        description="Ein eigener Fabling kann angemeldet werden. Leih-Fablinge aus Aufträgen sind ausgeschlossen.",
        color=discord.Color.blurple(),
    )
    embed.add_field(name="Gemessen wird", value=wertname, inline=True)
    embed.add_field(name="Preisgeld", value=siegel(wettbewerb.preisgeld), inline=True)
    embed.add_field(name="Beginn", value=_discord_zeit(wettbewerb.beginnt_am, "F"), inline=False)
    embed.add_field(name="Anmeldeschluss", value=_discord_zeit(wettbewerb.anmeldeschluss_am, "R"), inline=True)
    embed.add_field(name="Anmeldungen", value=str(len(anmeldungen)), inline=True)
    embed.set_footer(text=f"wettbewerb:{wettbewerb.id}")
    return embed


def wettbewerb_ansichten(kontext: Anwendungskontext) -> list[WettbewerbAnsicht]:
    return [
        WettbewerbAnsicht(kontext, wettbewerb.id)
        for server in kontext.server.auflisten()
        if (wettbewerb := kontext.wettbewerbe.nächster_offener_für_guild(server.guild_id)) is not None
    ]


def _teilnehmer_label(anmeldung: WettbewerbAnmeldung, fabling: Fabelwesen) -> str:
    return f"<@{anmeldung.spieler_id}>s Fabling **{fabling.spitzname}**"


async def _nächsten_wettbewerb_planen(kontext: Anwendungskontext, guild: discord.Guild, wettbewerb: Wettbewerb) -> None:
    kontext.wettbewerbe.speichern(wettbewerb.model_copy(update={"status": "abgeschlossen"}))
    nächster = wettbewerb_erstellen(str(guild.id), folgetermin(wettbewerb.beginnt_am))
    kontext.wettbewerbe.speichern(nächster)
    await wettbewerb_aktualisieren(kontext, guild)


def _eventkanal(kontext: Anwendungskontext, guild: discord.Guild) -> discord.TextChannel | None:
    konfiguration = kontext.server.holen(str(guild.id))
    if konfiguration is None or not konfiguration.events_kanal_id:
        return None
    kanal = guild.get_channel(int(konfiguration.events_kanal_id))
    if not isinstance(kanal, discord.TextChannel):
        log.warning("Gespeicherter Eventkanal existiert nicht mehr: %s (%s)", guild.name, guild.id)
        return None
    return kanal


async def _discord_event_anlegen(guild: discord.Guild, wettbewerb: Wettbewerb) -> str | None:
    wertname = WERTNAMEN.get(wettbewerb.wert, wettbewerb.wert)
    try:
        event = await guild.create_scheduled_event(
            name=f"Fabelbund-Wettbewerb: {wertname}",
            start_time=wettbewerb.beginnt_am,
            end_time=wettbewerb.beginnt_am + timedelta(hours=1),
            entity_type=discord.EntityType.external,
            privacy_level=discord.PrivacyLevel.guild_only,
            location="#events",
            description=f"Stat-Wettbewerb um {wertname}. Preisgeld: 300 Siegel.",
            reason="Fabelbund-Wettbewerb planen",
        )
    except (discord.Forbidden, discord.HTTPException, TypeError):
        log.exception("Discord-Event konnte nicht angelegt werden: %s (%s)", guild.name, guild.id)
        return None
    return str(event.id)


async def _wettbewerb_nachrichten(kanal: discord.TextChannel) -> dict[str, discord.Message]:
    nachrichten: dict[str, discord.Message] = {}
    bot_mitglied = kanal.guild.me
    async for nachricht in kanal.history(limit=WETTBEWERB_SCAN_LIMIT):
        if bot_mitglied is not None and nachricht.author.id != bot_mitglied.id:
            continue
        for embed in nachricht.embeds:
            footer = embed.footer.text or ""
            if footer.startswith("wettbewerb:"):
                nachrichten[footer.split(":", 1)[1]] = nachricht
    return nachrichten


def _anmeldung_einbettung(wettbewerb: Wettbewerb) -> discord.Embed:
    wertname = WERTNAMEN.get(wettbewerb.wert, wettbewerb.wert)
    embed = discord.Embed(title="Fabling anmelden", color=discord.Color.blurple())
    embed.add_field(name="Wettbewerb", value=wertname, inline=True)
    embed.add_field(name="Beginn", value=_discord_zeit(wettbewerb.beginnt_am, "R"), inline=True)
    return embed


def _discord_zeit(zeitpunkt: datetime, formatcode: str) -> str:
    return f"<t:{int(zeitpunkt.timestamp())}:{formatcode}>"
