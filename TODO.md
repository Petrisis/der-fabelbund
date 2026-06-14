# ToDos Der Fabelbund

Diese Liste ist unser gemeinsamer Arbeitsplan. Abgeschlossene Punkte bleiben kurz nachvollziehbar stehen, offene Punkte werden hier gesammelt und priorisiert.

## 1. Testumgebung verbessern

- [x] Testserver-Konfiguration vorbereitet
- [x] Testserver-spezifische Slash-Command-Synchronisierung
- [x] Konfigurierbarer Zeitfaktor für schnellere Tests
- [x] Nicht-destruktive Testoptionen vorbereitet
- [x] Start-/Stop-Skripte für den lokalen Testbot ergänzt
- [x] Spielerreset als eigenes Skript ergänzen
  - [x] löscht nur `spieler`, `fabelwesen`, `aktive_aufträge`, `aktivitäten`
  - [x] erhält `server_konfigurationen`
  - [ ] optional kombiniert: Stop -> Reset -> Start

## 2. Stat-Übersicht und Auftragsschema

- [x] Übersicht aller Fabling-Stats erstellen
  - [x] Zustandswerte
  - [x] Beziehungswerte
  - [x] Trainingswerte
  - [x] Risiko-/Gesundheitswerte
  - [x] Charakter-/Eigenheitswerte
- [x] Übersicht aller Spielerwerte erstellen
  - [x] Geld
  - [x] Ruf
  - [x] Ställe
  - [x] Lizenzen
  - [x] Fortschritt/Tutorialstatus
  - [x] ggf. Reputation nach Bereichen
- [x] MVP-relevante Stats und vorbereitete Stats festhalten
- [x] Balancing-Grundlage in `planung/stat-übersicht.md` dokumentieren
- [x] Auftragsschema in `planung/auftragsschema.md` dokumentieren
- [ ] Auftragsschema technisch vollständig durchsetzen
  - [ ] Aufträge prüfen grundsätzlich Zielzustände, nicht absolvierte Aktionen
  - [ ] erlaubte Ausnahmen explizit halten, z.B. Betreuungszeit, passende Futterpräferenz oder spätere Sondermechaniken
  - [ ] alte `abgeschlossene_aktion`-/`abgeschlossene_aktionen`-Ziele aus normalen Aufträgen migrieren oder als Übergang markieren
  - [ ] Tests ergänzen, die neue Aufträge gegen reine Aktionsabschlussprüfung absichern

## 3. Betreuung, Ställe und Content-Grundlage

- [x] Pflege- und Ruheaktionen erweitern
- [x] Erste Spiel-/Bindungsaktionen ergänzen
- [x] Erste leichte Trainingsaktionen ergänzen
- [x] Check-Aktionen ergänzen
- [x] Abbruchkonsequenzen systematisch modellieren
- [x] Doktorbesuch freischalten und Kostenmodell ergänzen
- [x] Stall- und Betreuungsansicht zusammenführen
  - [x] `/stall` und `/betreuung` durch `/fablinge` ersetzen
  - [x] Fabling-Auswahl für bis zu 25 Fablinge
  - [x] Futter- und Stallpriorität in der Fabling-Detailansicht behalten
  - [x] Betreuungsaktivitäten pro ausgewähltem Fabling starten
  - [x] Passive Aktivitäten erlauben Rücknavigation, aktive Betreuung bindet den Spieler
  - [x] Redundante Folgeaktionslisten aus Aktivitätsergebnissen entfernen
- [x] Laden und Inventar als erste Ökonomie-Grundlage ergänzen
- [x] Futterpräferenzen pro Fabling ergänzen
- [x] Futterpräferenz-Dropdown auf vorhandenes Inventar begrenzen
- [ ] Menügraph vollständig testen
  - [ ] Aufträge -> Fablinge -> Aktion -> Abholen -> Aufträge
  - [ ] Auftrag -> Laden -> Inventar -> Fablinge -> Auftrag
  - [ ] Inventar/Laden/Fablinge jeweils mit Rückweg zu Aufträgen
  - [ ] aktive Betreuung blockiert andere Menüs
  - [ ] passive Aktivitäten erlauben parallele Navigation

## 4. Tutorial und Einstieg

- [x] Tutorialstatus als Spielerwert einführen
- [x] Neuer Spieler startet ins Pflicht-Tutorial
- [x] Öffentlicher Einstieg über die Auftragswand
- [x] Tutorial vergibt Probe-Fablinge
- [x] Tutorial erklärt Schritt für Schritt, funktional
  - [x] Fablinge und Ställe
  - [x] Pflege und Ruhe
  - [x] Laden, Inventar und Ausrüstung
  - [x] Futterpräferenz
  - [x] aktive und passive Betreuung
  - [x] Training
  - [x] Check
  - [x] Starterwahl
  - [x] Abschluss als offizielles Mitglied
- [x] Tutorialzeiten auf kurze Test- und Einstiegsspannen bringen
  - [x] keine 30-Minuten-Bedingung in der Einführung verwenden
  - [x] zentrale Tutorialaktivitäten auf ca. 2-5 Minuten Spielzeit senken
  - [x] Testserver läuft aktuell über `scripts/start-bot.ps1` mit `10.0x`
- [x] Spieler kann nach dem Schließen einer ephemeren Ansicht wieder ins Tutorial zurückfinden
- [ ] Tutorial als spielbaren Qualitätsdurchlauf prüfen
  - [ ] frischen Durchlauf mit Spielerreset testen
  - [ ] jeden Schritt einmal normal abschließen
  - [ ] jeden Auftrag einmal absichtlich zu früh abgeben
  - [ ] prüfen, ob NPC-Hinweis verständlich sagt, was noch nicht passt
  - [ ] prüfen, ob Buttons an jeder Stelle zum nächsten sinnvollen Menü führen
- [ ] Tutorialziele vollständig zustandsbasiert machen
  - [ ] keine Tutorialabgabe darf `abgeschlossene_aktion` oder `abgeschlossene_aktionen` prüfen
  - [ ] Mehrfach-Fabling-Aufträge nutzen zielwertbasierte Einzelziele pro Fabling
  - [ ] Zeitbedingungen bleiben erlaubt, wenn Zeit selbst Lernziel ist
  - [ ] Tests ergänzen, die fehlschlagen, wenn Tutorialaufträge wieder Aktionsabschluss prüfen
- [ ] Tutorialtexte final glätten
  - [ ] keine Slash-Command-Verweise
  - [ ] keine redundanten "danach abholen/abgeben"-Erklärungen
  - [ ] Aufgabenblock beschreibt Zielzustand statt Klickanweisung
  - [ ] NPC-Texte aktiv formulieren
  - [ ] Tätigkeiten funktional erklären, z.B. müde -> Ruhe, Fell vernachlässigt -> Pflege, Vertrauen -> aktive Betreuung
- [ ] Tutorial-Fablinge eindeutig benennen
  - [ ] Besitzer-Spitznamen durchgehend verwenden
  - [ ] Rückgabetexte bei einem und mehreren Fablingen prüfen
  - [ ] Auftragsanzeige und Fablingübersicht mit diesen Namen testen
- [x] Nach Starterwahl Chronikmeldung vorbereiten

## 5. Nächster Spielfluss nach dem Tutorial

- [x] Manuelle Auftragsabgabe ergänzen
- [x] Aufträge teilen Leih-Fablinge zu
- [x] Leih-Fablinge gehen bei erfolgreicher Abgabe zurück in die Obhut ihres Auftraggebers
- [x] Auftragsansicht zeigt Beschreibung, Fabling-Zuteilung und Belohnung
- [x] Tutorialabgabe bietet direkten Button für den nächsten Auftrag
- [x] Fabling-Detailansicht zeigt zuerst Aktivitätskategorien und danach konkrete Aktionen
- [ ] NPC-Fehlschlagantworten systematisch einführen
  - [ ] jeder Auftrag bekommt `fehlschlag.hinweis`
  - [ ] Text nennt allgemein, was am Fabling noch nicht passt
  - [ ] keine internen Zahlenwerte im Spielertext
  - [ ] keine exakte Klicklösung verraten
- [ ] Mehrere einfache Pflegeaufträge ergänzen
- [ ] Erste Auswahl zwischen Aufträgen ermöglichen
- [ ] Belohnungen und Ruf sauberer staffeln
- [ ] Prüfen, ob der Spieler nach dem Tutorial sinnvoll weiß, was er als Nächstes tun kann

## 6. Systeme nach dem Tutorial-MVP

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
- [ ] Wettbewerbe ausarbeiten
- [ ] Zucht vorbereiten
- [ ] Handel und Markt vorbereiten
- [ ] Events und Saisons vorbereiten
