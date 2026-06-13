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
from fabelbund.modelle.inhalte import ArtDefinition, AuftragDefinition, GegenstandDefinition, InhaltsKatalog, PflegeaktionDefinition
from fabelbund.modelle.laufzeit import SpielerProfil


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
            "dauer_sekunden": 600,
            "effekte": {"fellpflege": 12, "stimmung": 4, "stress": -3, "energie": -2},
            "abbruch_effekte": {"vertrauen": -1, "sicherheit": -1},
        }
    )
    ruhe = PflegeaktionDefinition.model_validate(
        {
            "aktion_id": "kontrollierte_ruhe",
            "name": "Kontrollierte Ruhe",
            "kategorie": "ruhe",
            "dauer_sekunden": 1800,
            "braucht_spieler": False,
            "effekte": {"energie": 14, "stress": -6, "muskelkater": -5},
            "abbruch_effekte": {"vertrauen": -2, "sicherheit": -2},
        }
    )
    training = PflegeaktionDefinition.model_validate(
        {
            "aktion_id": "ausdruck_üben",
            "name": "Ausdruck üben",
            "kategorie": "training",
            "dauer_sekunden": 900,
            "effekte": {"energie": -5, "stress": 2},
            "wettbewerb_effekte": {"ausdruck": 5},
        }
    )
    check = PflegeaktionDefinition.model_validate(
        {
            "aktion_id": "kurzer_blick",
            "name": "Kurzer Blick",
            "kategorie": "check",
            "dauer_sekunden": 0,
            "effekte": {},
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
    tutorial_auftrag = AuftragDefinition.model_validate(
        {
            "auftrag_id": "tutorial_ruhe_001",
            "name": "Einführung: Ruhe einhalten",
            "art": "tutorial",
            "dauer_tage": 1,
            "ziele": {"abgeschlossene_aktion": "kontrollierte_ruhe"},
            "belohnungen": {"geld": 80, "ruf": {"pflege": 2, "zuverlässigkeit": 2}},
        }
    )
    futter = GegenstandDefinition.model_validate(
        {
            "gegenstand_id": "apfelstücke",
            "name": "Apfelstücke",
            "kategorie": "futter",
            "preis": 8,
            "effekte": {"stimmung": 3, "energie": 2},
        }
    )
    return InhaltsKatalog(
        arten={"gluthase": art},
        pflegeaktionen={
            "sanfte_fellpflege": aktion,
            "kontrollierte_ruhe": ruhe,
            "ausdruck_üben": training,
            "kurzer_blick": check,
        },
        aufträge={"pflege_einfach_001": auftrag, "tutorial_ruhe_001": tutorial_auftrag},
        gegenstände={"apfelstücke": futter},
    )


class SpielDienstTests(unittest.TestCase):
    def baue_spiel(self, datenbank_pfad: Path, zeitfaktor: float = 1.0) -> SpielDienst:
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
            zeitfaktor=zeitfaktor,
        )

    def erzeuge_starter(self, spiel: SpielDienst, nutzer_id: str = "123") -> None:
        self.speichere_offiziellen_spieler(spiel, nutzer_id)
        art = spiel.inhalte.arten["gluthase"]
        starter = spiel.fabrik.erzeuge_starter(nutzer_id, art)
        spiel.fabelwesen.speichern(starter)

    def erzeuge_zweiten_fabling(self, spiel: SpielDienst, nutzer_id: str = "123") -> None:
        art = spiel.inhalte.arten["gluthase"]
        fabling = spiel.fabrik.erzeuge_starter(nutzer_id, art).model_copy(
            update={"id": "fw_zweit", "spitzname": "Glutfreund"}
        )
        spiel.fabelwesen.speichern(fabling)

    def speichere_offiziellen_spieler(self, spiel: SpielDienst, nutzer_id: str = "123") -> None:
        spieler = SpielerProfil(
            nutzer_id=nutzer_id,
            tutorialstatus="abgeschlossen",
            tutorialschritt="fertig",
            offizielles_mitglied=True,
        )
        spiel.spieler.speichern(spieler)

    def test_profil_erzeugung_startet_pflicht_tutorial(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            spieler = spiel.stelle_spieler_sicher("123")
            sammlung = spiel.sammlung("123")
            kapazität = spiel.stall_kapazität("123")
            hat_freien_stall = spiel.hat_freien_stall("123")

        self.assertEqual(spieler.geld, 500)
        self.assertEqual(spieler.tutorialstatus, "aktiv")
        self.assertEqual(spieler.tutorialschritt, "ruhe_starten")
        self.assertEqual(kapazität, 3)
        self.assertEqual(len(sammlung), 1)
        self.assertTrue(sammlung[0].status["tutorial_fabling"])
        self.assertTrue(hat_freien_stall)

    def test_pflegeaktion_kann_einfachen_auftrag_abschließen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            self.erzeuge_starter(spiel)
            spiel.pflegeauftrag_starten("123")
            ergebnis = spiel.pflege_anwenden("123", "sanfte_fellpflege")
            abgabe = spiel.auftrag_abgeben("123")
            spieler = spiel.spieler.holen("123")

        self.assertFalse(ergebnis.auftrag_abgeschlossen)
        self.assertTrue(abgabe.erfolgreich)
        self.assertEqual(abgabe.geld_erhalten, 300)
        self.assertIsNotNone(spieler)
        assert spieler is not None
        self.assertEqual(spieler.geld, 800)
        self.assertEqual(spieler.ruf["pflege"], 12)
        self.assertEqual(spieler.ruf["zuverlässigkeit"], 5)

    def test_pflegeauftrag_braucht_fabling(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            self.speichere_offiziellen_spieler(spiel)
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

    def test_zeitfaktor_verkürzt_aktivitätsdauer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3", zeitfaktor=100)
            self.erzeuge_starter(spiel)

            aktivität = spiel.pflegeaktivität_starten("123", "sanfte_fellpflege")
            dauer = (aktivität.endet_am - aktivität.gestartet_am).total_seconds()

        self.assertAlmostEqual(dauer, 6, delta=1)

    def test_pflegeaktivität_wird_nach_ablauf_abgeholt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            self.erzeuge_starter(spiel)
            aktivität = spiel.pflegeaktivität_starten("123", "sanfte_fellpflege")

            mit_vergangenem_ende = aktivität.model_copy(update={"endet_am": datetime.now(timezone.utc) - timedelta(seconds=1)})
            spiel.aktivitäten.speichern(mit_vergangenem_ende)

            ergebnis = spiel.aktivität_abholen("123")
            abgabe = spiel.auftrag_abgeben("123")
            spieler = spiel.spieler.holen("123")

        self.assertEqual(ergebnis.aktivität.status, "abgeschlossen")
        self.assertEqual(ergebnis.änderungen["fellpflege"], 12)
        self.assertFalse(ergebnis.auftrag_abgeschlossen)
        self.assertTrue(abgabe.erfolgreich)
        self.assertIsNotNone(spieler)
        assert spieler is not None
        self.assertEqual(spieler.geld, 800)

    def test_passive_aktivitäten_dürfen_parallel_laufen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            self.erzeuge_starter(spiel)
            self.erzeuge_zweiten_fabling(spiel)
            erster = spiel.sammlung("123")[0]
            zweiter = spiel.sammlung("123")[1]
            erste_ruhe = spiel.pflegeaktivität_starten("123", "kontrollierte_ruhe", erster.id)
            zweite_ruhe = spiel.pflegeaktivität_starten("123", "kontrollierte_ruhe", zweiter.id)
            laufende = spiel.laufende_aktivitäten("123")

        self.assertEqual(len(laufende), 2)
        self.assertFalse(erste_ruhe.braucht_spieler)
        self.assertFalse(zweite_ruhe.braucht_spieler)

    def test_aktive_aktivität_blockiert_weitere_aktive_betreuung(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            self.erzeuge_starter(spiel)

            spiel.pflegeaktivität_starten("123", "sanfte_fellpflege")
            mit_fehler = None
            try:
                spiel.pflegeaktivität_starten("123", "ausdruck_üben")
            except ValueError as fehler:
                mit_fehler = str(fehler)

        self.assertEqual(mit_fehler, "Du betreust gerade schon einen Fabling aktiv.")

    def test_abbruch_schreibt_log_und_senkt_bindungswerte(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            self.erzeuge_starter(spiel)
            fabling = spiel.sammlung("123")[0]
            vertrauen_vorher = int(fabling.zustand["vertrauen"])
            sicherheit_vorher = int(fabling.zustand["sicherheit"])
            aktivität = spiel.pflegeaktivität_starten("123", "kontrollierte_ruhe")

            ergebnis = spiel.aktivität_abbrechen("123", aktivität.id)
            log = ergebnis.fabelwesen.status["aktivitätslog"]

        self.assertLess(ergebnis.fabelwesen.zustand["vertrauen"], vertrauen_vorher)
        self.assertLess(ergebnis.fabelwesen.zustand["sicherheit"], sicherheit_vorher)
        self.assertEqual(log[-1]["status"], "abgebrochen")
        self.assertEqual(log[-1]["kategorie"], "ruhe")

    def test_training_erhöht_wettbewerbswert(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            self.erzeuge_starter(spiel)
            fabling = spiel.sammlung("123")[0]
            vorher = int(fabling.wettbewerbswerte["ausdruck"])
            aktivität = spiel.pflegeaktivität_starten("123", "ausdruck_üben")
            spiel.aktivitäten.speichern(aktivität.model_copy(update={"endet_am": datetime.now(timezone.utc) - timedelta(seconds=1)}))

            ergebnis = spiel.aktivität_abholen("123", aktivität.id)

        self.assertGreater(ergebnis.fabelwesen.wettbewerbswerte["ausdruck"], vorher)
        self.assertEqual(ergebnis.wettbewerb_änderungen["ausdruck"], 5)

    def test_laden_und_futter_verändern_inventar_und_fabling(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            self.erzeuge_starter(spiel)
            fabling = spiel.sammlung("123")[0]
            stimmung_vorher = int(fabling.zustand["stimmung"])

            kauf = spiel.gegenstand_kaufen("123", "apfelstücke", anzahl=2)
            fütterung = spiel.futter_geben("123", "apfelstücke", fabling.id)
            inventar = spiel.inventar("123")

        self.assertEqual(kauf.kosten, 16)
        self.assertEqual(inventar["apfelstücke"], 1)
        self.assertGreater(fütterung.fabelwesen.zustand["stimmung"], stimmung_vorher)

    def test_tutorial_ruheauftrag_wird_per_abgabe_abgeschlossen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            spieler = spiel.stelle_spieler_sicher("123")
            auftrag = spiel.pflegeauftrag_starten("123")
            aktivität = spiel.pflegeaktivität_starten("123", "kontrollierte_ruhe")
            spiel.aktivitäten.speichern(aktivität.model_copy(update={"endet_am": datetime.now(timezone.utc) - timedelta(seconds=1)}))

            spiel.aktivität_abholen("123", aktivität.id)
            abgabe = spiel.auftrag_abgeben("123")
            aktualisierter_spieler = spiel.spieler.holen("123")

        self.assertEqual(spieler.tutorialschritt, "ruhe_starten")
        self.assertEqual(auftrag.auftrag_id, "tutorial_ruhe_001")
        self.assertTrue(abgabe.erfolgreich)
        self.assertEqual(abgabe.geld_erhalten, 80)
        self.assertIsNotNone(aktualisierter_spieler)
        assert aktualisierter_spieler is not None
        self.assertEqual(aktualisierter_spieler.tutorialschritt, "pflege_und_ausrüstung")


if __name__ == "__main__":
    unittest.main()
