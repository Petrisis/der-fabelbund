from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class BotKonfiguration:
    token: str
    daten_ordner: Path
    datenbank_pfad: Path
    befehle_synchronisieren: bool = False
    testserver_id: int | None = None
    zeitfaktor: float = 1.0


def lade_konfiguration() -> BotKonfiguration:
    lade_umgebungsdatei()
    return BotKonfiguration(
        token=os.environ.get("DISCORD_TOKEN", ""),
        daten_ordner=Path(os.environ.get("FABELBUND_DATEN_ORDNER", "daten")),
        datenbank_pfad=Path(os.environ.get("FABELBUND_DATENBANK_PFAD", "fabelbund.sqlite3")),
        befehle_synchronisieren=os.environ.get("FABELBUND_BEFEHLE_SYNCHRONISIEREN", "0") == "1",
        testserver_id=_optionale_int_umgebung("FABELBUND_TESTSERVER_ID"),
        zeitfaktor=_float_umgebung("FABELBUND_ZEITFAKTOR", 1.0),
    )


def lade_umgebungsdatei(pfad: Path = Path(".env")) -> None:
    if not pfad.exists():
        return
    for zeile in pfad.read_text(encoding="utf-8").splitlines():
        zeile = zeile.strip()
        if not zeile or zeile.startswith("#") or "=" not in zeile:
            continue
        schlüssel, wert = zeile.split("=", 1)
        schlüssel = schlüssel.strip()
        wert = wert.strip().strip("\"'")
        if schlüssel and schlüssel not in os.environ:
            os.environ[schlüssel] = wert


def _optionale_int_umgebung(name: str) -> int | None:
    wert = os.environ.get(name, "").strip()
    if not wert:
        return None
    return int(wert)


def _float_umgebung(name: str, standard: float) -> float:
    wert = os.environ.get(name, "").strip()
    if not wert:
        return standard
    zahl = float(wert.replace(",", "."))
    if zahl <= 0:
        raise ValueError(f"{name} muss größer als 0 sein.")
    return zahl
