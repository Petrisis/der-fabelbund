# Der Fabelbund

Der Fabelbund ist ein Python-Discord-Bot für ein datengetriebenes Sammel- und Managementspiel rund um fiktive Fabelwesen.

Spieler übernehmen die Rolle von Betreuern: Sie pflegen Fabelwesen, nehmen Aufträge an, bauen Ruf auf und schalten später anspruchsvollere Lizenzen, Wettbewerbe, Zuchtlinien und Handel frei.

## Status

Früher MVP. Der spielbare Kern ist bewusst klein gehalten, damit Datenmodell, Persistenz und Discord-Interaktion sauber wachsen können.

Aktuell umgesetzt:

- Discord-Bot-Start mit Slash-Befehlen
- YAML-Inhaltsdaten für Arten, Pflegeaktionen und Aufträge
- Pydantic-Validierung der YAML-Daten
- SQLite-Persistenz
- Spielerprofil mit Geld, Ruf und Lizenzen
- Starter-Fabelwesen
- `/profil`, `/sammlung`, `/auftrag`, `/pflege`
- einfache Pflegeaktion per Button
- einfacher Pflegeauftrag mit Geld- und Rufbelohnung
- GitHub-Pages-Vorbereitung für Rechtstexte

Noch nicht umgesetzt:

- Wettbewerbe
- Zucht
- Eier und Vererbung
- Vertragslogik für fremde Fabelwesen
- Sportwettkämpfe
- Handel und Markt
- Events und Saisons

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
rechtliches/     Rechtliche Markdown-Entwürfe
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

Für die erste Befehlsregistrierung während der Entwicklung:

```powershell
$env:FABELBUND_BEFEHLE_SYNCHRONISIEREN = "1"
$env:FABELBUND_TESTSERVER_ID = "deine Discord-Server-ID"
python -m fabelbund_bot.bot
```

Wenn `FABELBUND_TESTSERVER_ID` gesetzt ist, werden Slash-Befehle nur für diesen Testserver synchronisiert. Das ist für MVP-Tests schneller als eine globale Registrierung.

## Tests

```powershell
python -m pytest
```

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

