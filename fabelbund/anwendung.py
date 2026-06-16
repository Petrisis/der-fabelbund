from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fabelbund.datenbank.datenbank import Datenbank
from fabelbund.datenbank.speicher.aktivität_speicher import AktivitätSpeicher
from fabelbund.datenbank.speicher.auftrag_speicher import AuftragSpeicher
from fabelbund.datenbank.speicher.fabelwesen_speicher import FabelwesenSpeicher
from fabelbund.datenbank.speicher.server_speicher import ServerSpeicher
from fabelbund.datenbank.speicher.spieler_speicher import SpielerSpeicher
from fabelbund.datenbank.speicher.wettbewerb_speicher import WettbewerbSpeicher
from fabelbund.dienste.auftrag_dienst import AuftragDienst
from fabelbund.dienste.fabelwesen_fabrik import FabelwesenFabrik
from fabelbund.dienste.pflege_dienst import PflegeDienst
from fabelbund.dienste.spiel_dienst import SpielDienst
from fabelbund.dienste.yaml_lader import YamlLader


@dataclass(frozen=True)
class Anwendungskontext:
    spiel: SpielDienst
    server: ServerSpeicher
    wettbewerbe: WettbewerbSpeicher

    @classmethod
    def aus_pfaden(cls, daten_ordner: Path, datenbank_pfad: Path, zeitfaktor: float = 1.0) -> "Anwendungskontext":
        inhalte = YamlLader(daten_ordner).lade_alle()
        datenbank = Datenbank(datenbank_pfad)
        datenbank.migrieren()

        spieler_speicher = SpielerSpeicher(datenbank)
        fabelwesen_speicher = FabelwesenSpeicher(datenbank)
        auftrag_speicher = AuftragSpeicher(datenbank)
        aktivität_speicher = AktivitätSpeicher(datenbank)
        server_speicher = ServerSpeicher(datenbank)
        wettbewerb_speicher = WettbewerbSpeicher(datenbank)

        spiel = SpielDienst(
            inhalte=inhalte,
            spieler=spieler_speicher,
            fabelwesen=fabelwesen_speicher,
            aufträge=auftrag_speicher,
            aktivitäten=aktivität_speicher,
            fabrik=FabelwesenFabrik(),
            pflege=PflegeDienst(),
            auftrag_dienst=AuftragDienst(),
            zeitfaktor=zeitfaktor,
        )
        return cls(spiel=spiel, server=server_speicher, wettbewerbe=wettbewerb_speicher)
