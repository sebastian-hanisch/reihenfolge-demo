"""Eigenschaftstests (ORACLE-PLAYBOOK §5.2): Aussagen, die für beide Kerne gelten müssen, ohne dass man das richtige Ergebnis kennt.

Die Zählungen dieser Datei stehen in der README (Befunde): Zellen = Schüsse je Mannschaft 1 bis 8 mal neun Werte von p mal d von 0,01 bis 0,25 in Schritten von 0,01, soweit p - d mindestens 0,05 bleibt."""

from functools import lru_cache

import numpy as np
import pytest

import rei_algorithm as A
import rei_choice as H
import rei_constants as C
from rei_rng import SplitMix64

P_GRID = (0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.9, 0.95)


def grid():
    """Alle Zellen (r, p, d) mit d > 0 und p - d >= 0,05."""
    for r in range(1, 9):
        for p in P_GRID:
            for i in range(1, 26):
                d = round(0.01 * i, 2)
                if p - d >= 0.05 - 1e-9:
                    yield r, p, d


@lru_cache(maxsize=None)
def equal(order, r, p, d):
    return A.exact_shootout(order, r, p, p, d, d)


def test_grid_has_the_documented_size():
    assert sum(1 for _ in grid()) == 1800


def test_without_dependence_the_order_does_not_matter_even_for_unequal_teams():
    """Bei unabhängigen Schüssen sind ABAB und ABBA gleich (gleich stark: genau 50 %; ungleich stark: dieselbe Zahl)."""
    for r in range(1, 9):
        for pa in P_GRID:
            for pb in P_GRID:
                abab = A.exact_shootout("ABAB", r, pa, pb, 0.0, 0.0).win_a
                abba = A.exact_shootout("ABBA", r, pa, pb, 0.0, 0.0).win_a
                assert abab == pytest.approx(abba, abs=1e-12), (r, pa, pb)
                if pa == pb:
                    assert abab == pytest.approx(0.5, abs=1e-12)


def test_abab_equals_the_sudden_death_formula_for_every_number_of_shots():
    """Gemessen in allen 1.800 Zellen plus d = 0 (nicht bewiesen): bei ABAB und gleich starken Mannschaften ist die Gewinnchance der ersten Mannschaft (1 - p + d) / (2 (1 - p) + d)."""
    worst = 0.0
    cells = 0
    for r, p, d in list(grid()) + [(r, p, 0.0) for r in range(1, 9) for p in P_GRID]:
        theory = (1 - p + d) / (2 * (1 - p) + d)
        worst = max(worst, abs(equal("ABAB", r, p, d).win_a - theory))
        cells += 1
    assert cells == 1800 + 72 and worst < 1e-12


def test_abba_is_closer_to_fifty_percent_than_abab_and_never_below_it_in_all_cells():
    closer = never_below = 0
    largest = 0.0
    for r, p, d in grid():
        abab, abba = equal("ABAB", r, p, d).win_a, equal("ABBA", r, p, d).win_a
        closer += abs(abba - 0.5) < abs(abab - 0.5)
        never_below += abba >= 0.5
        largest = max(largest, abba - 0.5)
    assert closer == 1800 and never_below == 1800
    assert largest == pytest.approx(0.0712, abs=5e-5)       # größter Vorteil der ersten Mannschaft bei ABBA in den Zellen (1 Schuss, p = 0,95, d = 0,25)


def test_second_team_shoots_more_often_trailing_under_abab_in_all_cells_and_the_gap_is_smaller_under_abba():
    larger = smaller = 0
    for r, p, d in grid():
        a, b = equal("ABAB", r, p, d), equal("ABBA", r, p, d)
        larger += a.trailing_b > a.trailing_a
        smaller += (a.trailing_b - a.trailing_a) > (b.trailing_b - b.trailing_a)
    assert larger == 1800 and smaller == 1800


def test_advantage_of_the_first_team_grows_with_d_under_abab():
    for p in (0.5, 0.75, 0.9):
        values = [equal("ABAB", 5, p, round(0.01 * i, 2)).win_a for i in range(0, 25) if p - 0.01 * i >= 0.05]
        assert all(b > a for a, b in zip(values, values[1:]))


def test_probabilities_are_in_range_and_sum_to_one():
    for r, p, d in list(grid())[::37]:
        for order in C.ORDERS:
            e = equal(order, r, p, d)
            assert 0.0 <= e.win_a <= 1.0 and e.win_a + e.win_b == pytest.approx(1.0)


def test_same_seed_same_result_and_different_seed_different_shootouts():
    a = A.simulate("ABAB", 5, 0.75, 0.75, 0.1, 0.1, 200, 5)
    assert a == A.simulate("ABAB", 5, 0.75, 0.75, 0.1, 0.1, 200, 5)
    assert a != A.simulate("ABAB", 5, 0.75, 0.75, 0.1, 0.1, 200, 6)


# --- Wahlreihenfolge -----------------------------------------------------------------------------------------------------------------------------

def test_every_person_picks_equally_often_when_m_is_a_multiple_of_k_for_schlange():
    for k in (2, 3, 4):
        for rounds in (1, 2, 3, 5):
            seq = H.pick_sequence("Schlange", k, k * rounds)
            assert [seq.count(i) for i in range(k)] == [rounds] * k


def test_thue_morse_balances_the_picks_in_blocks_of_k_to_the_power_j():
    """Prouhet-Eigenschaft (hier gemessen, nicht bewiesen): in den ersten k^j Schritten wählt jede Person k^(j-1) Mal."""
    for k in (2, 3, 4):
        for j in (1, 2, 3):
            seq = H.pick_sequence("Thue-Morse", k, k ** j)
            assert [seq.count(i) for i in range(k)] == [k ** (j - 1)] * k, (k, j)


def test_picks_per_person_of_reihum_differ_by_at_most_one_and_the_first_get_the_extra():
    for k in (2, 3, 4):
        for m in range(k, 25):
            seq = H.pick_sequence("Reihum", k, m)
            counts = [seq.count(i) for i in range(k)]
            assert max(counts) - min(counts) <= 1 and counts == sorted(counts, reverse=True)


def test_item_order_does_not_change_the_totals():
    common, own = H.base_draws(31, 30, 3, 8)
    values = H.mix(common, own, 0.3)
    perm = np.array([5, 2, 7, 0, 3, 6, 1, 4])        # feste Umnummerierung der Güter
    for rule in C.RULES:
        seq = H.pick_sequence(rule, 3, 8)
        assert H.batch_totals(values, seq) == pytest.approx(H.batch_totals(values[:, :, perm], seq), abs=1e-12)


def test_scaling_all_values_scales_the_totals():
    common, own = H.base_draws(32, 30, 2, 8)
    values = H.mix(common, own, 0.5)
    seq = H.pick_sequence("Schlange", 2, 8)
    assert H.batch_totals(3.0 * values, seq) == pytest.approx(3.0 * H.batch_totals(values, seq), abs=1e-12)


def test_with_identical_valuations_reihum_never_favours_a_later_person():
    """w = 1: alle bewerten gleich. Bei Reihum nimmt die erste Person in jeder Runde das beste verbleibende Gut: ihr Wert ist in jeder Bewertungsmatrix mindestens so groß wie der jeder späteren Person."""
    for k, m in ((2, 9), (3, 12), (4, 10)):
        common, own = H.base_draws(33, 100, k, m)
        totals = H.batch_totals(H.mix(common, own, 1.0), H.pick_sequence("Reihum", k, m))
        assert np.all(totals[:, 0] >= totals[:, k - 1] - 1e-12)


def test_sum_of_all_totals_is_the_sum_of_the_chosen_values():
    common, own = H.base_draws(34, 20, 3, 9)
    values = H.mix(common, own, 0.6)
    for rule in C.RULES:
        seq = H.pick_sequence(rule, 3, 9)
        for s in range(20):
            owner = H.allocate(values[s], seq)
            assert sum(H.totals_of(values[s], owner, 3)) == pytest.approx(sum(values[s][owner[g], g] for g in range(9)))
            assert sorted(owner) == sorted(seq)               # jeder Schritt vergibt genau ein Gut


def test_same_zufalls_seed_same_measurement_and_other_seeds_differ():
    a = H.measure("Reihum", 2, 6, 0.3, seeds=(1, 2), per_seed=20)
    assert a == H.measure("Reihum", 2, 6, 0.3, seeds=(1, 2), per_seed=20)
    assert a != H.measure("Reihum", 2, 6, 0.3, seeds=(3, 4), per_seed=20)
    assert SplitMix64(1).random() != SplitMix64(2).random()
