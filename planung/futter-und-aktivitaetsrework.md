# Futter- und Aktivitätsrework

Dieses Dokument hält konzeptionelle Umbauten fest, die nicht in die aktuelle MVP-Mechanik eingreifen sollen, solange Tutorial und Standardaufträge darauf aufbauen.

## Futter, Sättigung und Leckerlis

Aktueller Stand:

- Fablinge besitzen einen internen Wert `sättigung`.
- Futter wird automatisch aus dem Inventar genommen, wenn Sättigung niedrig genug ist.
- Die aktuelle Futterpräferenz ist noch eng mit dem Begriff Lieblingsfutter vermischt.

Ziel für ein späteres Rework:

- Fablinge essen Standardfutter automatisch nur bis zu einer Sättigung von 65.
- Standardfutter kann später Kategorien bekommen, z.B. nach Element, Lebensraum oder Artengruppe.
- Das bisherige Lieblingsfutter wird konzeptionell zu Leckerlis verschoben.
- Leckerlis geben ebenfalls 20 Futterwert, sind aber kein Ersatz für die Grundversorgung.
- Leckerlis geben für eine Zeitspanne, die 20 Futterwert entspricht, Buffs auf Aktivitäten.
- Diese Buffs müssen so berechnet werden, dass klar ist, ob die Futterabrechnung häufiger laufen muss als nur beim Öffnen der Fabling-Übersicht.
- Durch Leckerlis braucht das Spiel wieder eine bewusste `Futter geben`-Aktion.
- `Futter geben` soll entweder aus dem Inventar oder aus der Fabling-Detailansicht erreichbar sein.
- Das Tutorial muss dann umgebaut werden: Spieler kaufen Leckerlis und finden heraus, was ein Fabling am liebsten isst.
- Fablinge brauchen sichtbare Reaktionen auf nicht bevorzugte Leckerlis, damit Beobachtung und Auswahl spielbar werden.

Offene Designfragen:

- Welche Buffs geben Leckerlis konkret: Aktivitätsertrag, Stressreduktion, Vertrauenszuwachs oder Risikosenkung?
- Wie lange läuft ein Leckerli-Buff bei normalem Servertempo und bei Testserver-Zeitfaktor?
- Wird ein Leckerli-Buff pro Fabling gespeichert oder pro nächster Aktivität verbraucht?
- Wie reagieren Fablinge auf falsche Leckerlis: neutral, leicht enttäuscht, Stress, keine Wirkung?
- Wie verhindern wir, dass Leckerlis zur Pflichtoptimierung vor jeder kleinen Aktion werden?

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
