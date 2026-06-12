from __future__ import annotations

import random
from uuid import uuid4

from fabelbund.modelle.inhalte import ArtDefinition
from fabelbund.modelle.laufzeit import Fabelwesen


class FabelwesenFabrik:
    def erzeuge_starter(self, besitzer_id: str, art: ArtDefinition) -> Fabelwesen:
        return Fabelwesen(
            id=f"fw_{uuid4().hex[:12]}",
            art_id=art.art_id,
            spitzname=art.name,
            besitzer_id=besitzer_id,
            betreuer_id=besitzer_id,
            seltenheit=art.grundseltenheit,
            element=art.element,
            lebensraum=art.lebensraum,
            herkunft={"methode": "starter", "generation": 1, "eltern": []},
            gene=self._wuerfle_gene(art),
            persoenlichkeit=self._wuerfle_persoenlichkeit(art),
            wettbewerbswerte={schluessel: int(wert) for schluessel, wert in art.grundwerte.items() if schluessel in _WETTBEWERBSWERTE},
            sportwerte={schluessel: int(wert) for schluessel, wert in art.grundwerte.items() if schluessel in _SPORTWERTE},
            zustand={
                "gesundheit": 100,
                "stimmung": 68,
                "energie": 72,
                "stress": 18,
                "vertrauen": 35,
                "fellpflege": 48,
                "muskelkater": 0,
                "verletzungsrisiko": 4,
            },
            zucht={"fruchtbarkeit": 2, "abklingzeit_bis": None, "zucht_gesperrt": False},
            status={"aktiver_vertrag_id": None, "nicht_verfuegbar_bis": None},
        )

    def _wuerfle_gene(self, art: ArtDefinition) -> dict[str, str]:
        gene: dict[str, str] = {}
        for gen_name, seltenheits_map in art.genpools.items():
            gewoehnliche_werte = seltenheits_map.get("gewoehnlich") or next(iter(seltenheits_map.values()), [])
            if gewoehnliche_werte:
                gene[gen_name] = random.choice(gewoehnliche_werte)
        return gene

    def _wuerfle_persoenlichkeit(self, art: ArtDefinition) -> dict[str, object]:
        gewichte = art.persoenlichkeits_gewichte or {"neugierig": 1}
        temperament = random.choices(list(gewichte), weights=list(gewichte.values()), k=1)[0]
        return {
            "temperament": temperament,
            "mag": ["ruhige_pflege"],
            "mag_nicht": ["uebertraining"],
            "staerken": ["harmonie"],
            "schwaechen": ["stress"],
        }


_WETTBEWERBSWERTE = {"schoenheit", "eleganz", "charme", "intelligenz", "ausdruck", "disziplin", "harmonie"}
_SPORTWERTE = {"staerke", "beweglichkeit", "ausdauer", "technik", "deckung", "kontrolle", "kampfgeist"}
