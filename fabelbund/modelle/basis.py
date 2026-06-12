from __future__ import annotations

WETTBEWERBSWERT_SCHLÜSSEL = {
    "schönheit",
    "eleganz",
    "charme",
    "intelligenz",
    "ausdruck",
    "disziplin",
    "harmonie",
}

SPORTWERT_SCHLÜSSEL = {
    "stärke",
    "beweglichkeit",
    "ausdauer",
    "technik",
    "deckung",
    "kontrolle",
    "kampfgeist",
}

ZUSTAND_SCHLÜSSEL = {
    "gesundheit",
    "stimmung",
    "energie",
    "stress",
    "vertrauen",
    "fellpflege",
    "muskelkater",
    "verletzungsrisiko",
}

RUF_SCHLÜSSEL = {
    "pflege",
    "training",
    "zucht",
    "schönheit",
    "eleganz",
    "sport",
    "zuverlässigkeit",
    "handel",
}


def begrenze_prozent(wert: int) -> int:
    return max(0, min(100, wert))


def standard_ruf() -> dict[str, int]:
    return {schlüssel: 0 for schlüssel in RUF_SCHLÜSSEL}
