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
        if aktion.braucht_spieler:
            aktive_aktivität = self.laufende_aktive_spieleraktivität(nutzer_id)
            if aktive_aktivität is not None:
                raise ValueError("Du betreust gerade schon einen Fabling aktiv.")

        laufend = self.aktivitäten.laufende_für_fabelwesen_holen(fabelwesen.id)
        if laufend is not None:
            return laufend

        jetzt = datetime.now(timezone.utc)
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
            gestartet_am=jetzt,
            endet_am=jetzt + timedelta(seconds=self._skalierte_dauer(aktion.dauer_sekunden)),
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
                    wettbewerb_änderungen=wettbewerb_änderungen,
                    sport_änderungen=sport_änderungen,
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
