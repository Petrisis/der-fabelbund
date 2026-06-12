from __future__ import annotations

from dataclasses import dataclass

from fabelbund.datenbank.speicher.auftrag_speicher import AuftragSpeicher
from fabelbund.datenbank.speicher.fabelwesen_speicher import FabelwesenSpeicher
from fabelbund.datenbank.speicher.spieler_speicher import SpielerSpeicher
from fabelbund.dienste.auftrag_dienst import AuftragDienst
from fabelbund.dienste.fabelwesen_fabrik import FabelwesenFabrik
from fabelbund.dienste.pflege_dienst import PflegeDienst
from fabelbund.modelle.inhalte import InhaltsKatalog
from fabelbund.modelle.laufzeit import AktiverAuftrag, Fabelwesen, SpielerProfil


@dataclass
class PflegeErgebnis:
    fabelwesen: Fabelwesen
    auftrag_abgeschlossen: bool
    geld_erhalten: int
    ruf_erhalten: dict[str, int]


class SpielDienst:
    def __init__(
        self,
        inhalte: InhaltsKatalog,
        spieler: SpielerSpeicher,
        fabelwesen: FabelwesenSpeicher,
        aufträge: AuftragSpeicher,
        fabrik: FabelwesenFabrik,
        pflege: PflegeDienst,
        auftrag_dienst: AuftragDienst,
    ) -> None:
        self.inhalte = inhalte
        self.spieler = spieler
        self.fabelwesen = fabelwesen
        self.aufträge = aufträge
        self.fabrik = fabrik
        self.pflege = pflege
        self.auftrag_dienst = auftrag_dienst

    def stelle_spieler_sicher(self, nutzer_id: str) -> SpielerProfil:
        spieler = self.spieler.holen(nutzer_id)
        if spieler is None:
            spieler = SpielerProfil(nutzer_id=nutzer_id)
            self.spieler.speichern(spieler)
        if not self.fabelwesen.für_besitzer_auflisten(nutzer_id):
            starter_art = self.inhalte.arten.get("gluthase") or next(iter(self.inhalte.arten.values()))
            starter = self.fabrik.erzeuge_starter(nutzer_id, starter_art)
            self.fabelwesen.speichern(starter)
        return spieler

    def sammlung(self, nutzer_id: str) -> list[Fabelwesen]:
        self.stelle_spieler_sicher(nutzer_id)
        return self.fabelwesen.für_besitzer_auflisten(nutzer_id)

    def pflegeauftrag_starten(self, nutzer_id: str) -> AktiverAuftrag:
        self.stelle_spieler_sicher(nutzer_id)
        aktiver_auftrag = self.aufträge.aktiven_holen(nutzer_id)
        if aktiver_auftrag is not None:
            return aktiver_auftrag
        fabelwesen = self.fabelwesen.für_besitzer_auflisten(nutzer_id)[0]
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
