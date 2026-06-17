# Futter- und Aktivitätsrework

Dieses Dokument hält konzeptionelle Umbauten fest, die Tutorial, Standardaufträge und spätere Balancing-Arbeit betreffen.

## Futter, Sättigung und Leckerlis

MVP-Stand:

- Fablinge besitzen einen internen Wert `sättigung`.
- Standardfutter wird automatisch aus dem Inventar genommen, wenn Sättigung niedrig genug ist.
- Fablinge essen Standardfutter automatisch nur bis zu einer Sättigung von 65.
- `Basisfutter` ist vorerst das neutrale Standardfutter.
- Standardfutter kann später Kategorien bekommen, z.B. nach Element, Lebensraum oder Artengruppe.
- Das bisherige Lieblingsfutter wird im Spiel als Lieblingsleckerli interpretiert.
- Leckerlis geben ebenfalls 20 Futterwert, sind aber kein Ersatz für die Grundversorgung.
- Leckerlis werden bewusst in der Fabling-Detailansicht gegeben.
- Das Lieblingsleckerli gibt für eine Zeitspanne, die 20 Futterwert entspricht, einen leichten Bonus auf positive Aktivitätseffekte.
- Nicht bevorzugte Leckerlis sättigen ebenfalls, geben aber keinen Buff und erzeugen eine zurückhaltendere Reaktion.
- Das Tutorial nutzt Leckerlis als Beobachtungsaufgabe: Spieler kaufen Leckerlis und finden heraus, was ein Fabling am liebsten isst.
- Der Laden bietet Leckerlis als eigenes Untermenü an; im Tutorial wird die Auswahl auf das richtige Leckerli plus zwei günstige Alternativen begrenzt.
- Die Starter-Fablinge sind alle `gewöhnlich`; ihre Leckerlis bleiben im günstigen Einstiegsbereich.

Getroffene Zwischenentscheidungen:

- Buff-Art: positive Aktivitätseffekte werden leicht verstärkt; negative Effekte werden nicht verstärkt und nicht reduziert.
- Buff-Dauer: 20 Futterwert entsprechen bei 100 Futterwert Verbrauch pro Tag 4,8 Stunden Spielzeit. Der Testserver-Zeitfaktor verkürzt die reale Dauer entsprechend.
- Speicherung: Buffs werden pro Fabling mit Ablaufzeit gespeichert, nicht als einmaliger Verbrauch.
- Falsches Leckerli: keine harte Strafe, aber keine Begeisterung und kein Buff.
- Pflichtoptimierung wird vorerst durch geringe Stärke, begrenzte Dauer und Vorratskosten begrenzt.

Offene Designfragen:

- Wenn bis zu 25 Leckerlis existieren, muss pro Fabling gespeichert werden, welche Leckerlis bereits getestet wurden. Bis das Lieblingsleckerli gefunden ist, sollen falsche Tests als `❌ Name` sichtbar bleiben. Sobald das Lieblingsleckerli einmal gegeben wurde, zeigt die Fabling-Ansicht nur noch dieses Lieblingsleckerli mit passendem Emoji.
- Brauchen unterschiedliche Elemente später unterschiedliche Standardfutter?
- Sollen Lieblingsleckerlis langfristig pro Art, pro Persönlichkeit oder pro individuellem Fabling variieren?
- Sollen Leckerlis später gezieltere Bufftypen haben, z.B. Training, Ruhe, Wettbewerb oder Bindung?
- Wie viele Leckerlis brauchen wir, damit Beobachtung spielbar bleibt, ohne reines Raten zu werden?

## Kurze und lange Aktivitäten

Aktueller Stand:

- Aktivitäten liegen fließend zwischen etwa 1 Minute und 2 Stunden.
- Kurze und lange Aktivitäten erfüllen noch keine klar getrennten Spielfunktionen.

Ziel für ein späteres Rework:

- Kurze Aktivitäten sollen bewusst für aktive Online-Zeit gedacht sein.
- Spieler können durch kurze Aktivitäten mehrere kleine Entscheidungen treffen und Fortschritt gezielt steuern.
- Lange Aktivitäten sollen klar als AFK-Planung funktionieren.
- Lange Aktivitäten sollten weniger Klickdichte brauchen, aber stärkere Planung und höhere Konsequenzen haben.
- Diese Trennung muss gemeinsam diskutiert werden, bevor wir weitere Aktivitätsmengen ausbauen.

Offene Designfragen:

- Welche Zeitklassen wollen wir verwenden, z.B. sofort, kurz, mittel, lang, sehr lang?
- Welche Systeme gehören zu kurzer aktiver Betreuung und welche zu AFK-Aktivitäten?
- Wie stark dürfen lange Aktivitäten im Vergleich zu mehreren kurzen Aktivitäten sein?
- Welche Risiken entstehen durch lange Aktivitäten: Überlastung, Stress, verpasste Abholung, Verwahrlosung?
- Wie hängen Zeitklassen mit Aufträgen, Wettbewerben und Leckerli-Buffs zusammen?
