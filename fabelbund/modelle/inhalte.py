from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator

from fabelbund.modelle.basis import SPORTWERT_SCHLUESSEL, WETTBEWERBSWERT_SCHLUESSEL, ZUSTAND_SCHLUESSEL


class ArtDefinition(BaseModel):
    art_id: str
    name: str
    grundseltenheit: str
    element: str
    lebensraum: str
    grundwerte: dict[str, int]
    genpools: dict[str, dict[str, list[str]]] = Field(default_factory=dict)
    persoenlichkeits_gewichte: dict[str, int] = Field(default_factory=dict)
    wettbewerbs_neigungen: dict[str, float] = Field(default_factory=dict)
    sport_neigungen: dict[str, float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def pruefe_grundwerte(self) -> "ArtDefinition":
        erwartete_schluessel = WETTBEWERBSWERT_SCHLUESSEL | SPORTWERT_SCHLUESSEL
        fehlende_schluessel = erwartete_schluessel - set(self.grundwerte)
        if fehlende_schluessel:
            raise ValueError(f"{self.art_id} hat fehlende Grundwerte: {sorted(fehlende_schluessel)}")
        return self


class PflegeaktionDefinition(BaseModel):
    aktion_id: str
    name: str
    beschreibung: str = ""
    effekte: dict[str, int]
    markierungen: list[str] = Field(default_factory=list)

    @field_validator("effekte")
    @classmethod
    def pruefe_effekte(cls, effekte: dict[str, int]) -> dict[str, int]:
        unbekannt = set(effekte) - ZUSTAND_SCHLUESSEL
        if unbekannt:
            raise ValueError(f"Unbekannte Pflegeeffekt-Schluessel: {sorted(unbekannt)}")
        return effekte


class AuftragDefinition(BaseModel):
    auftrag_id: str
    name: str
    art: str
    dauer_tage: int = Field(gt=0)
    voraussetzungen: dict[str, object] = Field(default_factory=dict)
    ziele: dict[str, object]
    belohnungen: dict[str, object]
    fehlschlag: dict[str, object] = Field(default_factory=dict)


class InhaltsKatalog(BaseModel):
    arten: dict[str, ArtDefinition]
    pflegeaktionen: dict[str, PflegeaktionDefinition]
    auftraege: dict[str, AuftragDefinition]
