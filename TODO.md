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
  - [x] Bundsiegel
  - [x] Ruf
  - [x] Ställe
  - [x] Lizenzen
  - [x] Fortschritt/Tutorialstatus
  - [x] ggf. Reputation nach Bereichen
- [x] MVP-relevante Stats und vorbereitete Stats festhalten
- [x] Balancing-Grundlage in `planung/stat-übersicht.md` dokumentieren
- [x] Auftragsschema in `planung/auftragsschema.md` dokumentieren
- [ ] Auftragsschema technisch vollständig durchsetzen
  - [x] öffentliche Standardaufträge prüfen Zielzustände, nicht absolvierte Aktionen
  - [x] erlaubte Ausnahmen explizit halten, z.B. Betreuungszeit, passende Futterpräferenz oder spätere Sondermechaniken
  - [x] alte `abgeschlossene_aktion`-/`abgeschlossene_aktionen`-Ziele aus normalen Aufträgen migrieren
  - [x] Tests ergänzen, die neue öffentliche Aufträge gegen reine Aktionsabschlussprüfung absichern
  - [ ] technische Übergangsfelder `abgeschlossene_aktion` und `abgeschlossene_aktionen` später entfernen oder klar als Legacy markieren

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
  - [x] jeden Schritt einmal normal abschließen
  - [ ] jeden Auftrag einmal absichtlich zu früh abgeben
  - [x] prüfen, ob NPC-Hinweis grundsätzlich sagt, was noch nicht passt
  - [ ] prüfen, ob Buttons an jeder Stelle zum nächsten sinnvollen Menü führen
- [ ] Tutorialziele vollständig zustandsbasiert machen
  - [x] keine Tutorialabgabe darf `abgeschlossene_aktion` oder `abgeschlossene_aktionen` prüfen
  - [x] Mehrfach-Fabling-Aufträge nutzen zielwertbasierte Einzelziele pro Fabling
  - [x] Zeitbedingungen bleiben erlaubt, wenn Zeit selbst Lernziel ist
  - [ ] Tests ergänzen, die fehlschlagen, wenn Tutorialaufträge wieder Aktionsabschluss prüfen
- [ ] Tutorialtexte final glätten
  - [x] keine Slash-Command-Verweise in Tutorial-Auftragstexten
  - [ ] keine redundanten "danach abholen/abgeben"-Erklärungen
  - [ ] Aufgabenblock beschreibt Zielzustand statt Klickanweisung
  - [x] NPC-Texte aktiv formulieren
  - [x] Tätigkeiten funktional erklären, z.B. müde -> Ruhe, Fell vernachlässigt -> Pflege, Vertrauen -> aktive Betreuung
- [ ] Tutorial-Fablinge eindeutig benennen
  - [x] Besitzer-Spitznamen in Tutorialaufträgen durchgehend verwenden
  - [x] Rückgabetexte bei einem und mehreren Fablingen per Test absichern
  - [ ] Auftragsanzeige und Fablingübersicht mit diesen Namen im Discord-Flow testen
- [x] Nach Starterwahl Chronikmeldung vorbereiten

## 5. Nächster Spielfluss nach dem Tutorial

- [x] Manuelle Auftragsabgabe ergänzen
- [x] Aufträge teilen Leih-Fablinge zu
- [x] Leih-Fablinge gehen bei erfolgreicher Abgabe zurück in die Obhut ihres Auftraggebers
- [x] Auftragsansicht zeigt Beschreibung, Fabling-Zuteilung und Belohnung
- [x] Tutorialabgabe bietet direkten Button für den nächsten Auftrag
- [x] Fabling-Detailansicht zeigt zuerst Aktivitätskategorien und danach konkrete Aktionen
- [ ] NPC-Fehlschlagantworten systematisch einführen
  - [x] jeder Tutorialauftrag bekommt `fehlschlag.hinweis`
  - [x] Tutorialtexte nennen allgemein, was am Fabling noch nicht passt
  - [x] normale öffentliche Aufträge bekommen `fehlschlag.hinweis`
  - [x] Text nennt allgemein, was am Fabling noch nicht passt
  - [x] keine internen Zahlenwerte im Spielertext
  - [x] keine exakte Klicklösung verraten
- [x] Mehrere einfache Standardaufträge ergänzen
  - [x] Pflegeauftrag mit IST-/SOLL-Zustand
  - [x] Ruheauftrag mit IST-/SOLL-Zustand
  - [x] Babysitting-Auftrag mit Betreuungszeit und Stabilitätsziel
  - [x] Trainingsauftrag mit Wettbewerbsziel
  - [x] Futterzuweisung bleibt auf das Tutorial beschränkt
- [x] Erste Auswahl zwischen Aufträgen ermöglichen
- [ ] Belohnungen und Ruf sauberer staffeln
- [ ] Prüfen, ob der Spieler nach dem Tutorial sinnvoll weiß, was er als Nächstes tun kann

## 6. Systeme nach dem Tutorial-MVP

- [ ] Dauerhafte Grundbedürfnisse modellieren
  - [ ] Pflegezustand der Fablinge lässt graduell nach, damit regelmäßig Pflegebedarf entsteht
  - [x] Futter wird über Zeit verbraucht
  - [x] Fablinge speichern einen internen Sättigungszustand
  - [x] Sättigung leert sich über Zeit
  - [x] Fablinge fressen automatisch aus dem Inventar
  - [x] Futterreihenfolge: bevorzugtes Futter, neutrales Futter, sonstiges Futter
  - [x] Lieblingsfutter gibt keinen Nährwertbonus
  - [ ] niedrige Sättigung deutlicher in Zustandstexten sichtbar machen
  - [ ] kritische Hungerereignisse in die Chronik posten
  - [ ] Entzug durch den Fabelbund bei kritischer Gesundheit modellieren
  - [ ] Ruf-/Rangverlust bei Entzug modellieren
- [ ] Futterökonomie balancen
  - [x] neutrales Basisfutter ergänzen
  - [x] Richtwert vorbereiten: etwa fünf normale Futtereinheiten pro Fabling und Tag
  - [ ] Preise nach erstem Playtest auf moderate tägliche Deflation prüfen
- [ ] Wettbewerbe ausarbeiten
- [ ] Zucht vorbereiten
- [ ] Handel und Markt vorbereiten
- [ ] Events und Saisons vorbereiten
