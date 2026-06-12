from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fabelbund.datenbank.datenbank import Datenbank
from fabelbund.datenbank.speicher.auftrag_speicher import AuftragSpeicher
from fabelbund.datenbank.speicher.fabelwesen_speicher import FabelwesenSpeicher
from fabelbund.datenbank.speicher.spieler_speicher import SpielerSpeicher
from fabelbund.dienste.auftrag_dienst import AuftragDienst
from fabelbund.dienste.fabelwesen_fabrik import FabelwesenFabrik
from fabelbund.dienste.pflege_dienst import PflegeDienst
from fabelbund.dienste.spiel_dienst import SpielDienst
from fabelbund.dienste.yaml_lader import YamlLader


@dataclass(frozen=True)
class Anwendungskontext:
    spiel: SpielDienst

    @classmethod
    def aus_pfaden(cls, daten_ordner: Path, datenbank_pfad: Path) -> "Anwendungskontext":
        inhalte = YamlLader(daten_ordner).lade_alle()
        datenbank = Datenbank(datenbank_pfad)
        datenbank.migrieren()

        spieler_speicher = SpielerSpeicher(datenbank)
        fabelwesen_speicher = FabelwesenSpeicher(datenbank)
        auftrag_speicher = AuftragSpeicher(datenbank)

        spiel = SpielDienst(
            inhalte=inhalte,
            spieler=spieler_speicher,
            fabelwesen=fabelwesen_speicher,
            auftraege=auftrag_speicher,
            fabrik=FabelwesenFabrik(),
            pflege=PflegeDienst(),
            auftrag_dienst=AuftragDienst(),
        )
        return cls(spiel=spiel)
