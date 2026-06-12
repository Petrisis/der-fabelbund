from __future__ import annotations

from fabelbund.modelle.basis import begrenze_prozent
from fabelbund.modelle.inhalte import PflegeaktionDefinition
from fabelbund.modelle.laufzeit import Fabelwesen


class PflegeDienst:
    def anwenden(self, fabelwesen: Fabelwesen, aktion: PflegeaktionDefinition) -> Fabelwesen:
        daten = fabelwesen.model_copy(deep=True)
        for schlüssel, veränderung in aktion.effekte.items():
            aktueller_wert = int(daten.zustand.get(schlüssel, 0))
            daten.zustand[schlüssel] = begrenze_prozent(aktueller_wert + veränderung)
        daten.zustand["verletzungsrisiko"] = self._risiko_aus_zustand(daten)
        return daten

    def _risiko_aus_zustand(self, fabelwesen: Fabelwesen) -> int:
        basis = int(fabelwesen.zustand.get("verletzungsrisiko", 0))
        stress = int(fabelwesen.zustand.get("stress", 0))
        muskelkater = int(fabelwesen.zustand.get("muskelkater", 0))
        energie = int(fabelwesen.zustand.get("energie", 0))
        gesundheit = int(fabelwesen.zustand.get("gesundheit", 100))
        belastung = max(0, stress - 60) // 5 + max(0, muskelkater - 45) // 5 + max(0, 35 - energie) // 5
        erholung = max(0, gesundheit - 90) // 10
        return begrenze_prozent(basis + belastung - erholung)
