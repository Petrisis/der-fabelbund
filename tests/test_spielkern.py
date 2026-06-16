from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

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
from fabelbund.dienste.wettbewerb_dienst import leistungswert, wettbewerb_erstellen
from fabelbund.dienste.yaml_lader import YamlLader
from fabelbund.anwendung import Anwendungskontext
from fabelbund.discord.befehle.inventar import InventarAnsicht
from fabelbund.discord.befehle.profil import ProfilAnsicht, profil_einbettung_mit_inventar
from fabelbund.discord.auftragswand import AuftragsnavigationAnsicht, EinzelauftragAnsicht
from fabelbund.discord.ansichten.stall_ansicht import StallAnsicht
from fabelbund.discord.darstellung import (
    aktivität_ergebnis_einbettung,
    auftrag_einbettung,
    auftragsfortschritt_text,
    auftragsaushang_einbettung,
    auftragswand_einbettung,
    betreuungszeit_text,
    statuszeilen,
    veränderung_text,
    zustand_text,
)
from fabelbund.discord.server_einrichtung import guild_ids_für_nachholeinrichtung
from fabelbund.modelle.inhalte import ArtDefinition, AuftragDefinition, GegenstandDefinition, InhaltsKatalog, PflegeaktionDefinition
from fabelbund.modelle.laufzeit import ServerKonfiguration, SpielerProfil, WettbewerbAnmeldung
from fabelbund_bot.bot import FabelbundBot


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
            "folgeaktionen": ["kontrollierte_ruhe", "kurzer_blick"],
        }
    )
    moosluchs = art.model_copy(update={"art_id": "moosluchs", "name": "Moosluchs", "element": "wald", "grundseltenheit": "selten"})
    quellfink = art.model_copy(update={"art_id": "quellfink", "name": "Quellfink", "element": "wasser"})
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
    spiel = PflegeaktionDefinition.model_validate(
        {
            "aktion_id": "gemeinsames_spiel",
            "name": "Gemeinsames Spiel",
            "kategorie": "spiel",
            "dauer_sekunden": 900,
            "effekte": {"vertrauen": 7, "stimmung": 12, "stress": -2, "energie": -8},
        }
    )
    pause = PflegeaktionDefinition.model_validate(
        {
            "aktion_id": "kurze_pause",
            "name": "Kurze Pause",
            "kategorie": "ruhe",
            "dauer_sekunden": 900,
            "braucht_spieler": False,
            "effekte": {"energie": 5, "stress": -2, "stimmung": 1},
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
    doktorbesuch = PflegeaktionDefinition.model_validate(
        {
            "aktion_id": "doktorbesuch",
            "name": "Doktorbesuch",
            "kategorie": "check",
            "dauer_sekunden": 900,
            "kosten": 60,
            "braucht_spieler": False,
            "abbrechbar": False,
            "effekte": {},
        }
    )
    auftrag = AuftragDefinition.model_validate(
        {
            "auftrag_id": "pflege_einfach_001",
            "name": "Grundpflegeauftrag",
            "art": "pflege",
            "öffentlich": True,
            "aushang_gewicht": 100,
            "mindestens_offizielles_mitglied": True,
            "dauer_tage": 3,
            "fabelwesen": [
                {
                    "art_id": "moosluchs",
                    "spitzname": "Glutgast",
                    "charakter": "stolz und pflegeempfindlich",
                    "lieblingsfutter": "apfelstücke",
                }
            ],
            "ziele": {
                "gesundheit_mindestens": 80,
                "stimmung_mindestens": 55,
                "stress_höchstens": 25,
                "fellpflege_mindestens": 55,
            },
            "belohnungen": {"geld": 45, "ruf": {"pflege": 12, "zuverlässigkeit": 5}},
        }
    )
    tutorial_auftrag = AuftragDefinition.model_validate(
        {
            "auftrag_id": "tutorial_ruhe_001",
            "name": "Einführung: Ruhe einhalten",
            "art": "tutorial",
            "dauer_tage": 1,
            "fabelwesen": [
                {
                    "art_id": "gluthase",
                    "spitzname": "Miras Gluthase",
                    "charakter": "aufgeweckt und ruhelos",
                    "lieblingsfutter": "apfelstücke",
                    "starter_kandidat": True,
                }
            ],
            "ziele": {"energie_mindestens": 49, "stress_höchstens": 32},
            "belohnungen": {"geld": 45, "ruf": {"pflege": 2, "zuverlässigkeit": 2}},
        }
    )
    tutorial_pflege = AuftragDefinition.model_validate(
        {
            "auftrag_id": "tutorial_pflege_002",
            "name": "Einführung: Pflege und Ausrüstung",
            "art": "tutorial",
            "dauer_tage": 1,
            "fabelwesen": [
                {
                    "art_id": "gluthase",
                    "spitzname": "Branns Moosluchs",
                    "charakter": "stolz und pflegeempfindlich",
                    "lieblingsfutter": "apfelstücke",
                    "starter_kandidat": True,
                }
            ],
            "ziele": {"fellpflege_mindestens": 50},
            "belohnungen": {"geld": 180, "ruf": {"pflege": 3, "zuverlässigkeit": 1}},
        }
    )
    tutorial_aktiv_passiv = AuftragDefinition.model_validate(
        {
            "auftrag_id": "tutorial_aktiv_passiv_003",
            "name": "Einführung: Aktive und passive Betreuung",
            "art": "tutorial",
            "dauer_tage": 1,
            "fabelwesen": [
                {"art_id": "quellfink", "spitzname": "Miras Quellfink", "starter_kandidat": True},
                {"art_id": "gluthase", "spitzname": "Miras Gluthase", "starter_kandidat": True},
            ],
            "ziele": {
                "fabling_ziele": [
                    {"spitzname": "Miras Quellfink", "energie_mindestens": 50, "stress_höchstens": 28},
                    {"spitzname": "Miras Gluthase", "vertrauen_mindestens": 42, "stimmung_mindestens": 54},
                ],
            },
            "belohnungen": {"geld": 25, "ruf": {"pflege": 3, "zuverlässigkeit": 3}},
        }
    )
    tutorial_futter = AuftragDefinition.model_validate(
        {
            "auftrag_id": "tutorial_futter_004",
            "name": "Einführung: Futtervorlieben",
            "art": "tutorial",
            "dauer_tage": 1,
            "fabelwesen": [
                {"art_id": "moosluchs", "spitzname": "Jonnas Moosluchs", "lieblingsfutter": "kräuterheu", "starter_kandidat": True},
            ],
            "ziele": {"futter_priorität": "kräuterheu"},
            "belohnungen": {"geld": 20, "ruf": {"pflege": 2, "zuverlässigkeit": 2}},
        }
    )
    tutorial_betreuung = AuftragDefinition.model_validate(
        {
            "auftrag_id": "tutorial_betreuung_005",
            "name": "Einführung: Betreuungszeit",
            "art": "tutorial",
            "dauer_tage": 1,
            "fabelwesen": [
                {
                    "art_id": "quellfink",
                    "spitzname": "Jonnas Quellfink",
                    "starter_kandidat": True,
                    "start_zustand": {"vertrauen": 34},
                },
            ],
            "ziele": {
                "betreuungsdauer_sekunden": 240,
                "vertrauen_mindestens": 41,
            },
            "belohnungen": {"geld": 25, "ruf": {"pflege": 3, "zuverlässigkeit": 4}},
        }
    )
    tutorial_wettbewerb = AuftragDefinition.model_validate(
        {
            "auftrag_id": "tutorial_wettbewerb_006",
            "name": "Einführung: Wettbewerbsvorbereitung",
            "art": "tutorial",
            "dauer_tage": 1,
            "fabelwesen": [
                {"art_id": "gluthase", "spitzname": "Branns Gluthase", "starter_kandidat": True},
            ],
            "ziele": {"wettbewerb_mindestens": {"ausdruck": 50}},
            "belohnungen": {"geld": 30, "ruf": {"pflege": 4, "zuverlässigkeit": 5}},
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
    kräuterheu = GegenstandDefinition.model_validate(
        {
            "gegenstand_id": "kräuterheu",
            "name": "Kräuterheu",
            "kategorie": "futter",
            "preis": 7,
            "effekte": {"gesundheit": 1},
        }
    )
    basisfutter = GegenstandDefinition.model_validate(
        {
            "gegenstand_id": "basisfutter",
            "name": "Basisfutter",
            "kategorie": "futter",
            "preis": 6,
            "effekte": {"energie": 1},
            "markierungen": ["futter", "neutral", "normal"],
        }
    )
    honigbeeren = GegenstandDefinition.model_validate(
        {
            "gegenstand_id": "honigbeeren",
            "name": "Honigbeeren",
            "kategorie": "futter",
            "preis": 9,
            "effekte": {"stimmung": 4, "energie": 1},
            "markierungen": ["futter", "normal"],
        }
    )
    return InhaltsKatalog(
        arten={"gluthase": art, "moosluchs": moosluchs, "quellfink": quellfink},
        pflegeaktionen={
            "sanfte_fellpflege": aktion,
            "kontrollierte_ruhe": ruhe,
            "gemeinsames_spiel": spiel,
            "kurze_pause": pause,
            "ausdruck_üben": training,
            "kurzer_blick": check,
            "doktorbesuch": doktorbesuch,
        },
        aufträge={
            "pflege_einfach_001": auftrag,
            "tutorial_ruhe_001": tutorial_auftrag,
            "tutorial_pflege_002": tutorial_pflege,
            "tutorial_aktiv_passiv_003": tutorial_aktiv_passiv,
            "tutorial_futter_004": tutorial_futter,
            "tutorial_betreuung_005": tutorial_betreuung,
            "tutorial_wettbewerb_006": tutorial_wettbewerb,
        },
        gegenstände={"apfelstücke": futter, "kräuterheu": kräuterheu, "basisfutter": basisfutter, "honigbeeren": honigbeeren},
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
            geld=500,
            tutorialstatus="abgeschlossen",
            tutorialschritt="fertig",
            offizielles_mitglied=True,
        )
        spiel.spieler.speichern(spieler)

    def schließe_aktivität_ab(self, spiel: SpielDienst, aktivität) -> None:
        jetzt = datetime.now(timezone.utc)
        dauer = max(1.0, (aktivität.endet_am - aktivität.gestartet_am).total_seconds())
        spiel.aktivitäten.speichern(
            aktivität.model_copy(
                update={
                    "gestartet_am": jetzt - timedelta(seconds=dauer + 1),
                    "endet_am": jetzt - timedelta(seconds=1),
                }
            )
        )
        spiel.aktivität_abholen(aktivität.spieler_id, aktivität.id)

    def test_profil_erzeugung_wartet_auf_bewussten_tutorialstart(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            spieler = spiel.stelle_spieler_sicher("123")
            kapazität = spiel.stall_kapazität("123")
            hat_freien_stall = spiel.hat_freien_stall("123")
            sammlung = spiel.sammlung("123")
            gestartet = spiel.tutorial_starten("123")

        self.assertEqual(spieler.geld, 0)
        self.assertEqual(spieler.tutorialstatus, "neu")
        self.assertEqual(spieler.tutorialschritt, "registrierung")
        self.assertEqual(kapazität, 1)
        self.assertEqual(len(sammlung), 0)
        self.assertTrue(hat_freien_stall)
        self.assertEqual(gestartet.tutorialstatus, "aktiv")
        self.assertEqual(gestartet.tutorialschritt, "ruhe_starten")

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
        self.assertEqual(abgabe.geld_erhalten, 45)
        self.assertIsNotNone(spieler)
        assert spieler is not None
        self.assertEqual(spieler.geld, 545)
        self.assertEqual(spieler.ruf["pflege"], 12)
        self.assertEqual(spieler.ruf["zuverlässigkeit"], 5)

    def test_auftrag_teilt_leih_fabling_zu(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            self.speichere_offiziellen_spieler(spiel)
            auftrag = spiel.pflegeauftrag_starten("123")
            sammlung = spiel.sammlung("123")

        self.assertEqual(auftrag.auftrag_id, "pflege_einfach_001")
        self.assertEqual(len(sammlung), 1)
        self.assertTrue(sammlung[0].status["leih_fabling"])

    def test_fablingkauf_kostet_mehrere_normale_aufträge(self) -> None:
        katalog = YamlLader(Path("daten")).lade_alle()
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            öffentliche_belohnungen = [
                int(auftrag.belohnungen.get("geld", 0))
                for auftrag in getattr(katalog, "aufträge").values()
                if getattr(auftrag, "öffentlich") and auftrag.dauer_stunden == 1
            ]
            gewöhnlicher_preis = spiel.fabelwesen_preis("gluthase")
            seltener_preis = spiel.fabelwesen_preis("moosluchs")

        self.assertGreaterEqual(gewöhnlicher_preis, max(öffentliche_belohnungen) * 4)
        self.assertGreaterEqual(seltener_preis, max(öffentliche_belohnungen) * 10)

    def test_fablingkauf_zieht_siegel_ab_und_braucht_stallplatz(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            self.speichere_offiziellen_spieler(spiel)
            ergebnis = spiel.fabelwesen_kaufen("123", "gluthase")
            sammlung = spiel.sammlung("123")
            fehlertext = None
            try:
                spiel.fabelwesen_kaufen("123", "gluthase")
            except ValueError as fehler:
                fehlertext = str(fehler)

        self.assertEqual(ergebnis.preis, 240)
        self.assertEqual(ergebnis.spieler.geld, 260)
        self.assertEqual(len(sammlung), 1)
        self.assertTrue(sammlung[0].status["gekaufter_fabling"])
        self.assertEqual(fehlertext, "Du brauchst zuerst einen freien Stallplatz.")

    def test_öffentliche_aufträge_schließen_tutorial_aus(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            aufträge = spiel.öffentliche_aufträge()

        self.assertEqual([auftrag.auftrag_id for auftrag in aufträge], ["pflege_einfach_001"])

    def test_öffentlichen_auftrag_kann_nur_offizielles_mitglied_annehmen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            fehlertext = None
            try:
                spiel.öffentlichen_auftrag_annehmen("123", "pflege_einfach_001", "guild_1")
            except ValueError as fehler:
                fehlertext = str(fehler)

        self.assertEqual(fehlertext, "Diesen Auftrag kannst du erst nach dem Tutorial annehmen.")

    def test_öffentlichen_auftrag_annehmen_erzeugt_leih_fabling_und_quelle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            self.speichere_offiziellen_spieler(spiel)
            auftrag = spiel.öffentlichen_auftrag_annehmen("123", "pflege_einfach_001", "guild_1")
            sammlung = spiel.sammlung("123")
            verfügbare = spiel.öffentliche_aufträge()

        self.assertEqual(auftrag.fortschritt["quelle"], "auftragswand")
        self.assertEqual(auftrag.fortschritt["guild_id"], "guild_1")
        self.assertEqual(len(sammlung), 1)
        self.assertTrue(sammlung[0].status["leih_fabling"])
        self.assertEqual(verfügbare, [])

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
        self.assertEqual(ergebnis.aktivität.folgeaktionen, ["kontrollierte_ruhe", "kurzer_blick"])
        self.assertFalse(ergebnis.auftrag_abgeschlossen)
        self.assertTrue(abgabe.erfolgreich)
        self.assertIsNotNone(spieler)
        assert spieler is not None
        self.assertEqual(spieler.geld, 545)

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

    def test_yaml_trainingsaktionen_decken_alle_wettbewerbswerte_ab(self) -> None:
        katalog = YamlLader(Path("daten")).lade_alle()
        erwartete_werte = {"schönheit", "eleganz", "charme", "intelligenz", "ausdruck", "disziplin", "harmonie"}
        hauptwerte = {
            wert
            for aktion in katalog.pflegeaktionen.values()
            if aktion.kategorie == "training" and aktion.name.endswith("trainieren")
            for wert, änderung in aktion.wettbewerb_effekte.items()
            if änderung >= 5
        }
        intensitäten = {
            wert: {
                aktion.intensität
                for aktion in katalog.pflegeaktionen.values()
                if aktion.kategorie == "training" and wert in aktion.markierungen
            }
            for wert in erwartete_werte
        }

        self.assertEqual(hauptwerte, erwartete_werte)
        self.assertTrue(all(stufen == {"kurz", "gründlich", "ausgiebig"} for stufen in intensitäten.values()))

    def test_trainingsansicht_nutzt_wertauswahl_und_danach_drei_stufen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            datenbank = Datenbank(Path(tmp) / "test.sqlite3")
            datenbank.migrieren()
            spiel = SpielDienst(
                inhalte=YamlLader(Path("daten")).lade_alle(),
                spieler=SpielerSpeicher(datenbank),
                fabelwesen=FabelwesenSpeicher(datenbank),
                aufträge=AuftragSpeicher(datenbank),
                aktivitäten=AktivitätSpeicher(datenbank),
                fabrik=FabelwesenFabrik(),
                pflege=PflegeDienst(),
                auftrag_dienst=AuftragDienst(),
            )
            self.erzeuge_starter(spiel)
            fabling = spiel.sammlung("123")[0]

            wertansicht = StallAnsicht(spiel, "123", [fabling], 1, fabling.id, "training")
            stufenansicht = StallAnsicht(spiel, "123", [fabling], 1, fabling.id, "training:ausdruck")

        wertbuttons = [kind for kind in wertansicht.children if getattr(kind, "custom_id", "").startswith("stall:training:")]
        stufenbuttons = [kind for kind in stufenansicht.children if getattr(kind, "custom_id", "").startswith("stall:aktion:")]
        self.assertEqual(len(wertbuttons), 7)
        self.assertEqual(len(stufenbuttons), 3)
        self.assertEqual([button.label for button in stufenbuttons], ["Kurz (10m)", "Gründlich (1h)", "Ausgiebig (2h)"])

    def test_checkansicht_blendet_kostenlosen_sofortcheck_als_button_aus(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            datenbank = Datenbank(Path(tmp) / "test.sqlite3")
            datenbank.migrieren()
            spiel = SpielDienst(
                inhalte=YamlLader(Path("daten")).lade_alle(),
                spieler=SpielerSpeicher(datenbank),
                fabelwesen=FabelwesenSpeicher(datenbank),
                aufträge=AuftragSpeicher(datenbank),
                aktivitäten=AktivitätSpeicher(datenbank),
                fabrik=FabelwesenFabrik(),
                pflege=PflegeDienst(),
                auftrag_dienst=AuftragDienst(),
            )
            self.erzeuge_starter(spiel)
            fabling = spiel.sammlung("123")[0]

            ansicht = StallAnsicht(spiel, "123", [fabling], 1, fabling.id, "check")

        ids = [getattr(kind, "custom_id", "") for kind in ansicht.children]
        self.assertNotIn("stall:aktion:kurzer_blick", ids)
        self.assertIn("stall:aktion:genauer_check", ids)
        self.assertIn("stall:aktion:doktorbesuch", ids)

    def test_doktorbesuch_kostet_geld_und_bucht_nicht_doppelt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            self.erzeuge_starter(spiel)
            vorher = spiel.spieler.holen("123")
            assert vorher is not None

            erste_aktivität = spiel.pflegeaktivität_starten("123", "doktorbesuch")
            zweite_aktivität = spiel.pflegeaktivität_starten("123", "doktorbesuch")
            nachher = spiel.spieler.holen("123")

        self.assertEqual(erste_aktivität.id, zweite_aktivität.id)
        self.assertFalse(erste_aktivität.abbrechbar)
        self.assertFalse(erste_aktivität.braucht_spieler)
        self.assertIsNotNone(nachher)
        assert nachher is not None
        self.assertEqual(nachher.geld, vorher.geld - 60)

    def test_doktorbesuch_braucht_genug_geld(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            self.erzeuge_starter(spiel)
            spieler = spiel.spieler.holen("123")
            assert spieler is not None
            spiel.spieler.speichern(spieler.model_copy(update={"geld": 20}))
            fehlertext = None

            try:
                spiel.pflegeaktivität_starten("123", "doktorbesuch")
            except ValueError as fehler:
                fehlertext = str(fehler)

        self.assertEqual(fehlertext, "Dafür hast du nicht genug Bundsiegel.")

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
            spieler = spiel.tutorial_starten("123")
            auftrag = spiel.pflegeauftrag_starten("123")
            aktivität = spiel.pflegeaktivität_starten("123", "kontrollierte_ruhe")
            spiel.aktivitäten.speichern(aktivität.model_copy(update={"endet_am": datetime.now(timezone.utc) - timedelta(seconds=1)}))

            spiel.aktivität_abholen("123", aktivität.id)
            abgabe = spiel.auftrag_abgeben("123")
            nächster_auftrag = spiel.pflegeauftrag_starten("123")
            aktualisierter_spieler = spiel.spieler.holen("123")
            sammlung_nach_abgabe = spiel.sammlung("123")

        self.assertEqual(spieler.tutorialschritt, "ruhe_starten")
        self.assertEqual(auftrag.auftrag_id, "tutorial_ruhe_001")
        self.assertTrue(abgabe.erfolgreich)
        self.assertEqual(abgabe.geld_erhalten, 45)
        self.assertEqual(nächster_auftrag.auftrag_id, "tutorial_pflege_002")
        self.assertEqual(len(sammlung_nach_abgabe), 1)
        self.assertIsNotNone(aktualisierter_spieler)
        assert aktualisierter_spieler is not None
        self.assertEqual(aktualisierter_spieler.tutorialschritt, "pflege_und_ausrüstung")

    def test_tutorial_nutzt_kurze_aktionsdauern(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            spieler = spiel.tutorial_starten("123").model_copy(
                update={"tutorialschritt": "pflege_und_ausrüstung"}
            )
            spiel.spieler.speichern(spieler)
            pflegeauftrag = spiel.pflegeauftrag_starten("123")
            pflege = spiel.pflegeaktivität_starten("123", "sanfte_fellpflege")
            self.schließe_aktivität_ab(spiel, pflege)
            spiel.auftrag_abgeben("123")
            spieler = spiel.spieler.holen("123")
            assert spieler is not None
            spieler = spieler.model_copy(update={"tutorialschritt": "aktiv_passiv"})
            spiel.spieler.speichern(spieler)
            aktiv_passiv = spiel.pflegeauftrag_starten("123")
            fablinge = spiel.sammlung("123")
            quellfink = next(fabling for fabling in fablinge if fabling.art_id == "quellfink")
            gluthase = next(fabling for fabling in fablinge if fabling.art_id == "gluthase")
            ruhe = spiel.pflegeaktivität_starten("123", "kontrollierte_ruhe", quellfink.id)
            spiel_aktivität = spiel.pflegeaktivität_starten("123", "gemeinsames_spiel", gluthase.id)

        self.assertEqual(pflegeauftrag.auftrag_id, "tutorial_pflege_002")
        self.assertEqual(round((pflege.endet_am - pflege.gestartet_am).total_seconds()), 120)
        self.assertEqual(aktiv_passiv.auftrag_id, "tutorial_aktiv_passiv_003")
        self.assertEqual(round((ruhe.endet_am - ruhe.gestartet_am).total_seconds()), 180)
        self.assertEqual(round((spiel_aktivität.endet_am - spiel_aktivität.gestartet_am).total_seconds()), 180)

        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            spieler = spiel.tutorial_starten("123").model_copy(
                update={"tutorialschritt": "betreuungszeit"}
            )
            spiel.spieler.speichern(spieler)
            betreuungsauftrag = spiel.pflegeauftrag_starten("123")
            fabling = spiel.sammlung("123")[0]
            spiel_aktivität = spiel.pflegeaktivität_starten("123", "gemeinsames_spiel", fabling.id)
            self.schließe_aktivität_ab(spiel, spiel_aktivität)
            pause = spiel.pflegeaktivität_starten("123", "kurze_pause", fabling.id)

        self.assertEqual(betreuungsauftrag.auftrag_id, "tutorial_betreuung_005")
        self.assertEqual(round((spiel_aktivität.endet_am - spiel_aktivität.gestartet_am).total_seconds()), 120)
        self.assertEqual(round((pause.endet_am - pause.gestartet_am).total_seconds()), 120)

        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            spieler = spiel.tutorial_starten("123").model_copy(
                update={"tutorialschritt": "wettbewerb_vorbereitung"}
            )
            spiel.spieler.speichern(spieler)
            wettbewerbsauftrag = spiel.pflegeauftrag_starten("123")
            fabling = spiel.sammlung("123")[0]
            training = spiel.pflegeaktivität_starten("123", "ausdruck_üben", fabling.id)

        self.assertEqual(wettbewerbsauftrag.auftrag_id, "tutorial_wettbewerb_006")
        self.assertEqual(round((training.endet_am - training.gestartet_am).total_seconds()), 180)

    def test_tutorial_führt_bis_zur_offiziellen_mitgliedschaft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3", zeitfaktor=1000)

            spiel.tutorial_starten("123")
            erster_auftrag = spiel.pflegeauftrag_starten("123")
            ruhe = spiel.pflegeaktivität_starten("123", "kontrollierte_ruhe")
            self.schließe_aktivität_ab(spiel, ruhe)
            spiel.auftrag_abgeben("123")

            zweiter_auftrag = spiel.pflegeauftrag_starten("123")
            pflege = spiel.pflegeaktivität_starten("123", "sanfte_fellpflege")
            self.schließe_aktivität_ab(spiel, pflege)
            zweite_abgabe = spiel.auftrag_abgeben("123")
            nach_pflege = spiel.spieler.holen("123")
            ausbau = spiel.stallausbau_starten("123")
            spieler_mit_abgelaufenem_ausbau = spiel.spieler.holen("123")
            assert spieler_mit_abgelaufenem_ausbau is not None
            spiel.spieler.speichern(
                spieler_mit_abgelaufenem_ausbau.model_copy(
                    update={"tutorialpfad": f"stallausbau:{(datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()}"}
                )
            )
            spiel.stallausbau_abholen("123")
            nach_ausbau = spiel.spieler.holen("123")

            dritter_auftrag = spiel.pflegeauftrag_starten("123")
            fablinge = spiel.sammlung("123")
            ruhe_fabling = next(fabling for fabling in fablinge if fabling.art_id == "quellfink")
            spiel_fabling = next(fabling for fabling in fablinge if fabling.art_id == "gluthase")
            self.schließe_aktivität_ab(spiel, spiel.pflegeaktivität_starten("123", "kontrollierte_ruhe", ruhe_fabling.id))
            self.schließe_aktivität_ab(spiel, spiel.pflegeaktivität_starten("123", "gemeinsames_spiel", spiel_fabling.id))
            dritte_abgabe = spiel.auftrag_abgeben("123")

            vierter_auftrag = spiel.pflegeauftrag_starten("123")
            moosluchs = spiel.sammlung("123")[0]
            spiel.gegenstand_kaufen("123", "kräuterheu")
            spiel.futterpriorität_setzen("123", moosluchs.id, "kräuterheu")
            vierte_abgabe = spiel.auftrag_abgeben("123")

            fünfter_auftrag = spiel.pflegeauftrag_starten("123")
            quellfink = spiel.sammlung("123")[0]
            self.schließe_aktivität_ab(spiel, spiel.pflegeaktivität_starten("123", "gemeinsames_spiel", quellfink.id))
            self.schließe_aktivität_ab(spiel, spiel.pflegeaktivität_starten("123", "kurze_pause", quellfink.id))
            fünfte_abgabe = spiel.auftrag_abgeben("123")

            sechster_auftrag = spiel.pflegeauftrag_starten("123")
            wettbewerbs_fabling = spiel.sammlung("123")[0]
            self.schließe_aktivität_ab(spiel, spiel.pflegeaktivität_starten("123", "ausdruck_üben", wettbewerbs_fabling.id))
            sechste_abgabe = spiel.auftrag_abgeben("123")
            vor_starterwahl = spiel.spieler.holen("123")

            starter = spiel.tutorial_starter_wählen("123", "gluthase")
            abgeschlossen = spiel.spieler.holen("123")

        self.assertEqual(erster_auftrag.auftrag_id, "tutorial_ruhe_001")
        self.assertEqual(zweiter_auftrag.auftrag_id, "tutorial_pflege_002")
        self.assertTrue(zweite_abgabe.erfolgreich)
        self.assertIsNotNone(nach_pflege)
        assert nach_pflege is not None
        self.assertEqual(nach_pflege.tutorialschritt, "stall_ausbauen")
        self.assertEqual(ausbau.status, "läuft")
        self.assertIsNotNone(nach_ausbau)
        assert nach_ausbau is not None
        self.assertEqual(nach_ausbau.freigeschaltete_ställe, 2)
        self.assertEqual(nach_ausbau.tutorialschritt, "aktiv_passiv")
        self.assertEqual(dritter_auftrag.auftrag_id, "tutorial_aktiv_passiv_003")
        self.assertTrue(dritte_abgabe.erfolgreich)
        self.assertIn("Quellfink", dritte_abgabe.rückgabe_text)
        self.assertIn("Gluthase", dritte_abgabe.rückgabe_text)
        self.assertEqual(vierter_auftrag.auftrag_id, "tutorial_futter_004")
        self.assertTrue(vierte_abgabe.erfolgreich)
        self.assertEqual(fünfter_auftrag.auftrag_id, "tutorial_betreuung_005")
        self.assertTrue(fünfte_abgabe.erfolgreich)
        self.assertEqual(sechster_auftrag.auftrag_id, "tutorial_wettbewerb_006")
        self.assertTrue(sechste_abgabe.erfolgreich)
        self.assertIsNotNone(vor_starterwahl)
        assert vor_starterwahl is not None
        self.assertEqual(vor_starterwahl.tutorialschritt, "starter_wählen")
        self.assertEqual(starter.art_id, "gluthase")
        self.assertIsNotNone(abgeschlossen)
        assert abgeschlossen is not None
        self.assertEqual(abgeschlossen.tutorialstatus, "abgeschlossen")
        self.assertEqual(abgeschlossen.tutorialschritt, "fertig")
        self.assertTrue(abgeschlossen.offizielles_mitglied)
        self.assertIn("mitglied:fabelbund", abgeschlossen.lizenzen)

    def test_spielerreset_löscht_spieldaten_aber_keine_serverkonfiguration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            datenbank_pfad = Path(tmp) / "test.sqlite3"
            spiel = self.baue_spiel(datenbank_pfad)
            server = ServerSpeicher(Datenbank(datenbank_pfad))
            server.speichern(
                ServerKonfiguration(
                    guild_id="1",
                    eingerichtet=True,
                    kategorie_id="2",
                    aufträge_kanal_id="3",
                    chronik_kanal_id="4",
                    events_kanal_id="5",
                )
            )
            spiel.tutorial_starten("123")
            spiel.pflegeauftrag_starten("123")
            fabling = spiel.sammlung("123")[0]
            spiel.pflegeaktivität_starten("123", "kontrollierte_ruhe", fabling.id)

            spiel.spielerfortschritt_zurücksetzen("123")
            spieler = spiel.spieler.holen("123")
            sammlung = spiel.sammlung("123")
            auftrag = spiel.aktiver_auftrag("123")
            aktivitäten = spiel.laufende_aktivitäten("123")
            serverkonfiguration = server.holen("1")

        self.assertIsNone(spieler)
        self.assertEqual(sammlung, [])
        self.assertIsNone(auftrag)
        self.assertEqual(aktivitäten, [])
        self.assertIsNotNone(serverkonfiguration)
        assert serverkonfiguration is not None
        self.assertTrue(serverkonfiguration.eingerichtet)

    def test_auftragsansicht_zeigt_betreuungszeit_zielpunkt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            spieler = spiel.tutorial_starten("123").model_copy(
                update={"tutorialschritt": "betreuungszeit"}
            )
            spiel.spieler.speichern(spieler)
            auftrag = spiel.pflegeauftrag_starten("123")
            definition = spiel.inhalte.aufträge[auftrag.auftrag_id]
            fabling = spiel.sammlung("123")[0]

            text = betreuungszeit_text(auftrag, definition, [fabling])
            embed = auftrag_einbettung(auftrag, definition, fabling, [fabling])

        self.assertIn("Gesammelt: 0s von 4m.", text)
        self.assertIn("Früheste Abgabe", text)
        self.assertTrue(any(feld.name == "Betreuungszeit" for feld in embed.fields))
        self.assertTrue(any(feld.name == "Ausgangslage und Ziel" for feld in embed.fields))

    def test_öffentliche_standardaufträge_sind_zustandsbasiert(self) -> None:
        katalog = YamlLader(Path("daten")).lade_alle()
        öffentliche_aufträge = [
            auftrag
            for auftrag in katalog.aufträge.values()
            if auftrag.öffentlich and auftrag.art != "tutorial"
        ]
        einbettung = auftragswand_einbettung(öffentliche_aufträge[:3])
        aushang = auftragsaushang_einbettung(öffentliche_aufträge[0])

        self.assertGreaterEqual(len(öffentliche_aufträge), 4)
        self.assertEqual(einbettung.fields, [])
        self.assertTrue(any(feld.name == "Ausgangslage und Ziel" for feld in aushang.fields))
        for auftrag in öffentliche_aufträge:
            self.assertNotIn("abgeschlossene_aktion", auftrag.ziele, auftrag.auftrag_id)
            self.assertNotIn("abgeschlossene_aktionen", auftrag.ziele, auftrag.auftrag_id)
            self.assertNotIn("futter_priorität", auftrag.ziele, auftrag.auftrag_id)
            self.assertNotIn("gefüttert", auftrag.ziele, auftrag.auftrag_id)
            self.assertTrue(auftrag.fehlschlag.get("hinweis"), auftrag.auftrag_id)

    def test_öffentliche_aufträge_haben_drei_zeitvarianten_mit_sublinearer_belohnung(self) -> None:
        katalog = YamlLader(Path("daten")).lade_alle()
        öffentliche_aufträge = [
            auftrag
            for auftrag in katalog.aufträge.values()
            if auftrag.öffentlich and auftrag.art != "tutorial"
        ]
        gruppen: dict[str, dict[int, AuftragDefinition]] = {}
        for auftrag in öffentliche_aufträge:
            basis_id = auftrag.auftrag_id.removesuffix("_3h").removesuffix("_5h")
            gruppen.setdefault(basis_id, {})[int(auftrag.dauer_stunden or 0)] = auftrag

        self.assertEqual(len(öffentliche_aufträge), len(gruppen) * 3)
        for varianten in gruppen.values():
            self.assertEqual(set(varianten), {1, 3, 5})
            for stunden, auftrag in varianten.items():
                self.assertEqual(auftrag.ziele.get("betreuungsdauer_sekunden"), stunden * 3600)
            geld_1h = int(varianten[1].belohnungen.get("geld", 0))
            geld_3h = int(varianten[3].belohnungen.get("geld", 0))
            geld_5h = int(varianten[5].belohnungen.get("geld", 0))
            self.assertGreater(geld_3h, geld_1h)
            self.assertGreater(geld_5h, geld_3h)
            self.assertLess(geld_3h, geld_1h * 3)
            self.assertLess(geld_5h, geld_1h * 5)

    def test_öffentliche_aufträge_decken_neue_arten_und_fehlende_stats_ab(self) -> None:
        katalog = YamlLader(Path("daten")).lade_alle()
        öffentliche_aufträge = [
            auftrag
            for auftrag in katalog.aufträge.values()
            if auftrag.öffentlich and auftrag.art != "tutorial"
        ]
        neue_arten = {
            "aschmarder",
            "dornenkatze",
            "farnwidder",
            "funkenkraehe",
            "kohligel",
            "nebelkauz",
            "rindenfuchs",
            "schilfhirsch",
            "tropfenmolch",
        }
        genutzte_arten = {
            fabling.art_id
            for auftrag in öffentliche_aufträge
            for fabling in auftrag.fabelwesen
        }
        zielwerte: set[str] = set()
        for auftrag in öffentliche_aufträge:
            if auftrag.ziele.get("sicherheit_mindestens") is not None:
                zielwerte.add("sicherheit")
            if auftrag.ziele.get("sättigung_mindestens") is not None:
                zielwerte.add("sättigung")
            wettbewerb = auftrag.ziele.get("wettbewerb_mindestens")
            if isinstance(wettbewerb, dict):
                zielwerte.update(str(schlüssel) for schlüssel in wettbewerb)

        self.assertTrue(neue_arten <= genutzte_arten)
        self.assertTrue(
            {"sicherheit", "sättigung", "schönheit", "eleganz", "charme", "intelligenz", "disziplin", "harmonie"}
            <= zielwerte
        )
        for auftrag in öffentliche_aufträge:
            seltenheiten = [katalog.arten[fabling.art_id].grundseltenheit for fabling in auftrag.fabelwesen]
            if "selten" in seltenheiten and not auftrag.auftrag_id.startswith("pflege_einfach_001"):
                self.assertLessEqual(auftrag.aushang_gewicht, 25, auftrag.auftrag_id)

    def test_auftrag_dienst_prüft_sicherheit_und_sättigung_als_zielwerte(self) -> None:
        katalog = YamlLader(Path("daten")).lade_alle()
        definition = katalog.aufträge["sattigung_kohligel_001"]
        definition = definition.model_copy(
            deep=True,
            update={"ziele": {schlüssel: wert for schlüssel, wert in definition.ziele.items() if schlüssel != "betreuungsdauer_sekunden"}},
        )
        zugeteilt = definition.fabelwesen[0]
        fabling = FabelwesenFabrik().erzeuge_starter("123", katalog.arten[zugeteilt.art_id])
        for schlüssel, wert in zugeteilt.start_zustand.items():
            fabling.zustand[schlüssel] = wert

        frühe_abgabe = AuftragDienst().ziele_erfüllt(definition, fabling, [fabling])
        fabling.zustand["sättigung"] = 75
        fabling.zustand["gesundheit"] = 85
        fabling.zustand["stress"] = 20
        spätere_abgabe = AuftragDienst().ziele_erfüllt(definition, fabling, [fabling])

        self.assertFalse(frühe_abgabe)
        self.assertTrue(spätere_abgabe)

    def test_auftragswand_nutzt_navigation_und_einzelne_aushänge(self) -> None:
        katalog = YamlLader(Path("daten")).lade_alle()
        auftrag = next(
            auftrag
            for auftrag in katalog.aufträge.values()
            if auftrag.öffentlich and auftrag.art != "tutorial"
        )
        kontext = SimpleNamespace(spiel=SimpleNamespace(öffentliche_aufträge=lambda: [auftrag]))

        navigation = AuftragsnavigationAnsicht(kontext)
        aushang = auftragsaushang_einbettung(auftrag)
        aktiver_auftrag = AuftragDienst().erstelle_aktiven_auftrag("123", auftrag, "fw_1")
        detail = auftrag_einbettung(aktiver_auftrag, auftrag)
        ansicht = EinzelauftragAnsicht(kontext, "guild_1", auftrag.auftrag_id)

        self.assertEqual([kind.label for kind in navigation.children], ["Auftrag", "Fablinge", "Inventar"])
        self.assertFalse(aushang.footer.text)
        self.assertFalse(any(feld.name == "Voraussetzung" and "offizielles Mitglied" in feld.value for feld in aushang.fields))
        self.assertTrue(any(feld.name == "Mindestbetreuung" for feld in aushang.fields))
        self.assertTrue(any(feld.name == "Mindestbetreuung" for feld in detail.fields))
        self.assertEqual(len(ansicht.children), 1)
        self.assertEqual(ansicht.children[0].custom_id, f"auftragswand:annehmen:{auftrag.auftrag_id}")

    def test_futterpriorität_steuert_bevorzugtes_futter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            self.erzeuge_starter(spiel)
            fabling = spiel.sammlung("123")[0]
            spiel.gegenstand_kaufen("123", "apfelstücke", anzahl=1)
            spiel.gegenstand_kaufen("123", "kräuterheu", anzahl=1)

            aktualisiert = spiel.futterpriorität_setzen("123", fabling.id, "apfelstücke")
            aktualisiert = spiel.futterpriorität_setzen("123", fabling.id, "kräuterheu")
            aktualisiert = spiel.futterpriorität_setzen("123", fabling.id, "apfelstücke")
            fütterung = spiel.futter_geben("123", "apfelstücke", fabling.id)

        self.assertEqual(aktualisiert.status["futter_priorität"], ["apfelstücke"])
        self.assertTrue(fütterung.lieblingsfutter)

    def test_futterpriorität_braucht_futter_im_inventar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            self.erzeuge_starter(spiel)
            fabling = spiel.sammlung("123")[0]
            fehlertext = None

            try:
                spiel.futterpriorität_setzen("123", fabling.id, "kräuterheu")
            except ValueError as fehler:
                fehlertext = str(fehler)

        self.assertEqual(fehlertext, "Dieses Futter ist nicht in deinem Inventar.")

    def test_profil_und_inventar_sind_per_buttons_verbunden(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            self.speichere_offiziellen_spieler(spiel)
            spiel.gegenstand_kaufen("123", "apfelstücke", anzahl=2)
            kontext = SimpleNamespace(spiel=spiel)

            profil = ProfilAnsicht(kontext, "123")
            inventar = InventarAnsicht(kontext, "123")
            embed = profil_einbettung_mit_inventar(kontext, "123")

        self.assertTrue(any(kind.label == "Inventar" for kind in profil.children))
        self.assertTrue(any(kind.label == "Profil" for kind in inventar.children))
        self.assertFalse(any("geben" in str(kind.label).lower() for kind in inventar.children))
        inventar_feld = next(feld for feld in embed.fields if feld.name == "Inventar")
        self.assertIn("Apfelstücke", inventar_feld.value)

    def test_fablinge_fressen_automatisch_bevorzugtes_futter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            self.erzeuge_starter(spiel)
            spiel.gegenstand_kaufen("123", "apfelstücke", anzahl=1)
            fabling = spiel.sammlung("123")[0]
            fabling.persönlichkeit["lieblingsfutter"] = "apfelstücke"
            fabling.zustand["sättigung"] = 80
            fabling.status["sättigung_geprüft_am"] = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
            spiel.fabelwesen.speichern(fabling)

            aktualisiert = spiel.sammlung("123")[0]
            inventar = spiel.inventar("123")

        self.assertEqual(aktualisiert.status["letztes_futter"], "apfelstücke")
        self.assertEqual(aktualisiert.status["letztes_futter_art"], "bevorzugt")
        self.assertNotIn("apfelstücke", inventar)
        self.assertGreater(aktualisiert.zustand["sättigung"], 0)

    def test_fablinge_fressen_neutrales_futter_als_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            self.erzeuge_starter(spiel)
            spiel.gegenstand_kaufen("123", "basisfutter", anzahl=1)
            fabling = spiel.sammlung("123")[0]
            fabling.persönlichkeit["lieblingsfutter"] = "apfelstücke"
            fabling.zustand["sättigung"] = 80
            fabling.status["sättigung_geprüft_am"] = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
            spiel.fabelwesen.speichern(fabling)

            aktualisiert = spiel.sammlung("123")[0]

        self.assertEqual(aktualisiert.status["letztes_futter"], "basisfutter")
        self.assertEqual(aktualisiert.status["letztes_futter_art"], "neutral")

    def test_spielaktivität_spricht_nicht_von_pflegewirkung(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            self.erzeuge_starter(spiel)
            aktivität = spiel.pflegeaktivität_starten("123", "gemeinsames_spiel")
            spiel.aktivitäten.speichern(
                aktivität.model_copy(update={"endet_am": datetime.now(timezone.utc) - timedelta(seconds=1)})
            )

            ergebnis = spiel.aktivität_abholen("123", aktivität.id)
            text = veränderung_text(ergebnis)

        self.assertNotIn("Pflege", text)
        self.assertNotIn("Fell", text)
        self.assertIn("Stimmung 🟩", text)
        self.assertIn("Energie 🟥", text)

    def test_kostenlose_einschätzung_bleibt_narrativ_und_statuscheck_nutzt_balken(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            self.erzeuge_starter(spiel)
            fabling = spiel.sammlung("123")[0]
            fabling.wettbewerbswerte["ausdruck"] = 45
            spiel.fabelwesen.speichern(fabling)

            fabling = spiel.sammlung("123")[0]
            einschätzung = zustand_text(fabling)
            balken = "\n".join(statuszeilen(fabling))

        self.assertNotIn("🟦", einschätzung)
        self.assertTrue("wirkt" in einschätzung or "Eindruck" in einschätzung)
        self.assertIn("Energie 🟦🟦🟦🟧⬛", balken)
        self.assertIn("Sättigung 🍖🍖🍖🍖🦴", balken)
        self.assertIn("Ausdruck 🟦🟦🟧⬛⬛", balken)
        self.assertLessEqual(len(balken), 1024)

    def test_offener_auftrag_zeigt_bedingungen_als_rot_grün_balken(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            self.speichere_offiziellen_spieler(spiel)
            aktiver_auftrag = spiel.pflegeauftrag_starten("123")
            auftrag = spiel.inhalte.aufträge[aktiver_auftrag.auftrag_id]
            fabling = spiel.sammlung("123")[0]
            fabling.zustand["gesundheit"] = 90
            fabling.zustand["stimmung"] = 40
            fabling.zustand["stress"] = 50
            fabling.zustand["fellpflege"] = 70
            spiel.fabelwesen.speichern(fabling)

            text = auftragsfortschritt_text(auftrag, spiel.auftrag_fablinge(aktiver_auftrag))

        self.assertIn("Gesundheit 🟩", text)
        self.assertIn("Stimmung 🟥", text)
        self.assertIn("Stress 🟥", text)
        self.assertIn("Fellpflege 🟩", text)
        self.assertNotIn("wirkt", text)

    def test_serverkonfiguration_wird_gespeichert(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            datenbank = Datenbank(Path(tmp) / "test.sqlite3")
            datenbank.migrieren()
            speicher = ServerSpeicher(datenbank)
            speicher.speichern(
                ServerKonfiguration(
                    guild_id="1",
                    eingerichtet=True,
                    kategorie_id="2",
                    aufträge_kanal_id="3",
                    chronik_kanal_id="4",
                    events_kanal_id="5",
                    auftragswand_nachricht_id="6",
                )
            )
            geladen = speicher.holen("1")
            alle = speicher.auflisten()

        self.assertIsNotNone(geladen)
        assert geladen is not None
        self.assertTrue(geladen.eingerichtet)
        self.assertEqual(geladen.aufträge_kanal_id, "3")
        self.assertEqual(geladen.auftragswand_nachricht_id, "6")
        self.assertEqual(len(alle), 1)

    def test_migration_legt_server_einrichtungsstatus_an(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            datenbank = Datenbank(Path(tmp) / "test.sqlite3")
            datenbank.migrieren()
            with datenbank.verbinden() as verbindung:
                spalten = {
                    zeile["name"]
                    for zeile in verbindung.execute("PRAGMA table_info(server_konfigurationen)").fetchall()
                }

        self.assertIn("eingerichtet", spalten)

    def test_migration_legt_wettbewerbstabellen_an(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            datenbank = Datenbank(Path(tmp) / "test.sqlite3")
            datenbank.migrieren()
            with datenbank.verbinden() as verbindung:
                tabellen = {
                    zeile["name"]
                    for zeile in verbindung.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
                }

        self.assertIn("wettbewerbe", tabellen)
        self.assertIn("wettbewerb_anmeldungen", tabellen)

    def test_wettbewerb_anmeldung_wird_pro_spieler_ersetzt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            datenbank = Datenbank(Path(tmp) / "test.sqlite3")
            datenbank.migrieren()
            speicher = WettbewerbSpeicher(datenbank)
            wettbewerb = wettbewerb_erstellen("12345", datetime.now(timezone.utc) + timedelta(days=2), wert="ausdruck")
            speicher.speichern(wettbewerb)
            speicher.anmelden(WettbewerbAnmeldung(wettbewerb_id=wettbewerb.id, spieler_id="7", fabelwesen_id="fw_1"))
            speicher.anmelden(WettbewerbAnmeldung(wettbewerb_id=wettbewerb.id, spieler_id="7", fabelwesen_id="fw_2"))

            anmeldungen = speicher.anmeldungen(wettbewerb.id)

        self.assertEqual(len(anmeldungen), 1)
        self.assertEqual(anmeldungen[0].fabelwesen_id, "fw_2")

    def test_wettbewerbsleistung_nutzt_stat_als_hauptfaktor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spiel = self.baue_spiel(Path(tmp) / "test.sqlite3")
            self.erzeuge_starter(spiel)
            fabling = spiel.sammlung("123")[0]
            schwach = fabling.model_copy(deep=True)
            stark = fabling.model_copy(deep=True)
            schwach.wettbewerbswerte["ausdruck"] = 10
            stark.wettbewerbswerte["ausdruck"] = 80
            schwach.zustand.update({"gesundheit": 75, "stimmung": 50, "energie": 50, "stress": 20})
            stark.zustand.update({"gesundheit": 75, "stimmung": 50, "energie": 50, "stress": 20})

        self.assertGreater(leistungswert(stark, "ausdruck"), leistungswert(schwach, "ausdruck"))

    def test_nur_nicht_eingerichtete_guilds_werden_nachgeholt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            datenbank = Datenbank(Path(tmp) / "test.sqlite3")
            datenbank.migrieren()
            speicher = ServerSpeicher(datenbank)
            speicher.speichern(
                ServerKonfiguration(
                    guild_id="1",
                    eingerichtet=True,
                    kategorie_id="2",
                    aufträge_kanal_id="3",
                    chronik_kanal_id="4",
                    events_kanal_id="5",
                )
            )

            nachzuholen = guild_ids_für_nachholeinrichtung(
                speicher,
                [SimpleNamespace(id=1), SimpleNamespace(id=2)],
            )

        self.assertEqual(nachzuholen, ["2"])


class BotLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_einrichtungscommand_wird_nicht_registriert(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            datenbank = Datenbank(Path(tmp) / "test.sqlite3")
            datenbank.migrieren()
            spiel = SpielDienstTests().baue_spiel(Path(tmp) / "spiel.sqlite3")
            kontext = Anwendungskontext(
                spiel=spiel,
                server=ServerSpeicher(datenbank),
                wettbewerbe=WettbewerbSpeicher(datenbank),
            )
            bot = FabelbundBot(kontext, befehle_synchronisieren=False, testserver_id=None)

            await bot.setup_hook()
            befehlsnamen = {befehl.name for befehl in bot.tree.get_commands()}
            await bot.close()

        self.assertNotIn("fabelbund_einrichten", befehlsnamen)
        self.assertIn("profil", befehlsnamen)


if __name__ == "__main__":
    unittest.main()
