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
    kategorie: str = "pflege"
    intensität: str = "mittel"
    effekte: dict[str, int] = Field(default_factory=dict)
    wettbewerb_effekte: dict[str, int] = Field(default_factory=dict)
    sport_effekte: dict[str, int] = Field(default_factory=dict)
    abbruch_effekte: dict[str, int] = Field(default_factory=dict)
    dauer_sekunden: int = Field(default=180, ge=0)
    braucht_spieler: bool = True
    abbrechbar: bool = True
    gesperrt: bool = False
    markierungen: list[str] = Field(default_factory=list)

    @field_validator("effekte")
    @classmethod
    def prüfe_effekte(cls, effekte: dict[str, int]) -> dict[str, int]:
        unbekannt = set(effekte) - ZUSTAND_SCHLÜSSEL
        if unbekannt:
            raise ValueError(f"Unbekannte Pflegeeffekt-Schlüssel: {sorted(unbekannt)}")
        return effekte

    @field_validator("wettbewerb_effekte")
    @classmethod
    def prüfe_wettbewerb_effekte(cls, effekte: dict[str, int]) -> dict[str, int]:
        unbekannt = set(effekte) - WETTBEWERBSWERT_SCHLÜSSEL
        if unbekannt:
            raise ValueError(f"Unbekannte Wettbewerbseffekt-Schlüssel: {sorted(unbekannt)}")
        return effekte

    @field_validator("sport_effekte")
    @classmethod
    def prüfe_sport_effekte(cls, effekte: dict[str, int]) -> dict[str, int]:
        unbekannt = set(effekte) - SPORTWERT_SCHLÜSSEL
        if unbekannt:
            raise ValueError(f"Unbekannte Sporteffekt-Schlüssel: {sorted(unbekannt)}")
        return effekte

    @field_validator("abbruch_effekte")
    @classmethod
    def prüfe_abbruch_effekte(cls, effekte: dict[str, int]) -> dict[str, int]:
        unbekannt = set(effekte) - ZUSTAND_SCHLÜSSEL
        if unbekannt:
            raise ValueError(f"Unbekannte Abbrucheffekt-Schlüssel: {sorted(unbekannt)}")
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


class GegenstandDefinition(BaseModel):
    gegenstand_id: str
    name: str
    kategorie: str
    preis: int = Field(ge=0)
    beschreibung: str = ""
    effekte: dict[str, int] = Field(default_factory=dict)
    markierungen: list[str] = Field(default_factory=list)

    @field_validator("effekte")
    @classmethod
    def prüfe_effekte(cls, effekte: dict[str, int]) -> dict[str, int]:
        unbekannt = set(effekte) - ZUSTAND_SCHLÜSSEL
        if unbekannt:
            raise ValueError(f"Unbekannte Gegenstandseffekt-Schlüssel: {sorted(unbekannt)}")
        return effekte


class InhaltsKatalog(BaseModel):
    arten: dict[str, ArtDefinition]
    pflegeaktionen: dict[str, PflegeaktionDefinition]
    aufträge: dict[str, AuftragDefinition]
    gegenstände: dict[str, GegenstandDefinition]
