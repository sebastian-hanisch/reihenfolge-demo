"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text); die App ruft `getattr(st, Art)(Text)`."""

import rei_evaluation as ev


def test_shootout_without_dependence_is_an_info_with_both_numbers():
    kind, text = ev.verdict_shootout(0.0, "ABAB", 0.5, 0.5, 0.5)
    assert kind == "info"
    assert "(d = 0)" in text and "bei ABAB mit **50.0 %**" in text and "bei ABBA mit **50.0 %**" in text
    assert "entscheidet die Reihenfolge nichts" in text


def test_shootout_threshold_of_one_percentage_point_is_exclusive():
    kind, text = ev.verdict_shootout(0.05, "ABBA", 0.509, 0.60, 0.509)
    assert kind == "success" and "**50.9 %**" in text and "unter einem Prozentpunkt" in text and "ABAB 60.0 %, ABBA 50.9 %" in text
    kind, _ = ev.verdict_shootout(0.05, "ABBA", 0.510001, 0.60, 0.510001)
    assert kind == "warning"
    kind, _ = ev.verdict_shootout(0.05, "ABBA", 0.489999, 0.60, 0.489999)
    assert kind == "warning"


def test_shootout_warning_names_the_favoured_team_and_the_size():
    kind, text = ev.verdict_shootout(0.1, "ABAB", 0.60, 0.60, 0.52)
    assert kind == "warning"
    assert "**60.0 %**" in text and "Vorteil der ersten Mannschaft von 10.0 Prozentpunkten" in text and "ABAB 60.0 %, ABBA 52.0 %" in text
    kind, text = ev.verdict_shootout(0.1, "ABBA", 0.45, 0.60, 0.45)
    assert kind == "warning" and "Vorteil der zweiten Mannschaft von 5.0 Prozentpunkten" in text


def test_sweep_d_verdict_counts_the_cells_where_abba_is_closer():
    rows = [{"d": 0.0, "abab": 0.5, "abba": 0.5}, {"d": 0.1, "abab": 0.58, "abba": 0.51}, {"d": 0.2, "abab": 0.64, "abba": 0.54}, {"d": 0.3, "abab": 0.55, "abba": 0.56}]
    kind, text = ev.verdict_sweep_d(rows)
    assert kind == "info"
    assert "Bei d = 0.30 gewinnt die erste Mannschaft mit 55.0 % (ABAB) und 56.0 % (ABBA)" in text
    assert "in 2 von 3 gemessenen Werten d > 0" in text          # d = 0 zählt nicht; bei d = 0.3 ist ABAB näher an 50 %


def test_sweep_r_verdict_names_the_spread_of_abab_and_the_run_of_abba():
    rows = [{"r": 1, "abab": 0.5455, "abba": 0.5118}, {"r": 4, "abab": 0.5455, "abba": 0.5078}, {"r": 8, "abab": 0.5460, "abba": 0.5062}]
    kind, text = ev.verdict_sweep_r(rows)
    assert kind == "info"
    assert "54.5 % bei 1 Schuss je Mannschaft, 54.6 % bei 8; Spanne 0.05 Prozentpunkte" in text
    assert "ABBA: 51.2 % bei 1, 50.6 % bei 8" in text


def test_probe_verdict_inside_and_outside_the_band():
    res = {"n": 10000, "freq": 0.552, "exact": 0.545, "se": 0.005, "inside": True}
    kind, text = ev.verdict_probe(res)
    assert kind == "success" and "10.000 nachgespielte" in text and "55.2 %, exakt 54.5 %" in text and "±1.5 Prozentpunkte" in text and text.endswith("im Band.")
    kind, text = ev.verdict_probe({**res, "freq": 0.58, "inside": False})
    assert kind == "warning" and text.endswith("außerhalb des Bandes.")


def test_probe_flag_follows_the_three_sigma_band():
    near = ev.probe(ev.Settings(order="ABAB", r=5, p=0.75, d=0.05), n=2000, seed=1)
    assert near["inside"] == (abs(near["freq"] - near["exact"]) <= 3.0 * near["se"])
    assert near["n"] == 2000 and 0 <= near["wins"] <= 2000


def _rows(adv, se=0.01, n=2000, picks=(5, 5)):
    names = ("Reihum", "Schlange", "Thue-Morse")
    return [{"rule": r, "advantage": a, "se": se, "n": n, "picks": picks, "first": 0.0, "last": 0.0, "by_seed": (a,)} for r, a in zip(names, adv)]


def test_choice_verdict_names_all_three_advantages_and_the_smallest():
    kind, text = ev.verdict_choice(_rows((0.25, 0.07, -0.08)), 2, 10)
    assert kind == "info"
    assert "Mittel über 2.000 Bewertungsmatrizen: Reihum +0.25, Schlange +0.07, Thue-Morse -0.08" in text
    assert "Standardfehler je höchstens 0.01" in text and "Betragsmäßig am kleinsten ist Schlange" in text
    assert "Abstand zu Thue-Morse beträgt 0.01, zwei Standardfehler eines einzelnen Wertes sind 0.02" in text
    assert "nicht unterscheidbar" in text                                   # 0,01 < 2 · 0,01: kein Befund (die README nennt die Regel)
    _, wide = ev.verdict_choice(_rows((0.25, 0.07, -0.20)), 2, 10)
    assert "Betragsmäßig am kleinsten ist Schlange" in wide and "Abstand der Beträge ist größer" in wide and "nicht unterscheidbar" not in wide


def test_choice_verdict_warns_when_m_is_not_a_multiple_of_k_and_names_the_extra_picks():
    kind, text = ev.verdict_choice(_rows((0.4, 0.2, -0.2)), 2, 9)
    assert kind == "warning" and "Bei 9 Gütern und 2 Personen wählt die erste Person einmal öfter" in text
    kind, text = ev.verdict_choice(_rows((0.4, 0.2, -0.2)), 3, 11)
    assert kind == "warning" and "Bei 11 Gütern und 3 Personen wählen die ersten 2 Personen einmal öfter" in text
    assert ev.verdict_choice(_rows((0.4, 0.2, -0.2)), 3, 12)[0] == "info"


def test_choice_verdict_smallest_absolute_value_also_for_negative_numbers():
    _, text = ev.verdict_choice(_rows((0.3, -0.2, -0.05)), 2, 10)
    assert "Betragsmäßig am kleinsten ist Thue-Morse" in text and "Abstand zu Schlange beträgt 0.15" in text and "nicht unterscheidbar" not in text


def test_sweep_w_and_m_verdicts_name_first_and_last_values():
    rows_w = [{"w": 0.0, "Reihum": 0.249, "Schlange": 0.068, "Thue-Morse": -0.08}, {"w": 1.0, "Reihum": 0.457, "Schlange": 0.092, "Thue-Morse": -0.098}]
    kind, text = ev.verdict_sweep_w(rows_w)
    assert kind == "info" and "Reihum: +0.25 bei w = 0.0, +0.46 bei w = 1.0" in text and "Schlange: +0.07 und +0.09" in text and "Thue-Morse: -0.08 und -0.10" in text
    rows_m = [{"m": 4, "Reihum": 0.23, "Schlange": -0.03, "Thue-Morse": -0.03}, {"m": 16, "Reihum": 0.27, "Schlange": -0.03, "Thue-Morse": -0.02}]
    kind, text = ev.verdict_sweep_m(rows_m)
    assert kind == "info" and "Bei m = 4 Gütern: Reihum +0.23, Schlange -0.03, Thue-Morse -0.03" in text and "bei m = 16: +0.27, -0.03, -0.02" in text


def test_de_int_uses_points_as_thousands_separator():
    assert ev.de_int(10000) == "10.000" and ev.de_int(999) == "999" and ev.de_int(2000) == "2.000"
