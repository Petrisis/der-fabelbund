from __future__ import annotations

from pathlib import Path
from typing import Any

from fabelbund.modelle.inhalte import ArtDefinition, AuftragDefinition, InhaltsKatalog, PflegeaktionDefinition


class YamlLader:
    def __init__(self, daten_ordner: Path) -> None:
        self.daten_ordner = daten_ordner

    def lade_alle(self) -> InhaltsKatalog:
        return InhaltsKatalog(
            arten=self.lade_arten(),
            pflegeaktionen=self.lade_pflegeaktionen(),
            auftraege=self.lade_auftraege(),
        )

    def lade_arten(self) -> dict[str, ArtDefinition]:
        arten_ordner = self.daten_ordner / "arten"
        arten: dict[str, ArtDefinition] = {}
        for pfad in sorted(arten_ordner.glob("*.yaml")):
            definition = ArtDefinition.model_validate(self._lies_yaml(pfad))
            if definition.art_id in arten:
                raise ValueError(f"Doppelte art_id: {definition.art_id}")
            arten[definition.art_id] = definition
        if not arten:
            raise ValueError(f"Keine Arten-YAML-Dateien gefunden in {arten_ordner}")
        return arten

    def lade_pflegeaktionen(self) -> dict[str, PflegeaktionDefinition]:
        pfad = self.daten_ordner / "aktionen" / "pflege.yaml"
        roh = self._lies_yaml(pfad)
        aktionen: dict[str, PflegeaktionDefinition] = {}
        for aktion_id, nutzlast in roh.get("pflegeaktionen", {}).items():
            definition = PflegeaktionDefinition.model_validate({"aktion_id": aktion_id, **nutzlast})
            aktionen[aktion_id] = definition
        if not aktionen:
            raise ValueError(f"Keine Pflegeaktionen gefunden in {pfad}")
        return aktionen

    def lade_auftraege(self) -> dict[str, AuftragDefinition]:
        pfad = self.daten_ordner / "auftraege" / "pflege.yaml"
        roh = self._lies_yaml(pfad)
        auftraege: dict[str, AuftragDefinition] = {}
        for nutzlast in roh.get("auftraege", []):
            definition = AuftragDefinition.model_validate(nutzlast)
            if definition.auftrag_id in auftraege:
                raise ValueError(f"Doppelte auftrag_id: {definition.auftrag_id}")
            auftraege[definition.auftrag_id] = definition
        if not auftraege:
            raise ValueError(f"Keine Auftraege gefunden in {pfad}")
        return auftraege

    @staticmethod
    def _lies_yaml(pfad: Path) -> dict[str, Any]:
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError("PyYAML wird benoetigt. Installation: pip install -r requirements.txt") from exc

        if not pfad.exists():
            raise FileNotFoundError(pfad)
        with pfad.open("r", encoding="utf-8") as datei:
            daten = yaml.safe_load(datei) or {}
        if not isinstance(daten, dict):
            raise ValueError(f"YAML-Wurzel muss eine Zuordnung sein: {pfad}")
        return daten
