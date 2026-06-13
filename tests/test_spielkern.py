from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fabelbund.datenbank.datenbank import Datenbank
from fabelbund.datenbank.speicher.aktivität_speicher import AktivitätSpeicher
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
            aktivitäten=AktivitätSpeicher(datenbank),
            fabrik=FabelwesenFabrik(),
            pflege=PflegeDienst(),
            auftrag_dienst=AuftragDienst(),
        )

    def erzeuge_starter(self, spiel: SpielDienst, nutzer_id: str = "123") -> None:
        art = spiel.inhalte.arten["gluthase"]
        starter = spiel.fabrik.erzeuge_starter(nutzer_id, art)
        spiel.fabelwesen.speichern(starter)

    def test_profil_erzeugung_startet_ohne_fabling(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            spieler = spiel.stelle_spieler_sicher("123")
            sammlung = spiel.sammlung("123")
            kapazität = spiel.stall_kapazität("123")
            hat_freien_stall = spiel.hat_freien_stall("123")

        self.assertEqual(spieler.geld, 500)
        self.assertEqual(spieler.freigeschaltete_ställe, 1)
        self.assertEqual(spieler.stalltypen, {"neutral": 1})
        self.assertEqual(len(sammlung), 0)
        self.assertEqual(kapazität, 1)
        self.assertTrue(hat_freien_stall)

    def test_pflegeaktion_kann_einfachen_auftrag_abschließen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            self.erzeuge_starter(spiel)
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

    def test_pflegeauftrag_braucht_fabling(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            with self.assertRaisesRegex(ValueError, "noch keinen Fabling"):
                spiel.pflegeauftrag_starten("123")

    def test_stallpriorität_wird_am_fabling_gespeichert(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            self.erzeuge_starter(spiel)
            fabling = spiel.sammlung("123")[0]

            aktualisiert = spiel.stallpriorität_setzen("123", fabling.id, "neutral")
            belegung = spiel.stallbelegung("123")

        self.assertEqual(aktualisiert.status["stall_priorität"], "neutral")
        self.assertEqual(belegung[0].stalltyp, "neutral")
        self.assertEqual(belegung[0].belegt, 1)

    def test_inaktivität_erzeugt_abholbare_selbstbeschäftigung(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            self.erzeuge_starter(spiel)
            fabling = spiel.sammlung("123")[0].model_copy(deep=True)
            fabling.status["zuletzt_versorgt_am"] = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()
            spiel.fabelwesen.speichern(fabling)

            spiel.sammlung("123")
            aktivität = spiel.laufende_aktivität("123")
            ergebnis = spiel.aktivität_abholen("123")

        self.assertIsNotNone(aktivität)
        assert aktivität is not None
        self.assertFalse(aktivität.abbrechbar)
        self.assertEqual(aktivität.aktion_id, "selbstbeschäftigung")
        self.assertGreater(ergebnis.änderungen.get("energie", 0), 0)
        self.assertNotIn("vertrauen", ergebnis.änderungen)

    def test_verwahrlosung_senkt_vertrauen_nach_einem_tag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            self.erzeuge_starter(spiel)
            fabling = spiel.sammlung("123")[0].model_copy(deep=True)
            vertrauen_vorher = int(fabling.zustand["vertrauen"])
            fabling.status["zuletzt_versorgt_am"] = (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat()
            spiel.fabelwesen.speichern(fabling)

            spiel.sammlung("123")
            ergebnis = spiel.aktivität_abholen("123")

        self.assertLess(ergebnis.fabelwesen.zustand["vertrauen"], vertrauen_vorher)

    def test_pflegeaktivität_wird_nach_ablauf_abgeholt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            self.erzeuge_starter(spiel)
            aktivität = spiel.pflegeaktivität_starten("123", "sanfte_fellpflege")

            mit_vergangenem_ende = aktivität.model_copy(update={"endet_am": datetime.now(timezone.utc) - timedelta(seconds=1)})
            spiel.aktivitäten.speichern(mit_vergangenem_ende)

            ergebnis = spiel.aktivität_abholen("123")
            spieler = spiel.spieler.holen("123")

        self.assertEqual(ergebnis.aktivität.status, "abgeschlossen")
        self.assertEqual(ergebnis.änderungen["fellpflege"], 12)
        self.assertTrue(ergebnis.auftrag_abgeschlossen)
        self.assertIsNotNone(spieler)
        assert spieler is not None
        self.assertEqual(spieler.geld, 800)


if __name__ == "__main__":
    unittest.main()
