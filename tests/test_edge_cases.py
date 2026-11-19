"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): genau zwei Elemente, Gleichstände, inklusive Grenzen, Reglergrenzen."""

import numpy as np
import pytest

import rei_algorithm as A
import rei_choice as H
import rei_constants as C
import rei_evaluation as ev
from rei_rng import SplitMix64


def test_one_shot_each_is_the_smallest_shootout_and_has_no_early_stop():
    for order in ("ABAB", "ABBA"):
        e = A.exact_shootout(order, 1, 0.75, 0.75, 0.05, 0.05)
        assert e.p_early_stop == 0.0 and e.shots_reg == pytest.approx(2.0)
        assert len(e.stop_probs) == 2 and e.stop_probs[0] == 0.0
    assert A.exact_shootout("ABAB", 1, 0.75, 0.75, 0.0, 0.0).win_a == pytest.approx(0.5)


def test_two_shots_each_abba_differs_from_abab_only_through_the_dependence():
    assert A.exact_shootout("ABAB", 2, 0.7, 0.7, 0.0, 0.0).win_a == pytest.approx(A.exact_shootout("ABBA", 2, 0.7, 0.7, 0.0, 0.0).win_a)
    assert A.exact_shootout("ABAB", 2, 0.7, 0.7, 0.1, 0.1).win_a > A.exact_shootout("ABBA", 2, 0.7, 0.7, 0.1, 0.1).win_a


def test_slider_extremes_of_the_shootout_are_valid():
    for order in C.ORDERS:
        for r in (C.R_MIN, C.R_MAX):
            for p in (C.P_MIN, C.P_MAX):
                for d in (C.D_MIN, C.D_MAX):
                    e = A.exact_shootout(order, r, p, p, d, d)
                    assert 0.0 < e.win_a < 1.0 and e.win_a + e.win_b == pytest.approx(1.0)
    assert C.P_MIN - C.D_MAX > 0.0          # die Trefferwahrscheinlichkeit im Rückstand bleibt auch an den Reglergrenzen positiv


def test_shot_with_zero_probability_never_scores(scripted):
    """p = 0,5, d = 0,5, R = 1: A trifft (0,1 < 0,5), B liegt zurück und trifft mit 0 nie, auch nicht bei dem Zufallswert 0,0: A gewinnt 1 : 0 nach zwei Schüssen."""
    shots = A.play_shootout(scripted([0.1, 0.0]), "ABAB", 1, 0.5, 0.5, 0.5, 0.5)
    assert [(s.team, s.probability, s.hit) for s in shots] == [("A", 0.5, True), ("B", 0.0, False)]
    assert shots[-1].decided and (shots[-1].score_a, shots[-1].score_b) == (1, 0)


def test_invalid_number_of_shots_is_rejected():
    with pytest.raises(ValueError):
        A.exact_shootout("ABAB", 0, 0.7, 0.7, 0.0, 0.0)


def test_each_person_picks_exactly_once_when_m_equals_k():
    for k in (2, 3, 4):
        for rule in C.RULES:
            assert sorted(H.pick_sequence(rule, k, k)) == list(range(k)), (rule, k)


def test_thue_morse_with_m_equal_k_by_hand():
    assert H.pick_sequence("Thue-Morse", 2, 2) == (0, 1)
    assert H.pick_sequence("Thue-Morse", 3, 3) == (0, 1, 2)
    assert H.pick_sequence("Thue-Morse", 4, 4) == (0, 1, 2, 3)


def test_smallest_choice_instance_of_the_app_runs_for_all_rules_and_weights():
    for rule in C.RULES:
        for w in (C.W_MIN, C.W_MAX):
            res = H.measure(rule, C.K_MIN, C.M_MIN, w, seeds=(1,), per_seed=20)
            assert np.isfinite(res["advantage"]) and res["n"] == 20


def test_largest_choice_instance_of_the_app_runs_for_all_rules():
    for rule in C.RULES:
        res = H.measure(rule, C.K_MAX, C.M_MAX, C.W_MAX, seeds=(1,), per_seed=10)
        assert np.isfinite(res["advantage"])


def test_all_equal_values_give_every_person_the_same_value_per_pick():
    values = np.full((2, 4), 0.5)
    assert H.totals_of(values, H.allocate(values, H.pick_sequence("Reihum", 2, 4)), 2) == pytest.approx([1.0, 1.0])


def test_identical_valuations_with_w_one_have_no_conflict_free_choice():
    """w = 1: beide wollen dasselbe Gut; die erste Person bekommt das beste, die zweite das zweitbeste."""
    values = np.array([[0.9, 0.5, 0.1, 0.3], [0.9, 0.5, 0.1, 0.3]])
    assert H.pick_steps(values, (0, 1, 0, 1)) == [(0, 0), (1, 1), (0, 3), (1, 2)]


def test_m_sweep_contains_only_multiples_of_k_inside_the_bounds():
    for k in range(C.K_MIN, C.K_MAX + 1):
        ms = ev.m_sweep(k)
        assert ms and all(m % k == 0 and C.M_MIN <= m <= C.M_MAX for m in ms)
