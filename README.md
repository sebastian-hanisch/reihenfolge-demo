# Wann zählt die Reihenfolge? Elfmeterschießen und Wahlreihenfolge – Streamlit-Demo

<!-- Live-Link nach dem Deploy direkt hierher setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-reihenfolge-demo.streamlit.app/)** -->

Wurzel der Linie **„Wettbewerbsverzerrung erklärt“** (Bereich Wertung und Wahl, Konzepte-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“). Die Demo fragt: **Bei gleich starken Seiten, wann entscheidet die Reihenfolge überhaupt?**
Zwei Beispiele: das **Elfmeterschießen** (fünf Schüsse je Mannschaft mit vorzeitigem Abbruch, danach Sudden Death; Reihenfolge ABAB oder ABBA) und das **abwechselnde Wählen unteilbarer Güter** (reihum, Schlange, Thue-Morse) im zweiten Reiter. Alles mit erfundenen Mannschaften und
Zufallsbewertungen, keine Felddaten, keine echten Vereine.

Abgrenzung im Portfolio: [`round-robin-demo`](https://github.com/sebastian-hanisch/round-robin-demo) konstruiert den Spielplan eines Rundenturniers (Zirkelmethode, Berger-Tafeln), [`bracket-seeding-demo`](https://github.com/sebastian-hanisch/bracket-seeding-demo) die Setzliste im K.-o.-System;
beide legen fest, **wer gegen wen** antritt, nicht, wer innerhalb einer Begegnung zuerst schießt oder wählt. [`unteilbare-gueter-demo`](https://github.com/sebastian-hanisch/unteilbare-gueter-demo) vergleicht fünf Verteilungsregeln auf denselben Bewertungen nach Neidfreiheit, EF1, EFX und Pareto-Optimalität;
„Reihum“ ist dort eine der fünf Regeln, die Frage nach dem Vorteil der ersten Person und die Wahlfolgen Schlange und Thue-Morse gibt es dort nicht. Umgekehrt nimmt diese Demo keine Fairnesskriterien in den Blick. Ein Rückverweis in `unteilbare-gueter-demo` steht noch nicht (dort nichts geändert).

## Ergebnis in Kürze

Alle Zahlen sind gemessen (`tests/test_claims.py`); das Elfmeterschießen exakt, die Wahlreihenfolge als Mittel über 2.000 Bewertungsmatrizen (5 feste Zufalls-Seeds zu je 400).

- **Ohne Abhängigkeit zählt die Reihenfolge nicht.** Zwei gleich starke Mannschaften, 5 Schüsse, Schüsse unabhängig (d = 0): die erste Mannschaft gewinnt bei ABAB und bei ABBA **genau zu 50 %** für p = 0,3, 0,5, 0,7 und 0,9. Auch bei ungleich starken Mannschaften (A mit 0,8, B mit 0,6) sind beide Reihenfolgen gleich (79,95 %).
- **Abhängigkeit erzeugt den Vorteil, ABBA dämpft ihn.** Trifft ein Schütze im Rückstand mit p − d (p = 0,75, 5 Schüsse), gewinnt die erste Mannschaft bei ABAB mit **54,5 %** (d = 0,05), 58,3 % (0,10), 61,5 % (0,15), 66,7 % (0,25); bei ABBA mit **50,7 %**, 51,5 %, 52,5 %, 55,0 %.
- **Bei ABAB hängt der Vorteil nicht an der Schusszahl:** die Gewinnchance der ersten Mannschaft ist (1 − p + d) / (2 (1 − p) + d), in allen 1.872 geprüften Zellen (R = 1 bis 8, p − d mindestens 0,05) mit einer Abweichung unter 1e-12 (gemessen, nicht bewiesen); **bei ABBA** liegt sie in 1.800 von 1.800 Zellen mit d > 0 näher an 50 % und nie darunter (kleinster Wert 50,04 %, größter 57,1 %).
- **Eine Deutung (Messung, keine Herleitung):** bei ABAB schießt die zweite Mannschaft öfter im Rückstand (Standardfall: 3,29 erwartete Schüsse gegen 0,95 der ersten), bei ABBA ausgeglichener (2,35 gegen 1,92).
- **Der vorzeitige Abbruch ändert den Sieger nie** (0 von 1.024 Schussfolgen), er spart nur Schüsse.
- **Wahlreihenfolge** (2 Personen, 10 Güter, unabhängiger Geschmack): die erste Person erreicht bei **Reihum** im Mittel 0,249 mehr als die letzte (Standardfehler 0,017), bei **Schlange** 0,068, bei **Thue-Morse** −0,080 (die zweite Person liegt vorn). Bei 9 Gütern wählt die erste Person einmal öfter: 0,416 / 0,199 / −0,212.

## Kernfrage

Beim Elfmeterschießen schießt eine Mannschaft zuerst; es gibt eine Debatte, ob das einen Vorteil bringt. Das Modell trennt zwei Fälle: **unabhängige Schüsse** (jeder Schuss trifft mit p, egal wie es steht) und **abhängige Schüsse** (wer zurückliegt, trifft mit p − d). Die Demo zeigt für ABAB und ABBA, dass im ersten Fall die Reihenfolge keinen Vorteil erzeugt (die Begründung gilt für jede Reihenfolge der Schüsse, gerechnet sind diese beiden), und rechnet im zweiten Fall exakt, wie groß er ist und wie viel eine andere Reihenfolge davon nimmt.
Dieselbe Frage stellt der zweite Reiter dem Wählen unteilbarer Güter: Wer zuerst wählt, nimmt sich das Beste; wie viel das nach der gesamten Verteilung ausmacht, hängt an der Wahlfolge.

## Modell

**Elfmeterschießen** (`rei_algorithm.py`). Mannschaft A schießt als erste. Ein Schütze trifft mit p, wenn seine Mannschaft vor dem Schuss nicht zurückliegt, und mit p − d, wenn sie zurückliegt. Regelzeit: R Schüsse je Mannschaft (Voreinstellung 5); sie endet vorzeitig, sobald eine Seite auch dann nicht mehr einzuholen wäre, wenn sie
alle restlichen Schüsse trifft und die andere alle verfehlt. Bei Gleichstand folgt der **Sudden Death** in Paaren aus je einem Schuss je Mannschaft, bis ein Paar trennt (Treffer und Fehlschuss). **ABAB:** A schießt in jedem Paar zuerst, auch im Sudden Death. **ABBA:** in den Paaren 1, 3, 5, … beginnt A, in 2, 4, 6, … B; bei fünf Schüssen beginnt das Paar 6 mit B.
Im Sudden Death liegt nur der Zweite eines Paares zurück, und nur nach einem Treffer des Ersten.

**Wahlreihenfolge** (`rei_choice.py`). k Personen (2 bis 4) wählen abwechselnd je ein unteilbares Gut aus m Gütern (4 bis 24); jede Person nimmt das ihr wertvollste freie Gut (Gleichstand: kleinere Gutnummer); Bewertungen sind additiv. Wahlfolgen: **Reihum** (t mod k), **Schlange** (vorwärts, rückwärts, vorwärts, …), **Thue-Morse** (Stellensumme von t zur Basis k modulo k; für k = 2 die Thue-Morse-Folge ABBABAAB…, für k > 2 die Verallgemeinerung nach Prouhet,
aus dem Gedächtnis, nicht nachgelesen). Geschmack: v = w · c + (1 − w) · e mit gleichverteilten Zufallszahlen c (je Gut, für alle gleich) und e (je Person und Gut); w = 0 heißt unabhängiger Geschmack, w = 1 gleiche Bewertung aller. Gemessen wird der **Vorteil der ersten gegenüber der letzten Person**, gemittelt über die Bewertungsmatrizen.
Formeln und Symbole im 📐-Expander der App.

## Methodik

- **Kleine Einheiten mit Mini-Instanzen von Hand** (DEMO-PLAYBOOK §1b): Schussfolge beider Reihenfolgen, Abbruchregel an der Grenze, Ein-Schuss-Fall mit Rechnung im Kommentar (R = 1, p = 0,5, d = 0,1: 6/11), erwartete Schüsse und Schüsse im Rückstand von Hand, Monte-Carlo-Simulation mit einem vorgegebenen Zufallsstrom; Wahlfolgen für zwei bis vier Personen, Zuteilung an einer 2 × 3-Bewertungsmatrix.
- **Orakel** (`tests/test_oracle_reihenfolge.py`, anderer Rechenweg): (1) Aufzählung aller 2^(2R) Schussfolgen der Regelzeit (R bis 6) mit eigener Abbruchlogik, auch für ungleich starke Mannschaften und verschiedene d, gegen die Vorwärtsrekursion des Kerns (Sieg, Gleichstand, erwartete Schüsse, Schüsse im Rückstand); (2) der Sudden Death in geschlossener Form mit Brüchen (`fractions`) gegen die Paar-für-Paar-Schleife;
  (3) der Abbruch ändert den Sieger auf allen 1.024 Schussfolgen nie; (4) die Monte-Carlo-Simulation mit dem Zufallsgenerator der Demo gegen die exakte Wahrscheinlichkeit und die erwartete Schusszahl im Band von 4,5 Standardfehlern; (5) die Wahlreihenfolge bei w = 0: der Erwartungswert aus der Aufzählung **aller Rangprofile** gegen die Messreihe;
  (6) die vektorisierte Wahl gegen eine Schleife in reinem Python, Thue-Morse (k = 2) gegen die Parität der Binärstellen.
- **Eigenschaftstests** (`tests/test_eigenschaften_reihenfolge.py`): ohne Abhängigkeit sind beide Reihenfolgen gleich (auch ungleich stark); die ABAB-Formel in allen Zellen; ABBA näher an 50 %; Umnummerieren der Güter und Skalieren der Werte; bei gleicher Bewertung begünstigt Reihum nie eine spätere Person; Prouhet-Ausgewogenheit der Thue-Morse-Folge.
- **Zufall:** SplitMix64 (`rei_rng.py`, wörtliche Kopie der geprüften Vorlage aus den Website-Werkzeugen, `tests/test_copies.py`), plattformfest. Die Messreihen der Wahlreihenfolge ziehen ihre Zahlen vektorisiert (`random_stream`), bitgleich mit dem Generator (Test). Gleiche Reglerwerte und gleicher Zufalls-Seed geben dasselbe Ergebnis.
- **Verdikte** sind reine Funktionen (`tests/test_verdicts.py`); die Texte der Presets sind gegen die Rechnung getestet (`tests/test_presets.py`).

## Befunde (gemessen, keine Behauptungen)

Elfmeterschießen: exakt (Rekursion), zwei gleich starke Mannschaften, A schießt zuerst. Wahlreihenfolge: Mittel über 2.000 Bewertungsmatrizen (5 Zufalls-Seeds 100000 bis 100004 zu je 400); die Tests prüfen ein Band von ±0,0006 um die genannte Zahl.

| Frage | Befund | Test |
|---|---|---|
| Stimmt der Kern? | Regelzeit gleich der Aufzählung aller Schussfolgen (R = 1 bis 5, acht Fälle für p und d, bis 1e-12), Sudden Death gleich der geschlossenen Form mit Brüchen, Wahl gleich der Schleife in reinem Python und gleich dem Erwartungswert aus allen Rangprofilen (k = 2: m = 4, 5; k = 3: m = 4) im Band von 4,5 Standardfehlern | `test_oracle_reihenfolge.py` |
| Zählt die Reihenfolge ohne Abhängigkeit? | **Nein.** d = 0, 5 Schüsse: A gewinnt bei p = 0,3 / 0,5 / 0,7 / 0,9 genau zu 50,00 % in beiden Reihenfolgen; bei A mit 0,8 gegen B mit 0,6 gleich 79,95 % in beiden | `test_claims.py::test_independent_shots_give_fifty_percent_in_both_orders_for_four_values_of_p`, `…::test_unequal_teams_without_dependence_have_the_same_probability_in_both_orders`, `test_eigenschaften_reihenfolge.py` (alle Paare aus neun Werten von p, R = 1 bis 8) |
| Wie groß ist der Vorteil mit Abhängigkeit (p = 0,75, 5 Schüsse)? | d = 0,05 / 0,10 / 0,15 / 0,25: **ABAB 54,5 / 58,3 / 61,5 / 66,7 %**, **ABBA 50,7 / 51,5 / 52,5 / 55,0 %**; der Standardfall bei ABAB sind 6/11 | `test_claims.py::test_first_team_with_dependence_for_the_four_values_of_d`, `…::test_abab_at_the_standard_case_is_six_elevenths` |
| Hängt ABAB an der Schusszahl? | Nein: (1 − p + d) / (2 (1 − p) + d) in allen **1.872** Zellen (R = 1 bis 8; 1.800 mit d > 0, 72 mit d = 0; p − d mindestens 0,05), größte Abweichung unter 1e-12; **gemessen, nicht bewiesen** | `test_claims.py::test_abab_follows_the_sudden_death_formula_for_every_number_of_shots_in_1872_cells` |
| Dämpft ABBA überall? | In **1.800 von 1.800** Zellen mit d > 0 näher an 50 % als ABAB, nie unter 50 % (kleinster Wert 50,04 %, größter 57,1 %) | `test_claims.py::test_abba_is_closer_to_fifty_percent_in_1800_of_1800_cells_and_never_below` |
| Wo entsteht der Vorteil (Standardfall, d = 0,05)? | **ABAB:** A gewinnt die Regelzeit mit 41,3 %, B mit 34,4 %, Gleichstand 24,3 %; den Sudden Death gewinnt A mit 54,5 %. **ABBA:** 38,8 % und 36,8 %, im Sudden Death gewinnt A nur 48,8 %: dort hat die zweite Mannschaft den Vorteil; das Paar 6 beginnt mit ihr (Deutung, nicht getrennt gemessen) | `test_claims.py::test_where_the_advantage_arises_in_the_standard_case` |
| Wer schießt öfter im Rückstand? | Erwartete Schüsse im Rückstand (d = 0,05): ABAB A 0,95, B 3,29; ABBA A 1,92, B 2,35; bei d = 0: ABAB 0,99 und 3,44, ABBA 2,05 und 2,38. Bei ABAB öfter B als A in 1.800 von 1.800 Zellen, die Lücke bei ABBA in allen kleiner (Deutung: dort entsteht der Abschlag-Vorteil, nicht als Ursache bewiesen) | `test_claims.py::test_shots_taken_while_trailing` |
| Was bringt der Abbruch? | Ohne Abhängigkeit (p = 0,75, 5 Schüsse): die Regelzeit endet in 44,3 % vor dem letzten Schuss, erwartet 9,25 statt 10 Schüsse, mit Sudden Death 10,80 statt 11,55; **der Sieger ändert sich nie** (0 von 1.024 Schussfolgen) | `test_claims.py::test_early_stop_saves_shots_but_not_the_winner`, `test_oracle_reihenfolge.py::test_early_stop_never_changes_the_winner_on_all_1024_sequences` |
| Schusszahl (p = 0,75, d = 0,10)? | ABAB 58,3 % bei jeder Schusszahl von 1 bis 8; ABBA 52,4 % bei 1, 51,5 % bei 5, 51,4 % bei 8 Schüssen | `test_claims.py::test_number_of_shots_per_team` |
| Stimmt die Monte-Carlo-Simulation? | 10.000 simulierte Elfmeterschießen (Zufalls-Seed 100000, Standardfall): 55,2 % gegen exakt 54,5 %, Band ±3 Standardfehler = ±1,5 Prozentpunkte; eine Zahl, kein Mittel über Zufalls-Seeds | `test_claims.py::test_the_replay_of_the_app_for_the_standard_case` |
| Vorteil der ersten Person beim Wählen (k = 2, m = 10, w = 0)? | **Reihum +0,249**, Schlange +0,068, **Thue-Morse −0,080** (Standardfehler je 0,017; Reihum je Zufalls-Seed 0,218 bis 0,281). Gesamtwert bei Reihum: erste Person 3,332, letzte 3,083. Bei w = 1: +0,457 / +0,092 / −0,098 | `test_claims.py::test_advantage_of_the_first_person_by_rule`, `…::test_standard_errors_and_seed_ranges_of_the_default_case`, `…::test_mean_totals_of_the_default_case` |
| Andere Personen- und Gütermengen? | Bei 9 Gütern (die erste Person wählt 5-mal, die zweite 4-mal; bei Thue-Morse umgekehrt): +0,416 / +0,199 / −0,212. Drei Personen, 12 Güter: +0,346 / −0,102 / −0,121; vier Personen, 12 Güter: +0,373 / +0,205 / −0,045 | `test_claims.py::test_advantage_of_the_first_person_by_rule`, `…::test_picks_per_person_in_the_odd_case` |
| Hängt es am Geschmack (k = 2, m = 10)? | In den 11 gemessenen Werten von w liegt Reihum zwischen +0,224 und +0,457 (bei w = 0: +0,249, bei w = 1: +0,457), Schlange zwischen +0,060 und +0,092, Thue-Morse zwischen −0,098 und −0,052 | `test_claims.py::test_taste_similarity_series_of_reihum` |
| Hängt es an der Gütermenge (k = 2, w = 0, m = 4, 6, 8, 12, 16)? | Reihum zwischen +0,201 und +0,266, in allen fünf Werten positiv; Schlange zwischen −0,034 und +0,073 und Thue-Morse zwischen −0,141 und +0,041 **wechseln das Vorzeichen** (Schlange: +0,073 bei m = 6 gegen etwa −0,03 bei m = 4, 8, 12, 16, die kleinen Werte liegen nur ein bis drei Standardfehler von null entfernt; Thue-Morse: größter Betrag −0,141 bei m = 6); bei m = 4 sind beide dieselbe Folge ABBA | `test_claims.py::test_number_of_goods_series_for_two_persons`, `…::test_for_m_equal_four_schlange_and_thue_morse_coincide` |
| Presets | Jede Hilfe passt zur Rechnung (Unabhängig = genau 50 %; bei Druck ABAB schießt die zweite Mannschaft öfter im Rückstand, bei ABBA ist der Vorteil kleiner; bei ähnlichem Geschmack ist der Vorteil bei Reihum größer als bei unabhängigem) | `test_presets.py`, `test_app.py::test_every_preset_shows_the_verdict_of_its_own_settings` |

## Befunde und Korrekturen gegenüber dem Plan

- **„ABBA“ der Vormessung war die Thue-Morse-Folge.** Die Vormessung (M1) rechnete die Reihenfolge ABBABAABBA und fand dort einen Wert knapp unter 50 %. Die Demo setzt ABBA nach dem Auftrag um (Paare wechseln: AB, BA, AB, BA, AB, danach im Sudden Death weiter, das Paar 6 beginnt mit B); dort liegt die erste Mannschaft **über** 50 % (50,7 % bei d = 0,05).
  Thue-Morse im Elfmeterschießen ist in der Demo nicht gerechnet; die Vormessungszahl für ABBA gilt nicht für ABBA hier.
- **ABAB: ein Satz, den der Plan nicht hatte.** Die Gewinnchance der ersten Mannschaft hängt in allen geprüften Zellen nicht an der Schusszahl; die Vormessung hatte nur 5 Schüsse.
- **Die Vormessung ABAB** (54,5 % bei d = 0,05 und p = 0,75) stimmt mit der Demo überein (54,5 %).
- **Eine geschlossene Form für die Wahl war falsch.** Als Orakel war zuerst vorgesehen, der Erwartungswert des besten freien Guts im Schritt t sei (m − t) / (m − t + 1). Das gilt nicht: Was einer Person bleibt, hängt von ihren früheren Wahlen ab (sie hat ihre besten Güter schon genommen). Die Messreihe widersprach der Formel deutlich (Scratch-Lauf, k = 2, m = 9, Reihum, w = 0: rund 14 Standardfehler Abstand, nicht im Test).
  Orakel ist jetzt die Aufzählung aller Rangprofile (bei w = 0 hängt der Ausgang nur an den Rangfolgen; ein Gut auf Platz pos hat den Erwartungswert (m − pos) / (m + 1)).
- **Wahlreihenfolge als Reiter dieser Demo** statt als eigene Demo: ein Reiter mit Abgrenzung zu `unteilbare-gueter-demo`.
- **Port:** 10060 ist nur vergeben (nicht in `.claude/launch.json`).

## Ehrliche Grenzen

- **Der Abschlag d ist ein Regler, keine Schätzung.** Dass Schützen im Rückstand schlechter treffen, ist hier eine Annahme; ob und wie stark das echt ist und ob es einen Startvorteil gibt, sagt die Demo nicht. Zur Wirklichkeit (nur aus Suchergebnissen, nicht im Volltext gelesen): die IFAB hat ABBA im Elfmeterschießen 2018 verworfen, die Evidenz zu einem Startvorteil ist uneinheitlich, in Daten ist er umstritten.
- **Nur zwei gleich starke Mannschaften in der App.** Die Rechnung kann ungleiche p und d (Tests), die App zeigt nur gleich starke und eine Zeile mit ungleichen ohne Abhängigkeit.
- **Der Abschlag hängt nur vom Rückstand ab,** nicht von der Höhe des Rückstands, der Nummer des Schusses oder dem Schützen.
- **ABBA hier heißt: Paare wechseln den Beginn.** Andere Reihenfolgen (Thue-Morse im Elfmeterschießen, ABBAAB…) sind nicht gerechnet.
- **Wahlreihenfolge: Stichprobe.** 2.000 Bewertungsmatrizen je Zelle; Unterschiede unterhalb von etwa zwei Standardfehlern sind kein Befund. Die Standardfehler gelten für das Mittel über alle Matrizen, die Spalten je Zufalls-Seed zeigen die Streuung zwischen fünf Messreihen. Das Geschmacksmodell (gleichverteilt, ein gemeinsamer Wert je Gut mit Gewicht w) ist eine Annahme.
- **Ehrliche Bewertung, additiv.** Wer weiß, nach welcher Folge gewählt wird, kann strategisch anders bewerten oder wählen; das ist nicht modelliert. Wie sich die Zahlen mit der Zahl der Güter ändern (Experiment 3), ist für Vielfache von k gemessen; die Vorzeichen von Schlange und Thue-Morse wechseln dabei (die kleinen Werte liegen bei ein bis drei Standardfehlern), ein einfaches Gesetz ist nicht belegt.
- **Mehrere Wahlen sind nicht unabhängig voneinander** (frühere Wahlen verändern, was später bleibt); die Standardfehler berücksichtigen nur die Streuung zwischen den Bewertungsmatrizen.
- **Nur mit dem Streamlit-Testrahmen (AppTest) geprüft**, nicht mit echten Mausklicks im Browser und nicht mit dem Linux-Check (Docker).

## Bewusst nicht umgesetzt

- **Eine „Catch-Up“-Wahlfolge** (der Zurückliegende wählt weiter): der Wortlaut einer vollständig beschriebenen Regel liegt nicht vor, eine eigene Ableitung wäre keine geprüfte Regel, ein Orakel gäbe es nicht.
- **Thue-Morse oder andere Folgen im Elfmeterschießen,** ungleich starke Mannschaften als Regler, Abschlag nach Höhe des Rückstands.
- **Fairnesskriterien (Neid, EF1, EFX, Pareto)** für die Wahlfolgen: dafür ist `unteilbare-gueter-demo` da.
- **Strategisches Bewerten und Wählen** sowie nicht additive Bewertungen.
- **Felddaten** (echte Elfmeterschießen, echte Aufteilungen).
- **PDF-Export** (die Demo hat keine Ergebnisse, die man ausdrucken müsste).

## Literatur (nicht im Volltext gelesen)

Alle Angaben aus dem Gedächtnis oder aus Suchergebnissen, ungeprüft: Apesteguia und Palacios-Huerta (2010, American Economic Review) zum Startvorteil im Elfmeterschießen; Prouhet (1851) und Thue (1912) zur Thue-Morse-Folge; IFAB-Entscheidung zu ABBA 2018 (Suchergebnisse).
Keine Zahl dieser README stammt aus der Literatur.

## Verifikation

- **Kern:** Handrechnungen auf Mini-Instanzen, Orakel (Aufzählung, Brüche, Rangprofile, Schleife), Eigenschaftstests, Randfälle (ein Schuss je Mannschaft, Reglergrenzen, m = k, Wahrscheinlichkeit 0).
- **Presets:** vollständig, Werte innerhalb der Reglergrenzen, Standard-Preset gleich Standardeinstellung, jede Hilfe gegen die Rechnung.
- **Oberfläche:** AppTest: jeder Knopf, jeder Regler an Minimum und Maximum, jede Auswahl, alle Minima und alle Maxima zugleich, Permalink, Kennzahlen aus den Reglerwerten (Schlüsselwörter), Verdikte gegen die Kernrechnung, Footer, Laufzeit-Importe.
- **Layout:** Schnellstart oben in der Seitenleiste, fester Kopf, aktives Preset hervorgehoben; jede Regleränderung hebt die Markierung auf (`tests/test_layout.py`).
- **Nicht geprüft:** Docker/Linux-Check, Browseransicht (KaTeX, Sticky-Kopf), Lesetest der Texte, erneute Prüfung nach den Korrekturen der unabhängigen Aussagenprüfung (diese ist gelaufen, ihre Korrekturen sind eingearbeitet).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: zwei Reiter, Experimente, Annahmen, Formeln |
| `rei_algorithm.py` | Kern Elfmeterschießen: Schussfolge, Regelzeit-Rekursion, Sudden Death, Monte-Carlo-Simulation |
| `rei_choice.py` | Kern Wahlreihenfolge: Wahlfolgen, Zuteilung, vektorisierte Messreihe |
| `rei_constants.py` | Regler-Grenzen, feste Annahmen, Farben, Presets |
| `rei_evaluation.py` | Kennzahlen, Messreihen, Verdikte als reine Funktionen |
| `rei_layout.py` | Fester Kopf (Stylesheet) |
| `rei_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `rei_rng.py` | SplitMix64, wörtliche Kopie der geprüften Vorlage |
| `rei_scenario.py` | Das gezeigte Elfmeterschießen und die gezeigten Bewertungen |
| `rei_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Handrechnungen, Orakel, Eigenschaften, Claims, Verdikte, Randfälle, Presets, Abbildungen, Layout, AppTest, Footer, Laufzeit-Importe, Kopie-Test |

## Tests

**203 Tests**, grün; Laufzeit unter Windows im Test-venv seriell 24 Sekunden (ein Lauf am 2026-11-18; die Zeit hängt stark von der Auslastung des Rechners ab). Aufruf: `pytest tests/ -q`; der größte Teil der Zeit geht in die AppTest-Läufe und den Import von Streamlit.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly und NumPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Wettbewerbsverzerrung: Reihenfolge und Anreize](https://sebastianhanisch.net/konzepte-wettbewerbsverzerrung.html).
