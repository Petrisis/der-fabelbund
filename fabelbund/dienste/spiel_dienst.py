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
    auftrag_abgeschlossen: bool
    geld_erhalten: int
    ruf_erhalten: dict[str, int]


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
    ) -> None:
        self.inhalte = inhalte
        self.spieler = spieler
        self.fabelwesen = fabelwesen
        self.aufträge = aufträge
        self.aktivitäten = aktivitäten
        self.fabrik = fabrik
        self.pflege = pflege
        self.auftrag_dienst = auftrag_dienst

    def stelle_spieler_sicher(self, nutzer_id: str) -> SpielerProfil:
        spieler = self.spieler.holen(nutzer_id)
        if spieler is None:
            spieler = SpielerProfil(nutzer_id=nutzer_id)
            self.spieler.speichern(spieler)
        return spieler

    def sammlung(self, nutzer_id: str) -> list[Fabelwesen]:
        self.stelle_spieler_sicher(nutzer_id)
        return self.fabelwesen.für_besitzer_auflisten(nutzer_id)

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

    def pflegeauftrag_starten(self, nutzer_id: str) -> AktiverAuftrag:
        self.stelle_spieler_sicher(nutzer_id)
        aktiver_auftrag = self.aufträge.aktiven_holen(nutzer_id)
        if aktiver_auftrag is not None:
            return aktiver_auftrag
        fabelwesen_liste = self.fabelwesen.für_besitzer_auflisten(nutzer_id)
        if not fabelwesen_liste:
            raise ValueError("Du hast noch keinen Fabling. Das Tutorial wird dir den ersten Fabling anvertrauen.")
        fabelwesen = fabelwesen_liste[0]
        auftrag = self.inhalte.aufträge["pflege_einfach_001"]
        aktiver_auftrag = self.auftrag_dienst.erstelle_aktiven_auftrag(nutzer_id, auftrag, fabelwesen.id)
        self.aufträge.speichern(aktiver_auftrag)
        return aktiver_auftrag

    def aktiver_auftrag(self, nutzer_id: str) -> AktiverAuftrag | None:
        return self.aufträge.aktiven_holen(nutzer_id)

    def pflege_anwenden(self, nutzer_id: str, aktion_id: str) -> PflegeErgebnis:
        spieler = self.stelle_spieler_sicher(nutzer_id)
        aktiver_auftrag = self.pflegeauftrag_starten(nutzer_id)
        fabelwesen = self.fabelwesen.holen(aktiver_auftrag.fabelwesen_id)
        if fabelwesen is None:
            raise ValueError(f"Auftrags-Fabelwesen nicht gefunden: {aktiver_auftrag.fabelwesen_id}")

        aktion = self.inhalte.pflegeaktionen[aktion_id]
        aktualisiert = self.pflege.anwenden(fabelwesen, aktion)
        self.fabelwesen.speichern(aktualisiert)

        auftrag = self.inhalte.aufträge[aktiver_auftrag.auftrag_id]
        if self.auftrag_dienst.ziele_erfüllt(auftrag, aktualisiert):
            geld_vorher = spieler.geld
            ruf_vorher = dict(spieler.ruf)
            spieler, abgeschlossen = self.auftrag_dienst.abschließen(spieler, aktiver_auftrag, auftrag)
            self.spieler.speichern(spieler)
            self.aufträge.speichern(abgeschlossen)
            return PflegeErgebnis(
                fabelwesen=aktualisiert,
                auftrag_abgeschlossen=True,
                geld_erhalten=spieler.geld - geld_vorher,
                ruf_erhalten={
                    schlüssel: spieler.ruf.get(schlüssel, 0) - ruf_vorher.get(schlüssel, 0)
                    for schlüssel in spieler.ruf
                    if spieler.ruf.get(schlüssel, 0) != ruf_vorher.get(schlüssel, 0)
                },
            )
        return PflegeErgebnis(fabelwesen=aktualisiert, auftrag_abgeschlossen=False, geld_erhalten=0, ruf_erhalten={})

    def laufende_aktivität(self, nutzer_id: str) -> Aktivität | None:
        self.stelle_spieler_sicher(nutzer_id)
        aktivitäten = self.aktivitäten.laufende_für_spieler_holen(nutzer_id)
        if not aktivitäten:
            return None
        return aktivitäten[0]

    def laufende_aktivität_für_fabelwesen(self, fabelwesen_id: str) -> Aktivität | None:
        return self.aktivitäten.laufende_für_fabelwesen_holen(fabelwesen_id)

    def pflegeaktivität_starten(self, nutzer_id: str, aktion_id: str) -> Aktivität:
        self.stelle_spieler_sicher(nutzer_id)
        aktiver_auftrag = self.pflegeauftrag_starten(nutzer_id)
        fabelwesen = self.fabelwesen.holen(aktiver_auftrag.fabelwesen_id)
        if fabelwesen is None:
            raise ValueError(f"Auftrags-Fabelwesen nicht gefunden: {aktiver_auftrag.fabelwesen_id}")

        laufend = self.aktivitäten.laufende_für_fabelwesen_holen(fabelwesen.id)
        if laufend is not None:
            return laufend

        aktion = self.inhalte.pflegeaktionen[aktion_id]
        jetzt = datetime.now(timezone.utc)
        aktivität = Aktivität(
            id=f"aktivität_{uuid4().hex[:12]}",
            spieler_id=nutzer_id,
            fabelwesen_id=fabelwesen.id,
            art="pflege",
            aktion_id=aktion.aktion_id,
            name=aktion.name,
            braucht_spieler=aktion.braucht_spieler,
            effekte=aktion.effekte,
            gestartet_am=jetzt,
            endet_am=jetzt + timedelta(seconds=aktion.dauer_sekunden),
        )
        self.aktivitäten.speichern(aktivität)
        return aktivität

    def aktivität_abholen(self, nutzer_id: str) -> AktivitätErgebnis:
        aktivität = self.laufende_aktivität(nutzer_id)
        if aktivität is None:
            raise ValueError("Es läuft keine Aktivität.")
        jetzt = datetime.now(timezone.utc)
        if jetzt < aktivität.endet_am:
            raise ValueError("Diese Aktivität ist noch nicht fertig.")
        return self._aktivität_beenden(nutzer_id, aktivität, jetzt, anteil=1.0, status="abgeschlossen")

    def aktivität_abbrechen(self, nutzer_id: str) -> AktivitätErgebnis:
        aktivität = self.laufende_aktivität(nutzer_id)
        if aktivität is None:
            raise ValueError("Es läuft keine Aktivität.")
        jetzt = datetime.now(timezone.utc)
        gesamtdauer = max(1.0, (aktivität.endet_am - aktivität.gestartet_am).total_seconds())
        vergangen = max(0.0, (jetzt - aktivität.gestartet_am).total_seconds())
        anteil = max(0.0, min(1.0, vergangen / gesamtdauer))
        return self._aktivität_beenden(nutzer_id, aktivität, jetzt, anteil=anteil, status="abgebrochen")

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

        aktualisiert, änderungen = self._effekte_anteilig_anwenden(fabelwesen, aktivität.effekte, anteil)
        self.fabelwesen.speichern(aktualisiert)

        beendete_aktivität = aktivität.model_copy(deep=True)
        beendete_aktivität.status = status
        beendete_aktivität.beendet_am = jetzt
        self.aktivitäten.speichern(beendete_aktivität)

        aktiver_auftrag = self.aufträge.aktiven_holen(nutzer_id)
        if aktiver_auftrag is not None:
            auftrag = self.inhalte.aufträge[aktiver_auftrag.auftrag_id]
            if self.auftrag_dienst.ziele_erfüllt(auftrag, aktualisiert):
                geld_vorher = spieler.geld
                ruf_vorher = dict(spieler.ruf)
                spieler, abgeschlossen = self.auftrag_dienst.abschließen(spieler, aktiver_auftrag, auftrag)
                self.spieler.speichern(spieler)
                self.aufträge.speichern(abgeschlossen)
                return AktivitätErgebnis(
                    aktivität=beendete_aktivität,
                    fabelwesen=aktualisiert,
                    anteil=anteil,
                    änderungen=änderungen,
                    auftrag_abgeschlossen=True,
                    geld_erhalten=spieler.geld - geld_vorher,
                    ruf_erhalten={
                        schlüssel: spieler.ruf.get(schlüssel, 0) - ruf_vorher.get(schlüssel, 0)
                        for schlüssel in spieler.ruf
                        if spieler.ruf.get(schlüssel, 0) != ruf_vorher.get(schlüssel, 0)
                    },
                )

        return AktivitätErgebnis(
            aktivität=beendete_aktivität,
            fabelwesen=aktualisiert,
            anteil=anteil,
            änderungen=änderungen,
            auftrag_abgeschlossen=False,
            geld_erhalten=0,
            ruf_erhalten={},
        )

    def _effekte_anteilig_anwenden(
        self,
        fabelwesen: Fabelwesen,
        effekte: dict[str, int],
        anteil: float,
    ) -> tuple[Fabelwesen, dict[str, int]]:
        daten = fabelwesen.model_copy(deep=True)
        änderungen: dict[str, int] = {}
        for schlüssel, wirkung in effekte.items():
            veränderung = int(round(wirkung * anteil))
            if veränderung == 0 and anteil > 0 and wirkung != 0:
                veränderung = 1 if wirkung > 0 else -1
            aktueller_wert = int(daten.zustand.get(schlüssel, 0))
            neuer_wert = begrenze_prozent(aktueller_wert + veränderung)
            tatsächliche_änderung = neuer_wert - aktueller_wert
            daten.zustand[schlüssel] = neuer_wert
            if tatsächliche_änderung:
                änderungen[schlüssel] = tatsächliche_änderung
        daten.zustand["verletzungsrisiko"] = self.pflege._risiko_aus_zustand(daten)
        return daten, änderungen
