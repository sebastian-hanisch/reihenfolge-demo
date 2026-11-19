"""Abbildungen: Achsen gesperrt, richtige Spuren und Werte (aus den Kernrechnungen, nicht aus der Abbildung)."""

import pytest

import rei_algorithm as A
import rei_constants as C
import rei_evaluation as ev
import rei_visualization as V


def _locked(fig):
    return all(ax.fixedrange for ax in (fig.layout.xaxis, fig.layout.yaxis))


def test_progress_has_two_lines_with_the_score_after_each_shot(scripted):
    shots = A.play_shootout(scripted([0.1, 0.9]), "ABAB", 1, 0.5, 0.5, 0.0, 0.0)           # A trifft, B verfehlt: 1 : 0 nach zwei Schüssen
    fig = V.build_progress(shots)
    assert _locked(fig) and len(fig.data) == 2
    assert list(fig.data[0].x) == [0, 1, 2] and list(fig.data[0].y) == [0, 1, 1] and list(fig.data[1].y) == [0, 0, 0]
    assert len(fig.layout.shapes) == 0                                                      # kein Sudden Death, keine Markierung


def test_progress_marks_the_sudden_death(scripted):
    shots = A.play_shootout(scripted([0.1, 0.1, 0.9, 0.1]), "ABAB", 1, 0.5, 0.5, 0.1, 0.1)   # 1 : 1, dann Sudden Death
    fig = V.build_progress(shots)
    assert len(fig.layout.shapes) == 1 and fig.layout.shapes[0].x0 == 2.5 and list(fig.data[1].y) == [0, 0, 1, 1, 2]


def test_stop_probabilities_figure_shows_percent_values():
    e = A.exact_shootout("ABAB", 5, 0.75, 0.75, 0.05, 0.05)
    fig = V.build_stop_probs(e.stop_probs)
    assert _locked(fig) and list(fig.data[0].y) == pytest.approx([100 * p for p in e.stop_probs])
    assert len(fig.data[0].x) == 10


def test_sweep_figures_use_the_exact_rows_in_percent():
    rows = ev.sweep_d(0.75, 5, ds=(0.0, 0.1))
    fig = V.build_sweep_d(rows, 0.1)
    assert _locked(fig) and [t.name for t in fig.data] == ["ABAB", "ABBA"]
    assert list(fig.data[0].y) == pytest.approx([50.0, 100 * ev.exact_equal("ABAB", 5, 0.75, 0.1).win_a])
    rows_r = ev.sweep_r(0.75, 0.1, rs=(1, 2, 3))
    fig = V.build_sweep_r(rows_r, 2)
    assert _locked(fig) and list(fig.data[1].x) == [1, 2, 3]


def test_totals_figure_has_one_bar_group_per_person():
    totals = {"Reihum": [1.0, 0.7], "Schlange": [0.9, 0.9], "Thue-Morse": [0.9, 0.9]}
    fig = V.build_totals(totals, 2)
    assert _locked(fig) and len(fig.data) == 2 and list(fig.data[0].y) == [1.0, 0.9, 0.9] and list(fig.data[1].y) == [0.7, 0.9, 0.9]


def test_choice_sweep_figure_has_one_line_per_rule_with_error_bars():
    rows = [{"w": 0.0, "Reihum": 0.2, "Reihum_se": 0.01, "Schlange": 0.1, "Schlange_se": 0.02, "Thue-Morse": -0.1, "Thue-Morse_se": 0.03},
            {"w": 1.0, "Reihum": 0.4, "Reihum_se": 0.01, "Schlange": 0.1, "Schlange_se": 0.02, "Thue-Morse": -0.1, "Thue-Morse_se": 0.03}]
    fig = V.build_choice_sweep(rows, "w", "Geschmacksähnlichkeit w")
    assert _locked(fig) and [t.name for t in fig.data] == list(C.RULES)
    assert list(fig.data[2].error_y.array) == pytest.approx([0.06, 0.06]) and list(fig.data[0].y) == [0.2, 0.4]
