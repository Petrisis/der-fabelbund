# Issue-Workflow

GitHub-Issues bleiben die Arbeitsliste für konkrete Fehler, Playtestfunde und kleinere Verbesserungen.

## Zustände

- Direkt schließen, wenn Akzeptanzkriterien umgesetzt, getestet und gepusht sind.
- Offen lassen, wenn eine Änderung zwar umgesetzt ist, aber im Testserver manuell geprüft werden soll.
- Offen lassen und neu zuschneiden, wenn die gewünschte Lösung technisch oder fachlich noch nicht entschieden ist.

## Kommentare

Nach einem umsetzenden Commit wird das Issue kommentiert:

- welcher Commit die Änderung enthält
- ob das Issue geschlossen wird
- ob noch manuelle Prüfung im Testserver nötig ist
- welche technische Einschränkung offen bleibt, falls das Issue nicht umgesetzt wurde

## Playtest-Prüfung

Issues mit umgesetztem Code, aber offenem Live-Test, bleiben offen. Nach bestätigtem Playtest werden sie geschlossen.

## Beispiel

Eine serverseitig getestete Regeländerung kann direkt geschlossen werden. Ein Text- oder UI-Verhalten, das im Discord-Flow wirken muss, bleibt bis zum Playtest offen.
