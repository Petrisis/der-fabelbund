# Fabling-Generierung

Dieses Dokument erklärt anderen Agenten, wie neue Fablinge für **Der Fabelbund** entworfen und als Inhaltsdaten vorbereitet werden. Es beschreibt den aktuellen Ist-Zustand des Codes und die gewünschten Spannweiten für neue Arten.

## Ziel

Neue Fablinge sollen spielerisch unterscheidbar, erzählerisch greifbar und technisch kompatibel sein. Eine neue Art braucht:

- eine klare Rolle in der Welt
- ein Element und einen Lebensraum
- Grundwerte für Wettbewerbe und Sport
- Genpools für sichtbare Varianten
- Persönlichkeitsgewichte
- Neigungen, die spätere Trainings- und Wettbewerbsprofile stützen
- passende Vorlieben, Abneigungen, Stärken, Schwächen und Gewohnheiten

## Speicherort

Arten liegen als YAML-Dateien unter:

```text
daten/arten/
```

Eine Datei beschreibt genau eine Art.

## Aktuelle YAML-Struktur

```yaml
art_id: "beispielart"
name: "Beispielart"
grundseltenheit: "gewöhnlich"
element: "wald"
lebensraum: "mooswald"

grundwerte:
  schönheit: 40
  eleganz: 45
  charme: 35
  intelligenz: 42
  ausdruck: 38
  disziplin: 34
  harmonie: 48
  stärke: 25
  beweglichkeit: 50
  ausdauer: 36
  technik: 40
  deckung: 24
  kontrolle: 35
  kampfgeist: 30

genpools:
  farben:
    gewöhnlich: ["moosgrün", "rindenbraun"]
    selten: ["silberblatt"]
  muster:
    gewöhnlich: ["einfarbig", "gefleckt"]
    selten: ["rankenmale"]

persönlichkeits_gewichte:
  scheu: 30
  neugierig: 25
  treu: 20
  wild: 10
  stolz: 15

wettbewerbs_neigungen:
  schönheit: 1.1
  eleganz: 1.2
  harmonie: 1.0

sport_neigungen:
  beweglichkeit: 1.2
  technik: 1.1
  stärke: 0.8
```

Alle Schlüssel müssen Deutsch mit sauberen Umlauten sein.

## Pflichtfelder

### `art_id`

Technischer Schlüssel in Kleinschreibung. Aktuell verwenden wir einfache deutsche Namen ohne Leerzeichen.

Beispiele:

- `gluthase`
- `moosluchs`
- `quellfink`

### `name`

Sichtbarer Artname. Der Name muss als Fabling-Art funktionieren und sollte nicht nach einer bloßen Tierkopie klingen. Gute Namen verbinden ein Naturmotiv mit einer vertrauten Tierform.

Beispiele:

- Gluthase
- Moosluchs
- Quellfink

### `grundseltenheit`

Aktuelle Werte:

- `gewöhnlich`
- `selten`
- `episch`, vorbereitet, sparsam verwenden

Für MVP-Content bevorzugt `gewöhnlich` und `selten`.

### `element`

Das Element beeinflusst später Stalltypen, Futterlogik, Texte und mögliche Aktionen.

Aktuell vorhanden:

- `glut`
- `wald`
- `wasser`

Weitere Elemente sind möglich, sollten aber erst eingeführt werden, wenn Stalltypen, Texte und Aktionen dafür geplant sind.

### `lebensraum`

Freier, aber konsistenter Schlüssel für die natürliche Umgebung.

Beispiele:

- `warmfeld`
- `mooswald`
- `bachufer`

## Grundwerte

Grundwerte sind interne Startwerte für Trainings- und Wettbewerbsprofile. Sie sind keine Zustandswerte und werden Spielern normalerweise nicht als Rohzahlen gezeigt.

Alle neuen Arten müssen alle folgenden Werte setzen.

### Wettbewerbswerte

- `schönheit`
- `eleganz`
- `charme`
- `intelligenz`
- `ausdruck`
- `disziplin`
- `harmonie`

### Sportwerte

- `stärke`
- `beweglichkeit`
- `ausdauer`
- `technik`
- `deckung`
- `kontrolle`
- `kampfgeist`

## Empfohlene Wertebereiche

Der aktuelle Content liegt ungefähr zwischen `20` und `58`. Neue MVP-Arten sollten in diesem Rahmen bleiben, damit sie nicht sofort alte Arten verdrängen.

### Allgemeine Skala

| Bereich | Bedeutung |
| --- | --- |
| 15-24 | klare Schwäche |
| 25-34 | unterdurchschnittlich |
| 35-44 | solide Basis |
| 45-54 | natürliche Stärke |
| 55-62 | deutliche Spezialität |
| 63+ | vorerst vermeiden, nur für spätere seltene Arten |

### Balancing-Regeln

- Gewöhnliche Arten: meist `20-56`.
- Seltene Arten: meist `25-60`, aber nicht überall besser.
- Eine Art soll 2-4 erkennbare Stärken haben.
- Eine Art soll 2-4 erkennbare Schwächen haben.
- Keine MVP-Art soll in mehr als einem Wert über `60` liegen.
- Durchschnittliche Summe soll grob mit bestehenden Arten vergleichbar bleiben.

Bestehende Profile:

- Gluthase: beweglich, charmant, kämpferisch, aber wenig diszipliniert und schwach in Deckung.
- Moosluchs: elegant, beweglich, technisch brauchbar, aber körperlich eher schwach.
- Quellfink: beweglich, harmonisch, elegant, aber wenig stark und wenig kämpferisch.

## Zustandswerte

Zustandswerte liegen immer auf einer internen `0-100`-Skala. Sie beschreiben den aktuellen Zustand eines konkreten Fablings, nicht die Art an sich.

Aktuelle Zustandswerte:

- `gesundheit`
- `stimmung`
- `energie`
- `sättigung`
- `stress`
- `vertrauen`
- `sicherheit`
- `fellpflege`
- `muskelkater`
- `verletzungsrisiko`

Standardwerte bei neu erzeugten Starter-Fablingen:

```yaml
gesundheit: 100
stimmung: 68
energie: 72
sättigung: 80
stress: 18
vertrauen: 35
sicherheit: 45
fellpflege: 48
muskelkater: 0
verletzungsrisiko: 4
```

Auftrags-Fablinge dürfen davon abweichen. Auftragstexte sollen dann aus dem Ist-Zustand ein klares Problem und aus dem Soll-Zustand ein klares Ziel machen.

## Genpools

Genpools definieren sichtbare Varianten. Aktuell würfelt die Fabrik pro Genpool nur aus `gewöhnlich`; seltene Varianten sind vorbereitet, aber noch nicht vollständig ausgespielt.

Empfohlene Genpools:

- `farben`
- `muster`

Optional später:

- `augen`
- `hornform`
- `schwanzform`
- `fellstruktur`
- `flügel`

Regeln:

- Gewöhnliche Varianten müssen bodenständig und häufig wirken.
- Seltene Varianten dürfen auffallen, aber nicht wie Endgame-Belohnungen wirken.
- Epische Varianten sparsam verwenden.
- Namen bleiben kurz und deutsch.

Gute Beispiele:

- `kohle`
- `glutrot`
- `moosgrün`
- `rindenbraun`
- `bachblau`
- `kieselgrau`

## Persönlichkeit

Aktuell wird genau ein `temperament` aus `persönlichkeits_gewichte` gewürfelt. Die Gewichte sind relative Wahrscheinlichkeiten.

Vorhandene Temperamente:

- `neugierig`
- `treu`
- `wild`
- `stolz`
- `scheu`

Empfehlung:

- Pro Art 4-5 Temperamente gewichten.
- Ein Haupttemperament darf bei `30-40` liegen.
- Nebenvarianten liegen meist bei `10-25`.
- Die Summe muss nicht 100 sein, sollte aber gut lesbar bleiben.

### Temperament-Leitlinien

`neugierig`
: Lernt gerne, lässt sich eher auf Checks, Spiel und neue Reize ein.

`treu`
: Reagiert gut auf wiederholte Betreuung, Verlässlichkeit und ruhige Routinen.

`wild`
: Braucht Bewegung, kann auf zu enge Kontrolle oder Langeweile schlechter reagieren.

`stolz`
: Mag klare Aufgaben und sichtbare Erfolge, reagiert empfindlicher auf chaotische Behandlung.

`scheu`
: Braucht Sicherheit, Ruhe und langsame Annäherung; Stress sollte bei dieser Art wichtiger sein.

## Eigenschaften und Habits

Der Code erzeugt aktuell folgende Persönlichkeitsfelder:

```python
{
    "temperament": "...",
    "mag": ["ruhige_pflege"],
    "mag_nicht": ["übertraining"],
    "stärken": ["harmonie"],
    "schwächen": ["stress"],
}
```

Diese Felder sind vorbereitet und sollen künftig artspezifischer werden. Neue Arten sollen deshalb schon in der Planung passende Einträge bekommen, auch wenn die Fabrik sie noch nicht vollständig aus YAML übernimmt.

### Vorlieben

Vorlieben sind Dinge, die ein Fabling gerne annimmt. Sie sollen Verhalten erklären, nicht reine Boni sein.

Beispiele:

- `ruhige_pflege`
- `kurze_spiele`
- `wassergeräusche`
- `warme_liegeplätze`
- `strukturierte_übungen`
- `weiche_bürsten`

### Abneigungen

Abneigungen beschreiben Reize oder Betreuung, die Stress, Misstrauen oder schlechtere Kooperation auslösen können.

Beispiele:

- `übertraining`
- `laute_umgebung`
- `hektische_pflege`
- `nasse_kälte`
- `enge_räume`
- `zu_viele_wiederholungen`

### Stärken

Stärken sind natürliche Vorteile. Sie müssen zu den Grundwerten passen.

Beispiele:

- `harmonie`
- `beweglichkeit`
- `ausdruck`
- `technik`
- `ausdauer`

### Schwächen

Schwächen sind natürliche Schwierigkeiten oder empfindliche Bereiche.

Beispiele:

- `stress`
- `deckung`
- `disziplin`
- `stärke`
- `muskelkater`

### Habits

Habits sind wiedererkennbare Gewohnheiten, die später Textvariation, Aufträge oder Ereignisse beeinflussen können.

Beispiele:

- ruht erst, wenn die Umgebung still ist
- sucht nach Wasserstellen
- versteckt Pflegewerkzeug
- sammelt kleine glänzende Dinge
- läuft vor dem Schlafen feste Runden
- beobachtet neue Betreuer lange aus der Entfernung

Habits sollen nicht bloß niedlich sein. Sie sollen spielerisch andeuten, welche Betreuung passt.

## Lieblingsleckerli

Das Feld `lieblingsfutter` wird im aktuellen MVP als Lieblingsleckerli interpretiert. Es ist keine stärkere Nahrung und ersetzt kein Standardfutter. Ein passendes Leckerli sättigt wie jedes andere Leckerli, wird aber sichtbar besser angenommen und gibt kurzzeitig einen leichten Bonus auf positive Aktivitätseffekte.

Futterlogik:

- Standardfutter wird automatisch für die Grundversorgung genutzt
- automatische Grundversorgung füllt nur bis Sättigung 65 auf
- Leckerlis werden bewusst in der Fabling-Detailansicht gegeben
- falsche Leckerlis sättigen ebenfalls, erzeugen aber keinen Buff
- Futter senkt Hunger über `sättigung`

Neue Arten dürfen eine typische Leckerli-Vorliebe bekommen, aber nicht jede Art braucht sofort eine eigene neue Leckerlisorte. Wenn eine Art ein neues Lieblingsleckerli nennt, muss dieses als Gegenstand ergänzt werden, bevor es spielbar beobachtet werden kann.

## Wettbewerbs- und Sportneigungen

Neigungen sind Multiplikatoren für spätere Systeme. Sie sollen das Profil der Art ausdrücken.

Empfohlene Werte:

| Wert | Bedeutung |
| --- | --- |
| 0.7-0.85 | deutliche Schwäche |
| 0.9-1.0 | neutral |
| 1.1-1.2 | Stärke |
| 1.25-1.3 | klare Spezialität |
| >1.3 | vorerst vermeiden |

Regeln:

- Neigungen müssen zu Grundwerten passen.
- Nicht jeder hohe Grundwert braucht zusätzlich eine hohe Neigung.
- Eine Art darf in einem Bereich schwach starten, aber gute Lernneigung haben. Das muss absichtlich sein.

## Entwurfsablauf für neue Arten

1. Konzept in einem Satz formulieren.
2. Element und Lebensraum festlegen.
3. Rolle im Spiel bestimmen: Pflegeauftrag, Training, Wettbewerb, später Zucht oder Spezialauftrag.
4. Grundwerte verteilen.
5. Zwei bis vier Stärken und Schwächen prüfen.
6. Genpools anlegen.
7. Persönlichkeitsgewichte setzen.
8. Vorlieben, Abneigungen, Stärken, Schwächen und Habits notieren.
9. Prüfen, ob Name und Begriffe deutsch, eindeutig und markenrechtlich eigenständig wirken.
10. YAML-Datei anlegen und Tests laufen lassen.

## Beispiel-Checkliste

- Ist der Name ein Fabelbund-Name und keine bekannte Markenassoziation?
- Hat die Art ein klares Element?
- Sind alle 14 Grundwerte vorhanden?
- Liegen die Werte im MVP-Rahmen?
- Gibt es erkennbare Schwächen?
- Gibt es mindestens zwei gewöhnliche Farben oder Muster?
- Sind Umlaute korrekt?
- Sind Temperamente plausibel gewichtet?
- Sind Habits betreuungsrelevant?
- Kann ein Auftrag mit dieser Art ein klares Ist/Soll-Problem formulieren?

## Aktuelle technische Grenze

Die Fabrik übernimmt derzeit aus YAML:

- Art-ID
- Name
- Seltenheit
- Element
- Lebensraum
- Grundwerte
- gewöhnliche Genpoolwerte
- Persönlichkeitsgewichte für `temperament`

Noch nicht vollständig aus YAML übernommen:

- artspezifische `mag`
- artspezifische `mag_nicht`
- artspezifische `stärken`
- artspezifische `schwächen`
- Habits

Diese Felder sollen trotzdem bei neuen Artkonzepten mitgedacht werden, damit der spätere Ausbau konsistent bleibt.
