# ToDos Der Fabelbund

Diese Liste enthält nur offene Punkte. Priorisierte Aufgaben stehen in nummerierten Blöcken. Themenzweige ohne feste Reihenfolge stehen in Buchstabenblöcken.

## 1. Playtest-Qualität und Tutorialfluss

- [ ] Tutorial einmal absichtlich mit zu früher Auftragsabgabe pro Auftrag testen.
- [ ] Prüfen, ob Buttons an jeder Tutorialstelle zum nächsten sinnvollen Menü führen.
- [ ] Aufgabenblöcke im Tutorial so glätten, dass sie Zielzustände beschreiben statt Klickanweisungen.
- [ ] Auftragsanzeige und Fablingübersicht mit eindeutig benannten Tutorial-Fablingen im Discord-Flow testen.
- [ ] Prüfen und absichern, dass aktive Betreuung andere Menüs blockiert.
- [ ] Prüfen, ob Spieler nach dem Tutorial sinnvoll erkennen, was sie als Nächstes tun können.

## 2. Auftrags- und Belohnungsbalancing

- [ ] Belohnungen und Ruf für normale Aufträge sauber staffeln.
- [ ] 1h-, 3h- und 5h-Auftragsvarianten im Playtest auf Aufwand, Schwierigkeit und Siegelbelohnung prüfen.
- [ ] Auftragswand-Rotation und Aushang-Gewichte prüfen, damit seltene Fablinge selten bleiben und trotzdem genug Abwechslung entsteht.
- [ ] Fabling-Preise gegen neue längere Aufträge prüfen.
- [ ] Futterpreise nach erstem Playtest auf moderate tägliche Deflation prüfen.

## 3. Auftragsschema technisch härten

- [ ] Technische Übergangsfelder `abgeschlossene_aktion` und `abgeschlossene_aktionen` entfernen oder klar als Legacy markieren.
- [ ] Tests ergänzen, die fehlschlagen, wenn Tutorialaufträge wieder reine Aktionsabschlussprüfung nutzen.
- [ ] Erlaubte Sonderziele dokumentieren und technisch abgrenzen, z.B. Mindestbetreuung, Futterzuordnung nur im Tutorial oder spätere Sondermechaniken.

## 4. Dauerhafte Grundbedürfnisse

- [ ] Pflegezustand der Fablinge graduell nachlassen lassen, damit regelmäßiger Pflegebedarf entsteht.
- [ ] Niedrige Sättigung deutlicher in Zustandstexten sichtbar machen.
- [ ] Kritische Hungerereignisse in die Chronik posten.
- [ ] Entzug durch den Fabelbund bei kritischer Gesundheit modellieren.
- [ ] Ruf-/Rangverlust bei Entzug modellieren.

## A. Futter- und Leckerli-Rework

Details und Originalgedanken stehen in `planung/futter-und-aktivitaetsrework.md`; vor Umsetzung vollständig lesen.

- [ ] Futter- und Leckerli-Rework im kompletten Tutorialdurchlauf testen.
- [ ] Getestete Leckerlis pro Fabling speichern und anzeigen: falsche Versuche als `❌ Name`, nach Treffer nur noch Lieblingsleckerli mit Emoji.

## B. Aktivitätszeiten und Online-/AFK-Spiel

Details und Originalgedanken stehen in `planung/futter-und-aktivitaetsrework.md`; vor Umsetzung vollständig lesen.

- [ ] Kurze aktive Tätigkeiten und lange AFK-Aktivitäten sauber unterscheiden.
- [ ] Zeitklassen und deren Spielfunktion gemeinsam festlegen.
- [ ] Auswirkungen auf Aufträge, Wettbewerbsvorbereitung und Buffs prüfen.
- [ ] Entscheiden, wie kurze Aktivitätsspam-Phasen und lange Offline-Planung zusammenspielen sollen.

## C. Wettbewerbe

- [ ] Wettbewerbssystem narrativ ausarbeiten.
- [ ] Ranglisten- und Ergebnisdarstellung mit Text statt nur Zahlen vorbereiten.
- [ ] Wettbewerbsvorbereitung mit Trainingswerten, Zustand, Stress und Gesundheit balancen.
- [ ] Belohnungen, Ruf und spätere Lizenzlogik für Wettbewerbe festlegen.

## D. Zucht

- [ ] Zuchtgrundregeln entwerfen.
- [ ] Vererbung, Seltenheit, Farben, Muster und Sperrzeiten planen.
- [ ] Voraussetzungen für eigene Zucht nach dem Tutorial definieren.

## E. Handel und Markt

- [ ] Handelssystem konzeptionell vorbereiten.
- [ ] Marktregeln für Fablinge, Futter, Ausrüstung und spätere Spezialgegenstände festlegen.
- [ ] Schutzregeln gegen Missbrauch und versehentliche Verluste definieren.

## F. Events und Saisons

- [ ] Eventtypen definieren.
- [ ] Saisonale Wettbewerbe, seltene Fabling-Angebote und besondere Aufträge planen.
- [ ] Chronik- und Kanalverhalten für Events festlegen.

## G. Test- und Betriebskomfort

- [ ] Optionales Kombiskript vorbereiten: Stop -> Spielerreset -> Start.
