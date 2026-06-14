# Der Fabelbund

![Der Fabelbund Logo](docs/assets/fabelbund-logo.png)

Der Fabelbund ist ein Python-Discord-Bot für ein datengetriebenes Sammel- und Managementspiel rund um fiktive Fabelwesen.

Spieler übernehmen die Rolle von Betreuern: Sie pflegen Fabelwesen, nehmen Aufträge an, bauen Ruf auf und schalten später anspruchsvollere Lizenzen, Wettbewerbe, Zuchtlinien und Handel frei.

## Status

Tutorial-MVP. Der aktuelle Stand ist auf einen spielbaren Einstieg, eine stabile Testumgebung und saubere Grundlagen für weitere Aufträge ausgerichtet.

Aktuell umgesetzt:

- Discord-Bot-Start mit serverbezogener Slash-Command-Synchronisierung
- öffentliche Auftragswand mit dauerhaftem Tutorial-Einstieg
- Pflicht-Tutorial mit Probe-Fablingen, Auftragsabgabe und Starterwahl
- Chronik- und Auftragskanäle mit automatischer Servereinrichtung
- YAML-Inhaltsdaten für Arten, Aktionen, Gegenstände und Aufträge
- Pydantic-Validierung der Inhaltsdaten
- SQLite-Persistenz
- Spielerprofil mit Bundsiegeln, Ruf, Lizenzen, Ställen und Tutorialstatus
- Fabling- und Stallübersicht über `/fablinge`
- Fabling-Detailansicht mit Stallpriorität, Futterpräferenz und Aktivitätsauswahl
- Pflege, Ruhe, Spiel, Training und Checks als erste Betreuungsaktivitäten
- aktive und passive Aktivitäten mit Abholen, Abbrechen und Zeitfaktor
- Laden, Inventar, Futter und erste Ausrüstung
- zustandsbasierte Auftragsziele als Zielarchitektur
- GitHub-Pages-Vorbereitung für Rechtstexte
- Windows-Skripte zum Starten und Beenden des Testbots

Noch nicht umgesetzt oder noch nicht final:

- vollständige Migration aller Auftragsprüfungen auf Zielzustände
- systematische NPC-Hinweise bei nicht erfüllten Aufträgen
- freie Auftragsauswahl nach dem Tutorial
- Wettbewerbe
- Zucht
- Eier und Vererbung
- Vertragslogik für fremde Fabelwesen
- Handel und Markt
- Events und Saisons
- dauerhaftes Grundbedürfnis- und Lieblingsfutter-System

## Lore-Sprache

Die Organisation spricht offiziell von Fabelwesen. Ausgebildete Betreuer nennen sie meist Fablinge. In Akten kann später eine sachliche Klassifikation wie `FW-Klasse II` verwendet werden.

## Projektstruktur

```text
fabelbund/
  modelle/       Datenmodelle und Validierung
  dienste/       Spielregeln und Anwendungslogik
  datenbank/     SQLite-Zugriff und Speicherklassen
  discord/       Slash-Befehle, Ansichten und Darstellung

fabelbund_bot/   Bot-Start und Konfiguration
daten/           YAML-Inhalte
docs/            GitHub-Pages-Quelle
planung/         Balancing, Schemas und Projektstand
rechtliches/     Rechtliche Markdown-Entwürfe
scripts/         lokale Betriebs- und Testskripte
tests/           Automatisierte Tests
```

## Lokales Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Setze danach `DISCORD_TOKEN` in `.env` oder in deiner Shell-Umgebung.

```powershell
python -m fabelbund_bot.bot
```

Alternativ kann der Bot unter Windows manuell über die Projektskripte gestartet und beendet werden:

```powershell
.\scripts\start-bot.ps1
.\scripts\stop-bot.ps1
```

`start-bot.ps1` startet den Bot im Hintergrund und schreibt nach `bot.log` und `bot.err`. Im aktuellen Entwicklungsstand setzt das Skript automatisch `FABELBUND_BEFEHLE_SYNCHRONISIEREN=1` und `FABELBUND_ZEITFAKTOR=10.0`, damit der Bot auf dem konfigurierten Testserver mit zehnfachem Spieltempo läuft. Für einen sichtbaren Vordergrundstart:

```powershell
.\scripts\start-bot.ps1 -Vordergrund
```

Wenn bereits eine Bot-Instanz läuft, startet `start-bot.ps1` keine zweite Instanz. `stop-bot.ps1` beendet alle laufenden `fabelbund_bot.bot`-Prozesse. Unter Windows können dabei ein Hauptprozess und ein zugehöriger Python-Kindprozess angezeigt werden; das ist kein zweiter Bot.

Für einen vollständigen Reset der Spielerdaten auf dem Testserver:

```powershell
.\scripts\spieler-reset.ps1 -Bestätigen
```

Das Skript löscht Spieler, Fablinge, aktive Aufträge und Aktivitäten. Server-Konfigurationen bleiben erhalten.

Für die erste Befehlsregistrierung während der Entwicklung:

```powershell
$env:FABELBUND_BEFEHLE_SYNCHRONISIEREN = "1"
$env:FABELBUND_TESTSERVER_ID = "deine Discord-Server-ID"
python -m fabelbund_bot.bot
```

Wenn `FABELBUND_TESTSERVER_ID` gesetzt ist, werden Slash-Befehle nur für diesen Testserver synchronisiert. Das ist für MVP-Tests schneller als eine globale Registrierung.

Für schnelle Tests kann `FABELBUND_ZEITFAKTOR` gesetzt werden. Der Faktor wirkt linear: Bei `100` dauert eine Aktion mit 10 Minuten Spielzeit real etwa 6 Sekunden.

## Tests

```powershell
python -m pytest
python -m compileall fabelbund fabelbund_bot tests
```

## Planung

- [TODO.md](TODO.md) ist die laufende Arbeitsliste.
- [planung/projektstand.md](planung/projektstand.md) hält Projektregeln, aktuellen Stand und nächste Blöcke fest.
- [planung/stat-übersicht.md](planung/stat-übersicht.md) beschreibt interne Werte und Balancing-Grundlagen.
- [planung/auftragsschema.md](planung/auftragsschema.md) ist die verbindliche Regel für neue Aufträge.
- [planung/lore-und-narrativer-stil.md](planung/lore-und-narrativer-stil.md) beschreibt Setting, Begriffe und Erzählstil.
- [planung/fabling-generierung.md](planung/fabling-generierung.md) erklärt die Erzeugung neuer Fablinge und ihre Wertebereiche.
- [docs/issue-workflow.md](docs/issue-workflow.md) beschreibt, wie GitHub-Issues bearbeitet und geschlossen werden.

## GitHub Pages

Die GitHub-Pages-Quelle liegt in `docs/`.

Vorgesehene öffentliche Links:

- Nutzungsbedingungen: `https://petrisis.github.io/der-fabelbund/nutzungsbedingungen/`
- Datenschutz: `https://petrisis.github.io/der-fabelbund/datenschutz/`

Vor der Verwendung im Discord Developer Portal müssen Betreibername, Kontaktadresse und Support-Link in den Rechtstexten ersetzt werden.

## Öffentliches Repo

Das Bot-Token gehört ausschließlich in `.env`. Diese Datei ist durch `.gitignore` ausgeschlossen und darf nicht committed werden.

Vor dem Umschalten auf `public` sollte die Git-Historie bereinigt werden, damit keine alten Arbeitstitel oder internen Zwischenstände sichtbar bleiben.

## Entwicklung

Empfohlener Ablauf:

- `main` bleibt der stabile Stand
- neue Systeme kommen in kleinen Feature-Branches
- jede Änderung wird mit Tests abgesichert
- Inhalte bleiben datengetrieben in YAML
- persistente Spielstände gehören in die Datenbank, nicht in YAML
- neue Aufträge prüfen Zielzustände, nicht bloß abgeschlossene Aktionen
