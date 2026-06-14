# ToDos Der Fabelbund

Diese Liste ist unser gemeinsamer Arbeitsplan. Abgeschlossene Punkte bleiben kurz nachvollziehbar stehen, offene Punkte werden hier gesammelt und priorisiert.

## 1. Testumgebung verbessern

- [x] Testserver-Konfiguration vorbereitet
- [x] Testserver-spezifische Slash-Command-Synchronisierung
- [x] Konfigurierbarer Zeitfaktor für schnellere Tests
- [x] Nicht-destruktive Testoptionen vorbereitet

## 2. Stat-Übersicht entwerfen

- [x] Übersicht aller Fabling-Stats erstellen
  - [x] Zustandswerte
  - [x] Beziehungswerte
  - [x] Trainingswerte
  - [x] Risiko-/Gesundheitswerte
  - [x] Charakter-/Eigenheitswerte
- [x] Pro Stat festhalten
  - [x] was der Stat bedeutet
  - [x] ob Spieler ihn direkt sehen
  - [x] ob Spieler ihn nur als Textbeschreibung sehen
  - [x] wodurch er steigt
  - [x] wodurch er sinkt
  - [x] welche Systeme ihn verwenden
- [x] Übersicht aller Spielerwerte erstellen
  - [x] Geld
  - [x] Ruf
  - [x] Ställe
  - [x] Lizenzen
  - [x] Fortschritt/Tutorialstatus
  - [x] ggf. Reputation nach Bereichen
- [x] Gemeinsam entscheiden, welche Stats MVP-relevant sind und welche nur vorbereitet werden
- [x] Ziel: klares internes Balancing-Dokument erstellen, bevor Content stark erweitert wird

## 3. Erste Content-Erweiterung

- [x] Pflege- und Ruheaktionen erweitern
  - [x] mehrere Wege pro Zielwert
  - [x] unterschiedliche Dauer
  - [x] unterschiedliche Intensität
  - [x] unterschiedliche Konsequenzen
  - [x] aktiv/passiv unterscheiden
- [x] Erste Spiel-/Bindungsaktionen ergänzen
  - [x] Vertrauen nur durch aktive Betreuung oder eingehaltene Zusagen
  - [x] kein Vertrauensgewinn durch bloßes Nichtstun
- [x] Erste leichte Trainingsaktionen ergänzen
  - [x] Trainingsfortschritt
  - [x] Energieverbrauch
  - [x] Stress/Muskelkater/Risiko
- [x] Check-Aktionen ergänzen
  - [x] Statuscheck
  - [x] Gesundheitscheck vorbereitet
  - [x] Einschätzung
  - [x] eher Information sichtbar machen als Werte direkt erhöhen
- [x] Abbruchkonsequenzen systematisch modellieren
  - [x] Ruhe abbrechen senkt Vertrauen und Sicherheit
  - [x] Schlaf abbrechen stärker
  - [x] Training abbrechen gibt Belastung, aber wenig Fortschritt
- [x] Doktorbesuch freischalten und Kostenmodell ergänzen
- [x] Stall- und Betreuungsansicht zusammenführen
  - [x] `/stall` und `/betreuung` durch `/fablinge` ersetzen
  - [x] Fabling-Auswahl für bis zu 25 Fablinge
  - [x] Futter- und Stallpriorität in der Fabling-Detailansicht behalten
  - [x] Betreuungsaktivitäten pro ausgewähltem Fabling starten
  - [x] Passive Aktivitäten erlauben Rücknavigation, aktive Betreuung bindet den Spieler
  - [x] Redundante Folgeaktionslisten aus Aktivitätsergebnissen entfernen
- [x] Aktionsauswahl pro Fabling direkt aus der Fabling-Ansicht starten
- [x] Ephemere Bedienansichten für längere Aktivitäten auf lange Timeouts umstellen

## 4. Tutorial und Einstieg

- [x] Tutorialstatus als Spielerwert einführen
- [x] Neuer Spieler startet ins Pflicht-Tutorial
- [x] Tutorial vergibt erste Probe-Fablinge
- [x] Tutorial erklärt Schritt für Schritt, funktional
  - [x] Profil
  - [x] Fablinge und Ställe über `/fablinge`
  - [x] ersten Fabling ansehen
  - [x] erste Pflege/Ruhe über Fabling-Detailansicht starten
  - [x] Aktivität abholen
  - [x] ersten Auftrag verstehen
- [ ] Tutorial als spielbaren Qualitätsdurchlauf prüfen
  - [ ] frischen Durchlauf mit Spielerreset testen
  - [ ] jeden Schritt einmal normal abschließen
  - [ ] jeden Auftrag einmal absichtlich zu früh abgeben
  - [ ] prüfen, ob NPC-Hinweis verständlich sagt, was noch nicht passt
  - [ ] prüfen, ob Buttons an jeder Stelle zum nächsten sinnvollen Menü führen
  - [x] prüfen, ob der Spieler nach dem Schließen einer ephemeren Ansicht wieder ins Tutorial zurückfindet
- [x] Erster Tutorialauftrag: Ruhe herstellen und Auftrag abgeben
- [x] Weitere Tutorialschritte ergänzen
  - [x] Pflege und Ausrüstung
  - [x] Starter-Fabling nach Probeaufträgen vergeben
  - [x] Futter kaufen
  - [x] Futter geben
  - [x] Fablinge/Ställe
  - [x] aktive Betreuung
  - [x] Training
  - [x] Check
  - [x] Abschluss als offizielles Mitglied
- [ ] Tutorialziele vollständig zustandsbasiert machen
  - [ ] keine Tutorialabgabe darf `abgeschlossene_aktion` oder `abgeschlossene_aktionen` prüfen
  - [ ] Mehrfach-Fabling-Aufträge nutzen zielwertbasierte Einzelziele pro Fabling
  - [ ] Zeitbedingungen bleiben erlaubt, wenn Zeit selbst Lernziel ist
  - [ ] Tests ergänzen, die fehlschlagen, wenn Tutorialaufträge wieder Aktionsabschluss prüfen
- [ ] Tutorialzeiten spaßfähig halten
  - [ ] alle Tutorialaktivitäten auf ca. 2-5 Minuten Spielzeit bringen
  - [x] Betreuungszeit-Auftrag auf 2-5 Minuten Gesamtzeit senken
  - [x] keine 30-Minuten-Bedingung in der Einführung verwenden
  - [ ] prüfen, ob Zeitfaktor 5x im Testserver daraus angenehme reale Wartezeiten macht
- [ ] Tutorialtexte auf erwachsenen, knappen Stil prüfen
  - [ ] keine Slash-Command-Verweise
  - [ ] keine redundanten "danach abholen/abgeben"-Erklärungen
  - [ ] Aufgabenblock beschreibt Zielzustand statt Klickanweisung
  - [ ] NPC-Texte aktiv formulieren
- [ ] Tutorial-Fablinge eindeutig benennen
  - [ ] Besitzer-Spitznamen durchgehend verwenden
  - [ ] Rückgabetexte bei einem und mehreren Fablingen prüfen
  - [ ] Auftragsanzeige und Fablingübersicht mit diesen Namen testen
- [ ] Danach erste spielbare Version mit echtem Einstieg testen

## 5. Danach: Aufträge und Spielfluss

- [x] Manuelle Auftragsabgabe ergänzen
- [x] Aufträge teilen Leih-Fablinge zu
- [x] Leih-Fablinge gehen bei erfolgreicher Abgabe zurück zum Fabelbund
- [x] Auftragsansicht zeigt Beschreibung, Fabling-Zuteilung und Belohnung
- [x] Tutorialabgabe bietet direkten Button für den nächsten Auftrag
- [x] Aktionen schlagen Folgeaktivitäten vor
- [x] Fabling-Detailansicht zeigt zuerst Aktivitätskategorien und danach konkrete Aktionen
- [x] Fablinge haben Futterpräferenzen
- [x] Grundinventar ergänzen
- [x] Laden mit ersten Futter-, Pflege- und Spielgegenständen ergänzen
- [x] Futter anwenden
- [ ] Auftragshauptlogik auf zustandsbasierte Abgaben ausrichten
  - [ ] Aufträge prüfen grundsätzlich Zielzustände, nicht absolvierte Aktionen
  - [ ] erlaubte Ausnahmen explizit halten, z.B. Betreuungszeit, passende Futterpräferenz oder spätere Sondermechaniken
  - [ ] alte `abgeschlossene_aktion`-/`abgeschlossene_aktionen`-Ziele aus normalen Aufträgen migrieren oder als Übergang markieren
  - [ ] Tests ergänzen, die neue Aufträge gegen reine Aktionsabschlussprüfung absichern
- [ ] Auftragsschema verbindlich machen
  - [ ] `planung/auftragsschema.md` finalisieren
  - [ ] aus `TODO.md` und `planung/stat-übersicht.md` darauf verweisen
  - [ ] neue Inhalte anhand dieses Schemas prüfen
- [ ] NPC-Fehlschlagantworten systematisch einführen
  - [ ] jeder Auftrag bekommt `fehlschlag.hinweis`
  - [ ] Text nennt allgemein, was am Fabling noch nicht passt
  - [ ] keine internen Zahlenwerte im Spielertext
  - [ ] keine exakte Klicklösung verraten
- [ ] Menügraph vollständig testen
  - [ ] Aufträge -> Fablinge -> Aktion -> Abholen -> Aufträge
  - [ ] Auftrag -> Laden -> Inventar -> Fablinge -> Auftrag
  - [ ] Inventar/Laden/Fablinge jeweils mit Rückweg zu Aufträgen
  - [ ] aktive Betreuung blockiert andere Menüs
  - [ ] passive Aktivitäten erlauben parallele Navigation
- [ ] Mehrere einfache Pflegeaufträge ergänzen
- [ ] Aufträge nicht nur als Zahlencheck denken
  - [ ] Betreuung über Zeit
  - [ ] passende Aktionen
  - [ ] Zustand des Fablings
- [ ] Erste Auswahl zwischen Aufträgen ermöglichen
- [ ] Belohnungen und Ruf sauberer staffeln
- [ ] Dauerhafte Grundbedürfnisse modellieren
  - [ ] Pflegezustand der Fablinge lässt graduell nach, damit regelmäßig Pflegebedarf entsteht
  - [ ] Futter wird über Zeit verdaut/verbraucht
  - [ ] Fablinge speichern einen internen Magen-/Sättigungszustand aus aufgenommenem Futter
  - [ ] Sättigung leert sich über Zeit
  - [ ] Hunger wird in Zustandstexten sichtbar, sobald der Magen-/Sättigungszustand niedrig ist
- [ ] Lieblingsfutter-Mechanik für MVP umsetzen
  - [ ] Solange Lieblingsfutter im Magen ist, werden positive Effekte wirksamer
  - [ ] Solange Lieblingsfutter im Magen ist, fallen negative Effekte schwächer aus
  - [ ] Stärke und Dauer des Lieblingsfutter-Bonus balancen
- [ ] Prüfen, ob der Spieler nach dem Tutorial sinnvoll weiß, was er als Nächstes tun kann

## 6. Betrieb und Testserver-Skripte

- [x] Start-/Stop-Skripte sauber einführen
  - [x] `scripts/start-bot.ps1` startet aktuell Testserver mit `5.0x`
  - [x] `scripts/stop-bot.ps1` beendet Bot-Prozesse
  - [x] README-Hinweise prüfen
  - [x] Prozessanzeige unterscheidet Hauptprozess und Python-Kindprozess
- [ ] Spielerreset als eigenes Skript ergänzen
  - [ ] löscht nur `spieler`, `fabelwesen`, `aktive_aufträge`, `aktivitäten`
  - [ ] erhält `server_konfigurationen`
  - [ ] optional kombiniert: Stop -> Reset -> Start
