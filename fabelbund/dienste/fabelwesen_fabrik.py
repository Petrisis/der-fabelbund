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
            gene=self._würfle_gene(art),
            persönlichkeit=self._würfle_persönlichkeit(art),
            wettbewerbswerte={schlüssel: int(wert) for schlüssel, wert in art.grundwerte.items() if schlüssel in _WETTBEWERBSWERTE},
            sportwerte={schlüssel: int(wert) for schlüssel, wert in art.grundwerte.items() if schlüssel in _SPORTWERTE},
            zustand={
                "gesundheit": 100,
                "stimmung": 68,
                "energie": 72,
                "sättigung": 80,
                "stress": 18,
                "vertrauen": 35,
                "sicherheit": 45,
                "fellpflege": 48,
                "muskelkater": 0,
                "verletzungsrisiko": 4,
            },
            zucht={"fruchtbarkeit": 2, "abklingzeit_bis": None, "zucht_gesperrt": False},
            status={
                "aktiver_vertrag_id": None,
                "nicht_verfügbar_bis": None,
                "zuletzt_versorgt_am": None,
            },
        )

    def _würfle_gene(self, art: ArtDefinition) -> dict[str, str]:
        gene: dict[str, str] = {}
        for gen_name, seltenheits_map in art.genpools.items():
            gewöhnliche_werte = seltenheits_map.get("gewöhnlich") or next(iter(seltenheits_map.values()), [])
            if gewöhnliche_werte:
                gene[gen_name] = random.choice(gewöhnliche_werte)
        return gene

    def _würfle_persönlichkeit(self, art: ArtDefinition) -> dict[str, object]:
        gewichte = art.persönlichkeits_gewichte or {"neugierig": 1}
        temperament = random.choices(list(gewichte), weights=list(gewichte.values()), k=1)[0]
        return {
            "temperament": temperament,
            "mag": ["ruhige_pflege"],
            "mag_nicht": ["übertraining"],
            "stärken": ["harmonie"],
            "schwächen": ["stress"],
            "lieblingsfutter": random.choice(art.lieblingsfutter) if art.lieblingsfutter else None,
        }


_WETTBEWERBSWERTE = {"schönheit", "eleganz", "charme", "intelligenz", "ausdruck", "disziplin", "harmonie"}
_SPORTWERTE = {"stärke", "beweglichkeit", "ausdauer", "technik", "deckung", "kontrolle", "kampfgeist"}
