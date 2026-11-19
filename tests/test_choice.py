"""Wahlreihenfolge: jede Einheit gegen Handrechnung auf Mini-Instanzen (DEMO-PLAYBOOK §1b)."""

import numpy as np
import pytest

import rei_choice as H
from rei_rng import SplitMix64


def letters(seq):
    return "".join("ABCD"[i] for i in seq)


def test_pick_sequences_by_hand():
    assert letters(H.pick_sequence("Reihum", 2, 6)) == "ABABAB"
    assert letters(H.pick_sequence("Reihum", 3, 7)) == "ABCABCA"
    assert letters(H.pick_sequence("Schlange", 2, 8)) == "ABBAABBA"
    assert letters(H.pick_sequence("Schlange", 3, 7)) == "ABCCBAA"
    assert letters(H.pick_sequence("Thue-Morse", 2, 8)) == "ABBABAAB"
    assert letters(H.pick_sequence("Thue-Morse", 2, 10)) == "ABBABAABBA"
    # Basis 3: Stellensummen von t = 0..8 sind 0, 1, 2, 1, 2, 3, 2, 3, 4, modulo 3: 0, 1, 2, 1, 2, 0, 2, 0, 1
    assert letters(H.pick_sequence("Thue-Morse", 3, 9)) == "ABCBCACAB"


def test_digit_sum():
    assert H.digit_sum(0, 2) == 0 and H.digit_sum(7, 2) == 3 and H.digit_sum(8, 3) == 4 and H.digit_sum(26, 3) == 6


def test_unknown_rule_and_invalid_sizes_are_rejected():
    with pytest.raises(ValueError):
        H.pick_sequence("Zufall", 2, 4)
    with pytest.raises(ValueError):
        H.pick_sequence("Reihum", 0, 4)
    assert H.pick_sequence("Reihum", 2, 0) == ()


def test_allocation_by_hand_with_reihum_and_schlange(mini_values):
    """Person 1: 0,9 / 0,5 / 0,1, Person 2: 0,8 / 0,7 / 0,2. Reihum (ABA): 1 nimmt Gut 1 (0,9), 2 nimmt Gut 2 (0,7), 1 bekommt Gut 3 (0,1): Summen 1,0 und 0,7.
    Schlange (ABB): 1 nimmt Gut 1, 2 nimmt Gut 2 (0,7), 2 nimmt Gut 3 (0,2): Summen 0,9 und 0,9."""
    reihum = H.pick_sequence("Reihum", 2, 3)
    assert H.pick_steps(mini_values, reihum) == [(0, 0), (1, 1), (0, 2)]
    assert H.allocate(mini_values, reihum) == (0, 1, 0)
    assert H.totals_of(mini_values, H.allocate(mini_values, reihum), 2) == pytest.approx([1.0, 0.7])
    schlange = H.pick_sequence("Schlange", 2, 3)
    assert H.allocate(mini_values, schlange) == (0, 1, 1)
    assert H.totals_of(mini_values, H.allocate(mini_values, schlange), 2) == pytest.approx([0.9, 0.9])
    assert H.pick_sequence("Thue-Morse", 2, 3) == schlange            # für drei Schritte dieselbe Folge ABB


def test_ties_are_resolved_by_the_smaller_good_index():
    values = np.array([[0.5, 0.5, 0.5], [0.5, 0.5, 0.5]])
    assert H.pick_steps(values, (0, 1, 0)) == [(0, 0), (1, 1), (0, 2)]


def test_batch_matches_the_single_allocation_on_the_mini_instance(mini_values):
    values = mini_values[None, :, :]
    for rule, expected in (("Reihum", [1.0, 0.7]), ("Schlange", [0.9, 0.9])):
        seq = H.pick_sequence(rule, 2, 3)
        assert H.batch_totals(values, seq)[0] == pytest.approx(expected)


def test_mix_by_hand():
    common = np.array([[0.2, 0.4]])
    own = np.array([[[0.0, 1.0], [0.5, 0.5]]])
    assert H.mix(common, own, 0.5)[0] == pytest.approx(np.array([[0.1, 0.7], [0.35, 0.45]]))
    assert H.mix(common, own, 0.0)[0] == pytest.approx(own[0])
    assert H.mix(common, own, 1.0)[0] == pytest.approx(np.array([[0.2, 0.4], [0.2, 0.4]]))


def test_make_values_is_deterministic_and_has_the_right_shape():
    a = H.make_values(SplitMix64(5), 3, 7, 0.4)
    b = H.make_values(SplitMix64(5), 3, 7, 0.4)
    assert a.shape == (3, 7) and np.array_equal(a, b)
    assert 0.0 <= a.min() and a.max() < 1.0
    identical = H.make_values(SplitMix64(5), 3, 7, 1.0)
    assert np.array_equal(identical[0], identical[1]) and np.array_equal(identical[1], identical[2])     # w = 1: alle bewerten gleich


def test_base_draws_use_the_same_stream_as_make_values():
    common, own = H.base_draws(9, 2, 2, 3)
    rng = SplitMix64(9)
    first = H.make_values(rng, 2, 3, 0.5)
    assert H.mix(common, own, 0.5)[0] == pytest.approx(first)


def test_measure_returns_consistent_fields():
    res = H.measure("Reihum", 2, 4, 0.0, seeds=(1, 2), per_seed=30)
    assert res["n"] == 60 and len(res["advantage_by_seed"]) == 2
    assert res["advantage"] == pytest.approx(res["mean_totals"][0] - res["mean_totals"][1])
    assert res["advantage_se"] > 0
    assert H.measure("Reihum", 2, 4, 0.0, seeds=(1, 2), per_seed=30) == res


def test_random_stream_equals_the_generator_of_the_demo_number_for_number():
    for seed in (0, 1, 35, 100000, 2 ** 64 - 1):
        rng = SplitMix64(seed)
        reference = [rng.random() for _ in range(50)]
        assert H.random_stream(seed, 50).tolist() == reference                 # bitgleich, nicht nur ungefähr


def test_base_draws_equal_the_loop_over_the_generator():
    rng = SplitMix64(123)
    common, own = H.base_draws(123, 6, 3, 5)
    for s in range(6):
        assert common[s].tolist() == [rng.random() for _ in range(5)]
        for i in range(3):
            assert own[s, i].tolist() == [rng.random() for _ in range(5)]
