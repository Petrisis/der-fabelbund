from __future__ import annotations

WETTBEWERBSWERT_SCHLUESSEL = {
    "schoenheit",
    "eleganz",
    "charme",
    "intelligenz",
    "ausdruck",
    "disziplin",
    "harmonie",
}

SPORTWERT_SCHLUESSEL = {
    "staerke",
    "beweglichkeit",
    "ausdauer",
    "technik",
    "deckung",
    "kontrolle",
    "kampfgeist",
}

ZUSTAND_SCHLUESSEL = {
    "gesundheit",
    "stimmung",
    "energie",
    "stress",
    "vertrauen",
    "fellpflege",
    "muskelkater",
    "verletzungsrisiko",
}

RUF_SCHLUESSEL = {
    "pflege",
    "training",
    "zucht",
    "schoenheit",
    "eleganz",
    "sport",
    "zuverlaessigkeit",
    "handel",
}


def begrenze_prozent(wert: int) -> int:
    return max(0, min(100, wert))


def standard_ruf() -> dict[str, int]:
    return {schluessel: 0 for schluessel in RUF_SCHLUESSEL}
