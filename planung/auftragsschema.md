# Auftragsschema Der Fabelbund

Dieses Schema gilt für alle künftigen Aufträge, Tutorialaufgaben und normalen Aushänge.

## Umsetzungsstatus

Das Schema ist die Zielarchitektur. Neue Inhalte sollen ihm direkt folgen. Ältere oder schnell gewachsene Inhalte können noch Übergangsfelder wie `abgeschlossene_aktion` enthalten und müssen schrittweise migriert werden.

Eine Abgabe darf nur dann nicht zustandsbasiert sein, wenn der geprüfte Punkt selbst das Lern- oder Auftragsziel ist. Zulässige Ausnahmen sind aktuell:

- eine tatsächliche Betreuungsdauer
- eine erkannte Leckerli-Vorliebe, wenn Beobachtung und Zuordnung selbst das Lernziel sind
- spätere explizite Sondermechaniken

## Grundsatz

Aufträge prüfen bei der Abgabe Zielzustände, nicht absolvierte Aktionen.

Aktionen sind Vorschläge, Werkzeuge oder naheliegende Wege. Sie dürfen in Beschreibung, Aufgabe, Buttons und Tutorialtext genannt werden. Sie sind aber nicht selbst die Abgabebedingung.

Gute Auftragsziele beantworten:

- Wie soll der Fabling am Ende wirken?
- Welche internen Werte bilden diesen Zustand ab?
- Welche Mindest- oder Höchstwerte sind für die Abgabe nötig?
- Welche Aktionen können diesen Zustand erreichen?
- Welche Alternativen dürfen ebenfalls funktionieren?

## Erlaubte Zielprüfungen

Aufträge dürfen direkt prüfen:

- Zustandswerte wie Gesundheit, Energie, Stress, Stimmung und Fellpflege
- Beziehungswerte, wenn der Auftrag diese Beziehung ausdrücklich zum Thema macht, z.B. Vertrauen oder Sicherheit
- Trainings- und Wettbewerbswerte wie Ausdruck, Harmonie oder Technik
- Zeitbedingungen, wenn Betreuungsdauer selbst Teil des Auftrags ist
- Auswahlentscheidungen wie passendes Lieblingsleckerli, wenn der Auftrag Beobachtung oder Zuordnung trainiert

Abgeschlossene Aktionen dürfen nicht als normale Abgabebedingung verwendet werden. Felder wie `abgeschlossene_aktion` oder `abgeschlossene_aktionen` sind nur für alte Inhalte oder technische Übergänge erlaubt und sollen nicht für neue Aufträge verwendet werden.

Wenn ein Auftrag eine bestimmte Aktion empfiehlt, muss trotzdem ein passender Zielzustand geprüft werden. Beispiel: Ein Tutorial darf `Angeleitete Ruhe` nennen, die Abgabe prüft aber Energie und Stress.

## Mehrere Fablinge

Wenn ein Auftrag mehrere Fablinge zuteilt, müssen Zielwerte pro Fabling beschrieben werden. Dafür wird `fabling_ziele` verwendet.

Beispiel:

```yaml
ziele:
  fabling_ziele:
    - spitzname: "Miras Quellfink"
      energie_mindestens: 50
      stress_höchstens: 28
    - spitzname: "Miras Gluthase"
      vertrauen_mindestens: 45
      stimmung_mindestens: 54
```

Die Prüfung soll damit fachlich sagen: Dieser bestimmte Fabling hat den gewünschten Zustand erreicht.

## Aufgabenformulierung

Die sichtbare Aufgabe soll keine Rohzahlen nennen. Sie beschreibt den gewünschten Zustand und kann eine naheliegende Handlung nennen.

Gut:

- `Miras Quellfink soll ausgeruhter und ruhiger wirken.`
- `Branns Moosluchs soll sichtbar gepflegt wirken.`
- `Jonnas Quellfink soll Vertrauen fassen und über eine verlässliche Zeit betreut werden.`

Schlecht:

- `Schließe Kontrollierte Ruhe ab.`
- `Nutze exakt Gemeinsames Spiel.`
- `Erreiche Energie 50 und Stress 28.`

## NPC-Antwort bei nicht erfüllter Abgabe

Jeder Auftrag braucht eine allgemeine, passende Antwort des NPCs, wenn die Abgabe noch nicht möglich ist.

Diese Antwort steht in:

```yaml
fehlschlag:
  hinweis: "Mira sagt: „Er ist mir noch zu erschöpft und zu unruhig.“"
```

Der Text soll:

- aus Sicht des Auftraggebers plausibel sein
- keine internen Zahlen nennen
- grob sagen, was am Fabling noch nicht passt
- nicht exakt verraten, welche einzelne Aktion geklickt werden muss

## Tutorial

Tutorialaufträge folgen denselben Regeln wie normale Aufträge. Sie dürfen stärker führen, aber die Abgabe bleibt zustandsbasiert.

Tutorialaktionen dürfen kürzere Dauer-Overrides haben, damit Tests und Einstieg nicht zäh werden. Diese Dauer-Overrides ändern nicht die normalen Aktionen im späteren Spiel.
