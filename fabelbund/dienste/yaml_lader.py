from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from fabelbund.modelle.inhalte import ArtDefinition, AuftragDefinition, GegenstandDefinition, InhaltsKatalog, PflegeaktionDefinition


class YamlLader:
    def __init__(self, daten_ordner: Path) -> None:
        self.daten_ordner = daten_ordner

    def lade_alle(self) -> InhaltsKatalog:
        return InhaltsKatalog(
            arten=self.lade_arten(),
            pflegeaktionen=self.lade_pflegeaktionen(),
            aufträge=self.lade_aufträge(),
            gegenstände=self.lade_gegenstände(),
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

    def lade_aufträge(self) -> dict[str, AuftragDefinition]:
        pfad = self.daten_ordner / "aufträge" / "pflege.yaml"
        roh = self._lies_yaml(pfad)
        aufträge: dict[str, AuftragDefinition] = {}
        for nutzlast in roh.get("aufträge", []):
            for variante in self._auftragsvarianten(nutzlast):
                definition = AuftragDefinition.model_validate(variante)
                if definition.auftrag_id in aufträge:
                    raise ValueError(f"Doppelte auftrag_id: {definition.auftrag_id}")
                aufträge[definition.auftrag_id] = definition
        if not aufträge:
            raise ValueError(f"Keine Aufträge gefunden in {pfad}")
        return aufträge

    @classmethod
    def _auftragsvarianten(cls, nutzlast: dict[str, Any]) -> list[dict[str, Any]]:
        if not nutzlast.get("öffentlich") or nutzlast.get("art") == "tutorial":
            return [nutzlast]
        varianten = []
        for stunden, suffix, ziel_delta, belohnungsfaktor, gewicht_delta in (
            (1, "", 0, 1.0, 0),
            (3, "_3h", 5, 1.6, -1),
            (5, "_5h", 9, 2.1, -2),
        ):
            variante = deepcopy(nutzlast)
            basis_id = str(variante["auftrag_id"])
            variante["auftrag_id"] = f"{basis_id}{suffix}"
            variante["name"] = f"{variante['name']} ({stunden}h)"
            variante["dauer_stunden"] = stunden
            variante["aushang_gewicht"] = max(1, int(variante.get("aushang_gewicht", 0)) + gewicht_delta)
            variante["ziele"] = cls._ziele_skalieren(variante.get("ziele", {}), ziel_delta, stunden)
            variante["ziele"]["betreuungsdauer_sekunden"] = stunden * 3600
            variante["belohnungen"] = cls._belohnungen_skalieren(variante.get("belohnungen", {}), belohnungsfaktor)
            varianten.append(variante)
        return varianten

    @classmethod
    def _ziele_skalieren(cls, ziele: dict[str, Any], ziel_delta: int, stunden: int) -> dict[str, Any]:
        skaliert = deepcopy(ziele)
        if ziel_delta <= 0:
            return skaliert
        for schlüssel, wert in list(skaliert.items()):
            if schlüssel == "fabling_ziele" and isinstance(wert, list):
                skaliert[schlüssel] = [
                    cls._ziele_skalieren(eintrag, ziel_delta, stunden) if isinstance(eintrag, dict) else eintrag
                    for eintrag in wert
                ]
            elif schlüssel == "wettbewerb_mindestens" and isinstance(wert, dict):
                skaliert[schlüssel] = {
                    ziel: min(100, int(anforderung) + ziel_delta)
                    for ziel, anforderung in wert.items()
                }
            elif schlüssel.endswith("_mindestens") and isinstance(wert, int):
                skaliert[schlüssel] = min(100, wert + ziel_delta)
            elif schlüssel.endswith("_höchstens") and isinstance(wert, int):
                skaliert[schlüssel] = max(0, wert - max(2, ziel_delta // 2))
        return skaliert

    @staticmethod
    def _belohnungen_skalieren(belohnungen: dict[str, Any], faktor: float) -> dict[str, Any]:
        skaliert = deepcopy(belohnungen)
        if "geld" in skaliert:
            skaliert["geld"] = int(round(int(skaliert["geld"]) * faktor))
        ruf = skaliert.get("ruf")
        if isinstance(ruf, dict):
            skaliert["ruf"] = {
                schlüssel: max(int(wert), int(round(int(wert) * (1 + (faktor - 1) * 0.5))))
                for schlüssel, wert in ruf.items()
            }
        return skaliert

    def lade_gegenstände(self) -> dict[str, GegenstandDefinition]:
        ordner = self.daten_ordner / "gegenstände"
        gegenstände: dict[str, GegenstandDefinition] = {}
        for pfad in sorted(ordner.glob("*.yaml")):
            roh = self._lies_yaml(pfad)
            for gegenstand_id, nutzlast in roh.get("gegenstände", {}).items():
                definition = GegenstandDefinition.model_validate({"gegenstand_id": gegenstand_id, **nutzlast})
                if definition.gegenstand_id in gegenstände:
                    raise ValueError(f"Doppelter gegenstand_id: {definition.gegenstand_id}")
                gegenstände[definition.gegenstand_id] = definition
        if not gegenstände:
            raise ValueError(f"Keine Gegenstände gefunden in {ordner}")
        return gegenstände

    @staticmethod
    def _lies_yaml(pfad: Path) -> dict[str, Any]:
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError("PyYAML wird benötigt. Installation: pip install -r requirements.txt") from exc

        if not pfad.exists():
            raise FileNotFoundError(pfad)
        with pfad.open("r", encoding="utf-8") as datei:
            daten = yaml.safe_load(datei) or {}
        if not isinstance(daten, dict):
            raise ValueError(f"YAML-Wurzel muss eine Zuordnung sein: {pfad}")
        return daten
