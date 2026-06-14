from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib

import discord

from fabelbund.dienste.spiel_dienst import AktivitätErgebnis, AuftragAbgabeErgebnis, FütterungErgebnis, KaufErgebnis
from fabelbund.modelle.inhalte import AuftragDefinition
from fabelbund.modelle.laufzeit import AktiverAuftrag, Aktivität, Fabelwesen, SpielerProfil


def siegel(betrag: int) -> str:
    return f"🏵️ {betrag} Siegel"


def siegel_übrig(betrag: int) -> str:
    return f"{siegel(betrag)} übrig"


def profil_einbettung(spieler: SpielerProfil) -> discord.Embed:
    embed = discord.Embed(title="Der Fabelbund", color=discord.Color.green())
    embed.add_field(name="Bundsiegel", value=siegel(spieler.geld), inline=True)
    embed.add_field(name="Ställe", value=str(spieler.freigeschaltete_ställe), inline=True)
    embed.add_field(name="Pflege-Ruf", value=str(spieler.ruf.get("pflege", 0)), inline=True)
    embed.add_field(name="Zuverlässigkeit", value=str(spieler.ruf.get("zuverlässigkeit", 0)), inline=True)
    embed.add_field(name="Mitgliedschaft", value="offiziell" if spieler.offizielles_mitglied else "Einführung", inline=True)
    embed.add_field(name="Tutorial", value=spieler.tutorialschritt.replace("_", " "), inline=True)
    hinweis = tutorial_hinweis_text(spieler)
    if hinweis:
        embed.add_field(name="Einführung", value=hinweis, inline=False)
    return embed


def tutorial_hinweis_text(spieler: SpielerProfil) -> str:
    if spieler.tutorialstatus != "aktiv":
        return ""
    return {
        "registrierung": "Starte über die Auftragswand mit `Los geht's!`.",
        "ruhe_starten": "Nimm Miras erste Probe an.",
        "pflege_und_ausrüstung": "Nimm den nächsten Probeauftrag an, kaufe eine Moosbürste und nutze Sanfte Fellpflege.",
        "stall_ausbauen": "Gehe zu deinen Fablingen und erweitere deinen Stall.",
        "aktiv_passiv": "Nimm den nächsten Auftrag an und kombiniere passive Ruhe mit aktiver Betreuung.",
        "futterauftrag": "Nimm den nächsten Auftrag an und setze die passende Futterpräferenz.",
        "betreuungszeit": "Nimm den nächsten Auftrag an und betreue den Fabling einige Minuten.",
        "wettbewerb_vorbereitung": "Nimm den nächsten Auftrag an und bereite einen Fabling auf einen Wettbewerb vor.",
        "starter_wählen": "Wähle deinen ersten eigenen Fabling.",
    }.get(spieler.tutorialschritt, "")


def fabelwesen_einbettung(fabelwesen: Fabelwesen, titel: str | None = None) -> discord.Embed:
    embed = discord.Embed(title=titel or fabelwesen.spitzname, color=discord.Color.blurple())
    embed.add_field(name="Art", value=lesbarer_artname(fabelwesen.art_id), inline=True)
    embed.add_field(name="Seltenheit", value=fabelwesen.seltenheit, inline=True)
    embed.add_field(name="Element", value=fabelwesen.element, inline=True)
    embed.add_field(name="Zustand", value=zustand_text(fabelwesen), inline=False)
    return embed


def auftrag_einbettung(
    aktiver_auftrag: AktiverAuftrag,
    auftrag: AuftragDefinition,
    fabelwesen: Fabelwesen | None = None,
    fabelwesen_liste: Sequence[Fabelwesen] | None = None,
) -> discord.Embed:
    embed = discord.Embed(title=auftrag.name, description=auftrag.beschreibung or None, color=discord.Color.gold())
    embed.add_field(name="Status", value=aktiver_auftrag.status, inline=True)
    if auftrag.npc:
        embed.add_field(name="Ansprechpartner", value=auftrag.npc, inline=True)
    zugeteilte = list(fabelwesen_liste or ([fabelwesen] if fabelwesen is not None else []))
    if zugeteilte:
        zeilen = []
        for eintrag in zugeteilte[:3]:
            charakter = eintrag.status.get("tutorial_charakter") or eintrag.status.get("auftrag_charakter")
            artname = lesbarer_artname(eintrag.art_id)
            wert = f"**{eintrag.spitzname}**"
            if eintrag.spitzname.casefold() != artname.casefold():
                wert += f" ({artname})"
            if charakter:
                wert += f"\n{charakter}"
            zeilen.append(wert)
        embed.add_field(name="Zugegeteilt", value="\n\n".join(zeilen), inline=False)
        zielbild = auftragszustand_text(auftrag, zugeteilte)
        if zielbild:
            embed.add_field(name="Ausgangslage und Ziel", value=zielbild, inline=False)
    betreuungszeit = betreuungszeit_text(aktiver_auftrag, auftrag, zugeteilte)
    if betreuungszeit:
        embed.add_field(name="Betreuungszeit", value=betreuungszeit, inline=False)
    embed.add_field(name="Belohnung", value=belohnung_text(auftrag), inline=False)
    return embed


def auftragszustand_text(auftrag: AuftragDefinition, fabelwesen_liste: Sequence[Fabelwesen]) -> str:
    ziele = auftrag.ziele
    if ziele.get("fabling_ziele"):
        zielzeilen = []
        for ziel in ziele.get("fabling_ziele", []):
            if not isinstance(ziel, dict):
                continue
            fabling = _passendes_fabling(fabelwesen_liste, ziel)
            if fabling is None:
                continue
            zeile = _zustandsvergleich_für_fabling(fabling, ziel)
            if zeile:
                zielzeilen.append(zeile)
        return "\n\n".join(zielzeilen)

    if not fabelwesen_liste:
        return ""
    return _zustandsvergleich_für_fabling(fabelwesen_liste[0], ziele)


def _passendes_fabling(fabelwesen_liste: Sequence[Fabelwesen], ziel: dict[str, object]) -> Fabelwesen | None:
    art_id = ziel.get("art_id")
    spitzname = ziel.get("spitzname")
    for fabling in fabelwesen_liste:
        if art_id is not None and fabling.art_id != str(art_id):
            continue
        if spitzname is not None and fabling.spitzname != str(spitzname):
            continue
        return fabling
    return None


def _zustandsvergleich_für_fabling(fabelwesen: Fabelwesen, ziele: dict[str, object]) -> str:
    aktuelle_werte = dict(fabelwesen.zustand)
    aktuelle_werte.update(_auftrags_ist_zustand(fabelwesen))
    return _zielvergleich_text(fabelwesen.spitzname, aktuelle_werte, fabelwesen.wettbewerbswerte, ziele)


def _zielvergleich_text(
    name: str,
    aktuelle_werte: dict[str, int],
    wettbewerbswerte: dict[str, int],
    ziele: dict[str, object],
) -> str:
    ist_teile: list[str] = []
    ziel_teile: list[str] = []
    for zielschlüssel, zustandsschlüssel, label, richtung in ZUSTANDSZIELE:
        zielwert = ziele.get(zielschlüssel)
        if zielwert is None:
            continue
        aktueller_wert = int(aktuelle_werte.get(zustandsschlüssel, 0))
        ist_teile.append(f"{label} {zustandsstufe(zustandsschlüssel, aktueller_wert)}")
        ziel_teile.append(f"{label} {zielstufe(zustandsschlüssel, int(zielwert), richtung)}")

    wettbewerb = ziele.get("wettbewerb_mindestens")
    if isinstance(wettbewerb, dict):
        for schlüssel, zielwert in wettbewerb.items():
            aktueller_wert = int(wettbewerbswerte.get(str(schlüssel), 0))
            label = schlüssel_label(str(schlüssel))
            ist_teile.append(f"{label} {trainingsstufe(aktueller_wert)}")
            ziel_teile.append(f"{label} mindestens {trainingsstufe(int(zielwert))}")

    if not ist_teile and not ziel_teile:
        return ""

    ist = "; ".join(ist_teile) or "keine besondere Abweichung"
    soll = "; ".join(ziel_teile) or "stabil bleiben"
    return f"**{name}**\nIst: {ist}.\nSoll: {soll}."


def auftragsaushang_ziel_text(auftrag: AuftragDefinition) -> str:
    if not auftrag.fabelwesen:
        return ""
    ziele = auftrag.ziele
    if ziele.get("fabling_ziele"):
        zeilen = []
        for ziel in ziele.get("fabling_ziele", []):
            if not isinstance(ziel, dict):
                continue
            definition = next((eintrag for eintrag in auftrag.fabelwesen if eintrag.spitzname == ziel.get("spitzname")), None)
            if definition is None:
                continue
            zeilen.append(_zielvergleich_text(definition.spitzname, definition.start_zustand, {}, ziel))
        return "\n\n".join(zeilen)
    definition = auftrag.fabelwesen[0]
    return _zielvergleich_text(definition.spitzname, definition.start_zustand, {}, ziele)


ZUSTANDSZIELE = (
    ("gesundheit_mindestens", "gesundheit", "Gesundheit", "mindestens"),
    ("energie_mindestens", "energie", "Energie", "mindestens"),
    ("stimmung_mindestens", "stimmung", "Stimmung", "mindestens"),
    ("vertrauen_mindestens", "vertrauen", "Vertrauen", "mindestens"),
    ("sicherheit_mindestens", "sicherheit", "Sicherheit", "mindestens"),
    ("fellpflege_mindestens", "fellpflege", "Fellpflege", "mindestens"),
    ("stress_höchstens", "stress", "Stress", "höchstens"),
)


def _auftrags_ist_zustand(fabelwesen: Fabelwesen) -> dict[str, int]:
    zustand = fabelwesen.status.get("auftrag_start_zustand")
    if not isinstance(zustand, dict):
        return fabelwesen.zustand
    return {str(schlüssel): int(wert) for schlüssel, wert in zustand.items() if isinstance(wert, int)}


def zielstufe(schlüssel: str, wert: int, richtung: str) -> str:
    stufe = zustandsstufe(schlüssel, wert)
    if richtung == "höchstens":
        return f"höchstens {stufe}"
    return f"mindestens {stufe}"


def zustandsstufe(schlüssel: str, wert: int) -> str:
    if schlüssel == "stress":
        if wert <= 20:
            return "sehr ruhig"
        if wert <= 35:
            return "ruhig genug"
        if wert <= 55:
            return "angespannt"
        return "deutlich gestresst"
    if schlüssel == "fellpflege":
        if wert >= 75:
            return "sehr gepflegt"
        if wert >= 55:
            return "ordentlich"
        if wert >= 40:
            return "ungeordnet"
        return "vernachlässigt"
    if schlüssel == "energie":
        if wert >= 75:
            return "voll verfügbar"
        if wert >= 55:
            return "ausreichend wach"
        if wert >= 40:
            return "müde"
        return "erschöpft"
    if schlüssel == "stimmung":
        if wert >= 75:
            return "sehr offen"
        if wert >= 55:
            return "ausgeglichen"
        if wert >= 40:
            return "gedämpft"
        return "verschlossen"
    if schlüssel in {"vertrauen", "sicherheit"}:
        if wert >= 75:
            return "sehr gefestigt"
        if wert >= 55:
            return "verlässlich"
        if wert >= 40:
            return "unsicher"
        return "brüchig"
    if wert >= 80:
        return "stabil"
    if wert >= 60:
        return "belastbar"
    if wert >= 40:
        return "angeschlagen"
    return "kritisch"


def trainingsstufe(wert: int) -> str:
    if wert >= 75:
        return "stark"
    if wert >= 50:
        return "solide"
    if wert >= 35:
        return "ausbaufähig"
    return "schwach"


def betreuungszeit_text(aktiver_auftrag: AktiverAuftrag, auftrag: AuftragDefinition, fabelwesen_liste: Sequence[Fabelwesen]) -> str:
    minimum = auftrag.ziele.get("betreuungsdauer_sekunden")
    if minimum is None:
        return ""
    ziel = int(minimum)
    gesammelt = betreuungszeit_gesammelt(fabelwesen_liste)
    offen = max(0, ziel - gesammelt)
    zeilen = [f"Gesammelt: {dauer_text(gesammelt)} von {dauer_text(ziel)}."]
    if offen <= 0:
        zeilen.append("Früheste Abgabe: jetzt.")
    else:
        zielzeit = datetime.now(timezone.utc) + timedelta(seconds=offen)
        zeilen.append(f"Früheste Abgabe bei fortlaufender Betreuung: <t:{unixzeit(zielzeit)}:R>.")
    return "\n".join(zeilen)


def betreuungszeit_gesammelt(fabelwesen_liste: Sequence[Fabelwesen]) -> int:
    gesamt = 0.0
    for fabelwesen in fabelwesen_liste:
        log = fabelwesen.status.get("aktivitätslog", [])
        if not isinstance(log, list):
            continue
        for eintrag in log:
            if not isinstance(eintrag, dict) or eintrag.get("status") != "abgeschlossen":
                continue
            if eintrag.get("spieldauer_sekunden") is not None:
                gesamt += float(eintrag["spieldauer_sekunden"])
                continue
            try:
                start = datetime.fromisoformat(str(eintrag["gestartet_am"]))
                ende = datetime.fromisoformat(str(eintrag["beendet_am"]))
            except (KeyError, TypeError, ValueError):
                continue
            gesamt += max(0.0, (ende - start).total_seconds())
    return int(round(gesamt))


def dauer_text(sekunden: int) -> str:
    minuten, restsekunden = divmod(max(0, int(sekunden)), 60)
    if minuten and restsekunden:
        return f"{minuten}m {restsekunden}s"
    if minuten:
        return f"{minuten}m"
    return f"{restsekunden}s"


def auftragswand_einbettung(aufträge: Sequence[AuftragDefinition]) -> discord.Embed:
    embed = discord.Embed(
        title="Auftragswand",
        description=(
            "Hier hängen öffentliche Aufträge aus. Jeder Auftrag wird einzeln veröffentlicht und kann direkt "
            "angenommen werden. Über die Schaltflächen darunter erreichst du deinen laufenden Auftrag, deine "
            "Fablinge und dein Inventar."
        ),
        color=discord.Color.gold(),
    )
    if not aufträge:
        embed.add_field(
            name="Keine offenen Aushänge",
            value="Im Moment ist kein passender öffentlicher Auftrag verfügbar.",
            inline=False,
        )
    return embed


def auftragsaushang_einbettung(auftrag: AuftragDefinition) -> discord.Embed:
    embed = discord.Embed(title=auftrag.name, description=auftrag.beschreibung or None, color=discord.Color.gold())
    fabelwesen_text = ", ".join(
        f"{eintrag.spitzname} ({lesbarer_artname(eintrag.art_id)})"
        for eintrag in auftrag.fabelwesen
    ) or "wird bei Annahme zugeteilt"
    zieltext = auftragsaushang_ziel_text(auftrag)
    embed.add_field(name="Leih-Fabling", value=fabelwesen_text, inline=False)
    if zieltext:
        embed.add_field(name="Ausgangslage und Ziel", value=zieltext, inline=False)
    embed.add_field(name="Voraussetzung", value=voraussetzung_text(auftrag), inline=True)
    embed.add_field(name="Belohnung", value=belohnung_text(auftrag), inline=True)
    embed.set_footer(text=f"auftrag:{auftrag.auftrag_id}")
    return embed


def auftrag_abgabe_einbettung(ergebnis: AuftragAbgabeErgebnis) -> discord.Embed:
    titel = "Auftrag abgegeben" if ergebnis.erfolgreich else "Auftrag noch offen"
    embed = discord.Embed(title=titel, color=discord.Color.gold())
    embed.add_field(name="Fabling", value=ergebnis.fabelwesen.spitzname, inline=True)
    if ergebnis.erfolgreich:
        ruf = ", ".join(f"{schlüssel} +{wert}" for schlüssel, wert in ergebnis.ruf_erhalten.items())
        belohnung = f"Du erhältst {ergebnis.geld_erhalten} Bundsiegel."
        embed.add_field(name="Belohnung", value=f"{belohnung}\n{ruf or 'Ruf unverändert'}", inline=False)
        if ergebnis.rückgabe_text:
            embed.add_field(name="Rückgabe", value=ergebnis.rückgabe_text, inline=False)
    embed.add_field(name="Einschätzung", value=ergebnis.hinweis, inline=False)
    return embed


def belohnung_text(auftrag: AuftragDefinition) -> str:
    geld = int(auftrag.belohnungen.get("geld", 0))
    ruf = auftrag.belohnungen.get("ruf", {})
    teile = [siegel(geld)] if geld else []
    if isinstance(ruf, dict):
        teile.extend(f"{schlüssel} +{wert}" for schlüssel, wert in ruf.items())
    return "\n".join(teile) or "Keine feste Belohnung"


def voraussetzung_text(auftrag: AuftragDefinition) -> str:
    teile: list[str] = []
    if auftrag.mindestens_offizielles_mitglied:
        teile.append("offizielles Mitglied")
    mindest_ruf = auftrag.voraussetzungen.get("mindest_ruf")
    if isinstance(mindest_ruf, dict):
        teile.extend(f"{schlüssel_label(str(schlüssel))} {wert}+" for schlüssel, wert in mindest_ruf.items())
    mindest_lizenz = auftrag.voraussetzungen.get("mindest_lizenz")
    if mindest_lizenz:
        teile.append(f"Lizenz {mindest_lizenz}")
    return ", ".join(teile) or "keine besondere Voraussetzung"


def kauf_einbettung(ergebnis: KaufErgebnis) -> discord.Embed:
    embed = discord.Embed(title="Einkauf abgeschlossen", color=discord.Color.green())
    embed.add_field(name="Gegenstand", value=f"{ergebnis.anzahl}x {ergebnis.name}", inline=True)
    embed.add_field(name="Kosten", value=siegel(ergebnis.kosten), inline=True)
    embed.add_field(name="Kontostand", value=siegel_übrig(ergebnis.spieler.geld), inline=False)
    return embed


def fütterung_einbettung(ergebnis: FütterungErgebnis) -> discord.Embed:
    embed = discord.Embed(title="Futter gegeben", color=discord.Color.green())
    embed.add_field(name="Fabling", value=ergebnis.fabelwesen.spitzname, inline=True)
    embed.add_field(name="Futter", value=ergebnis.name, inline=True)
    if ergebnis.lieblingsfutter:
        embed.add_field(name="Reaktion", value=f"{ergebnis.fabelwesen.spitzname} erkennt sein Lieblingsfutter sofort.", inline=False)
    else:
        embed.add_field(name="Reaktion", value=f"{ergebnis.fabelwesen.spitzname} nimmt das Futter ruhig an.", inline=False)
    return embed


def aktivität_einbettung(aktivität: Aktivität) -> discord.Embed:
    embed = discord.Embed(title=aktivität.name, color=discord.Color.teal())
    embed.add_field(name="Status", value="läuft", inline=True)
    embed.add_field(name="Fertig", value=f"<t:{unixzeit(aktivität.endet_am)}:R>", inline=True)
    if aktivität.braucht_spieler:
        embed.add_field(name="Betreuung", value="Du bleibst währenddessen bei dem Fabling.", inline=False)
    else:
        embed.add_field(name="Betreuung", value="Du kannst dich anderem widmen.", inline=False)
    return embed


def aktivität_ergebnis_einbettung(ergebnis: AktivitätErgebnis) -> discord.Embed:
    titel = "Aktivität abgeschlossen" if ergebnis.aktivität.status == "abgeschlossen" else "Aktivität abgebrochen"
    embed = discord.Embed(title=titel, color=discord.Color.teal())
    embed.add_field(name="Fabling", value=ergebnis.fabelwesen.spitzname, inline=True)
    embed.add_field(name="Aktivität", value=ergebnis.aktivität.name, inline=True)
    beobachtung = veränderung_text(ergebnis)
    if beobachtung:
        embed.add_field(name="Beobachtung", value=beobachtung, inline=False)
    training = trainingsfortschritt_text(ergebnis)
    if training:
        embed.add_field(name="Training", value=training, inline=False)
    if ergebnis.auftrag_abgeschlossen:
        ruf = ", ".join(f"{schlüssel} +{wert}" for schlüssel, wert in ergebnis.ruf_erhalten.items())
        belohnung = f"Du erhältst {ergebnis.geld_erhalten} Bundsiegel."
        embed.add_field(
            name="Auftrag abgeschlossen",
            value=f"{belohnung}\n{ruf or 'Ruf unverändert'}",
            inline=False,
        )
    return embed


def zustand_text(fabelwesen: Fabelwesen) -> str:
    zustand = fabelwesen.zustand
    einsetzungen = Zustandseinsetzungen.aus_zustand(fabelwesen.spitzname, zustand)
    vorlagen = (
        Textvorlage(
            "{name} wirkt {grundverfassung}. {pflege_satz} {belastung_satz}",
            braucht=("grundverfassung", "pflege_satz", "belastung_satz"),
        ),
        Textvorlage(
            "Bei {name} entsteht insgesamt ein {gesamtbild}. {energie_satz} {stress_satz}",
            braucht=("gesamtbild", "energie_satz", "stress_satz"),
        ),
    )
    return wähle_variante(vorlagen, f"{fabelwesen.id}:zustand").formatieren(einsetzungen)


def veränderung_text(ergebnis: AktivitätErgebnis) -> str:
    if ergebnis.aktivität.kategorie == "check":
        return check_text(ergebnis)
    if ergebnis.aktivität.aktion_id == "selbstbeschäftigung":
        return selbstbeschäftigung_text(ergebnis)

    einsetzungen = Änderungseinsetzungen.aus_ergebnis(ergebnis)
    if not einsetzungen.hat_inhalt:
        return f"{ergebnis.fabelwesen.spitzname} wirkt nach der Aktivität kaum verändert."

    vorlagen = (
        Textvorlage(
            "{name} kommt {abschluss} zurück. {hauptsatz} {nebensatz}",
            braucht=("abschluss", "hauptsatz", "nebensatz"),
        ),
        Textvorlage(
            "Bei {name} ist {hauptbild} zu sehen. {zusatzsatz}",
            braucht=("hauptbild", "zusatzsatz"),
        ),
    )
    vorlage = wähle_variante(vorlagen, ergebnis.aktivität.id)
    return vorlage.formatieren(einsetzungen)


def selbstbeschäftigung_text(ergebnis: AktivitätErgebnis) -> str:
    name = ergebnis.fabelwesen.spitzname
    varianten = (
        f"{name} hat sich eine ruhige Ecke gesucht und die Umgebung aufmerksam beobachtet. {zustand_text(ergebnis.fabelwesen)}",
        f"{name} hat sich selbst beschäftigt und zwischendurch sichtbar zur Ruhe gefunden. {zustand_text(ergebnis.fabelwesen)}",
        f"{name} hat die Zeit genutzt, um auf eigene Weise wieder etwas Ordnung in sich zu bringen. {zustand_text(ergebnis.fabelwesen)}",
    )
    return varianten[int(hashlib.sha1(ergebnis.fabelwesen.id.encode("utf-8")).hexdigest(), 16) % len(varianten)]


def check_text(ergebnis: AktivitätErgebnis) -> str:
    name = ergebnis.fabelwesen.spitzname
    if ergebnis.aktivität.aktion_id == "genauer_check":
        return f"Du hast mit {name} gespielt und dabei Pfoten, Kopf und Zähne genauer angeschaut. {zustand_text(ergebnis.fabelwesen)}"
    return zustand_text(ergebnis.fabelwesen)


def trainingsfortschritt_text(ergebnis: AktivitätErgebnis) -> str:
    zeilen: list[str] = []
    for schlüssel in ergebnis.wettbewerb_änderungen:
        wert = int(ergebnis.fabelwesen.wettbewerbswerte.get(schlüssel, 0))
        zeilen.append(f"{schlüssel_label(schlüssel)} {fortschrittsbalken(wert)}")
    for schlüssel in ergebnis.sport_änderungen:
        wert = int(ergebnis.fabelwesen.sportwerte.get(schlüssel, 0))
        zeilen.append(f"{schlüssel_label(schlüssel)} {fortschrittsbalken(wert)}")
    return "\n".join(zeilen)


def fortschrittsbalken(wert: int) -> str:
    gefüllt = max(0, min(5, round(wert / 20)))
    return "■" * gefüllt + "□" * (5 - gefüllt)


def schlüssel_label(schlüssel: str) -> str:
    return schlüssel.replace("_", " ").capitalize()


@dataclass(frozen=True)
class Textvorlage:
    text: str
    braucht: tuple[str, ...]

    def formatieren(self, einsetzungen: "Änderungseinsetzungen") -> str:
        werte = {name: getattr(einsetzungen, name) for name in self.braucht}
        return " ".join(self.text.format(name=einsetzungen.name, **werte).split())


@dataclass(frozen=True)
class Änderungseinsetzungen:
    name: str
    abschluss: str
    hauptsatz: str
    nebensatz: str
    hauptbild: str
    zusatzsatz: str
    hat_inhalt: bool

    @classmethod
    def aus_ergebnis(cls, ergebnis: AktivitätErgebnis) -> "Änderungseinsetzungen":
        name = ergebnis.fabelwesen.spitzname
        änderungen = ergebnis.änderungen
        positive_energie = max(0, änderungen.get("energie", 0))
        negative_energie = abs(min(0, änderungen.get("energie", 0)))
        stress_sinkt = abs(min(0, änderungen.get("stress", 0)))
        fellpflege = max(0, änderungen.get("fellpflege", 0))
        stimmung = max(0, änderungen.get("stimmung", 0))
        muskelkater = abs(min(0, änderungen.get("muskelkater", 0)))

        erholung = positive_energie + stress_sinkt + muskelkater
        pflege_und_stimmung = fellpflege + stimmung
        belastung = negative_energie + max(0, änderungen.get("stress", 0))
        stärkster = max(erholung, pflege_und_stimmung, belastung)

        if stärkster == 0:
            return cls(name, "", "", "", "", "", False)

        if erholung >= pflege_und_stimmung and erholung >= belastung:
            stufe = veränderungsstufe(erholung)
            return cls(
                name=name,
                abschluss=abschluss_erholung(stufe),
                hauptsatz=hauptsatz_erholung(stufe),
                nebensatz=nebensatz_fell_oder_stimmung(fellpflege, stimmung),
                hauptbild=hauptbild_erholung(stufe),
                zusatzsatz=zusatzsatz_fell_oder_stimmung(fellpflege, stimmung),
                hat_inhalt=True,
            )

        if pflege_und_stimmung >= belastung:
            stufe = veränderungsstufe(pflege_und_stimmung)
            if fellpflege <= 0 and stimmung > 0:
                return cls(
                    name=name,
                    abschluss=abschluss_stimmung(stufe),
                    hauptsatz=hauptsatz_stimmung(stufe),
                    nebensatz=nebensatz_beschäftigung_oder_müdigkeit(stress_sinkt, negative_energie),
                    hauptbild=hauptbild_stimmung(stufe),
                    zusatzsatz=zusatzsatz_beschäftigung_oder_müdigkeit(stress_sinkt, negative_energie),
                    hat_inhalt=True,
                )
            return cls(
                name=name,
                abschluss=abschluss_pflege(stufe),
                hauptsatz=hauptsatz_pflege(stufe),
                nebensatz=nebensatz_ruhe_oder_müdigkeit(stress_sinkt, negative_energie),
                hauptbild=hauptbild_pflege(stufe),
                zusatzsatz=zusatzsatz_ruhe_oder_müdigkeit(stress_sinkt, negative_energie),
                hat_inhalt=True,
            )

        stufe = veränderungsstufe(belastung)
        return cls(
            name=name,
            abschluss=abschluss_belastung(stufe),
            hauptsatz=hauptsatz_belastung(stufe),
            nebensatz=nebensatz_fell_oder_stimmung(fellpflege, stimmung),
            hauptbild=hauptbild_belastung(stufe),
            zusatzsatz=zusatzsatz_fell_oder_stimmung(fellpflege, stimmung),
            hat_inhalt=True,
        )


@dataclass(frozen=True)
class Zustandseinsetzungen:
    name: str
    grundverfassung: str
    pflege_satz: str
    belastung_satz: str
    gesamtbild: str
    energie_satz: str
    stress_satz: str

    @classmethod
    def aus_zustand(cls, name: str, zustand: dict[str, int]) -> "Zustandseinsetzungen":
        gesundheit = int(zustand.get("gesundheit", 0))
        stimmung = int(zustand.get("stimmung", 0))
        energie = int(zustand.get("energie", 0))
        stress = int(zustand.get("stress", 0))
        fellpflege = int(zustand.get("fellpflege", 0))

        return cls(
            name=name,
            grundverfassung=grundverfassung(gesundheit, stimmung),
            pflege_satz=pflege_satz(fellpflege),
            belastung_satz=belastung_satz(energie, stress),
            gesamtbild=gesamtbild(gesundheit, stimmung, energie, stress),
            energie_satz=energie_satz(energie),
            stress_satz=stress_satz(stress),
        )


def grundverfassung(gesundheit: int, stimmung: int) -> str:
    mittelwert = (gesundheit + stimmung) // 2
    if mittelwert >= 80:
        return "gesund, wach und zugewandt"
    if mittelwert >= 60:
        return "gesund und aufmerksam"
    if mittelwert >= 40:
        return "stabil, aber nicht ganz gelöst"
    return "angeschlagen und zurückhaltend"


def gesamtbild(gesundheit: int, stimmung: int, energie: int, stress: int) -> str:
    wert = (gesundheit + stimmung + energie + (100 - stress)) // 4
    if wert >= 80:
        return "sehr guter Eindruck"
    if wert >= 60:
        return "stabiler Eindruck"
    if wert >= 40:
        return "durchwachsener Eindruck"
    return "angespannter Eindruck"


def pflege_satz(fellpflege: int) -> str:
    if fellpflege >= 80:
        return "Sein Fell wirkt sauber und sehr gepflegt."
    if fellpflege >= 55:
        return "Sein Fell sieht ordentlich aus."
    if fellpflege >= 35:
        return "Sein Fell könnte etwas Aufmerksamkeit gebrauchen."
    return "Sein Fell wirkt vernachlässigt."


def belastung_satz(energie: int, stress: int) -> str:
    if energie >= 65 and stress <= 30:
        return "Er hat Energie und bleibt gut ansprechbar."
    if energie < 35 and stress >= 55:
        return "Er wirkt müde und braucht eine ruhigere Umgebung."
    if energie < 35:
        return "Er sollte nicht zu stark gefordert werden."
    if stress >= 55:
        return "Er wirkt unruhig und braucht etwas Abstand."
    return "Er ist belastbar genug für leichte Aufgaben."


def energie_satz(energie: int) -> str:
    if energie >= 75:
        return "Er ist wach und bereit, sich zu beschäftigen."
    if energie >= 50:
        return "Er hat genug Energie für leichte Aufgaben."
    if energie >= 30:
        return "Er wirkt spürbar erschöpft."
    return "Er braucht sichtbar Ruhe."


def stress_satz(stress: int) -> str:
    if stress <= 20:
        return "Dabei bleibt er ruhig und lässt sich gut führen."
    if stress <= 45:
        return "Dabei ist er leicht angespannt, aber ansprechbar."
    if stress <= 70:
        return "Dabei wirkt er unruhig und braucht eine ruhigere Umgebung."
    return "Dabei steht er deutlich unter Druck."


def abschluss_erholung(stufe: str) -> str:
    return {
        "leicht": "etwas ruhiger",
        "gut": "gut erholt",
        "deutlich": "deutlich gelöster",
        "auffallend": "auffallend ausgeruht",
    }[stufe]


def hauptsatz_erholung(stufe: str) -> str:
    return {
        "leicht": "Die Pause hat ihn ein wenig zur Ruhe gebracht.",
        "gut": "Er wirkt erholter und bleibt ruhiger als zuvor.",
        "deutlich": "Er wirkt sichtbar gelöster und bewegt sich entspannter.",
        "auffallend": "Die Erholung ist ihm klar anzumerken.",
    }[stufe]


def hauptbild_erholung(stufe: str) -> str:
    return {
        "leicht": "eine leichte Entspannung",
        "gut": "eine gute Erholung",
        "deutlich": "eine deutliche Entlastung",
        "auffallend": "eine starke Erholung",
    }[stufe]


def abschluss_pflege(stufe: str) -> str:
    return {
        "leicht": "etwas gepflegter",
        "gut": "gut versorgt",
        "deutlich": "deutlich gepflegter",
        "auffallend": "auffallend ordentlich",
    }[stufe]


def hauptsatz_pflege(stufe: str) -> str:
    return {
        "leicht": "Das Fell sieht etwas ordentlicher aus.",
        "gut": "Das Fell wirkt gut gepflegt und er wirkt zufriedener.",
        "deutlich": "Die Pflege ist klar zu sehen.",
        "auffallend": "Die Pflege hat einen starken Eindruck hinterlassen.",
    }[stufe]


def hauptbild_pflege(stufe: str) -> str:
    return {
        "leicht": "eine leichte Verbesserung der Pflege",
        "gut": "ein gepflegterer und zufriedenerer Eindruck",
        "deutlich": "eine deutliche Verbesserung der Pflege",
        "auffallend": "eine auffallend gute Pflegewirkung",
    }[stufe]


def abschluss_stimmung(stufe: str) -> str:
    return {
        "leicht": "etwas offener",
        "gut": "zufriedener",
        "deutlich": "deutlich zugewandter",
        "auffallend": "auffallend gelöst",
    }[stufe]


def hauptsatz_stimmung(stufe: str) -> str:
    return {
        "leicht": "Die Beschäftigung hat seine Stimmung leicht gehoben.",
        "gut": "Er wirkt zufriedener und lässt sich besser ansprechen.",
        "deutlich": "Er begegnet dir sichtbar offener.",
        "auffallend": "Die gemeinsame Zeit hat ihn klar gelöst.",
    }[stufe]


def hauptbild_stimmung(stufe: str) -> str:
    return {
        "leicht": "eine leichte Aufhellung",
        "gut": "ein zufriedenerer Eindruck",
        "deutlich": "eine deutlich offenere Haltung",
        "auffallend": "eine auffallend gelöste Stimmung",
    }[stufe]


def abschluss_belastung(stufe: str) -> str:
    return {
        "leicht": "etwas müder",
        "gut": "spürbar müder",
        "deutlich": "deutlich erschöpfter",
        "auffallend": "auffallend erschöpft",
    }[stufe]


def hauptsatz_belastung(stufe: str) -> str:
    return {
        "leicht": "Die Aktivität hat ihn leicht angestrengt.",
        "gut": "Die Aktivität hat ihn merklich Energie gekostet.",
        "deutlich": "Die Belastung ist deutlich zu sehen.",
        "auffallend": "Er braucht nach dieser Belastung dringend Ruhe.",
    }[stufe]


def hauptbild_belastung(stufe: str) -> str:
    return {
        "leicht": "eine leichte Ermüdung",
        "gut": "eine spürbare Ermüdung",
        "deutlich": "eine deutliche Erschöpfung",
        "auffallend": "eine auffallende Erschöpfung",
    }[stufe]


def nebensatz_fell_oder_stimmung(fellpflege: int, stimmung: int) -> str:
    if fellpflege >= 7 and stimmung >= 7:
        return "Auch Fell und Stimmung machen einen besseren Eindruck."
    if fellpflege >= 7:
        return "Sein Fell sieht ebenfalls ordentlicher aus."
    if stimmung >= 7:
        return "Er wirkt dabei auch zufriedener."
    return ""


def zusatzsatz_fell_oder_stimmung(fellpflege: int, stimmung: int) -> str:
    if fellpflege >= 7 and stimmung >= 7:
        return "Fell und Stimmung haben sich ebenfalls merklich verbessert."
    if fellpflege >= 7:
        return "Das Fell wirkt zusätzlich ordentlicher."
    if stimmung >= 7:
        return "Seine Stimmung wirkt zusätzlich heller."
    return ""


def nebensatz_ruhe_oder_müdigkeit(stress_sinkt: int, negative_energie: int) -> str:
    if stress_sinkt >= 7 and negative_energie >= 1:
        return "Dabei ist er ruhiger geworden, wirkt aber etwas müder."
    if stress_sinkt >= 7:
        return "Dabei ist er ruhiger geworden."
    if negative_energie >= 1:
        return "Die Pflege hat ihn allerdings etwas müde gemacht."
    return ""


def nebensatz_beschäftigung_oder_müdigkeit(stress_sinkt: int, negative_energie: int) -> str:
    if stress_sinkt >= 7 and negative_energie >= 1:
        return "Dabei ist er ruhiger geworden, wirkt aber etwas müder."
    if stress_sinkt >= 7:
        return "Dabei ist er ruhiger geworden."
    if negative_energie >= 1:
        return "Die Beschäftigung hat ihn allerdings etwas müde gemacht."
    return ""


def zusatzsatz_ruhe_oder_müdigkeit(stress_sinkt: int, negative_energie: int) -> str:
    if stress_sinkt >= 7 and negative_energie >= 1:
        return "Er bleibt ruhiger als zuvor, braucht danach aber etwas Pause."
    if stress_sinkt >= 7:
        return "Er bleibt ruhiger als zuvor."
    if negative_energie >= 1:
        return "Die Aktivität hat ihn ein wenig ermüdet."
    return ""


def zusatzsatz_beschäftigung_oder_müdigkeit(stress_sinkt: int, negative_energie: int) -> str:
    if stress_sinkt >= 7 and negative_energie >= 1:
        return "Er bleibt ruhiger als zuvor, braucht danach aber etwas Pause."
    if stress_sinkt >= 7:
        return "Er bleibt ruhiger als zuvor."
    if negative_energie >= 1:
        return "Die Beschäftigung hat ihn ein wenig ermüdet."
    return ""


def veränderungsstufe(wert: int) -> str:
    if wert <= 6:
        return "leicht"
    if wert <= 15:
        return "gut"
    if wert <= 30:
        return "deutlich"
    return "auffallend"


def wähle_variante(vorlagen: Sequence[Textvorlage], schlüssel: str) -> Textvorlage:
    index = int(hashlib.sha1(schlüssel.encode("utf-8")).hexdigest(), 16) % len(vorlagen)
    return vorlagen[index]


def gesundheit_text(wert: object) -> str:
    wert = int(wert)
    if wert >= 85:
        return "Gesundheit: wirkt kräftig und stabil."
    if wert >= 65:
        return "Gesundheit: macht einen ordentlichen Eindruck."
    if wert >= 40:
        return "Gesundheit: sollte im Blick behalten werden."
    return "Gesundheit: braucht dringend Betreuung."


def stimmung_text(wert: object) -> str:
    wert = int(wert)
    if wert >= 75:
        return "Stimmung: ist munter und offen."
    if wert >= 50:
        return "Stimmung: wirkt ausgeglichen."
    if wert >= 30:
        return "Stimmung: ist etwas gedrückt."
    return "Stimmung: zieht sich deutlich zurück."


def energie_text(wert: object) -> str:
    wert = int(wert)
    if wert >= 75:
        return "Energie: ist wach und bereit."
    if wert >= 50:
        return "Energie: reicht für leichte Aufgaben."
    if wert >= 30:
        return "Energie: wirkt spürbar erschöpft."
    return "Energie: braucht Ruhe."


def stress_text(wert: object) -> str:
    wert = int(wert)
    if wert <= 20:
        return "Stress: ist entspannt."
    if wert <= 45:
        return "Stress: ist leicht angespannt."
    if wert <= 70:
        return "Stress: wirkt unruhig."
    return "Stress: steht deutlich unter Druck."


def fellpflege_text(wert: object) -> str:
    wert = int(wert)
    if wert >= 80:
        return "Fellpflege: das Fell wirkt sehr gepflegt."
    if wert >= 55:
        return "Fellpflege: das Fell sieht ordentlich aus."
    if wert >= 35:
        return "Fellpflege: das Fell braucht Aufmerksamkeit."
    return "Fellpflege: das Fell ist klar vernachlässigt."


def lesbarer_artname(art_id: str) -> str:
    return " ".join(teil[:1].upper() + teil[1:] for teil in art_id.split("_"))


def unixzeit(zeitpunkt) -> int:
    return int(zeitpunkt.timestamp())
