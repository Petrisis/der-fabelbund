# Projektstand Der Fabelbund

Dieses Dokument ist der kurze Kontextanker für neue Arbeitsrunden. Ausführliche Details stehen in `TODO.md`, `planung/stat-übersicht.md` und `planung/auftragsschema.md`.

## Projektregeln

- Alles wird auf Deutsch geschrieben.
- Im Code, in Daten, in sichtbaren Texten und in Dokumenten werden saubere Umlaute verwendet.
- Der Name des Bots und Spiels ist `Der Fabelbund`.
- Fabelwesen heißen offiziell Fabelwesen; im Alltag heißen sie meist Fablinge.
- Zahlenwerte bleiben im Spieltext normalerweise verborgen. Spieler sehen Zustände als Einschätzungen.
- Aufträge prüfen Zielzustände. Aktionen sind Wege zum Ziel, nicht die eigentliche Abgabebedingung.
- Git-Push passiert nur auf ausdrückliche Freigabe.

## Aktueller Meilenstein

Der Stand ist ein Tutorial-MVP. Das Tutorial ist weitgehend spielbar und erklärt:

- Einstieg über die öffentliche Auftragswand
- Leih-Fablinge und Auftragsabgabe
- Fabling- und Stallübersicht
- Pflege, Ruhe, Spiel, Training und Check
- Laden, Inventar und Futterpräferenz
- aktive und passive Betreuung
- Starterwahl und Aufnahme in den Fabelbund

Nach der Starterwahl wird eine Chronikmeldung vorbereitet, damit sichtbar wird, dass ein Spieler offiziell Teil des Fabelbunds geworden ist.

## Bedienphilosophie

Slash Commands bleiben als technische Einstiegspunkte vorhanden, sollen aber im Spielgefühl nicht dominieren. Der Spieler soll nach Möglichkeit über Buttons und Menüs weitergeführt werden.

Wichtige Menüpunkte:

- Auftragswand
- Deine Fablinge
- Laden
- Inventar
- Aktivitätskategorien pro Fabling
- Abholen oder Abbrechen laufender Aktivitäten

Ephemere Ansichten dürfen lange offen bleiben, sind aber nicht unendlich verlässlich. Deshalb muss der Spieler über die Auftragswand und `/fablinge` wieder in den aktuellen Zustand zurückfinden.

## Architektur

- `daten/` enthält datengetriebene Inhalte.
- `fabelbund/modelle/` enthält validierte Datenmodelle.
- `fabelbund/dienste/` enthält Spielregeln und Anwendungslogik.
- `fabelbund/datenbank/` enthält SQLite-Zugriff und Speicherklassen.
- `fabelbund/discord/` enthält Discord-Darstellung, Views und Befehle.
- `tests/` enthält Regressionstests für Spielkern und zentrale Tutorialregeln.

## Testserver

`scripts/start-bot.ps1` startet den Bot aktuell mit:

- `FABELBUND_BEFEHLE_SYNCHRONISIEREN=1`
- `FABELBUND_ZEITFAKTOR=10.0`

Das ist bewusst testserverfreundlich. Später kann der Zeitfaktor wieder gesenkt oder konfigurierbar gemacht werden.

## Nächste technische Prioritäten

1. Tutorial vollständig durchspielen und offene Playtestpunkte glätten.
2. Alle Auftragsabgaben auf Zielzustände prüfen.
3. NPC-Fehlschlaghinweise systematisch einführen.
4. Spielerreset als Skript ergänzen.
5. Erste normale Auftragsauswahl nach dem Tutorial bauen.

## Offene Designentscheidungen

- Wie stark Lieblingsfutter positive und negative Effekte verändern soll.
- Wie dauerhafte Grundbedürfnisse getaktet werden.
- Wie Wettbewerbe konkret heißen, bewertet und freigeschaltet werden.
- Wie frei Spieler nach dem Tutorial zwischen Aufträgen wählen können.
