from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fabelbund.datenbank.datenbank import Datenbank
from fabelbund.datenbank.speicher.auftrag_speicher import AuftragSpeicher
from fabelbund.datenbank.speicher.fabelwesen_speicher import FabelwesenSpeicher
from fabelbund.datenbank.speicher.spieler_speicher import SpielerSpeicher
from fabelbund.dienste.auftrag_dienst import AuftragDienst
from fabelbund.dienste.fabelwesen_fabrik import FabelwesenFabrik
from fabelbund.dienste.pflege_dienst import PflegeDienst
from fabelbund.dienste.spiel_dienst import SpielDienst
from fabelbund.modelle.inhalte import ArtDefinition, AuftragDefinition, InhaltsKatalog, PflegeaktionDefinition


def inhalts_katalog() -> InhaltsKatalog:
    art = ArtDefinition.model_validate(
        {
            "art_id": "gluthase",
            "name": "Gluthase",
            "grundseltenheit": "gewöhnlich",
            "element": "glut",
            "lebensraum": "warmfeld",
            "grundwerte": {
                "schönheit": 34,
                "eleganz": 38,
                "charme": 52,
                "intelligenz": 36,
                "ausdruck": 45,
                "disziplin": 28,
                "harmonie": 42,
                "stärke": 32,
                "beweglichkeit": 56,
                "ausdauer": 40,
                "technik": 35,
                "deckung": 22,
                "kontrolle": 30,
                "kampfgeist": 48,
            },
            "genpools": {"farben": {"gewöhnlich": ["kohle"]}, "muster": {"gewöhnlich": ["einfarbig"]}},
            "persönlichkeits_gewichte": {"neugierig": 1},
        }
    )
    aktion = PflegeaktionDefinition.model_validate(
        {
            "aktion_id": "sanfte_fellpflege",
            "name": "Sanfte Fellpflege",
            "effekte": {"fellpflege": 12, "stimmung": 4, "stress": -3, "energie": -2},
        }
    )
    auftrag = AuftragDefinition.model_validate(
        {
            "auftrag_id": "pflege_einfach_001",
            "name": "Grundpflegeauftrag",
            "art": "pflege",
            "dauer_tage": 3,
            "ziele": {
                "gesundheit_mindestens": 80,
                "stimmung_mindestens": 55,
                "stress_höchstens": 25,
                "fellpflege_mindestens": 55,
            },
            "belohnungen": {"geld": 300, "ruf": {"pflege": 12, "zuverlässigkeit": 5}},
        }
    )
    return InhaltsKatalog(
        arten={"gluthase": art},
        pflegeaktionen={"sanfte_fellpflege": aktion},
        aufträge={"pflege_einfach_001": auftrag},
    )


class SpielDienstTests(unittest.TestCase):
    def baue_spiel(self, datenbank_pfad: Path) -> SpielDienst:
        datenbank = Datenbank(datenbank_pfad)
        datenbank.migrieren()
        return SpielDienst(
            inhalte=inhalts_katalog(),
            spieler=SpielerSpeicher(datenbank),
            fabelwesen=FabelwesenSpeicher(datenbank),
            aufträge=AuftragSpeicher(datenbank),
            fabrik=FabelwesenFabrik(),
            pflege=PflegeDienst(),
            auftrag_dienst=AuftragDienst(),
        )

    def test_profil_erzeugung_erstellt_starter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            spieler = spiel.stelle_spieler_sicher("123")
            sammlung = spiel.sammlung("123")

        self.assertEqual(spieler.geld, 500)
        self.assertEqual(len(sammlung), 1)
        self.assertEqual(sammlung[0].art_id, "gluthase")

    def test_pflegeaktion_kann_einfachen_auftrag_abschließen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            spiel.pflegeauftrag_starten("123")
            ergebnis = spiel.pflege_anwenden("123", "sanfte_fellpflege")
            spieler = spiel.spieler.holen("123")

        self.assertTrue(ergebnis.auftrag_abgeschlossen)
        self.assertEqual(ergebnis.geld_erhalten, 300)
        self.assertIsNotNone(spieler)
        assert spieler is not None
        self.assertEqual(spieler.geld, 800)
        self.assertEqual(spieler.ruf["pflege"], 12)
        self.assertEqual(spieler.ruf["zuverlässigkeit"], 5)


if __name__ == "__main__":
    unittest.main()
