# Trainings-Matrix Der Fabelbund

Dieses Dokument legt die numerische Grundlage für einfache Wettbewerbstrainings fest. Es ist die Referenz, bevor neue Trainingsaktionen in `daten/aktionen/pflege.yaml` umgesetzt werden.

Grundregel: Spieler sehen diese Zahlen normalerweise nicht. Sichtbar werden Dauer, grobe Belastung und spätere Einschätzungstexte.

## Balancing-Regeln

- Eine gezielte Standard-Trainingsaktion hebt ihren Hauptwert um `+5`.
- Passende Nebenwerte steigen meist um `+1` bis `+2`.
- Jede aktive Trainingsaktion kostet Energie und erzeugt Stress.
- Körperliche oder längere Trainingsformen erzeugen zusätzlich Muskelkater.
- Mentale Trainingsformen belasten weniger körperlich, aber eher Stress oder Stimmung.
- Vertrauen steigt nur dort, wo echte Zusammenarbeit entsteht.
- Training ist aktiv: Der Spieler ist währenddessen gebunden.
- Nach Training sollen Ruhe, kurze Checks oder leichte Pflege als Folgeaktionen naheliegen.
- Aktionsnamen in Buttons sollen klar sagen, welcher Wert trainiert wird. Atmosphärische Namen gehören in Beschreibungstexte, nicht in die primäre Auswahl.

## MVP-Trainingsaktionen

| Aktion | Hauptwert | Dauer | Zustandsänderungen | Wettbewerbsänderungen | Abbruchfolgen | Rolle |
| --- | --- | ---: | --- | --- | --- | --- |
| Schönheit trainieren | Schönheit | 12 Minuten | Energie `-7`, Stress `+2`, Fellpflege `+8`, Stimmung `+1` | Schönheit `+5`, Eleganz `+1`, Ausdruck `+1` | Vertrauen `-1`, Sicherheit `-1` | Schonendes Vorbereitungstraining über Erscheinung und Pflegebild. |
| Eleganz trainieren | Eleganz | 15 Minuten | Energie `-9`, Stress `+3`, Muskelkater `+1` | Eleganz `+5`, Schönheit `+1`, Harmonie `+1` | Vertrauen `-1`, Sicherheit `-1` | Ruhiges Bewegungs- und Haltungstraining. |
| Charme trainieren | Charme | 12 Minuten | Energie `-7`, Stress `+2`, Stimmung `+2`, Vertrauen `+1` | Charme `+5`, Ausdruck `+2`, Harmonie `+1` | Vertrauen `-1`, Sicherheit `-1` | Kontakt, Auftreten und positive Reaktion auf Betreuung. |
| Intelligenz trainieren | Intelligenz | 15 Minuten | Energie `-6`, Stress `+4`, Stimmung `-1` | Intelligenz `+5`, Disziplin `+1`, Harmonie `+1` | Vertrauen `-1`, Sicherheit `-1` | Aufgabenverständnis, Aufmerksamkeit und Problemlösen. |
| Ausdruck trainieren | Ausdruck | 15 Minuten | Energie `-9`, Stress `+4`, Muskelkater `+2` | Ausdruck `+5`, Charme `+2`, Disziplin `+1` | Vertrauen `-1`, Sicherheit `-1` | Bereits implementiertes Wettbewerbstraining für Präsenz. |
| Disziplin trainieren | Disziplin | 18 Minuten | Energie `-8`, Stress `+5`, Stimmung `-1`, Muskelkater `+1` | Disziplin `+5`, Intelligenz `+1`, Harmonie `+1` | Vertrauen `-2`, Sicherheit `-1` | Struktur, Wiederholung und verlässliches Folgen von Signalen. |
| Harmonie trainieren | Harmonie | 20 Minuten | Energie `-10`, Stress `+3`, Muskelkater `+2`, Vertrauen `+2` | Harmonie `+5`, Disziplin `+2`, Eleganz `+1` | Vertrauen `-2`, Sicherheit `-1` | Bereits implementiertes Zusammenspiel zwischen Fabling und Betreuer. |

## Abdeckung der Wettbewerbswerte

| Wettbewerbswert | Hauptaktion | Nebenaktionen |
| --- | --- | --- |
| Schönheit | Schönheit trainieren | Eleganz trainieren, Ausdruck trainieren |
| Eleganz | Eleganz trainieren | Schönheit trainieren, Harmonie trainieren |
| Charme | Charme trainieren | Ausdruck trainieren |
| Intelligenz | Intelligenz trainieren | Disziplin trainieren |
| Ausdruck | Ausdruck trainieren | Charme trainieren, Schönheit trainieren |
| Disziplin | Disziplin trainieren | Ausdruck trainieren, Harmonie trainieren, Intelligenz trainieren |
| Harmonie | Harmonie trainieren | Charme trainieren, Eleganz trainieren, Intelligenz trainieren, Disziplin trainieren |

## Intensitätsrahmen

Diese MVP-Aktionen sind mittlere Standardaktionen. Später können pro Wert weitere Varianten ergänzt werden.

| Intensität | Dauer | Hauptwert | Zustandskosten | Einsatz |
| --- | ---: | ---: | --- | --- |
| leicht | 5 bis 8 Minuten | `+2` bis `+3` | wenig Energieverlust, kaum Muskelkater, geringer Stress | Kurze Vorbereitung, Tutorial, niedrige Risiken. |
| mittel | 12 bis 20 Minuten | `+5` | merkliche Energiekosten, leichter Stress, teils Muskelkater | MVP-Standardtraining. |
| schwer | 30 bis 60 Minuten | `+8` bis `+10` | hoher Energieverlust, Stress, Muskelkater, Risiko | Später für fortgeschrittenes Training. |

## Zustandsgrenzen

Training soll nicht endlos gespammt werden. Für spätere Validierung sind diese Schwellen sinnvoll:

| Zustand | Warnbereich | Harte Sperre für schweres Training | Bedeutung |
| --- | ---: | ---: | --- |
| Energie | unter `35` | unter `20` | Fabling ist zu erschöpft für zuverlässiges Training. |
| Stress | über `55` | über `75` | Training wird unzuverlässig und riskant. |
| Muskelkater | über `35` | über `55` | Körperliche Aktionen werden riskanter. |
| Gesundheit | unter `60` | unter `40` | Training sollte durch Check oder Ruhe ersetzt werden. |

## Umsetzungshinweise

Für die nächste YAML-Umsetzung:

- Neue Aktionen gehören weiterhin in die Kategorie `training`.
- Alle MVP-Trainingsaktionen sind `braucht_spieler: true`.
- `folgeaktionen` sollten mindestens Ruhe, kurzen Check und eine thematisch passende nächste Trainingsaktion anbieten.
- Die bestehenden Aktionen `ausdruck_üben` und `harmonie_üben` passen numerisch bereits in diese Matrix. Sichtbar sollten sie künftig als `Ausdruck trainieren` und `Harmonie trainieren` auftreten.
- Aufträge prüfen später Zielzustände oder Wettbewerbswerte, nicht die abgeschlossene Trainingsaktion selbst.
