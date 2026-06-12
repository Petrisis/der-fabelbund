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

    def ziele_erfüllt(self, auftrag: AuftragDefinition, fabelwesen: Fabelwesen) -> bool:
        ziele = auftrag.ziele
        return (
            self._mindestens(fabelwesen, "gesundheit", ziele.get("gesundheit_mindestens"))
            and self._mindestens(fabelwesen, "stimmung", ziele.get("stimmung_mindestens"))
            and self._höchstens(fabelwesen, "stress", ziele.get("stress_höchstens"))
            and self._mindestens(fabelwesen, "fellpflege", ziele.get("fellpflege_mindestens"))
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
