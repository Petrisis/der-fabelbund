from __future__ import annotations

import discord

from fabelbund.anwendung import Anwendungskontext
from fabelbund.discord.darstellung import auftrag_einbettung, auftragswand_einbettung


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
        embed = auftrag_einbettung(aktiver_auftrag, auftrag, fabelwesen)
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


async def auftragswand_erstellen_oder_aktualisieren(kontext: Anwendungskontext, guild: discord.Guild) -> discord.Message | None:
    konfiguration = kontext.server.holen(str(guild.id))
    if konfiguration is None:
        return None
    kanal = guild.get_channel(int(konfiguration.aufträge_kanal_id))
    if not isinstance(kanal, discord.TextChannel):
        return None

    embed = auftragswand_einbettung(kontext.spiel.öffentliche_aufträge())
    view = AuftragswandAnsicht(kontext, str(guild.id))
    nachricht = None
    if konfiguration.auftragswand_nachricht_id:
        try:
            nachricht = await kanal.fetch_message(int(konfiguration.auftragswand_nachricht_id))
        except discord.NotFound:
            nachricht = None
    if nachricht is None:
        nachricht = await kanal.send(embed=embed, view=view)
    else:
        await nachricht.edit(embed=embed, view=view)

    kontext.server.speichern(konfiguration.model_copy(update={"auftragswand_nachricht_id": str(nachricht.id)}))
    return nachricht


async def auftragswand_aktualisieren(kontext: Anwendungskontext, guild: discord.Guild | None) -> None:
    if guild is None:
        return
    await auftragswand_erstellen_oder_aktualisieren(kontext, guild)


async def chronik_senden(kontext: Anwendungskontext, guild: discord.Guild | None, text: str) -> None:
    if guild is None:
        return
    konfiguration = kontext.server.holen(str(guild.id))
    if konfiguration is None:
        return
    kanal = guild.get_channel(int(konfiguration.chronik_kanal_id))
    if isinstance(kanal, discord.TextChannel):
        await kanal.send(text)
