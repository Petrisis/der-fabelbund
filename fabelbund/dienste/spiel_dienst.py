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
INAKTIVITÄT_START_SEKUNDEN = 60 * 60
INAKTIVITÄT_MAX_WIRKUNG_SEKUNDEN = 8 * 60 * 60
VERWAHRLOSUNG_START_SEKUNDEN = 24 * 60 * 60
TUTORIAL_DAUER_OVERRIDES_SEKUNDEN = {
    ("tutorial_pflege_002", "sanfte_fellpflege"): 120,
    ("tutorial_aktiv_passiv_003", "kontrollierte_ruhe"): 180,
    ("tutorial_aktiv_passiv_003", "gemeinsames_spiel"): 180,
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
        self.stelle_spieler_sicher(nutzer_id)
        fabelwesen = self.fabelwesen.für_besitzer_auflisten(nutzer_id)
        jetzt = datetime.now(timezone.utc)
        return [self._inaktivität_aktualisieren(fabling, jetzt) for fabling in fabelwesen]

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
        fabelwesen = self.fabelwesen.holen(fabelwesen_id)
        if fabelwesen is None or fabelwesen.besitzer_id != nutzer_id:
            raise ValueError("Dieser Fabling wurde nicht gefunden.")
        if gegenstand_id is not None:
            gegenstand = self.inhalte.gegenstände.get(gegenstand_id)
            if gegenstand is None or gegenstand.kategorie != "futter":
                raise ValueError("Dieses Futter ist nicht verfügbar.")

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
            raise ValueError("Dafür hast du nicht genug Geld.")
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
            raise ValueError("Dafür hast du nicht genug Geld.")

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
        futter_priorität = aktualisiertes_fabling.status.get("futter_priorität", [])
        if not isinstance(futter_priorität, list):
            futter_priorität = []
        lieblingsfutter = (
            (futter_priorität and str(futter_priorität[0]) == gegenstand_id)
            or aktualisiertes_fabling.persönlichkeit.get("lieblingsfutter") == gegenstand_id
        )
        if lieblingsfutter:
            effekte["stimmung"] = effekte.get("stimmung", 0) + 2
            effekte["vertrauen"] = effekte.get("vertrauen", 0) + 1

        änderungen = self._werte_anteilig_anwenden(aktualisiertes_fabling.zustand, effekte, 1.0, standardwert=0)
        aktualisiertes_fabling.zustand["verletzungsrisiko"] = self.pflege._risiko_aus_zustand(aktualisiertes_fabling)
        aktualisiertes_fabling.status["zuletzt_gefüttert_am"] = datetime.now(timezone.utc).isoformat()
        aktualisiertes_fabling.status["letztes_futter"] = gegenstand_id

        self.spieler.speichern(aktualisierter_spieler)
        self.fabelwesen.speichern(aktualisiertes_fabling)
        self._tutorial_nach_fütterung_aktualisieren(nutzer_id)
        return FütterungErgebnis(
            fabelwesen=aktualisiertes_fabling,
            gegenstand_id=gegenstand_id,
            name=gegenstand.name,
            lieblingsfutter=lieblingsfutter,
            änderungen=änderungen,
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
            return "Mira nickt zufrieden: Eine eingehaltene Ruhephase ist kein Stillstand, sondern verlässliche Betreuung."
        if auftrag.auftrag_id == "tutorial_pflege_002":
            return "Brann notiert die Rückgabe knapp: Sauberer Zustand, Auftrag erfüllt."
        return "Der Auftrag wurde sauber abgegeben."

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
        if auftrag.ziele.get("abgeschlossene_aktion") == "kontrollierte_ruhe":
            return f"{fabelwesen.spitzname} sollte zuerst eine vollständige Ruhephase abschließen."
        if auftrag.ziele.get("gefüttert"):
            return f"{fabelwesen.spitzname} wurde noch nicht passend versorgt."
        if auftrag.ziele.get("futter_priorität"):
            return f"{fabelwesen.spitzname} braucht erst die passende Futterpräferenz."
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
        self.stelle_spieler_sicher(nutzer_id)
        if fabelwesen_id is None:
            aktiver_auftrag = self.pflegeauftrag_starten(nutzer_id)
            fabelwesen_id = aktiver_auftrag.fabelwesen_id
        fabelwesen = self.fabelwesen.holen(fabelwesen_id)
        if fabelwesen is None or fabelwesen.besitzer_id != nutzer_id:
            raise ValueError("Dieser Fabling wurde nicht gefunden.")

        aktion = self.inhalte.pflegeaktionen[aktion_id]
        if aktion.gesperrt:
            raise ValueError("Diese Aktion ist noch nicht freigeschaltet.")
        if aktion.benötigter_gegenstand and self._inventar_anzahl(self.stelle_spieler_sicher(nutzer_id).inventar.get(aktion.benötigter_gegenstand)) <= 0:
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
