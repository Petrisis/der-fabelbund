from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fabelbund.datenbank.speicher.aktivität_speicher import AktivitätSpeicher
from fabelbund.datenbank.speicher.auftrag_speicher import AuftragSpeicher
from fabelbund.datenbank.speicher.fabelwesen_speicher import FabelwesenSpeicher
from fabelbund.datenbank.speicher.spieler_speicher import SpielerSpeicher
from fabelbund.dienste.auftrag_dienst import AuftragDienst
from fabelbund.dienste.fabelwesen_fabrik import FabelwesenFabrik
from fabelbund.dienste.pflege_dienst import PflegeDienst
from fabelbund.modelle.basis import begrenze_prozent
from fabelbund.modelle.inhalte import InhaltsKatalog
from fabelbund.modelle.laufzeit import AktiverAuftrag, Aktivität, Fabelwesen, SpielerProfil


MAXIMALE_FABLINGE_PRO_SPIELER = 25
FABELWESEN_PREISE_NACH_SELTENHEIT = {
    "gewöhnlich": 240,
    "selten": 520,
    "episch": 900,
}
INAKTIVITÄT_START_SEKUNDEN = 60 * 60
INAKTIVITÄT_MAX_WIRKUNG_SEKUNDEN = 8 * 60 * 60
VERWAHRLOSUNG_START_SEKUNDEN = 24 * 60 * 60
SÄTTIGUNG_VERBRAUCH_PRO_TAG = 100
SÄTTIGUNG_FRESSSCHWELLE = 65
SÄTTIGUNG_GRUNDVERSORGUNG_ZIELWERT = 65
SÄTTIGUNG_NÄHRWERT_NORMAL = 20
SÄTTIGUNG_NÄHRWERT_SONSTIG = 14
LECKERLI_NÄHRWERT = 20
LECKERLI_BUFF_SPIELSEKUNDEN = int(86400 * LECKERLI_NÄHRWERT / SÄTTIGUNG_VERBRAUCH_PRO_TAG)
LECKERLI_BUFF_FAKTOR = 1.1
TUTORIAL_DAUER_OVERRIDES_SEKUNDEN = {
    ("tutorial_pflege_002", "sanfte_fellpflege"): 120,
    ("tutorial_aktiv_passiv_003", "kontrollierte_ruhe"): 180,
    ("tutorial_aktiv_passiv_003", "gemeinsames_spiel"): 180,
    ("tutorial_betreuung_005", "gemeinsames_spiel"): 120,
    ("tutorial_betreuung_005", "kurze_pause"): 120,
    ("tutorial_wettbewerb_006", "ausdruck_üben"): 180,
}


@dataclass
class PflegeErgebnis:
    fabelwesen: Fabelwesen
    auftrag_abgeschlossen: bool
    geld_erhalten: int
    ruf_erhalten: dict[str, int]


@dataclass
class AktivitätErgebnis:
    aktivität: Aktivität
    fabelwesen: Fabelwesen
    anteil: float
    änderungen: dict[str, int]
    wettbewerb_änderungen: dict[str, int]
    sport_änderungen: dict[str, int]
    auftrag_abgeschlossen: bool
    geld_erhalten: int
    ruf_erhalten: dict[str, int]


@dataclass
class AuftragAbgabeErgebnis:
    auftrag: AktiverAuftrag
    fabelwesen: Fabelwesen
    erfolgreich: bool
    geld_erhalten: int
    ruf_erhalten: dict[str, int]
    hinweis: str
    rückgabe_text: str


@dataclass
class KaufErgebnis:
    spieler: SpielerProfil
    gegenstand_id: str
    name: str
    anzahl: int
    kosten: int


@dataclass
class FablingKaufErgebnis:
    spieler: SpielerProfil
    fabelwesen: Fabelwesen
    preis: int


@dataclass
class StallausbauErgebnis:
    spieler: SpielerProfil
    status: str
    endet_am: datetime | None = None


@dataclass
class FütterungErgebnis:
    fabelwesen: Fabelwesen
    gegenstand_id: str
    name: str
    lieblingsfutter: bool
    änderungen: dict[str, int]
    reaktion: str


@dataclass(frozen=True)
class StallBelegung:
    stalltyp: str
    kapazität: int
    fabelwesen_ids: tuple[str, ...]

    @property
    def belegt(self) -> int:
        return len(self.fabelwesen_ids)


class SpielDienst:
    def __init__(
        self,
        inhalte: InhaltsKatalog,
        spieler: SpielerSpeicher,
        fabelwesen: FabelwesenSpeicher,
        aufträge: AuftragSpeicher,
        aktivitäten: AktivitätSpeicher,
        fabrik: FabelwesenFabrik,
        pflege: PflegeDienst,
        auftrag_dienst: AuftragDienst,
        zeitfaktor: float = 1.0,
    ) -> None:
        self.inhalte = inhalte
        self.spieler = spieler
        self.fabelwesen = fabelwesen
        self.aufträge = aufträge
        self.aktivitäten = aktivitäten
        self.fabrik = fabrik
        self.pflege = pflege
        self.auftrag_dienst = auftrag_dienst
        self.zeitfaktor = max(0.001, zeitfaktor)

    def stelle_spieler_sicher(self, nutzer_id: str) -> SpielerProfil:
        spieler = self.spieler.holen(nutzer_id)
        if spieler is None:
            spieler = SpielerProfil(nutzer_id=nutzer_id)
            self.spieler.speichern(spieler)
        return spieler

    def spielerfortschritt_zurücksetzen(self, nutzer_id: str) -> None:
        self.aktivitäten.für_spieler_löschen(nutzer_id)
        self.aufträge.für_spieler_löschen(nutzer_id)
        self.fabelwesen.für_besitzer_löschen(nutzer_id)
        self.spieler.löschen(nutzer_id)

    def tutorial_starten(self, nutzer_id: str) -> SpielerProfil:
        spieler = self.spieler.holen(nutzer_id) or SpielerProfil(nutzer_id=nutzer_id)
        if spieler.tutorialstatus != "neu":
            return spieler

        aktualisiert = spieler.model_copy(deep=True)
        aktualisiert.tutorialstatus = "aktiv"
        aktualisiert.tutorialschritt = "ruhe_starten"
        aktualisiert.offizielles_mitglied = False
        aktualisiert.freigeschaltete_ställe = max(aktualisiert.freigeschaltete_ställe, 1)
        aktualisiert.stalltypen["neutral"] = max(int(aktualisiert.stalltypen.get("neutral", 0)), 1)
        self.spieler.speichern(aktualisiert)
        return aktualisiert

    def sammlung(self, nutzer_id: str) -> list[Fabelwesen]:
        spieler = self.stelle_spieler_sicher(nutzer_id)
        fabelwesen = self.fabelwesen.für_besitzer_auflisten(nutzer_id)
        jetzt = datetime.now(timezone.utc)
        aktualisierte_fablinge: list[Fabelwesen] = []
        aktualisierter_spieler = spieler.model_copy(deep=True)
        spieler_geändert = False
        for fabling in fabelwesen:
            ernährt, geändert = self._sättigung_aktualisieren(aktualisierter_spieler, fabling, jetzt)
            spieler_geändert = spieler_geändert or geändert
            aktualisierte_fablinge.append(self._inaktivität_aktualisieren(ernährt, jetzt))
        if spieler_geändert:
            self.spieler.speichern(aktualisierter_spieler)
        return aktualisierte_fablinge

    def stall_kapazität(self, nutzer_id: str) -> int:
        spieler = self.stelle_spieler_sicher(nutzer_id)
        return min(MAXIMALE_FABLINGE_PRO_SPIELER, spieler.freigeschaltete_ställe)

    def hat_freien_stall(self, nutzer_id: str) -> bool:
        return len(self.sammlung(nutzer_id)) < self.stall_kapazität(nutzer_id)

    def stalltypen(self, nutzer_id: str) -> dict[str, int]:
        spieler = self.stelle_spieler_sicher(nutzer_id)
        return {
            stalltyp: int(anzahl)
            for stalltyp, anzahl in spieler.stalltypen.items()
            if int(anzahl) > 0
        }

    def stallbelegung(self, nutzer_id: str) -> list[StallBelegung]:
        stalltypen = self.stalltypen(nutzer_id)
        fabelwesen = self.sammlung(nutzer_id)
        belegung: dict[str, list[str]] = {stalltyp: [] for stalltyp in stalltypen}

        for fabling in fabelwesen:
            stalltyp = self._passenden_stall_finden(fabling, stalltypen, belegung)
            if stalltyp is not None:
                belegung[stalltyp].append(fabling.id)

        return [
            StallBelegung(stalltyp=stalltyp, kapazität=kapazität, fabelwesen_ids=tuple(belegung.get(stalltyp, [])))
            for stalltyp, kapazität in stalltypen.items()
        ]

    def stallpriorität_setzen(self, nutzer_id: str, fabelwesen_id: str, stalltyp: str | None) -> Fabelwesen:
        fabelwesen = self.fabelwesen.holen(fabelwesen_id)
        if fabelwesen is None or fabelwesen.besitzer_id != nutzer_id:
            raise ValueError("Dieser Fabling wurde nicht gefunden.")
        if stalltyp is not None and stalltyp not in self.stalltypen(nutzer_id):
            raise ValueError("Dieser Stalltyp ist nicht verfügbar.")

        aktualisiert = fabelwesen.model_copy(deep=True)
        aktualisiert.status["stall_priorität"] = stalltyp
        self.fabelwesen.speichern(aktualisiert)
        return aktualisiert

    def futterpriorität_setzen(self, nutzer_id: str, fabelwesen_id: str, gegenstand_id: str | None) -> Fabelwesen:
        spieler = self.stelle_spieler_sicher(nutzer_id)
        fabelwesen = self.fabelwesen.holen(fabelwesen_id)
        if fabelwesen is None or fabelwesen.besitzer_id != nutzer_id:
            raise ValueError("Dieser Fabling wurde nicht gefunden.")
        if gegenstand_id is not None:
            gegenstand = self.inhalte.gegenstände.get(gegenstand_id)
            if gegenstand is None or gegenstand.kategorie != "futter":
                raise ValueError("Dieses Futter ist nicht verfügbar.")
            if self._inventar_anzahl(spieler.inventar.get(gegenstand_id)) <= 0:
                raise ValueError("Dieses Futter ist nicht in deinem Inventar.")

        aktualisiert = fabelwesen.model_copy(deep=True)
        if gegenstand_id is None:
            aktualisiert.status["futter_priorität"] = []
        else:
            aktualisiert.status["futter_priorität"] = [gegenstand_id]
        self.fabelwesen.speichern(aktualisiert)
        return aktualisiert

    def aktionsdauer_sekunden(self, nutzer_id: str, aktion_id: str) -> int:
        aktion = self.inhalte.pflegeaktionen[aktion_id]
        return self._aktionsdauer_für_spieler(nutzer_id, aktion_id, aktion.dauer_sekunden)

    def fabelwesen_preis(self, art_id: str) -> int:
        art = self.inhalte.arten.get(art_id)
        if art is None:
            raise ValueError("Diese Fabling-Art ist nicht verfügbar.")
        return FABELWESEN_PREISE_NACH_SELTENHEIT.get(art.grundseltenheit, 1200)

    def fabelwesen_kaufen(self, nutzer_id: str, art_id: str) -> FablingKaufErgebnis:
        spieler = self.stelle_spieler_sicher(nutzer_id)
        if not spieler.offizielles_mitglied:
            raise ValueError("Fablinge kannst du erst nach der Einführung kaufen.")
        art = self.inhalte.arten.get(art_id)
        if art is None:
            raise ValueError("Diese Fabling-Art ist nicht verfügbar.")
        if not self.hat_freien_stall(nutzer_id):
            raise ValueError("Du brauchst zuerst einen freien Stallplatz.")

        spieler = self.stelle_spieler_sicher(nutzer_id)
        preis = self.fabelwesen_preis(art_id)
        if spieler.geld < preis:
            raise ValueError("Dafür hast du nicht genug Bundsiegel.")

        aktualisierter_spieler = spieler.model_copy(deep=True)
        aktualisierter_spieler.geld -= preis
        fabelwesen = self.fabrik.erzeuge_starter(nutzer_id, art).model_copy(deep=True)
        fabelwesen.herkunft["methode"] = "eventmarkt"
        fabelwesen.status["gekaufter_fabling"] = True
        self.spieler.speichern(aktualisierter_spieler)
        self.fabelwesen.speichern(fabelwesen)
        return FablingKaufErgebnis(spieler=aktualisierter_spieler, fabelwesen=fabelwesen, preis=preis)

    def _passenden_stall_finden(
        self,
        fabelwesen: Fabelwesen,
        stalltypen: dict[str, int],
        belegung: dict[str, list[str]],
    ) -> str | None:
        priorität = fabelwesen.status.get("stall_priorität")
        kandidaten: list[str] = []
        if isinstance(priorität, str) and priorität:
            kandidaten.append(priorität)
        if fabelwesen.element not in kandidaten:
            kandidaten.append(fabelwesen.element)
        if "neutral" not in kandidaten:
            kandidaten.append("neutral")

        for stalltyp in kandidaten:
            if stalltyp in stalltypen and len(belegung.setdefault(stalltyp, [])) < stalltypen[stalltyp]:
                return stalltyp
        return None

    def stallausbau_starten(self, nutzer_id: str) -> StallausbauErgebnis:
        spieler = self.stelle_spieler_sicher(nutzer_id)
        if spieler.tutorialstatus == "aktiv" and spieler.tutorialschritt != "stall_ausbauen":
            raise ValueError("Ein Stallausbau ist gerade nicht Teil deiner Einführung.")
        if spieler.freigeschaltete_ställe >= MAXIMALE_FABLINGE_PRO_SPIELER:
            raise ValueError("Mehr Stallplätze sind aktuell nicht möglich.")
        if isinstance(spieler.tutorialpfad, str) and spieler.tutorialpfad.startswith("stallausbau:"):
            endet_am = datetime.fromisoformat(spieler.tutorialpfad.split(":", 1)[1])
            return StallausbauErgebnis(spieler=spieler, status="läuft", endet_am=endet_am)
        kosten = 180
        if spieler.geld < kosten:
            raise ValueError("Dafür hast du nicht genug Bundsiegel.")
        endet_am = datetime.now(timezone.utc) + timedelta(seconds=self._skalierte_dauer(60))
        aktualisiert = spieler.model_copy(deep=True)
        aktualisiert.geld -= kosten
        aktualisiert.tutorialpfad = f"stallausbau:{endet_am.isoformat()}"
        self.spieler.speichern(aktualisiert)
        return StallausbauErgebnis(spieler=aktualisiert, status="läuft", endet_am=endet_am)

    def stallausbau_abholen(self, nutzer_id: str) -> StallausbauErgebnis:
        spieler = self.stelle_spieler_sicher(nutzer_id)
        if not isinstance(spieler.tutorialpfad, str) or not spieler.tutorialpfad.startswith("stallausbau:"):
            raise ValueError("Es läuft kein Stallausbau.")
        endet_am = datetime.fromisoformat(spieler.tutorialpfad.split(":", 1)[1])
        if datetime.now(timezone.utc) < endet_am:
            return StallausbauErgebnis(spieler=spieler, status="läuft", endet_am=endet_am)
        aktualisiert = spieler.model_copy(deep=True)
        aktualisiert.freigeschaltete_ställe = min(MAXIMALE_FABLINGE_PRO_SPIELER, aktualisiert.freigeschaltete_ställe + 1)
        aktualisiert.stalltypen["neutral"] = int(aktualisiert.stalltypen.get("neutral", 0)) + 1
        aktualisiert.tutorialpfad = None
        if aktualisiert.tutorialstatus == "aktiv" and aktualisiert.tutorialschritt == "stall_ausbauen":
            aktualisiert.tutorialschritt = "aktiv_passiv"
        self.spieler.speichern(aktualisiert)
        return StallausbauErgebnis(spieler=aktualisiert, status="abgeschlossen")

    def pflegeauftrag_starten(self, nutzer_id: str) -> AktiverAuftrag:
        spieler = self.stelle_spieler_sicher(nutzer_id)
        aktiver_auftrag = self.aufträge.aktiven_holen(nutzer_id)
        if aktiver_auftrag is not None:
            return aktiver_auftrag
        auftrag_id = self._auftrag_id_für_spieler(spieler)
        if auftrag_id is None:
            raise ValueError("Für diesen Tutorialschritt gibt es keinen neuen Auftrag.")
        auftrag = self.inhalte.aufträge[auftrag_id]
        fabelwesen_liste = self._auftrag_fablinge_erzeugen(nutzer_id, auftrag)
        if not fabelwesen_liste:
            fabelwesen_liste = self.fabelwesen.für_besitzer_auflisten(nutzer_id)
        if not fabelwesen_liste:
            raise ValueError("Dieser Auftrag hat keinen zugeteilten Fabling.")
        fabelwesen = fabelwesen_liste[0]
        aktiver_auftrag = self.auftrag_dienst.erstelle_aktiven_auftrag(nutzer_id, auftrag, fabelwesen.id)
        aktiver_auftrag.fortschritt["fabelwesen_ids"] = [fabling.id for fabling in fabelwesen_liste]
        self.aufträge.speichern(aktiver_auftrag)
        return aktiver_auftrag

    def öffentliche_aufträge(self, limit: int = 3) -> list:
        aktive_öffentliche_ids = {
            auftrag.auftrag_id
            for auftrag in self.aufträge.aktive_auflisten()
            if auftrag.fortschritt.get("quelle") == "auftragswand"
        }
        aufträge = [
            auftrag
            for auftrag in self.inhalte.aufträge.values()
            if auftrag.öffentlich and auftrag.auftrag_id not in aktive_öffentliche_ids
        ]
        return sorted(aufträge, key=lambda eintrag: (-eintrag.aushang_gewicht, eintrag.auftrag_id))[:limit]

    def öffentlichen_auftrag_annehmen(self, nutzer_id: str, auftrag_id: str, guild_id: str | None = None) -> AktiverAuftrag:
        spieler = self.stelle_spieler_sicher(nutzer_id)
        aktiver_auftrag = self.aufträge.aktiven_holen(nutzer_id)
        if aktiver_auftrag is not None:
            raise ValueError("Du hast bereits einen aktiven Auftrag.")
        auftrag = self.inhalte.aufträge.get(auftrag_id)
        if auftrag is None or not auftrag.öffentlich:
            raise ValueError("Dieser Auftrag ist nicht öffentlich verfügbar.")
        if auftrag not in self.öffentliche_aufträge(limit=25):
            raise ValueError("Dieser Aushang ist nicht mehr verfügbar.")
        self._auftrag_voraussetzungen_prüfen(spieler, auftrag)
        if not self.hat_freien_stall(nutzer_id):
            raise ValueError("Du brauchst zuerst einen freien Stallplatz.")

        fabelwesen_liste = self._auftrag_fablinge_erzeugen(nutzer_id, auftrag)
        if not fabelwesen_liste:
            raise ValueError("Dieser Auftrag hat keinen zugeteilten Fabling.")
        fabelwesen = fabelwesen_liste[0]
        aktiver_auftrag = self.auftrag_dienst.erstelle_aktiven_auftrag(nutzer_id, auftrag, fabelwesen.id)
        aktiver_auftrag.fortschritt["quelle"] = "auftragswand"
        aktiver_auftrag.fortschritt["guild_id"] = guild_id
        aktiver_auftrag.fortschritt["fabelwesen_ids"] = [fabling.id for fabling in fabelwesen_liste]
        aktiver_auftrag.fortschritt["angenommen_am"] = datetime.now(timezone.utc).isoformat()
        self.aufträge.speichern(aktiver_auftrag)
        return aktiver_auftrag

    def _auftrag_voraussetzungen_prüfen(self, spieler: SpielerProfil, auftrag) -> None:
        if auftrag.mindestens_offizielles_mitglied and not spieler.offizielles_mitglied:
            raise ValueError("Diesen Auftrag kannst du erst nach dem Tutorial annehmen.")
        voraussetzungen = auftrag.voraussetzungen
        mindest_lizenz = voraussetzungen.get("mindest_lizenz")
        if mindest_lizenz and str(mindest_lizenz) not in spieler.lizenzen:
            raise ValueError("Dir fehlt die passende Lizenz für diesen Auftrag.")
        mindest_ruf = voraussetzungen.get("mindest_ruf")
        if isinstance(mindest_ruf, dict):
            for bereich, wert in mindest_ruf.items():
                if int(spieler.ruf.get(str(bereich), 0)) < int(wert):
                    raise ValueError("Dein Ruf reicht für diesen Auftrag noch nicht aus.")

    def _auftrag_id_für_spieler(self, spieler: SpielerProfil) -> str | None:
        if spieler.offizielles_mitglied:
            return "pflege_einfach_001"
        return {
            "ruhe_starten": "tutorial_ruhe_001",
            "pflege_und_ausrüstung": "tutorial_pflege_002",
            "aktiv_passiv": "tutorial_aktiv_passiv_003",
            "futterauftrag": "tutorial_futter_004",
            "abbruch_lernen": "tutorial_abbruch_005",
            "betreuungszeit": "tutorial_betreuung_005",
            "wettbewerb_vorbereitung": "tutorial_wettbewerb_006",
        }.get(spieler.tutorialschritt)

    def _auftrag_fablinge_erzeugen(self, nutzer_id: str, auftrag) -> list[Fabelwesen]:
        fabelwesen_liste: list[Fabelwesen] = []
        for zugeteilt in auftrag.fabelwesen:
            art = self.inhalte.arten.get(zugeteilt.art_id)
            if art is None:
                raise ValueError(f"Auftrags-Fabling-Art nicht gefunden: {zugeteilt.art_id}")
            fabling = self.fabrik.erzeuge_starter(nutzer_id, art).model_copy(deep=True)
            fabling.spitzname = zugeteilt.spitzname
            fabling.herkunft["methode"] = "auftrag"
            fabling.herkunft["auftrag_id"] = auftrag.auftrag_id
            fabling.status["leih_fabling"] = True
            fabling.status["auftrag_id"] = auftrag.auftrag_id
            fabling.status["starter_kandidat"] = zugeteilt.starter_kandidat
            fabling.status["tutorial_fabling"] = auftrag.art == "tutorial"
            fabling.status["auftrag_charakter"] = zugeteilt.charakter
            fabling.status["zuletzt_versorgt_am"] = None
            fabling.status["auftrag_start_zustand"] = dict(zugeteilt.start_zustand)
            for schlüssel, wert in zugeteilt.start_zustand.items():
                if schlüssel in fabling.zustand:
                    fabling.zustand[schlüssel] = wert
            if zugeteilt.lieblingsfutter:
                fabling.persönlichkeit["lieblingsfutter"] = zugeteilt.lieblingsfutter
            self.fabelwesen.speichern(fabling)
            fabelwesen_liste.append(fabling)
        return fabelwesen_liste

    def aktiver_auftrag(self, nutzer_id: str) -> AktiverAuftrag | None:
        return self.aufträge.aktiven_holen(nutzer_id)

    def pflege_anwenden(self, nutzer_id: str, aktion_id: str) -> PflegeErgebnis:
        aktiver_auftrag = self.pflegeauftrag_starten(nutzer_id)
        fabelwesen = self.fabelwesen.holen(aktiver_auftrag.fabelwesen_id)
        if fabelwesen is None:
            raise ValueError(f"Auftrags-Fabelwesen nicht gefunden: {aktiver_auftrag.fabelwesen_id}")

        aktion = self.inhalte.pflegeaktionen[aktion_id]
        aktualisiert = self.pflege.anwenden(fabelwesen, aktion)
        self.fabelwesen.speichern(aktualisiert)

        return PflegeErgebnis(fabelwesen=aktualisiert, auftrag_abgeschlossen=False, geld_erhalten=0, ruf_erhalten={})

    def auftrag_abgeben(self, nutzer_id: str) -> AuftragAbgabeErgebnis:
        spieler = self.stelle_spieler_sicher(nutzer_id)
        aktiver_auftrag = self.aufträge.aktiven_holen(nutzer_id)
        if aktiver_auftrag is None:
            raise ValueError("Du hast keinen aktiven Auftrag.")
        fabelwesen = self.fabelwesen.holen(aktiver_auftrag.fabelwesen_id)
        if fabelwesen is None:
            raise ValueError("Das Auftrags-Fabelwesen wurde nicht gefunden.")

        auftrag = self.inhalte.aufträge[aktiver_auftrag.auftrag_id]
        fabelwesen_liste = self._auftrag_fablinge_holen(aktiver_auftrag)
        if not self.auftrag_dienst.ziele_erfüllt(auftrag, fabelwesen, fabelwesen_liste):
            return AuftragAbgabeErgebnis(
                auftrag=aktiver_auftrag,
                fabelwesen=fabelwesen,
                erfolgreich=False,
                geld_erhalten=0,
                ruf_erhalten={},
                hinweis=self._auftrag_hinweis(auftrag, fabelwesen),
                rückgabe_text="",
            )

        geld_vorher = spieler.geld
        ruf_vorher = dict(spieler.ruf)
        aktualisierter_spieler, abgeschlossen = self.auftrag_dienst.abschließen(spieler, aktiver_auftrag, auftrag)
        aktualisierter_spieler = self._tutorial_nach_auftrag_aktualisieren(aktualisierter_spieler, abgeschlossen)
        self.spieler.speichern(aktualisierter_spieler)
        self.aufträge.speichern(abgeschlossen)
        rückgabe_fablinge = list(fabelwesen_liste or [fabelwesen])
        self._auftrag_fablinge_zurückgeben(abgeschlossen, fabelwesen)
        return AuftragAbgabeErgebnis(
            auftrag=abgeschlossen,
            fabelwesen=fabelwesen,
            erfolgreich=True,
            geld_erhalten=aktualisierter_spieler.geld - geld_vorher,
            ruf_erhalten={
                schlüssel: aktualisierter_spieler.ruf.get(schlüssel, 0) - ruf_vorher.get(schlüssel, 0)
                for schlüssel in aktualisierter_spieler.ruf
                if aktualisierter_spieler.ruf.get(schlüssel, 0) != ruf_vorher.get(schlüssel, 0)
            },
            hinweis=self._tutorial_hinweis_nach_abgabe(abgeschlossen),
            rückgabe_text=self._rückgabe_text(auftrag, rückgabe_fablinge),
        )

    def _auftrag_fablinge_zurückgeben(self, auftrag: AktiverAuftrag, hauptfabling: Fabelwesen) -> None:
        fabelwesen_ids = auftrag.fortschritt.get("fabelwesen_ids", [auftrag.fabelwesen_id])
        if not isinstance(fabelwesen_ids, list):
            fabelwesen_ids = [auftrag.fabelwesen_id]
        if hauptfabling.status.get("starter_kandidat"):
            spieler = self.spieler.holen(auftrag.spieler_id)
            if spieler is not None:
                aktualisiert = spieler.model_copy(deep=True)
                marker = f"starter_kennengelernt:{hauptfabling.art_id}"
                if marker not in aktualisiert.lizenzen:
                    aktualisiert.lizenzen.append(marker)
                self.spieler.speichern(aktualisiert)
        for fabelwesen_id in fabelwesen_ids:
            self.fabelwesen.löschen(str(fabelwesen_id))

    def _auftrag_fablinge_holen(self, auftrag: AktiverAuftrag) -> list[Fabelwesen]:
        fabelwesen_ids = auftrag.fortschritt.get("fabelwesen_ids", [auftrag.fabelwesen_id])
        if not isinstance(fabelwesen_ids, list):
            fabelwesen_ids = [auftrag.fabelwesen_id]
        fabelwesen_liste: list[Fabelwesen] = []
        for fabelwesen_id in fabelwesen_ids:
            fabling = self.fabelwesen.holen(str(fabelwesen_id))
            if fabling is not None:
                fabelwesen_liste.append(fabling)
        return fabelwesen_liste

    def auftrag_fablinge(self, auftrag: AktiverAuftrag) -> list[Fabelwesen]:
        return self._auftrag_fablinge_holen(auftrag)

    def auftrag_erfüllbar(self, aktiver_auftrag: AktiverAuftrag) -> bool:
        fabelwesen = self.fabelwesen.holen(aktiver_auftrag.fabelwesen_id)
        if fabelwesen is None:
            return False
        auftrag = self.inhalte.aufträge[aktiver_auftrag.auftrag_id]
        return self.auftrag_dienst.ziele_erfüllt(auftrag, fabelwesen, self._auftrag_fablinge_holen(aktiver_auftrag))

    def gegenstand_kaufen(self, nutzer_id: str, gegenstand_id: str, anzahl: int = 1) -> KaufErgebnis:
        if anzahl < 1:
            raise ValueError("Die Anzahl muss mindestens 1 sein.")
        spieler = self.stelle_spieler_sicher(nutzer_id)
        gegenstand = self.inhalte.gegenstände.get(gegenstand_id)
        if gegenstand is None:
            raise ValueError("Dieser Gegenstand wurde nicht gefunden.")
        kosten = gegenstand.preis * anzahl
        if spieler.geld < kosten:
            raise ValueError("Dafür hast du nicht genug Bundsiegel.")

        aktualisiert = spieler.model_copy(deep=True)
        aktualisiert.geld -= kosten
        aktualisiert.inventar[gegenstand_id] = self._inventar_eintrag_nach_kauf(
            aktualisiert.inventar.get(gegenstand_id),
            gegenstand_id,
            anzahl,
        )
        self.spieler.speichern(aktualisiert)
        aktualisiert = self._tutorial_nach_kauf_aktualisieren(aktualisiert, gegenstand_id)
        return KaufErgebnis(
            spieler=aktualisiert,
            gegenstand_id=gegenstand_id,
            name=gegenstand.name,
            anzahl=anzahl,
            kosten=kosten,
        )

    def inventar(self, nutzer_id: str) -> dict[str, object]:
        spieler = self.stelle_spieler_sicher(nutzer_id)
        return {
            gegenstand_id: eintrag
            for gegenstand_id, eintrag in spieler.inventar.items()
            if self._inventar_anzahl(eintrag) > 0
        }

    def futter_geben(self, nutzer_id: str, gegenstand_id: str, fabelwesen_id: str | None = None) -> FütterungErgebnis:
        spieler = self.stelle_spieler_sicher(nutzer_id)
        gegenstand = self.inhalte.gegenstände.get(gegenstand_id)
        if gegenstand is None or gegenstand.kategorie != "futter":
            raise ValueError("Dieser Gegenstand ist kein Futter.")
        if not self._ist_leckerli(gegenstand_id):
            raise ValueError("Dieses Futter gehört zur Grundversorgung. Leckerlis gibst du bewusst einem Fabling.")
        if self._inventar_anzahl(spieler.inventar.get(gegenstand_id)) <= 0:
            raise ValueError("Dieses Futter ist nicht in deinem Inventar.")

        if fabelwesen_id is None:
            aktiver_auftrag = self.aufträge.aktiven_holen(nutzer_id)
            if aktiver_auftrag is not None:
                fabelwesen_id = aktiver_auftrag.fabelwesen_id
            else:
                eigene_fabelwesen = self.fabelwesen.für_besitzer_auflisten(nutzer_id)
                if len(eigene_fabelwesen) != 1:
                    raise ValueError("Wähle zuerst in deinen Fablingen aus, welcher Fabling Futter bekommen soll.")
                fabelwesen_id = eigene_fabelwesen[0].id
        fabelwesen = self.fabelwesen.holen(fabelwesen_id)
        if fabelwesen is None or fabelwesen.besitzer_id != nutzer_id:
            raise ValueError("Dieser Fabling wurde nicht gefunden.")

        aktualisierter_spieler = spieler.model_copy(deep=True)
        aktualisierter_spieler.inventar[gegenstand_id] = self._inventar_anzahl(aktualisierter_spieler.inventar.get(gegenstand_id)) - 1
        if self._inventar_anzahl(aktualisierter_spieler.inventar[gegenstand_id]) <= 0:
            del aktualisierter_spieler.inventar[gegenstand_id]

        aktualisiertes_fabling = fabelwesen.model_copy(deep=True)
        effekte = dict(gegenstand.effekte)
        lieblingsfutter = self._ist_lieblingsleckerli(aktualisiertes_fabling, gegenstand_id)
        änderungen = self._werte_anteilig_anwenden(aktualisiertes_fabling.zustand, effekte, 1.0, standardwert=0)
        sättigung = int(aktualisiertes_fabling.zustand.get("sättigung", 80))
        aktualisiertes_fabling.zustand["sättigung"] = begrenze_prozent(sättigung + LECKERLI_NÄHRWERT)
        aktualisiertes_fabling.zustand["verletzungsrisiko"] = self.pflege._risiko_aus_zustand(aktualisiertes_fabling)
        aktualisiertes_fabling.status["zuletzt_gefüttert_am"] = datetime.now(timezone.utc).isoformat()
        aktualisiertes_fabling.status["letztes_leckerli"] = gegenstand_id
        aktualisiertes_fabling.status["letztes_leckerli_bevorzugt"] = lieblingsfutter
        if lieblingsfutter:
            aktualisiertes_fabling.status["lieblingsleckerli_gefunden"] = True
            aktualisiertes_fabling.status["leckerli_buff_quelle"] = gegenstand_id
            aktualisiertes_fabling.status["leckerli_buff_bis"] = (
                datetime.now(timezone.utc) + timedelta(seconds=self._skalierte_dauer(LECKERLI_BUFF_SPIELSEKUNDEN))
            ).isoformat()
            reaktion = f"{aktualisiertes_fabling.spitzname} erkennt das Leckerli sofort und wird sichtbar aufmerksamer."
        else:
            reaktion = f"{aktualisiertes_fabling.spitzname} nimmt das Leckerli an, bleibt aber eher höflich als begeistert."

        self.spieler.speichern(aktualisierter_spieler)
        self.fabelwesen.speichern(aktualisiertes_fabling)
        self._tutorial_nach_fütterung_aktualisieren(nutzer_id)
        return FütterungErgebnis(
            fabelwesen=aktualisiertes_fabling,
            gegenstand_id=gegenstand_id,
            name=gegenstand.name,
            lieblingsfutter=lieblingsfutter,
            änderungen=änderungen,
            reaktion=reaktion,
        )

    def _tutorial_nach_auftrag_aktualisieren(self, spieler: SpielerProfil, auftrag: AktiverAuftrag) -> SpielerProfil:
        aktualisiert = spieler.model_copy(deep=True)
        if auftrag.auftrag_id == "tutorial_ruhe_001":
            aktualisiert.tutorialschritt = "pflege_und_ausrüstung"
        elif auftrag.auftrag_id == "tutorial_pflege_002":
            aktualisiert.tutorialschritt = "stall_ausbauen"
        elif auftrag.auftrag_id == "tutorial_aktiv_passiv_003":
            aktualisiert.tutorialschritt = "futterauftrag"
        elif auftrag.auftrag_id == "tutorial_futter_004":
            aktualisiert.tutorialschritt = "abbruch_lernen"
        elif auftrag.auftrag_id == "tutorial_abbruch_005":
            aktualisiert.tutorialschritt = "betreuungszeit"
        elif auftrag.auftrag_id == "tutorial_betreuung_005":
            aktualisiert.tutorialschritt = "wettbewerb_vorbereitung"
        elif auftrag.auftrag_id == "tutorial_wettbewerb_006":
            aktualisiert.tutorialschritt = "starter_wählen"
        return aktualisiert

    def _tutorial_nach_kauf_aktualisieren(self, spieler: SpielerProfil, gegenstand_id: str) -> SpielerProfil:
        gegenstand = self.inhalte.gegenstände.get(gegenstand_id)
        if spieler.tutorialstatus == "aktiv" and spieler.tutorialschritt == "futter_kaufen" and gegenstand is not None and gegenstand.kategorie == "futter":
            aktualisiert = spieler.model_copy(deep=True)
            aktualisiert.tutorialschritt = "futter_geben"
            self.spieler.speichern(aktualisiert)
            return aktualisiert
        return spieler

    def _tutorial_nach_fütterung_aktualisieren(self, nutzer_id: str) -> None:
        spieler = self.spieler.holen(nutzer_id)
        if spieler is None or spieler.tutorialstatus != "aktiv" or spieler.tutorialschritt != "futter_geben":
            return
        aktualisiert = spieler.model_copy(deep=True)
        aktualisiert.tutorialschritt = "aktive_betreuung"
        self.spieler.speichern(aktualisiert)

    def _tutorial_nach_aktivität_aktualisieren(self, spieler: SpielerProfil, aktivität: Aktivität, status: str) -> None:
        if spieler.tutorialstatus != "aktiv" or status != "abgeschlossen":
            return
        nächster_schritt: str | None = None
        if spieler.tutorialschritt == "aktive_betreuung" and aktivität.kategorie == "spiel" and aktivität.braucht_spieler:
            nächster_schritt = "training"
        elif spieler.tutorialschritt == "training" and aktivität.kategorie == "training":
            nächster_schritt = "check"
        elif spieler.tutorialschritt == "check" and aktivität.kategorie == "check":
            aktualisiert = spieler.model_copy(deep=True)
            aktualisiert.tutorialstatus = "abgeschlossen"
            aktualisiert.tutorialschritt = "fertig"
            aktualisiert.offizielles_mitglied = True
            if "mitglied:fabelbund" not in aktualisiert.lizenzen:
                aktualisiert.lizenzen.append("mitglied:fabelbund")
            self.spieler.speichern(aktualisiert)
            return
        if nächster_schritt is None:
            return
        aktualisiert = spieler.model_copy(deep=True)
        aktualisiert.tutorialschritt = nächster_schritt
        self.spieler.speichern(aktualisiert)

    def _tutorial_starter_vergeben(self, nutzer_id: str) -> None:
        bestehende = [
            fabling
            for fabling in self.fabelwesen.für_besitzer_auflisten(nutzer_id)
            if not fabling.status.get("leih_fabling")
        ]
        if bestehende:
            return
        art = self.inhalte.arten.get("quellfink") or next(iter(self.inhalte.arten.values()))
        starter = self.fabrik.erzeuge_starter(nutzer_id, art).model_copy(deep=True)
        starter.spitzname = art.name
        starter.herkunft["methode"] = "tutorial_starter"
        starter.status["starter_fabling"] = True
        starter.status["zuletzt_versorgt_am"] = datetime.now(timezone.utc).isoformat()
        self.fabelwesen.speichern(starter)

    def tutorial_starter_wählen(self, nutzer_id: str, art_id: str) -> Fabelwesen:
        spieler = self.stelle_spieler_sicher(nutzer_id)
        if spieler.tutorialstatus != "aktiv" or spieler.tutorialschritt != "starter_wählen":
            raise ValueError("Die Starterwahl ist gerade nicht offen.")
        art = self.inhalte.arten.get(art_id)
        if art is None or art_id not in {"gluthase", "moosluchs", "quellfink"}:
            raise ValueError("Dieser Starter ist nicht verfügbar.")
        if not self.hat_freien_stall(nutzer_id):
            raise ValueError("Du brauchst zuerst einen freien Stallplatz.")
        starter = self.fabrik.erzeuge_starter(nutzer_id, art).model_copy(deep=True)
        starter.spitzname = art.name
        starter.herkunft["methode"] = "tutorial_starter"
        starter.status["starter_fabling"] = True
        starter.status["zuletzt_versorgt_am"] = datetime.now(timezone.utc).isoformat()
        self.fabelwesen.speichern(starter)
        aktualisiert = spieler.model_copy(deep=True)
        aktualisiert.tutorialstatus = "abgeschlossen"
        aktualisiert.tutorialschritt = "fertig"
        aktualisiert.offizielles_mitglied = True
        if "mitglied:fabelbund" not in aktualisiert.lizenzen:
            aktualisiert.lizenzen.append("mitglied:fabelbund")
        self.spieler.speichern(aktualisiert)
        return starter

    def _tutorial_hinweis_nach_abgabe(self, auftrag: AktiverAuftrag) -> str:
        if auftrag.auftrag_id == "tutorial_ruhe_001":
            return "Nach einer Aktion siehst du, welche Werte sich verbessert 🟩 oder verschlechtert 🟥 haben. Eine Ruhe nach anstrengenden Aktivitäten tut uns doch allen gut, oder?"
        if auftrag.auftrag_id == "tutorial_pflege_002":
            return "Hin und wieder tut deinen Fablingen ein bisschen Pflege gut. Denk daran, dass du passende Utensilien brauchst und selbst eine Pflege ein wenig Energie abverlangt."
        if auftrag.auftrag_id == "tutorial_aktiv_passiv_003":
            return "Wenn du deinen Stall noch mehr erweiterst, musst du vorausschauend planen: Mit welchem Fabling beschäftigst du dich aktiv, und wer kann in der Zeit zum Beispiel alleine ruhen?"
        if auftrag.auftrag_id == "tutorial_abbruch_005":
            return "Abbrechen beendet eine Aktivität sofort, kann aber Vertrauen und Sicherheit beschädigen. Nutze es, wenn du musst, aber plane lange aktive Betreuungen bewusst."
        return "Der Auftrag wurde abgegeben."

    def _rückgabe_text(self, auftrag, fabelwesen_liste: list[Fabelwesen]) -> str:
        namen = ", ".join(fabelwesen.spitzname for fabelwesen in fabelwesen_liste)
        verb = "gehen" if len(fabelwesen_liste) != 1 else "geht"
        if not namen:
            namen = "Der Fabling"
            verb = "geht"
        if auftrag.npc:
            return f"{namen} {verb} zurück in {auftrag.npc}s Obhut."
        return f"{namen} {verb} zurück in die Obhut der zuständigen Betreuung."

    def _auftrag_hinweis(self, auftrag, fabelwesen: Fabelwesen) -> str:
        hinweis = auftrag.fehlschlag.get("hinweis")
        if isinstance(hinweis, str) and hinweis:
            return hinweis
        if auftrag.ziele.get("fabling_ziele"):
            return "Die geforderten Zustände der zugeteilten Fablinge sind noch nicht erreicht."
        if auftrag.ziele.get("fellpflege_mindestens"):
            return f"{fabelwesen.spitzname} wirkt noch nicht gepflegt genug."
        if auftrag.ziele.get("wettbewerb_mindestens"):
            return f"{fabelwesen.spitzname} ist für diesen Probewettbewerb noch nicht gut genug vorbereitet."
        if auftrag.ziele.get("abgeschlossene_aktion") == "kontrollierte_ruhe":
            return f"{fabelwesen.spitzname} sollte zuerst eine vollständige Ruhephase abschließen."
        if auftrag.ziele.get("gefüttert"):
            return f"{fabelwesen.spitzname} wurde noch nicht passend versorgt."
        if auftrag.ziele.get("lieblingsleckerli_gegeben"):
            return f"{fabelwesen.spitzname} zeigt noch nicht, dass du sein bevorzugtes Leckerli gefunden hast."
        if auftrag.ziele.get("futter_priorität"):
            return f"{fabelwesen.spitzname} zeigt noch nicht, welches Leckerli er bevorzugt."
        if auftrag.ziele.get("betreuungsdauer_sekunden"):
            return f"{fabelwesen.spitzname} wurde noch nicht lange genug betreut."
        return f"{fabelwesen.spitzname} erfüllt den Auftrag noch nicht überzeugend."

    def laufende_aktivität(self, nutzer_id: str) -> Aktivität | None:
        self.stelle_spieler_sicher(nutzer_id)
        aktivitäten = self.aktivitäten.laufende_für_spieler_holen(nutzer_id)
        if not aktivitäten:
            return None
        return aktivitäten[0]

    def laufende_aktive_spieleraktivität(self, nutzer_id: str) -> Aktivität | None:
        self.stelle_spieler_sicher(nutzer_id)
        return self.aktivitäten.laufende_aktive_für_spieler_holen(nutzer_id)

    def laufende_aktivitäten(self, nutzer_id: str) -> list[Aktivität]:
        self.stelle_spieler_sicher(nutzer_id)
        return self.aktivitäten.laufende_für_spieler_holen(nutzer_id)

    def laufende_aktivität_für_fabelwesen(self, fabelwesen_id: str) -> Aktivität | None:
        return self.aktivitäten.laufende_für_fabelwesen_holen(fabelwesen_id)

    def pflegeaktivität_starten(self, nutzer_id: str, aktion_id: str, fabelwesen_id: str | None = None) -> Aktivität:
        spieler = self.stelle_spieler_sicher(nutzer_id)
        if fabelwesen_id is None:
            aktiver_auftrag = self.pflegeauftrag_starten(nutzer_id)
            fabelwesen_id = aktiver_auftrag.fabelwesen_id
        fabelwesen = self.fabelwesen.holen(fabelwesen_id)
        if fabelwesen is None or fabelwesen.besitzer_id != nutzer_id:
            raise ValueError("Dieser Fabling wurde nicht gefunden.")

        aktion = self.inhalte.pflegeaktionen[aktion_id]
        if aktion.gesperrt:
            raise ValueError("Diese Aktion ist noch nicht freigeschaltet.")
        if aktion.benötigter_gegenstand and self._inventar_anzahl(spieler.inventar.get(aktion.benötigter_gegenstand)) <= 0:
            gegenstand = self.inhalte.gegenstände.get(aktion.benötigter_gegenstand)
            name = gegenstand.name if gegenstand else aktion.benötigter_gegenstand
            raise ValueError(f"Für diese Aktion brauchst du: {name}.")
        if aktion.braucht_spieler:
            aktive_aktivität = self.laufende_aktive_spieleraktivität(nutzer_id)
            if aktive_aktivität is not None:
                raise ValueError("Du betreust gerade schon einen Fabling aktiv.")

        laufend = self.aktivitäten.laufende_für_fabelwesen_holen(fabelwesen.id)
        if laufend is not None:
            return laufend
        if aktion.kosten:
            if spieler.geld < aktion.kosten:
                raise ValueError("Dafür hast du nicht genug Bundsiegel.")
            aktualisierter_spieler = spieler.model_copy(deep=True)
            aktualisierter_spieler.geld -= aktion.kosten
            self.spieler.speichern(aktualisierter_spieler)

        jetzt = datetime.now(timezone.utc)
        dauer_sekunden = self._aktionsdauer_für_spieler(nutzer_id, aktion_id, aktion.dauer_sekunden)
        aktivität = Aktivität(
            id=f"aktivität_{uuid4().hex[:12]}",
            spieler_id=nutzer_id,
            fabelwesen_id=fabelwesen.id,
            art=aktion.kategorie,
            aktion_id=aktion.aktion_id,
            name=aktion.name,
            kategorie=aktion.kategorie,
            intensität=aktion.intensität,
            braucht_spieler=aktion.braucht_spieler,
            abbrechbar=aktion.abbrechbar,
            effekte=aktion.effekte,
            wettbewerb_effekte=aktion.wettbewerb_effekte,
            sport_effekte=aktion.sport_effekte,
            abbruch_effekte=aktion.abbruch_effekte,
            folgeaktionen=aktion.folgeaktionen,
            gestartet_am=jetzt,
            endet_am=jetzt + timedelta(seconds=self._skalierte_dauer(dauer_sekunden)),
        )
        self.aktivitäten.speichern(aktivität)
        return aktivität

    def aktivität_abholen(self, nutzer_id: str, aktivität_id: str | None = None) -> AktivitätErgebnis:
        aktivität = self._laufende_aktivität_finden(nutzer_id, aktivität_id)
        jetzt = datetime.now(timezone.utc)
        if jetzt < aktivität.endet_am:
            raise ValueError("Diese Aktivität ist noch nicht fertig.")
        return self._aktivität_beenden(nutzer_id, aktivität, jetzt, anteil=1.0, status="abgeschlossen")

    def aktivität_abbrechen(self, nutzer_id: str, aktivität_id: str | None = None) -> AktivitätErgebnis:
        aktivität = self._laufende_aktivität_finden(nutzer_id, aktivität_id)
        if not aktivität.abbrechbar:
            raise ValueError("Diese Aktivität kann nicht abgebrochen werden.")
        jetzt = datetime.now(timezone.utc)
        gesamtdauer = max(1.0, (aktivität.endet_am - aktivität.gestartet_am).total_seconds())
        vergangen = max(0.0, (jetzt - aktivität.gestartet_am).total_seconds())
        anteil = max(0.0, min(1.0, vergangen / gesamtdauer))
        return self._aktivität_beenden(nutzer_id, aktivität, jetzt, anteil=anteil, status="abgebrochen")

    def _laufende_aktivität_finden(self, nutzer_id: str, aktivität_id: str | None) -> Aktivität:
        if aktivität_id is None:
            aktivität = self.laufende_aktivität(nutzer_id)
        else:
            aktivität = self.aktivitäten.holen(aktivität_id)
            if aktivität is not None and (aktivität.spieler_id != nutzer_id or aktivität.status != "läuft"):
                aktivität = None
        if aktivität is None:
            raise ValueError("Es läuft keine Aktivität.")
        return aktivität

    def _aktivität_beenden(
        self,
        nutzer_id: str,
        aktivität: Aktivität,
        jetzt: datetime,
        anteil: float,
        status: str,
    ) -> AktivitätErgebnis:
        spieler = self.stelle_spieler_sicher(nutzer_id)
        fabelwesen = self.fabelwesen.holen(aktivität.fabelwesen_id)
        if fabelwesen is None:
            raise ValueError(f"Fabelwesen nicht gefunden: {aktivität.fabelwesen_id}")

        aktualisiert, änderungen, wettbewerb_änderungen, sport_änderungen = self._effekte_anteilig_anwenden(
            fabelwesen,
            aktivität.effekte,
            aktivität.wettbewerb_effekte,
            aktivität.sport_effekte,
            anteil,
        )
        if status == "abgebrochen":
            abbruch_änderungen = self._werte_anteilig_anwenden(
                aktualisiert.zustand,
                self._abbruch_effekte_berechnen(fabelwesen, aktivität),
                1.0,
                standardwert=50,
            )
            änderungen.update(abbruch_änderungen)
            aktualisiert.zustand["verletzungsrisiko"] = self.pflege._risiko_aus_zustand(aktualisiert)
        self.fabelwesen.speichern(aktualisiert)

        beendete_aktivität = aktivität.model_copy(deep=True)
        beendete_aktivität.status = status
        beendete_aktivität.beendet_am = jetzt
        self.aktivitäten.speichern(beendete_aktivität)
        aktualisiert.status["zuletzt_versorgt_am"] = jetzt.isoformat()
        aktualisiert = self._aktivitätslog_schreiben(
            aktualisiert,
            beendete_aktivität,
            anteil,
            änderungen,
            wettbewerb_änderungen,
            sport_änderungen,
        )
        self.fabelwesen.speichern(aktualisiert)
        self._werkzeug_abnutzen(spieler, beendete_aktivität)
        self._tutorial_nach_aktivität_aktualisieren(spieler, beendete_aktivität, status)

        return AktivitätErgebnis(
            aktivität=beendete_aktivität,
            fabelwesen=aktualisiert,
            anteil=anteil,
            änderungen=änderungen,
            wettbewerb_änderungen=wettbewerb_änderungen,
            sport_änderungen=sport_änderungen,
            auftrag_abgeschlossen=False,
            geld_erhalten=0,
            ruf_erhalten={},
        )

    def _effekte_anteilig_anwenden(
        self,
        fabelwesen: Fabelwesen,
        effekte: dict[str, int],
        wettbewerb_effekte: dict[str, int],
        sport_effekte: dict[str, int],
        anteil: float,
    ) -> tuple[Fabelwesen, dict[str, int], dict[str, int], dict[str, int]]:
        daten = fabelwesen.model_copy(deep=True)
        if self._leckerli_buff_aktiv(daten):
            effekte = self._leckerli_buff_anwenden(effekte)
            wettbewerb_effekte = self._leckerli_buff_anwenden(wettbewerb_effekte)
            sport_effekte = self._leckerli_buff_anwenden(sport_effekte)
        änderungen = self._werte_anteilig_anwenden(daten.zustand, effekte, anteil, standardwert=0)
        wettbewerb_änderungen = self._werte_anteilig_anwenden(daten.wettbewerbswerte, wettbewerb_effekte, anteil, standardwert=0)
        sport_änderungen = self._werte_anteilig_anwenden(daten.sportwerte, sport_effekte, anteil, standardwert=0)
        daten.zustand["verletzungsrisiko"] = self.pflege._risiko_aus_zustand(daten)
        return daten, änderungen, wettbewerb_änderungen, sport_änderungen

    def _werte_anteilig_anwenden(
        self,
        werte: dict[str, int],
        effekte: dict[str, int],
        anteil: float,
        standardwert: int,
    ) -> dict[str, int]:
        änderungen: dict[str, int] = {}
        for schlüssel, wirkung in effekte.items():
            veränderung = int(round(wirkung * anteil))
            if veränderung == 0 and anteil > 0 and wirkung != 0:
                veränderung = 1 if wirkung > 0 else -1
            aktueller_wert = int(werte.get(schlüssel, standardwert))
            neuer_wert = begrenze_prozent(aktueller_wert + veränderung)
            tatsächliche_änderung = neuer_wert - aktueller_wert
            werte[schlüssel] = neuer_wert
            if tatsächliche_änderung:
                änderungen[schlüssel] = tatsächliche_änderung
        return änderungen

    def _abbruch_effekte_berechnen(self, fabelwesen: Fabelwesen, aktivität: Aktivität) -> dict[str, int]:
        effekte = dict(aktivität.abbruch_effekte)
        if not effekte and aktivität.kategorie in {"ruhe", "training", "spiel"}:
            effekte = {"vertrauen": -1, "sicherheit": -1}

        bindung = (int(fabelwesen.zustand.get("vertrauen", 50)) + int(fabelwesen.zustand.get("sicherheit", 50))) / 2
        faktor = 0.75 if bindung >= 70 else 1.25 if bindung < 35 else 1.0

        wiederholungen = self._jüngste_abbrüche_zählen(fabelwesen, aktivität.kategorie)
        faktor += min(1.0, wiederholungen * 0.25)

        skaliert: dict[str, int] = {}
        for schlüssel, wert in effekte.items():
            if wert < 0:
                skaliert[schlüssel] = min(-1, int(round(wert * faktor)))
            else:
                skaliert[schlüssel] = int(round(wert * faktor))
        return skaliert

    def _jüngste_abbrüche_zählen(self, fabelwesen: Fabelwesen, kategorie: str) -> int:
        log = fabelwesen.status.get("aktivitätslog", [])
        if not isinstance(log, list):
            return 0
        anzahl = 0
        for eintrag in reversed(log[-10:]):
            if not isinstance(eintrag, dict):
                continue
            if eintrag.get("kategorie") != kategorie:
                continue
            if eintrag.get("status") == "abgebrochen":
                anzahl += 1
                continue
            break
        return anzahl

    def _aktivitätslog_schreiben(
        self,
        fabelwesen: Fabelwesen,
        aktivität: Aktivität,
        anteil: float,
        änderungen: dict[str, int],
        wettbewerb_änderungen: dict[str, int],
        sport_änderungen: dict[str, int],
    ) -> Fabelwesen:
        daten = fabelwesen.model_copy(deep=True)
        log = daten.status.get("aktivitätslog", [])
        if not isinstance(log, list):
            log = []
        geplante_dauer = (aktivität.endet_am - aktivität.gestartet_am).total_seconds() * self.zeitfaktor
        if geplante_dauer <= 0:
            aktion = self.inhalte.pflegeaktionen.get(aktivität.aktion_id)
            geplante_dauer = self._aktionsdauer_für_spieler(
                aktivität.spieler_id,
                aktivität.aktion_id,
                aktion.dauer_sekunden if aktion is not None else 0,
            )
        spieldauer = round(geplante_dauer * anteil)
        log.append(
            {
                "aktivität_id": aktivität.id,
                "aktion_id": aktivität.aktion_id,
                "name": aktivität.name,
                "kategorie": aktivität.kategorie,
                "intensität": aktivität.intensität,
                "status": aktivität.status,
                "anteil": round(anteil, 3),
                "gestartet_am": aktivität.gestartet_am.isoformat(),
                "endet_am": aktivität.endet_am.isoformat(),
                "beendet_am": aktivität.beendet_am.isoformat() if aktivität.beendet_am else None,
                "spieldauer_sekunden": spieldauer,
                "änderungen": änderungen,
                "wettbewerb_änderungen": wettbewerb_änderungen,
                "sport_änderungen": sport_änderungen,
            }
        )
        daten.status["aktivitätslog"] = log
        return daten

    def _sättigung_aktualisieren(self, spieler: SpielerProfil, fabelwesen: Fabelwesen, jetzt: datetime) -> tuple[Fabelwesen, bool]:
        daten = fabelwesen.model_copy(deep=True)
        if "sättigung" not in daten.zustand:
            daten.zustand["sättigung"] = 80

        letzter_wert = daten.status.get("sättigung_geprüft_am")
        if letzter_wert is None:
            daten.status["sättigung_geprüft_am"] = jetzt.isoformat()
            self.fabelwesen.speichern(daten)
            return daten, False

        try:
            letzter_zeitpunkt = datetime.fromisoformat(str(letzter_wert))
        except ValueError:
            letzter_zeitpunkt = jetzt
        vergangen = max(0.0, (jetzt - letzter_zeitpunkt).total_seconds()) * self.zeitfaktor
        verbrauch = int(vergangen / 86400 * SÄTTIGUNG_VERBRAUCH_PRO_TAG)
        if verbrauch <= 0:
            return daten, False

        daten.zustand["sättigung"] = begrenze_prozent(int(daten.zustand.get("sättigung", 80)) - verbrauch)
        daten.status["sättigung_geprüft_am"] = jetzt.isoformat()

        spieler_geändert = False
        while int(daten.zustand.get("sättigung", 0)) < SÄTTIGUNG_GRUNDVERSORGUNG_ZIELWERT:
            futter_id = self._automatisches_futter_wählen(spieler, daten)
            if futter_id is None:
                break
            spieler.inventar[futter_id] = self._inventar_anzahl(spieler.inventar.get(futter_id)) - 1
            if self._inventar_anzahl(spieler.inventar[futter_id]) <= 0:
                del spieler.inventar[futter_id]
            daten.zustand["sättigung"] = min(
                SÄTTIGUNG_GRUNDVERSORGUNG_ZIELWERT,
                begrenze_prozent(int(daten.zustand.get("sättigung", 0)) + self._futter_nährwert(daten, futter_id)),
            )
            daten.status["zuletzt_gefressen_am"] = jetzt.isoformat()
            daten.status["letztes_futter"] = futter_id
            daten.status["letztes_futter_art"] = self._futter_art(daten, futter_id)
            spieler_geändert = True
            if int(daten.zustand.get("sättigung", 0)) >= SÄTTIGUNG_GRUNDVERSORGUNG_ZIELWERT:
                break

        self._hungereffekte_anwenden(daten)
        daten.zustand["verletzungsrisiko"] = self.pflege._risiko_aus_zustand(daten)
        self.fabelwesen.speichern(daten)
        return daten, spieler_geändert

    def _automatisches_futter_wählen(self, spieler: SpielerProfil, fabelwesen: Fabelwesen) -> str | None:
        kandidaten = self._verfügbare_standardfutter_ids(spieler)
        if not kandidaten:
            return None

        neutrale = [
            futter_id
            for futter_id in kandidaten
            if "neutral" in self.inhalte.gegenstände[futter_id].markierungen
        ]
        if neutrale:
            return sorted(neutrale)[0]
        return sorted(kandidaten)[0]

    def _verfügbare_standardfutter_ids(self, spieler: SpielerProfil) -> list[str]:
        return [
            gegenstand_id
            for gegenstand_id in self._verfügbare_futter_ids(spieler)
            if self._ist_standardfutter(gegenstand_id)
        ]

    def _verfügbare_futter_ids(self, spieler: SpielerProfil) -> list[str]:
        return [
            gegenstand_id
            for gegenstand_id, eintrag in spieler.inventar.items()
            if self._inventar_anzahl(eintrag) > 0
            and (gegenstand := self.inhalte.gegenstände.get(gegenstand_id)) is not None
            and gegenstand.kategorie == "futter"
        ]

    def verfügbare_leckerli_ids(self, nutzer_id: str) -> list[str]:
        spieler = self.stelle_spieler_sicher(nutzer_id)
        return [
            gegenstand_id
            for gegenstand_id in self._verfügbare_futter_ids(spieler)
            if self._ist_leckerli(gegenstand_id)
        ]

    def _ist_leckerli(self, gegenstand_id: str) -> bool:
        gegenstand = self.inhalte.gegenstände.get(gegenstand_id)
        return gegenstand is not None and "leckerli" in gegenstand.markierungen

    def _ist_standardfutter(self, gegenstand_id: str) -> bool:
        gegenstand = self.inhalte.gegenstände.get(gegenstand_id)
        return gegenstand is not None and (
            "standardfutter" in gegenstand.markierungen
            or ("normal" in gegenstand.markierungen and "leckerli" not in gegenstand.markierungen)
        )

    @staticmethod
    def _ist_lieblingsleckerli(fabelwesen: Fabelwesen, gegenstand_id: str) -> bool:
        return fabelwesen.persönlichkeit.get("lieblingsfutter") == gegenstand_id

    def _leckerli_buff_aktiv(self, fabelwesen: Fabelwesen) -> bool:
        wert = fabelwesen.status.get("leckerli_buff_bis")
        if wert is None:
            return False
        try:
            return datetime.fromisoformat(str(wert)) > datetime.now(timezone.utc)
        except ValueError:
            return False

    @staticmethod
    def _leckerli_buff_anwenden(effekte: dict[str, int]) -> dict[str, int]:
        gebufft: dict[str, int] = {}
        for schlüssel, wert in effekte.items():
            if wert <= 0:
                gebufft[schlüssel] = wert
                continue
            erhöhter_wert = int(round(wert * LECKERLI_BUFF_FAKTOR))
            gebufft[schlüssel] = max(wert + 1, erhöhter_wert)
        return gebufft

    def _futter_nährwert(self, fabelwesen: Fabelwesen, gegenstand_id: str) -> int:
        art = self._futter_art(fabelwesen, gegenstand_id)
        if art in {"bevorzugt", "neutral"}:
            return SÄTTIGUNG_NÄHRWERT_NORMAL
        return SÄTTIGUNG_NÄHRWERT_SONSTIG

    def _futter_art(self, fabelwesen: Fabelwesen, gegenstand_id: str) -> str:
        priorität = fabelwesen.status.get("futter_priorität", [])
        if isinstance(priorität, list) and priorität and str(priorität[0]) == gegenstand_id:
            return "bevorzugt"
        if fabelwesen.persönlichkeit.get("lieblingsfutter") == gegenstand_id:
            return "bevorzugt"
        gegenstand = self.inhalte.gegenstände.get(gegenstand_id)
        if gegenstand is not None and "neutral" in gegenstand.markierungen:
            return "neutral"
        return "sonstiges"

    @staticmethod
    def _hungereffekte_anwenden(fabelwesen: Fabelwesen) -> None:
        sättigung = int(fabelwesen.zustand.get("sättigung", 80))
        if sättigung < 30:
            fabelwesen.zustand["stimmung"] = begrenze_prozent(int(fabelwesen.zustand.get("stimmung", 50)) - 3)
            fabelwesen.zustand["stress"] = begrenze_prozent(int(fabelwesen.zustand.get("stress", 0)) + 3)
        if sättigung < 10:
            fabelwesen.zustand["gesundheit"] = begrenze_prozent(int(fabelwesen.zustand.get("gesundheit", 100)) - 2)

    def _inaktivität_aktualisieren(self, fabelwesen: Fabelwesen, jetzt: datetime) -> Fabelwesen:
        if self.aktivitäten.laufende_für_fabelwesen_holen(fabelwesen.id) is not None:
            return fabelwesen

        letzter_wert = fabelwesen.status.get("zuletzt_versorgt_am")
        if letzter_wert is None:
            aktualisiert = fabelwesen.model_copy(deep=True)
            aktualisiert.status["zuletzt_versorgt_am"] = jetzt.isoformat()
            self.fabelwesen.speichern(aktualisiert)
            return aktualisiert

        letzter_zeitpunkt = datetime.fromisoformat(str(letzter_wert))
        vergangen = max(0.0, (jetzt - letzter_zeitpunkt).total_seconds()) * self.zeitfaktor
        if vergangen < INAKTIVITÄT_START_SEKUNDEN:
            return fabelwesen

        wirkdauer = min(vergangen - INAKTIVITÄT_START_SEKUNDEN, INAKTIVITÄT_MAX_WIRKUNG_SEKUNDEN)
        if wirkdauer <= 0:
            return fabelwesen

        anteil = wirkdauer / INAKTIVITÄT_MAX_WIRKUNG_SEKUNDEN
        effekte = self._selbstbeschäftigung_effekte(anteil, vergangen)
        gestartet_am = jetzt - timedelta(seconds=self._skalierte_dauer(wirkdauer))
        endet_am = jetzt
        aktivität = Aktivität(
            id=f"aktivität_{uuid4().hex[:12]}",
            spieler_id=fabelwesen.besitzer_id,
            fabelwesen_id=fabelwesen.id,
            art="selbstbeschäftigung",
            aktion_id="selbstbeschäftigung",
            name="Selbstbeschäftigung",
            kategorie="selbstbeschäftigung",
            intensität="passiv",
            braucht_spieler=False,
            abbrechbar=False,
            effekte=effekte,
            folgeaktionen=["kurzer_blick", "sanfte_fellpflege", "kontrollierte_ruhe"],
            gestartet_am=gestartet_am,
            endet_am=endet_am,
        )
        self.aktivitäten.speichern(aktivität)
        return fabelwesen

    def _selbstbeschäftigung_effekte(self, anteil: float, vergangen: float) -> dict[str, int]:
        effekte = {
            "energie": int(round(8 * anteil)),
            "stress": int(round(-4 * anteil)),
            "stimmung": int(round(3 * anteil)),
            "fellpflege": int(round(2 * anteil)),
        }
        if vergangen >= VERWAHRLOSUNG_START_SEKUNDEN:
            stunden_nach_start = (vergangen - VERWAHRLOSUNG_START_SEKUNDEN) / 3600
            effekte["vertrauen"] = -min(12, max(1, int(stunden_nach_start // 12) + 1))
        return {schlüssel: wert for schlüssel, wert in effekte.items() if wert != 0}

    def _skalierte_dauer(self, sekunden: float) -> float:
        if sekunden <= 0:
            return 0.0
        return max(1.0, sekunden / self.zeitfaktor)

    def _aktionsdauer_für_spieler(self, nutzer_id: str, aktion_id: str, standard: int) -> int:
        aktiver_auftrag = self.aufträge.aktiven_holen(nutzer_id)
        if aktiver_auftrag is None:
            return standard
        return TUTORIAL_DAUER_OVERRIDES_SEKUNDEN.get((aktiver_auftrag.auftrag_id, aktion_id), standard)

    def _inventar_anzahl(self, eintrag: object) -> int:
        if eintrag is None:
            return 0
        if isinstance(eintrag, dict):
            return int(eintrag.get("anzahl", 0))
        return int(eintrag)

    def _inventar_eintrag_nach_kauf(self, bisher: object, gegenstand_id: str, anzahl: int) -> object:
        gegenstand = self.inhalte.gegenstände.get(gegenstand_id)
        haltbarkeit = 20 if gegenstand is not None and "haltbarkeit_20" in gegenstand.markierungen else None
        bisherige_anzahl = self._inventar_anzahl(bisher)
        if haltbarkeit is None:
            return bisherige_anzahl + anzahl
        bestehende_haltbarkeit = []
        if isinstance(bisher, dict) and isinstance(bisher.get("haltbarkeit"), list):
            bestehende_haltbarkeit = [int(wert) for wert in bisher["haltbarkeit"]]
        bestehende_haltbarkeit.extend([haltbarkeit] * anzahl)
        return {"anzahl": bisherige_anzahl + anzahl, "haltbarkeit": bestehende_haltbarkeit}

    def _werkzeug_abnutzen(self, spieler: SpielerProfil, aktivität: Aktivität) -> None:
        if aktivität.status != "abgeschlossen":
            return
        aktion = self.inhalte.pflegeaktionen.get(aktivität.aktion_id)
        if aktion is None or not aktion.benötigter_gegenstand:
            return
        aktualisiert = spieler.model_copy(deep=True)
        eintrag = aktualisiert.inventar.get(aktion.benötigter_gegenstand)
        if not isinstance(eintrag, dict):
            return
        haltbarkeit = [int(wert) for wert in eintrag.get("haltbarkeit", [])]
        if not haltbarkeit:
            return
        haltbarkeit[0] -= 1
        haltbarkeit = [wert for wert in haltbarkeit if wert > 0]
        if haltbarkeit:
            aktualisiert.inventar[aktion.benötigter_gegenstand] = {"anzahl": len(haltbarkeit), "haltbarkeit": haltbarkeit}
        else:
            del aktualisiert.inventar[aktion.benötigter_gegenstand]
        self.spieler.speichern(aktualisiert)
