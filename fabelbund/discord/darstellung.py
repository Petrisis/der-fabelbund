from __future__ import annotations

import discord

from fabelbund.modelle.laufzeit import AktiverAuftrag, Fabelwesen, SpielerProfil


def profil_einbettung(spieler: SpielerProfil) -> discord.Embed:
    embed = discord.Embed(title="Der Fabelbund", color=discord.Color.green())
    embed.add_field(name="Geld", value=f"{spieler.geld} Credits", inline=True)
    embed.add_field(name="Pflege-Ruf", value=str(spieler.ruf.get("pflege", 0)), inline=True)
    embed.add_field(name="Zuverlaessigkeit", value=str(spieler.ruf.get("zuverlaessigkeit", 0)), inline=True)
    return embed


def fabelwesen_einbettung(fabelwesen: Fabelwesen, titel: str | None = None) -> discord.Embed:
    embed = discord.Embed(title=titel or fabelwesen.spitzname, color=discord.Color.blurple())
    embed.add_field(name="Art", value=fabelwesen.art_id, inline=True)
    embed.add_field(name="Seltenheit", value=fabelwesen.seltenheit, inline=True)
    embed.add_field(name="Element", value=fabelwesen.element, inline=True)
    embed.add_field(name="Zustand", value=zustand_text(fabelwesen), inline=False)
    return embed


def auftrag_einbettung(aktiver_auftrag: AktiverAuftrag, auftrag_name: str) -> discord.Embed:
    embed = discord.Embed(title=auftrag_name, color=discord.Color.gold())
    embed.add_field(name="Status", value=aktiver_auftrag.status, inline=True)
    embed.add_field(name="Fabelwesen", value=aktiver_auftrag.fabelwesen_id, inline=True)
    return embed


def zustand_text(fabelwesen: Fabelwesen) -> str:
    zustand = fabelwesen.zustand
    return "\n".join(
        [
            f"Gesundheit: {zustand.get('gesundheit', 0)}",
            f"Stimmung: {zustand.get('stimmung', 0)}",
            f"Energie: {zustand.get('energie', 0)}",
            f"Stress: {zustand.get('stress', 0)}",
            f"Vertrauen: {zustand.get('vertrauen', 0)}",
            f"Fellpflege: {zustand.get('fellpflege', 0)}",
            f"Muskelkater: {zustand.get('muskelkater', 0)}",
            f"Verletzungsrisiko: {zustand.get('verletzungsrisiko', 0)}",
        ]
    )
