# Der Fabelbund

Der Fabelbund ist ein Python-Discord-Bot fuer ein datengetriebenes Sammel- und Managementspiel rund um fiktive Fabelwesen.

Spieler uebernehmen die Rolle von Betreuern: Sie pflegen Fabelwesen, nehmen Auftraege an, bauen Ruf auf und schalten spaeter anspruchsvollere Lizenzen, Wettbewerbe, Zuchtlinien und Handel frei.

## Status

Frueher MVP. Der spielbare Kern ist bewusst klein gehalten, damit Datenmodell, Persistenz und Discord-Interaktion sauber wachsen koennen.

Aktuell umgesetzt:

- Discord-Bot-Start mit Slash-Befehlen
- YAML-Inhaltsdaten fuer Arten, Pflegeaktionen und Auftraege
- Pydantic-Validierung der YAML-Daten
- SQLite-Persistenz
- Spielerprofil mit Geld, Ruf und Lizenzen
- Starter-Fabelwesen
- `/profil`, `/sammlung`, `/auftrag`, `/pflege`
- einfache Pflegeaktion per Button
- einfacher Pflegeauftrag mit Geld- und Rufbelohnung
- GitHub-Pages-Vorbereitung fuer Rechtstexte

Noch nicht umgesetzt:

- Wettbewerbe
- Zucht
- Eier und Vererbung
- Vertragslogik fuer fremde Fabelwesen
- Sportwettkaempfe
- Handel und Markt
- Events und Saisons

## Lore-Sprache

Die Organisation spricht offiziell von Fabelwesen. Ausgebildete Betreuer nennen sie meist Fablinge. In Akten kann spaeter eine sachliche Klassifikation wie `FW-Klasse II` verwendet werden.

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
rechtliches/     Rechtliche Markdown-Entwuerfe
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

Fuer die erste Befehlsregistrierung waehrend der Entwicklung:

```powershell
$env:FABELBUND_BEFEHLE_SYNCHRONISIEREN = "1"
python -m fabelbund_bot.bot
```

## Tests

```powershell
python -m pytest
```

## GitHub Pages

Die GitHub-Pages-Quelle liegt in `docs/`.

Vorgesehene oeffentliche Links:

- Nutzungsbedingungen: `https://petrisis.github.io/der-fabelbund/nutzungsbedingungen/`
- Datenschutzerklaerung: `https://petrisis.github.io/der-fabelbund/datenschutzerklaerung/`

Vor der Verwendung im Discord Developer Portal muessen Betreibername, Kontaktadresse und Support-Link in den Rechtstexten ersetzt werden.

## Oeffentliches Repo

Das Bot-Token gehoert ausschliesslich in `.env`. Diese Datei ist durch `.gitignore` ausgeschlossen und darf nicht committed werden.

Vor dem Umschalten auf `public` sollte die Git-Historie bereinigt werden, damit keine alten Arbeitstitel oder internen Zwischenstaende sichtbar bleiben.

## Entwicklung

Empfohlener Ablauf:

- `main` bleibt der stabile Stand
- neue Systeme kommen in kleinen Feature-Branches
- jede Aenderung wird mit Tests abgesichert
- Inhalte bleiben datengetrieben in YAML
- persistente Spielstaende gehoeren in die Datenbank, nicht in YAML

