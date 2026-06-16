from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import random
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fabelbund.modelle.laufzeit import Fabelwesen, Wettbewerb, WettbewerbAnmeldung


try:
    BERLIN = ZoneInfo("Europe/Berlin")
except ZoneInfoNotFoundError:
    BERLIN = datetime.now().astimezone().tzinfo or timezone(timedelta(hours=1))
WETTBEWERBSWERTE = ("schönheit", "eleganz", "charme", "intelligenz", "ausdruck", "disziplin", "harmonie")
WETTBEWERB_PREISGELD = 300


@dataclass(frozen=True)
class Wettbewerbsleistung:
    anmeldung: WettbewerbAnmeldung
    fabelwesen: Fabelwesen
    punktzahl: int


def nächster_wettbewerbstermin(jetzt: datetime | None = None) -> datetime:
    jetzt = jetzt or datetime.now(timezone.utc)
    lokal = jetzt.astimezone(BERLIN)
    kandidat = lokal.replace(hour=17, minute=0, second=0, microsecond=0)
    if kandidat <= lokal + timedelta(minutes=30):
        kandidat += timedelta(days=2)
    return kandidat.astimezone(timezone.utc)


def folgetermin(vorheriger_termin: datetime) -> datetime:
    return (vorheriger_termin.astimezone(BERLIN) + timedelta(days=2)).astimezone(timezone.utc)


def wettbewerb_erstellen(guild_id: str, beginnt_am: datetime, wert: str | None = None) -> Wettbewerb:
    if wert is None:
        wert = WETTBEWERBSWERTE[(beginnt_am.toordinal() + int(guild_id[-2:])) % len(WETTBEWERBSWERTE)]
    anmeldeschluss = beginnt_am - timedelta(minutes=30)
    return Wettbewerb(
        id=f"wettbewerb_{uuid4().hex[:12]}",
        guild_id=guild_id,
        wert=wert,
        beginnt_am=beginnt_am,
        anmeldeschluss_am=anmeldeschluss,
        preisgeld=WETTBEWERB_PREISGELD,
    )


def leistungswert(fabelwesen: Fabelwesen, wert: str, zufall: random.Random | None = None) -> int:
    würfel = zufall or random
    basis = int(fabelwesen.wettbewerbswerte.get(wert, 0))
    gesundheit = int(fabelwesen.zustand.get("gesundheit", 100))
    stimmung = int(fabelwesen.zustand.get("stimmung", 50))
    energie = int(fabelwesen.zustand.get("energie", 50))
    stress = int(fabelwesen.zustand.get("stress", 0))
    muskelkater = int(fabelwesen.zustand.get("muskelkater", 0))
    risiko = int(fabelwesen.zustand.get("verletzungsrisiko", 0))

    zustandsanteil = (
        (gesundheit - 70) * 0.06
        + (stimmung - 50) * 0.04
        + (energie - 50) * 0.04
        - max(0, stress - 20) * 0.05
        - muskelkater * 0.04
        - risiko * 0.05
    )
    return max(0, round(basis + zustandsanteil + würfel.randint(-8, 8)))
