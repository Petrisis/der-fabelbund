from __future__ import annotations

from datetime import datetime, timezone
from pydantic import BaseModel, Field

from fabelbund.modelle.basis import standard_ruf


class SpielerProfil(BaseModel):
    nutzer_id: str
    geld: int = 0
    freigeschaltete_ställe: int = Field(default=1, ge=1)
    stalltypen: dict[str, int] = Field(default_factory=lambda: {"neutral": 1})
    inventar: dict[str, object] = Field(default_factory=dict)
    ruf: dict[str, int] = Field(default_factory=standard_ruf)
    lizenzen: list[str] = Field(default_factory=list)
    tutorialstatus: str = "neu"
    tutorialschritt: str = "registrierung"
    tutorialpfad: str | None = None
    offizielles_mitglied: bool = False
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


class Aktivität(BaseModel):
    id: str
    spieler_id: str
    fabelwesen_id: str
    art: str
    aktion_id: str
    name: str
    kategorie: str = "pflege"
    intensität: str = "mittel"
    braucht_spieler: bool
    abbrechbar: bool = True
    status: str = "läuft"
    effekte: dict[str, int] = Field(default_factory=dict)
    wettbewerb_effekte: dict[str, int] = Field(default_factory=dict)
    sport_effekte: dict[str, int] = Field(default_factory=dict)
    abbruch_effekte: dict[str, int] = Field(default_factory=dict)
    folgeaktionen: list[str] = Field(default_factory=list)
    gestartet_am: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    endet_am: datetime
    beendet_am: datetime | None = None


class ServerKonfiguration(BaseModel):
    guild_id: str
    eingerichtet: bool = False
    kategorie_id: str | None = None
    aufträge_kanal_id: str | None = None
    chronik_kanal_id: str | None = None
    events_kanal_id: str | None = None
    einstieg_nachricht_id: str | None = None
    auftragswand_nachricht_id: str | None = None
    eingerichtet_am: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    aktualisiert_am: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
