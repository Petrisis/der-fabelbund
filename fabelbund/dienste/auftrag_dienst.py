from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fabelbund.modelle.inhalte import AuftragDefinition
from fabelbund.modelle.laufzeit import AktiverAuftrag, Fabelwesen, SpielerProfil


class AuftragDienst:
    def erstelle_aktiven_auftrag(self, spieler_id: str, auftrag: AuftragDefinition, fabelwesen_id: str) -> AktiverAuftrag:
        return AktiverAuftrag(
            id=f"auftrag_{uuid4().hex[:12]}",
            spieler_id=spieler_id,
            auftrag_id=auftrag.auftrag_id,
            fabelwesen_id=fabelwesen_id,
            fortschritt={},
        )

    def ziele_erfüllt(self, auftrag: AuftragDefinition, fabelwesen: Fabelwesen, fabelwesen_liste: list[Fabelwesen] | None = None) -> bool:
        ziele = auftrag.ziele
        alle_fabelwesen = fabelwesen_liste or [fabelwesen]
        return (
            self._mindestens(fabelwesen, "gesundheit", ziele.get("gesundheit_mindestens"))
            and self._mindestens(fabelwesen, "stimmung", ziele.get("stimmung_mindestens"))
            and self._mindestens(fabelwesen, "energie", ziele.get("energie_mindestens"))
            and self._mindestens(fabelwesen, "vertrauen", ziele.get("vertrauen_mindestens"))
            and self._höchstens(fabelwesen, "stress", ziele.get("stress_höchstens"))
            and self._mindestens(fabelwesen, "fellpflege", ziele.get("fellpflege_mindestens"))
            and self._aktion_abgeschlossen(fabelwesen, ziele.get("abgeschlossene_aktion"))
            and self._aktionen_abgeschlossen(alle_fabelwesen, ziele.get("abgeschlossene_aktionen"))
            and self._kategorie_abgeschlossen(fabelwesen, ziele.get("abgeschlossene_kategorie"))
            and self._gefüttert(fabelwesen, ziele.get("gefüttert"))
            and self._futter_priorität(fabelwesen, ziele.get("futter_priorität"))
            and self._betreuungsdauer(alle_fabelwesen, ziele.get("betreuungsdauer_sekunden"))
            and self._wettbewerb_mindestens(fabelwesen, ziele.get("wettbewerb_mindestens"))
            and self._fabling_ziele(alle_fabelwesen, ziele.get("fabling_ziele"))
        )

    def abschließen(self, spieler: SpielerProfil, aktiv: AktiverAuftrag, auftrag: AuftragDefinition) -> tuple[SpielerProfil, AktiverAuftrag]:
        aktualisierter_spieler = spieler.model_copy(deep=True)
        aktualisierter_spieler.geld += int(auftrag.belohnungen.get("geld", 0))
        ruf = auftrag.belohnungen.get("ruf", {})
        if isinstance(ruf, dict):
            for schlüssel, wert in ruf.items():
                aktualisierter_spieler.ruf[schlüssel] = int(aktualisierter_spieler.ruf.get(schlüssel, 0)) + int(wert)

        abgeschlossener_auftrag = aktiv.model_copy(deep=True)
        abgeschlossener_auftrag.status = "abgeschlossen"
        abgeschlossener_auftrag.abgeschlossen_am = datetime.now(timezone.utc)
        return aktualisierter_spieler, abgeschlossener_auftrag

    @staticmethod
    def _mindestens(fabelwesen: Fabelwesen, schlüssel: str, minimum: object) -> bool:
        if minimum is None:
            return True
        return int(fabelwesen.zustand.get(schlüssel, 0)) >= int(minimum)

    @staticmethod
    def _höchstens(fabelwesen: Fabelwesen, schlüssel: str, maximum: object) -> bool:
        if maximum is None:
            return True
        return int(fabelwesen.zustand.get(schlüssel, 0)) <= int(maximum)

    @staticmethod
    def _aktion_abgeschlossen(fabelwesen: Fabelwesen, aktion_id: object) -> bool:
        if aktion_id is None:
            return True
        log = fabelwesen.status.get("aktivitätslog", [])
        if not isinstance(log, list):
            return False
        return any(
            isinstance(eintrag, dict)
            and eintrag.get("aktion_id") == str(aktion_id)
            and eintrag.get("status") == "abgeschlossen"
            for eintrag in log
        )

    @classmethod
    def _aktionen_abgeschlossen(cls, fabelwesen_liste: list[Fabelwesen], aktion_ids: object) -> bool:
        if aktion_ids is None:
            return True
        if not isinstance(aktion_ids, list):
            aktion_ids = [aktion_ids]
        return all(
            any(cls._aktion_abgeschlossen(fabelwesen, aktion_id) for fabelwesen in fabelwesen_liste)
            for aktion_id in aktion_ids
        )

    @staticmethod
    def _kategorie_abgeschlossen(fabelwesen: Fabelwesen, kategorie: object) -> bool:
        if kategorie is None:
            return True
        log = fabelwesen.status.get("aktivitätslog", [])
        if not isinstance(log, list):
            return False
        return any(
            isinstance(eintrag, dict)
            and eintrag.get("kategorie") == str(kategorie)
            and eintrag.get("status") == "abgeschlossen"
            for eintrag in log
        )

    @staticmethod
    def _gefüttert(fabelwesen: Fabelwesen, erwartet: object) -> bool:
        if erwartet is None:
            return True
        return bool(fabelwesen.status.get("zuletzt_gefüttert_am"))

    @staticmethod
    def _futter_priorität(fabelwesen: Fabelwesen, erwartet: object) -> bool:
        if erwartet is None:
            return True
        priorität = fabelwesen.status.get("futter_priorität", [])
        return isinstance(priorität, list) and bool(priorität) and str(priorität[0]) == str(erwartet)

    @staticmethod
    def _betreuungsdauer(fabelwesen_liste: list[Fabelwesen], minimum: object) -> bool:
        if minimum is None:
            return True
        gesamt = 0.0
        for fabelwesen in fabelwesen_liste:
            log = fabelwesen.status.get("aktivitätslog", [])
            if not isinstance(log, list):
                continue
            for eintrag in log:
                if not isinstance(eintrag, dict) or eintrag.get("status") != "abgeschlossen":
                    continue
                if eintrag.get("spieldauer_sekunden") is not None:
                    gesamt += float(eintrag["spieldauer_sekunden"])
                    continue
                try:
                    start = datetime.fromisoformat(str(eintrag["gestartet_am"]))
                    ende = datetime.fromisoformat(str(eintrag["beendet_am"]))
                except (KeyError, TypeError, ValueError):
                    continue
                gesamt += max(0.0, (ende - start).total_seconds())
        return gesamt >= int(minimum)

    @staticmethod
    def _wettbewerb_mindestens(fabelwesen: Fabelwesen, werte: object) -> bool:
        if werte is None:
            return True
        if not isinstance(werte, dict):
            return True
        return all(int(fabelwesen.wettbewerbswerte.get(str(schlüssel), 0)) >= int(wert) for schlüssel, wert in werte.items())

    @classmethod
    def _fabling_ziele(cls, fabelwesen_liste: list[Fabelwesen], ziele: object) -> bool:
        if ziele is None:
            return True
        if not isinstance(ziele, list):
            return False
        for ziel in ziele:
            if not isinstance(ziel, dict):
                return False
            fabelwesen = cls._passenden_fabling_finden(fabelwesen_liste, ziel)
            if fabelwesen is None:
                return False
            if not cls._zielwerte_erfüllt(fabelwesen, ziel):
                return False
        return True

    @staticmethod
    def _passenden_fabling_finden(fabelwesen_liste: list[Fabelwesen], ziel: dict[str, object]) -> Fabelwesen | None:
        art_id = ziel.get("art_id")
        spitzname = ziel.get("spitzname")
        for fabelwesen in fabelwesen_liste:
            if art_id is not None and fabelwesen.art_id != str(art_id):
                continue
            if spitzname is not None and fabelwesen.spitzname != str(spitzname):
                continue
            return fabelwesen
        return None

    @classmethod
    def _zielwerte_erfüllt(cls, fabelwesen: Fabelwesen, ziel: dict[str, object]) -> bool:
        prüfungen = {
            "gesundheit_mindestens": ("zustand", "gesundheit", "mindestens"),
            "stimmung_mindestens": ("zustand", "stimmung", "mindestens"),
            "energie_mindestens": ("zustand", "energie", "mindestens"),
            "vertrauen_mindestens": ("zustand", "vertrauen", "mindestens"),
            "sicherheit_mindestens": ("zustand", "sicherheit", "mindestens"),
            "fellpflege_mindestens": ("zustand", "fellpflege", "mindestens"),
            "stress_höchstens": ("zustand", "stress", "höchstens"),
        }
        for zielschlüssel, (bereich, wertschlüssel, vergleich) in prüfungen.items():
            erwartung = ziel.get(zielschlüssel)
            if erwartung is None:
                continue
            werte = getattr(fabelwesen, bereich)
            ist = int(werte.get(wertschlüssel, 0))
            soll = int(erwartung)
            if vergleich == "mindestens" and ist < soll:
                return False
            if vergleich == "höchstens" and ist > soll:
                return False
        wettbewerb = ziel.get("wettbewerb_mindestens")
        if wettbewerb is not None and not cls._wettbewerb_mindestens(fabelwesen, wettbewerb):
            return False
        return True
