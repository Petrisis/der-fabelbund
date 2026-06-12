from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import hashlib

import discord

from fabelbund.dienste.spiel_dienst import AktivitätErgebnis
from fabelbund.modelle.laufzeit import AktiverAuftrag, Aktivität, Fabelwesen, SpielerProfil


def profil_einbettung(spieler: SpielerProfil) -> discord.Embed:
    embed = discord.Embed(title="Der Fabelbund", color=discord.Color.green())
    embed.add_field(name="Geld", value=f"{spieler.geld} Credits", inline=True)
    embed.add_field(name="Pflege-Ruf", value=str(spieler.ruf.get("pflege", 0)), inline=True)
    embed.add_field(name="Zuverlässigkeit", value=str(spieler.ruf.get("zuverlässigkeit", 0)), inline=True)
    return embed


def fabelwesen_einbettung(fabelwesen: Fabelwesen, titel: str | None = None) -> discord.Embed:
    embed = discord.Embed(title=titel or fabelwesen.spitzname, color=discord.Color.blurple())
    embed.add_field(name="Art", value=lesbarer_artname(fabelwesen.art_id), inline=True)
    embed.add_field(name="Seltenheit", value=fabelwesen.seltenheit, inline=True)
    embed.add_field(name="Element", value=fabelwesen.element, inline=True)
    embed.add_field(name="Zustand", value=zustand_text(fabelwesen), inline=False)
    return embed


def auftrag_einbettung(aktiver_auftrag: AktiverAuftrag, auftrag_name: str) -> discord.Embed:
    embed = discord.Embed(title=auftrag_name, color=discord.Color.gold())
    embed.add_field(name="Status", value=aktiver_auftrag.status, inline=True)
    embed.add_field(name="Fabelwesen", value=aktiver_auftrag.fabelwesen_id, inline=True)
    return embed


def aktivität_einbettung(aktivität: Aktivität) -> discord.Embed:
    embed = discord.Embed(title=aktivität.name, color=discord.Color.teal())
    embed.add_field(name="Status", value="läuft", inline=True)
    embed.add_field(name="Fertig", value=f"<t:{unixzeit(aktivität.endet_am)}:R>", inline=True)
    if aktivität.braucht_spieler:
        embed.add_field(name="Betreuung", value="Du bist dabei gebunden.", inline=False)
    else:
        embed.add_field(name="Betreuung", value="Läuft ohne deine ständige Anwesenheit.", inline=False)
    return embed


def aktivität_ergebnis_einbettung(ergebnis: AktivitätErgebnis) -> discord.Embed:
    titel = "Aktivität abgeschlossen" if ergebnis.aktivität.status == "abgeschlossen" else "Aktivität abgebrochen"
    embed = discord.Embed(title=titel, color=discord.Color.teal())
    embed.add_field(name="Fabling", value=ergebnis.fabelwesen.spitzname, inline=True)
    embed.add_field(name="Aktivität", value=ergebnis.aktivität.name, inline=True)
    beobachtung = veränderung_text(ergebnis)
    if beobachtung:
        embed.add_field(name="Beobachtung", value=beobachtung, inline=False)
    if ergebnis.auftrag_abgeschlossen:
        ruf = ", ".join(f"{schlüssel} +{wert}" for schlüssel, wert in ergebnis.ruf_erhalten.items())
        embed.add_field(
            name="Auftrag abgeschlossen",
            value=f"+{ergebnis.geld_erhalten} Credits\n{ruf or 'Ruf unverändert'}",
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
        "deutlich": "Die Pflege ist deutlich zu sehen.",
        "auffallend": "Die Pflege hat einen starken Eindruck hinterlassen.",
    }[stufe]


def hauptbild_pflege(stufe: str) -> str:
    return {
        "leicht": "eine leichte Verbesserung der Pflege",
        "gut": "ein gepflegterer und zufriedenerer Eindruck",
        "deutlich": "eine deutliche Verbesserung der Pflege",
        "auffallend": "eine auffallend gute Pflegewirkung",
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


def zusatzsatz_ruhe_oder_müdigkeit(stress_sinkt: int, negative_energie: int) -> str:
    if stress_sinkt >= 7 and negative_energie >= 1:
        return "Er bleibt ruhiger als zuvor, braucht danach aber etwas Pause."
    if stress_sinkt >= 7:
        return "Er bleibt ruhiger als zuvor."
    if negative_energie >= 1:
        return "Die Aktivität hat ihn ein wenig ermüdet."
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
