from __future__ import annotations

from datetime import datetime, timezone
from pydantic import BaseModel, Field

from fabelbund.modelle.basis import standard_ruf


class SpielerProfil(BaseModel):
    nutzer_id: str
    geld: int = 500
    ruf: dict[str, int] = Field(default_factory=standard_ruf)
    lizenzen: list[str] = Field(default_factory=list)
    erstellt_am: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Fabelwesen(BaseModel):
    id: str
    art_id: str
    spitzname: str
    besitzer_id: str
    betreuer_id: str
    seltenheit: str
    element: str
    lebensraum: str
    herkunft: dict[str, object]
    gene: dict[str, str]
    persönlichkeit: dict[str, object]
    wettbewerbswerte: dict[str, int]
    sportwerte: dict[str, int]
    zustand: dict[str, int]
    zucht: dict[str, object] = Field(default_factory=dict)
    status: dict[str, object] = Field(default_factory=dict)


class AktiverAuftrag(BaseModel):
    id: str
    spieler_id: str
    auftrag_id: str
    fabelwesen_id: str
    status: str = "aktiv"
    fortschritt: dict[str, object] = Field(default_factory=dict)
    gestartet_am: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    abgeschlossen_am: datetime | None = None
