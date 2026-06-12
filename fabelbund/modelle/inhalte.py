from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator

from fabelbund.modelle.basis import SPORTWERT_SCHLÜSSEL, WETTBEWERBSWERT_SCHLÜSSEL, ZUSTAND_SCHLÜSSEL


class ArtDefinition(BaseModel):
    art_id: str
    name: str
    grundseltenheit: str
    element: str
    lebensraum: str
    grundwerte: dict[str, int]
    genpools: dict[str, dict[str, list[str]]] = Field(default_factory=dict)
    persönlichkeits_gewichte: dict[str, int] = Field(default_factory=dict)
    wettbewerbs_neigungen: dict[str, float] = Field(default_factory=dict)
    sport_neigungen: dict[str, float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def prüfe_grundwerte(self) -> "ArtDefinition":
        erwartete_schlüssel = WETTBEWERBSWERT_SCHLÜSSEL | SPORTWERT_SCHLÜSSEL
        fehlende_schlüssel = erwartete_schlüssel - set(self.grundwerte)
        if fehlende_schlüssel:
            raise ValueError(f"{self.art_id} hat fehlende Grundwerte: {sorted(fehlende_schlüssel)}")
        return self


class PflegeaktionDefinition(BaseModel):
    aktion_id: str
    name: str
    beschreibung: str = ""
    effekte: dict[str, int]
    markierungen: list[str] = Field(default_factory=list)

    @field_validator("effekte")
    @classmethod
    def prüfe_effekte(cls, effekte: dict[str, int]) -> dict[str, int]:
        unbekannt = set(effekte) - ZUSTAND_SCHLÜSSEL
        if unbekannt:
            raise ValueError(f"Unbekannte Pflegeeffekt-Schlüssel: {sorted(unbekannt)}")
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
    aufträge: dict[str, AuftragDefinition]
