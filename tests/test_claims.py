"""Jede Zahl der README („Ergebnis in Kürze“ und „Befunde“) wird hier nachgerechnet, über dieselben Auswertungsfunktionen wie in der App (DEMO-PLAYBOOK §4, §11a).

Das Elfmeterschießen ist exakt (Rekursion, Bruchzahlen auf mindestens vier Stellen); die Messreihen der Wahlreihenfolge sind Mittel über 2.000 Bewertungsmatrizen (5 feste Zufalls-Seeds
zu je 400, SplitMix64 aus rei_rng.py, auf jeder Plattform dieselben Zahlen); sie werden als Band von ±0,0006 um die in der README genannte Zahl mit drei Stellen geprüft.
Die Tabelle in der README nennt je Zeile den Test."""

from functools import lru_cache

import pytest

import rei_algorithm as A
import rei_choice as H
import rei_constants as C
import rei_evaluation as ev

BAND = 6e-4


@lru_cache(maxsize=None)
def eq(order, r, p, d):
    return ev.exact_equal(order, r, p, d)


@lru_cache(maxsize=None)
def table(k, m, w):
    return {t["rule"]: t for t in ev.choice_table(k, m, w)}


def grid():
    for r in range(1, 9):
        for p in (0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.9, 0.95):
            for i in range(1, 26):
                d = round(0.01 * i, 2)
                if p - d >= 0.05 - 1e-9:
                    yield r, p, d


# --- Elfmeterschießen --------------------------------------------------------------------------------------------------------------------------

def test_independent_shots_give_fifty_percent_in_both_orders_for_four_values_of_p():
    """README: 50,00 % bei ABAB und ABBA für p = 0,3 / 0,5 / 0,7 / 0,9 (5 Schüsse, d = 0)."""
    for p in C.P_TABLE:
        for order in C.ORDERS:
            assert eq(order, 5, p, 0.0).win_a == pytest.approx(0.5, abs=1e-9)


def test_unequal_teams_without_dependence_have_the_same_probability_in_both_orders():
    """README: A mit 0,8 gegen B mit 0,6 gewinnt in beiden Reihenfolgen mit 79,95 %."""
    row = ev.table_independent(5)[-1]
    assert round(100 * row["abab"], 2) == 79.95 and round(100 * row["abba"], 2) == 79.95
    assert row["abab"] == pytest.approx(row["abba"], abs=1e-12)


@pytest.mark.parametrize("d, abab, abba", [(0.05, 54.5, 50.7), (0.10, 58.3, 51.5), (0.15, 61.5, 52.5), (0.25, 66.7, 55.0)])
def test_first_team_with_dependence_for_the_four_values_of_d(d, abab, abba):
    """README: p = 0,75, 5 Schüsse: ABAB 54,5 / 58,3 / 61,5 / 66,7 %, ABBA 50,7 / 51,5 / 52,5 / 55,0 % bei d = 0,05 / 0,10 / 0,15 / 0,25."""
    assert round(100 * eq("ABAB", 5, 0.75, d).win_a, 1) == abab
    assert round(100 * eq("ABBA", 5, 0.75, d).win_a, 1) == abba


def test_abab_at_the_standard_case_is_six_elevenths():
    """README: 54,5 % sind 6/11 (= (1 - p + d) / (2 (1 - p) + d) mit p = 0,75, d = 0,05)."""
    assert eq("ABAB", 5, 0.75, 0.05).win_a == pytest.approx(6 / 11, abs=1e-12)


def test_abab_follows_the_sudden_death_formula_for_every_number_of_shots_in_1872_cells():
    """README: in 1.872 Zellen (R = 1 bis 8; 1.800 Zellen mit d von 0,01 bis 0,25 bei neun Werten von p, soweit p - d mindestens 0,05 bleibt, dazu 72 Zellen mit d = 0) weicht ABAB um weniger als 1e-12 von der Formel ab."""
    cells = [(r, p, d) for r, p, d in grid()] + [(r, p, 0.0) for r in range(1, 9) for p in (0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.9, 0.95)]
    assert len(cells) == 1872
    assert max(abs(eq("ABAB", r, p, d).win_a - (1 - p + d) / (2 * (1 - p) + d)) for r, p, d in cells) < 1e-12


def test_abba_is_closer_to_fifty_percent_in_1800_of_1800_cells_and_never_below():
    """README: ABBA liegt in 1.800 von 1.800 Zellen mit d > 0 näher an 50 % als ABAB, nie unter 50 % (kleinster Wert 50,04 %, größter 57,1 %)."""
    cells = list(grid())
    assert len(cells) == 1800
    values = [eq("ABBA", r, p, d).win_a for r, p, d in cells]
    assert sum(abs(eq("ABBA", r, p, d).win_a - 0.5) < abs(eq("ABAB", r, p, d).win_a - 0.5) for r, p, d in cells) == 1800
    assert min(values) >= 0.5 and round(100 * min(values), 2) == 50.04 and round(100 * max(values), 1) == 57.1


def test_where_the_advantage_arises_in_the_standard_case():
    """README: Standardfall (d = 0,05): ABAB: A gewinnt die Regelzeit mit 41,3 %, B mit 34,4 %, Gleichstand 24,3 %, den Sudden Death gewinnt A mit 54,5 %.
    ABBA: 38,8 % und 36,8 %, Sudden Death: A gewinnt 48,8 %."""
    a, b = eq("ABAB", 5, 0.75, 0.05), eq("ABBA", 5, 0.75, 0.05)
    assert [round(100 * x, 1) for x in (a.win_a_reg, a.win_b_reg, a.p_tie, a.win_a_sd)] == [41.3, 34.4, 24.3, 54.5]
    assert [round(100 * x, 1) for x in (b.win_a_reg, b.win_b_reg, b.win_a_sd)] == [38.8, 36.8, 48.8]


def test_shots_taken_while_trailing():
    """README: erwartete Schüsse im Rückstand (p = 0,75, d = 0,05, 5 Schüsse): ABAB A 0,95 und B 3,29; ABBA A 1,92 und B 2,35;
    bei d = 0 ABAB A 0,99 und B 3,44, ABBA A 2,05 und B 2,38; bei ABAB ist B in 1.800 von 1.800 Zellen öfter im Rückstand als A, und die Lücke ist bei ABBA in allen kleiner."""
    a, b = eq("ABAB", 5, 0.75, 0.05), eq("ABBA", 5, 0.75, 0.05)
    assert [round(x, 2) for x in (a.trailing_a, a.trailing_b, b.trailing_a, b.trailing_b)] == [0.95, 3.29, 1.92, 2.35]
    a0, b0 = eq("ABAB", 5, 0.75, 0.0), eq("ABBA", 5, 0.75, 0.0)
    assert [round(x, 2) for x in (a0.trailing_a, a0.trailing_b, b0.trailing_a, b0.trailing_b)] == [0.99, 3.44, 2.05, 2.38]
    assert sum(eq("ABAB", r, p, d).trailing_b > eq("ABAB", r, p, d).trailing_a for r, p, d in grid()) == 1800
    assert sum((eq("ABAB", r, p, d).trailing_b - eq("ABAB", r, p, d).trailing_a) > (eq("ABBA", r, p, d).trailing_b - eq("ABBA", r, p, d).trailing_a) for r, p, d in grid()) == 1800


def test_early_stop_saves_shots_but_not_the_winner():
    """README: ohne Abhängigkeit (p = 0,75, 5 Schüsse) endet die Regelzeit mit 44,3 % vor dem letzten Schuss; erwartet 9,25 statt 10 Schüsse in der Regelzeit,
    10,80 mit Sudden Death gegenüber 11,55 ohne Abbruch; der Sieger ändert sich auf keiner der 1.024 Schussfolgen (tests/test_oracle_reihenfolge.py)."""
    e = eq("ABAB", 5, 0.75, 0.0)
    assert round(100 * e.p_early_stop, 1) == 44.3
    assert round(e.shots_reg, 2) == 9.25 and round(e.shots_total, 2) == 10.80 and round(e.shots_without_stop, 2) == 11.55
    assert eq("ABBA", 5, 0.75, 0.0).shots_total == pytest.approx(e.shots_total)             # ohne Abhängigkeit hängt auch die Schusszahl nicht an der Reihenfolge


def test_number_of_shots_per_team():
    """README: bei p = 0,75, d = 0,10: ABAB 58,3 % bei jeder Schusszahl von 1 bis 8; ABBA 52,4 % bei 1, 51,5 % bei 5, 51,4 % bei 8 Schüssen."""
    assert {round(100 * eq("ABAB", r, 0.75, 0.10).win_a, 1) for r in range(1, 9)} == {58.3}
    assert [round(100 * eq("ABBA", r, 0.75, 0.10).win_a, 1) for r in (1, 5, 8)] == [52.4, 51.5, 51.4]


def test_the_replay_of_the_app_for_the_standard_case():
    """README: 10.000 nachgespielte Elfmeterschießen (Zufalls-Seed 100000, Standardfall): A gewinnt 55,2 % gegen exakt 54,5 % (Band ±3 Standardfehler: ±1,5 Prozentpunkte)."""
    res = ev.probe(ev.Settings())
    assert res["n"] == 10000 and res["wins"] == 5518
    assert round(100 * res["freq"], 1) == 55.2 and round(100 * res["exact"], 1) == 54.5 and round(100 * 3 * res["se"], 1) == 1.5 and res["inside"]


def test_pair_six_of_abba_starts_with_the_second_team():
    """README: bei fünf Schüssen beginnt im Sudden Death bei ABBA das Paar 6 mit B, bei ABAB beginnt A immer."""
    assert A.pair_first("ABBA", 6) == "B" and A.pair_first("ABAB", 6) == "A"


# --- Wahlreihenfolge ---------------------------------------------------------------------------------------------------------------------------

def adv(k, m, w):
    return {name: t["advantage"] for name, t in table(k, m, w).items()}


@pytest.mark.parametrize("k, m, w, values", [
    (2, 10, 0.0, (0.249, 0.068, -0.080)),
    (2, 10, 1.0, (0.457, 0.092, -0.098)),
    (2, 9, 0.0, (0.416, 0.199, -0.212)),
    (3, 12, 0.0, (0.346, -0.102, -0.121)),
    (4, 12, 0.0, (0.373, 0.205, -0.045)),
])
def test_advantage_of_the_first_person_by_rule(k, m, w, values):
    """README (Befunde, Wahlreihenfolge): erste minus letzte Person, Mittel über 2.000 Bewertungsmatrizen, Reihum / Schlange / Thue-Morse."""
    got = adv(k, m, w)
    assert [got[r] for r in C.RULES] == pytest.approx(list(values), abs=BAND)


def test_standard_errors_and_seed_ranges_of_the_default_case():
    """README: Standardfehler 0,017 je Regel (k = 2, m = 10, w = 0); Reihum je Zufalls-Seed zwischen 0,218 und 0,281."""
    t = table(2, 10, 0.0)
    assert all(round(x["se"], 3) == 0.017 for x in t.values())
    assert round(min(t["Reihum"]["by_seed"]), 3) == 0.218 and round(max(t["Reihum"]["by_seed"]), 3) == 0.281
    assert all(x["n"] == 2000 for x in t.values())


def test_mean_totals_of_the_default_case():
    """README: Gesamtwert der ersten und der letzten Person bei Reihum (k = 2, m = 10, w = 0): 3,332 und 3,083."""
    t = table(2, 10, 0.0)["Reihum"]
    assert (round(t["first"], 3), round(t["last"], 3)) == (3.332, 3.083)


def test_picks_per_person_in_the_odd_case():
    """README: bei 9 Gütern und 2 Personen wählt die erste Person bei Reihum und Schlange 5-mal, die zweite 4-mal; bei Thue-Morse ist es umgekehrt."""
    assert table(2, 9, 0.0)["Reihum"]["picks"] == (5, 4) and table(2, 9, 0.0)["Schlange"]["picks"] == (5, 4) and table(2, 9, 0.0)["Thue-Morse"]["picks"] == (4, 5)


def test_taste_similarity_series_of_reihum():
    """README: Reihum (k = 2, m = 10): +0,249 bei w = 0 und +0,457 bei w = 1; in den 11 gemessenen Werten von w zwischen +0,224 und +0,457; Schlange zwischen +0,060 und +0,092,
    Thue-Morse zwischen -0,098 und -0,052."""
    rows = ev.sweep_w(2, 10)
    reihum = [r["Reihum"] for r in rows]
    assert len(rows) == 11 and reihum[0] == pytest.approx(0.249, abs=BAND) and reihum[-1] == pytest.approx(0.457, abs=BAND)
    assert (min(reihum), max(reihum)) == pytest.approx((0.224, 0.457), abs=BAND)
    assert (min(r["Schlange"] for r in rows), max(r["Schlange"] for r in rows)) == pytest.approx((0.060, 0.092), abs=BAND)
    assert (min(r["Thue-Morse"] for r in rows), max(r["Thue-Morse"] for r in rows)) == pytest.approx((-0.098, -0.052), abs=BAND)


def test_number_of_goods_series_for_two_persons():
    """README: k = 2, w = 0, m = 4 / 6 / 8 / 12 / 16: Reihum zwischen +0,201 und +0,266 (immer positiv), Schlange zwischen -0,034 und +0,073, Thue-Morse zwischen -0,141 und +0,041;
    Schlange und Thue-Morse wechseln das Vorzeichen."""
    rows = ev.sweep_m(2, 0.0)
    assert [r["m"] for r in rows] == [4, 6, 8, 12, 16]
    assert (min(r["Reihum"] for r in rows), max(r["Reihum"] for r in rows)) == pytest.approx((0.201, 0.266), abs=BAND)
    assert (min(r["Schlange"] for r in rows), max(r["Schlange"] for r in rows)) == pytest.approx((-0.034, 0.073), abs=BAND)
    assert (min(r["Thue-Morse"] for r in rows), max(r["Thue-Morse"] for r in rows)) == pytest.approx((-0.141, 0.041), abs=BAND)
    for rule in ("Schlange", "Thue-Morse"):
        assert min(r[rule] for r in rows) < 0 < max(r[rule] for r in rows)


def test_for_m_equal_four_schlange_and_thue_morse_coincide():
    """README: bei m = 4 und zwei Personen sind Schlange und Thue-Morse dieselbe Folge ABBA und geben dieselben Zahlen."""
    assert H.pick_sequence("Schlange", 2, 4) == H.pick_sequence("Thue-Morse", 2, 4)
    row = ev.sweep_m(2, 0.0)[0]
    assert row["Schlange"] == row["Thue-Morse"]


def test_sizes_of_the_measurement():
    """README: 5 feste Zufalls-Seeds zu je 400 Bewertungsmatrizen = 2.000 je Zelle."""
    assert C.SWEEP_SEEDS == tuple(range(100000, 100005)) and C.INSTANCES_PER_SEED == 400
    assert len(C.SWEEP_SEEDS) * C.INSTANCES_PER_SEED == 2000
