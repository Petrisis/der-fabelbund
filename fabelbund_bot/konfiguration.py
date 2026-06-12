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


def lade_konfiguration() -> BotKonfiguration:
    return BotKonfiguration(
        token=os.environ.get("DISCORD_TOKEN", ""),
        daten_ordner=Path(os.environ.get("FABELBUND_DATEN_ORDNER", "daten")),
        datenbank_pfad=Path(os.environ.get("FABELBUND_DATENBANK_PFAD", "fabelbund.sqlite3")),
        befehle_synchronisieren=os.environ.get("FABELBUND_BEFEHLE_SYNCHRONISIEREN", "0") == "1",
    )
