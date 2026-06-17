# Stat-Übersicht Der Fabelbund

Dieses Dokument beschreibt die internen Werte von Fablingen und Spielern. Ziel ist ein klares Balancing-Fundament, bevor wir Content stark erweitern.

Grundregel: Zahlen bleiben intern. Spieler sehen nur dort Zahlen, wo sie Spielökonomie oder Besitz direkt betreffen. Fabling-Zustände werden normalerweise als Einschätzungstext ausgegeben.

## Fabling-Stats

### Zustandswerte

| Stat | Bedeutung | Sichtbarkeit | Steigt durch | Sinkt durch | Verwendet von |
| --- | --- | --- | --- | --- | --- |
| Gesundheit | Körperlicher Grundzustand des Fablings. Hohe Gesundheit macht Aktivitäten sicherer und stabiler. | Nur als Textbeschreibung | Schonung, Heilbehandlung, gute Pflege, lange stabile Phasen | Vernachlässigung, Verletzung, Überlastung, Krankheit | Aufträge, Risiko, Training, Wettbewerbe |
| Energie | Kurzfristige verfügbare Kraft. Bestimmt, ob der Fabling Aufgaben gut angehen kann. | Nur als Textbeschreibung | Ruhe, Schlaf, leichte Erholung, passende Nahrung | Training, Spiel, Pflege, Stress, lange Aktivität | Aktivitätsstart, Training, Pflege, Aufträge |
| Stress | Aktuelle innere Belastung. Hoher Stress verschlechtert Kooperation und erhöht Risiken. | Nur als Textbeschreibung | Überforderung, Abbruch, ungeeignete Aktion, Wettbewerbsdruck | Ruhe, vertraute Umgebung, sanfte Betreuung, gelungene Routinen | Risiko, Vertrauen, Training, Aktivitätstexte |
| Stimmung | Momentane Laune und Offenheit. Beeinflusst, wie positiv Betreuung wahrgenommen wird. | Nur als Textbeschreibung | Spiel, passende Pflege, Lieblingsleckerlis, gute Erholung | Langeweile, Abbruch, Stress, ungeeignete Umgebung | Betreuung, Bindung, Texte, Aufträge |
| Fellpflege | Äußerer Pflegezustand. Wichtig für Pflegeaufträge und später Schönheit/Wettbewerbe. | Nur als Textbeschreibung | Pflege, Bad, Bürsten, Selbstpflege in Ruhe | Zeit, Aktivität, Vernachlässigung, ungeeignete Umgebung | Pflegeaufträge, Wettbewerbe, Status |
| Muskelkater | Kurzfristige körperliche Belastungsfolge nach Training oder starker Aktivität. | Nur als Textbeschreibung | Training, lange Bewegung, Überlastung | Schlaf, Massage, lockeres Bewegen, Ruhe | Training, Verletzungsrisiko, Erholung |

### Beziehungswerte

| Stat | Bedeutung | Sichtbarkeit | Steigt durch | Sinkt durch | Verwendet von |
| --- | --- | --- | --- | --- | --- |
| Vertrauen | Wie sicher sich der Fabling beim Spieler fühlt. Vertrauen ist kein passiver Offline-Ertrag. | Nur als Textbeschreibung | aktive Betreuung, eingehaltene Zusagen, gutes Abholen, schwierige Situationen gemeinsam meistern | gebrochene Zusagen, Schlaf/Ruhe abbrechen, Vernachlässigung ab 24h | Kooperation, Training, Pflege, spätere Vertragslogik |
| Bindung | Langfristige Beziehung über einzelne Aktionen hinaus. Kann später aus Vertrauen, Historie und gemeinsamen Erfolgen entstehen. | Vorbereitet, später als Text | wiederholte gute Betreuung, gemeinsame Erfolge, stabile Routinen | lange Vernachlässigung, schlechte Behandlung | spätere Zucht, seltene Ereignisse, Spezialaktionen |
| Sicherheit | Gefühl von verlässlicher Umgebung. Nützlich für scheue oder empfindliche Fablinge. | Vorbereitet, später als Text | vertrauter Stall, passende Stallpriorität, ruhige Aktionen | häufige Wechsel, Stress, Abbruch | Charakterreaktionen, Stallbonus |

### Trainingswerte

| Stat | Bedeutung | Sichtbarkeit | Steigt durch | Sinkt durch | Verwendet von |
| --- | --- | --- | --- | --- | --- |
| Beweglichkeit | Körperliche Wendigkeit. | Nur bei Trainings-/Wettbewerbsbewertung, nicht als Rohzahl | leichtes Training, Spiel, Parcours | lange Vernachlässigung nach späterer Regel, Verletzung | Sport, Training, Wettbewerbe |
| Ausdauer | Fähigkeit, längere Belastung durchzuhalten. | Nur bei Trainings-/Wettbewerbsbewertung, nicht als Rohzahl | Ausdauertraining, Spaziergang, moderate Wiederholung | Verletzung, lange Vernachlässigung nach späterer Regel | Sport, Training, Aufträge |
| Stärke | Kraft und Durchsetzung. | Nur bei Trainings-/Wettbewerbsbewertung, nicht als Rohzahl | Krafttraining, kontrollierte Belastung | Verletzung, Überlastungspausen | Sport, Training |
| Technik | Gelernte Ausführung von Aufgaben. | Nur bei Trainings-/Wettbewerbsbewertung, nicht als Rohzahl | gezieltes Training, Wiederholung, Check-Aktionen | lange Vernachlässigung nach späterer Regel | Sport, Training, Wettbewerbe |
| Ausdruck | Präsentation, Körpersprache und Präsenz. | Nur bei Wettbewerbsbewertung, nicht als Rohzahl | Spiel, Showtraining, Vertrauen | Stress, schlechte Stimmung | Schönheit, Wettbewerbe |
| Harmonie | Zusammenspiel zwischen Fabling und Betreuer. | Nur bei Wettbewerbsbewertung, nicht als Rohzahl | Vertrauen, gemeinsames Training, ruhige Routine | Stress, gebrochene Zusagen | Wettbewerbe, Bindungsaktionen |

### Risiko- und Gesundheitswerte

| Stat | Bedeutung | Sichtbarkeit | Steigt durch | Sinkt durch | Verwendet von |
| --- | --- | --- | --- | --- | --- |
| Verletzungsrisiko | Wahrscheinlichkeit, dass Belastung schiefgeht. Wird aus Zustand und Aktivität beeinflusst. | Nur als Warntext | hoher Stress, Muskelkater, niedrige Energie, harte Aktivität | Ruhe, Gesundheitscheck, schonende Bewegung | Training, Wettbewerbe, Aktivitätsausgang |
| Erschöpfung | Verdichteter Warnwert aus Energie, Stress und Muskelkater. Kann später statt eigener Speicherung berechnet werden. | Nur als Text | Belastung, Schlafmangel, Training | Ruhe, Schlaf, Massage | Status, Aktivitätsfreigabe |
| Krankheitsanfälligkeit | Langfristige Folge schlechter Gesundheit und Vernachlässigung. | Vorbereitet, später als Text | lange schlechte Pflege, niedrige Gesundheit | stabile Pflege, Heilung | spätere Ereignisse |

### Charakter- und Eigenheitswerte

| Wert | Bedeutung | Sichtbarkeit | Steigt durch | Sinkt durch | Verwendet von |
| --- | --- | --- | --- | --- | --- |
| Temperament | Grundtendenz des Fablings, z.B. neugierig, scheu, wild, treu. | Direkt als Beschreibung möglich | nicht als normaler Stat | nicht als normaler Stat | Aktionseignung, Textvariation, Risiken |
| Vorlieben | Dinge, die der Fabling mag. | Über Beobachtung/Check sichtbar | Entdeckung durch Betreuung | nicht als normaler Stat | Bonus auf passende Aktionen |
| Abneigungen | Dinge, die Stress auslösen können. | Über Beobachtung/Check sichtbar | Entdeckung durch Betreuung | nicht als normaler Stat | Risiko und Stress bei Aktionen |
| Stärken | Natürliche Vorteile. | Später über Einschätzung sichtbar | nicht als normaler Stat | nicht als normaler Stat | Training, Wettbewerbe |
| Schwächen | Natürliche Nachteile. | Später über Einschätzung sichtbar | nicht als normaler Stat | nicht als normaler Stat | Training, Risiken |

## Spielerwerte

| Wert | Bedeutung | Sichtbarkeit | Steigt durch | Sinkt durch | Verwendet von |
| --- | --- | --- | --- | --- | --- |
| Bundsiegel | Allgemeine Spielwährung. | Direkt sichtbar | Aufträge, Wettbewerbe, Handel | Käufe, Behandlung, Stallerweiterung | Ökonomie |
| Ruf | Bereichsbezogene Reputation, aktuell z.B. Pflege und Zuverlässigkeit. | Direkt oder als Rang sichtbar | erfüllte Aufträge, gute Betreuung, faire Verträge | abgebrochene Zusagen, Fehlschläge, Missbrauch | Aufträge, Freischaltungen, Vertragslogik |
| Freigeschaltete Ställe | Anzahl nutzbarer Stallplätze. | Direkt sichtbar | Kauf, Tutorial, Meilensteine | normalerweise nicht sinkend | Besitzgrenze, Fabling-Annahme |
| Stalltypen | Gebaute Stallarten nach Element oder neutral. | Direkt in Stallübersicht sichtbar | Kauf, Ausbau, Questbelohnungen | normalerweise nicht sinkend | automatische Belegung, Komfort, spätere Boni |
| Lizenzen | Freischaltungen für Systeme und Schwierigkeitsgrade. | Direkt sichtbar | Tutorial, Ruf, Prüfungen | normalerweise nicht sinkend | Aufträge, Training, Handel, Wettbewerbe |
| Tutorialstatus | Fortschritt im Einstieg. | Nur über aktuelle Tutorialschritte sichtbar | Tutorialaktionen | nicht sinkend | Einstieg, Freischaltungen |
| Fortschritt | Allgemeiner langfristiger Spielfortschritt. | Als Meilensteine sichtbar | Aufträge, Sammeln, Training, Story | nicht sinkend | Freischaltungen, Inhalte |

## MVP-Kandidaten

Diese Liste ist ein Vorschlag und muss gemeinsam entschieden werden.

### Wahrscheinlich MVP-relevant

- Gesundheit
- Energie
- Stress
- Stimmung
- Fellpflege
- Vertrauen
- Sicherheit
- Bindung
- Muskelkater
- Verletzungsrisiko
- Trainingswerte
- Bundsiegel
- Ruf
- Freigeschaltete Ställe
- Stalltypen
- Tutorialstatus

### Vorbereiten, aber nicht prominent spielen

- Wettbewerbswerte
- Vorlieben
- Abneigungen
- Stärken
- Schwächen
- Krankheitsanfälligkeit

## Designentscheidungen

### Auftragsschema

Die verbindliche Regel für neue Aufträge steht in [auftragsschema.md](auftragsschema.md). Kurzfassung: Auftragsabgaben prüfen Zielzustände, nicht abgeschlossene Aktionen. Aktionen sind Wege zum Ziel, aber nicht selbst die Abgabebedingung.

### Auftragsprüfungen

Aufträge dürfen direkt prüfen:

- Gesundheit
- Stimmung
- Fellpflege
- Stress, bevorzugt als Nicht-größer-als-Kriterium
- alle Trainingswerte

Andere Werte wie Vertrauen, Sicherheit oder Bindung sollen eher indirekt über Aktivitätsqualität, Freischaltungen oder Textreaktionen wirken, solange wir keinen klaren Auftragstyp haben, der diese Werte bewusst in den Mittelpunkt stellt.

### Abbruchfolgen

Abbruch ist nicht neutral. Sicherheit und Vertrauen sollen bei gebrochenen Zusagen minimal sinken. Die Stärke des Verlusts hängt vom Beziehungskontext ab:

- hohe Bindung dämpft den Verlust
- geringe Bindung verstärkt den Verlust
- wiederholte Abbrüche ähnlicher Zusagen verschlechtern Sicherheit und Vertrauen zunehmend
- Ruhephasen sind empfindlich
- Schlaf ist besonders empfindlich und soll stärker reagieren

Konkrete Zahlen werden später anhand erster Live-Tests festgelegt.

### Verwahrlosung

Verwahrlosung ist kein einzelner Stat, sondern ein Gesamtbild aus schlechten Beziehungswerten, schlechter Stimmung, hohem Stress und niedriger Pflege. Sie öffnet perspektivisch den Weg zu Verwilderung: Der Fabling fühlt sich weniger domestiziert und weniger sicher in der Betreuung.

Textregel:

- frühe Andeutungen klein und vorsichtig formulieren
- bei schlechteren Werten deutlicher werden
- bei sehr schlechten Werten klare Verwahrlosungs- oder Verwilderungssprache verwenden
- Zahlen bleiben intern

### Trainingswerte

Alle Trainingswerte sollen grundsätzlich spielbar werden. Für den MVP dürfen sie einfach und klar starten; die Differenzierung entsteht über Aktionen, Dauer, Intensität, Risiko und spätere Wettbewerbe.

Die konkrete numerische Grundlage für Wettbewerbstrainings steht in [trainings-matrix.md](trainings-matrix.md).

### Checks

Checks sind Informationsaktionen. Ein Check verändert grundsätzlich keine Werte. Er macht Beobachtungen, Risiken, Vorlieben, Abneigungen oder Einschätzungen sichtbar.

Ausnahmen sind nur spätere Spezialfälle über Charakter-/Eigenheitslogik, z.B. ein Fabling, das durch zu häufiges Kontrollieren misstrauisch oder gestresst wird. Das ist keine MVP-Grundregel.
