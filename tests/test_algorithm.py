"""Elfmeterschießen: jede Einheit gegen Handrechnung auf Mini-Instanzen (DEMO-PLAYBOOK §1b). Die Gegenproben mit anderem Rechenweg stehen in test_oracle_reihenfolge.py."""

import pytest

import rei_algorithm as A
from rei_rng import SplitMix64


def test_shot_order_of_both_rules():
    assert "".join(A.shot_order("ABAB", 5)) == "ABABABABAB"
    assert "".join(A.shot_order("ABBA", 5)) == "ABBAABBAAB"      # Paare: AB | BA | AB | BA | AB
    assert "".join(A.shot_order("ABBA", 1)) == "AB"
    assert "".join(A.shot_order("ABBA", 2)) == "ABBA"


def test_pair_first_alternates_for_abba_and_stays_a_for_abab_also_in_sudden_death():
    assert [A.pair_first("ABAB", k) for k in range(1, 9)] == ["A"] * 8
    assert [A.pair_first("ABBA", k) for k in range(1, 9)] == list("ABABABAB")
    assert A.pair_first("ABBA", 6) == "B" and A.pair_first("ABBA", 7) == "A"     # fünf Schüsse: das Paar 6 beginnt mit der zweiten Mannschaft


def test_unknown_order_is_rejected():
    with pytest.raises(ValueError):
        A.shot_order("AABB", 5)


def test_shot_probability_drops_only_when_trailing():
    assert A.shot_probability(0.75, 0.05, 0, 0) == 0.75
    assert A.shot_probability(0.75, 0.05, 2, 1) == 0.75           # vorn
    assert A.shot_probability(0.75, 0.05, 1, 2) == pytest.approx(0.70)
    assert A.shot_probability(0.30, 0.25, 0, 1) == pytest.approx(0.05)
    assert A.shot_probability(0.1, 0.25, 0, 1) == 0.0              # nie negativ


def test_decided_means_the_other_side_cannot_catch_up():
    assert not A.decided(1, 0, 1, 1)         # A vorn, B hat noch 1 Schuss: B kann ausgleichen
    assert A.decided(2, 0, 0, 1)             # 2 : 0, B hat 1 Schuss: nicht mehr einzuholen
    assert A.decided(0, 1, 0, 0)             # alle Schüsse gespielt
    assert not A.decided(1, 1, 0, 0)         # Gleichstand ist nie entschieden
    assert A.decided(3, 0, 1, 2)             # 3 > 0 + 2
    assert not A.decided(2, 0, 1, 2)         # 2 > 2 ist falsch: die Grenze gilt nicht inklusive


def test_one_shot_each_by_hand_with_dependence():
    """R = 1, ABAB, p = 0,5, d = 0,1: A trifft mit 0,5. B schießt danach: nach einem Treffer von A im Rückstand (0,4), sonst mit 0,5.
    A gewinnt die Regelzeit mit 0,5 * 0,6 = 0,30, B mit 0,5 * 0,5 = 0,25, Gleichstand 0,5 * 0,4 + 0,5 * 0,5 = 0,45.
    Sudden Death: erster gewinnt das Paar mit x = 0,5 * 0,6 = 0,30, zweiter mit y = 0,25, also gewinnt A mit 0,30 / 0,55 = 6/11.
    Gesamt: 0,30 + 0,45 * 6/11 = 6/11 = (1 - p + d) / (2 (1 - p) + d)."""
    e = A.exact_shootout("ABAB", 1, 0.5, 0.5, 0.1, 0.1)
    assert e.win_a_reg == pytest.approx(0.30) and e.win_b_reg == pytest.approx(0.25) and e.p_tie == pytest.approx(0.45)
    assert e.win_a_sd == pytest.approx(6 / 11)
    assert e.win_a == pytest.approx(6 / 11) and e.win_b == pytest.approx(5 / 11)
    assert e.shots_reg == pytest.approx(2.0) and e.p_early_stop == 0.0     # bei einem Schuss je Mannschaft gibt es keinen Abbruch vor dem letzten Schuss


def test_expected_shots_in_the_sudden_death_by_hand():
    """R = 1, ABAB, p = 0,5, d = 0,1: ein Paar des Sudden Death endet mit 0,30 + 0,25 = 0,55, Fortsetzung c = 0,45; erwartete Paare 1 / 0,55 = 20/11, also 40/11 Schüsse.
    Gesamt: 2 + 0,45 * 40/11."""
    e = A.exact_shootout("ABAB", 1, 0.5, 0.5, 0.1, 0.1)
    assert e.shots_total == pytest.approx(2 + 0.45 * 40 / 11)
    assert e.shots_without_stop == pytest.approx(e.shots_total)             # R = 1: der Abbruch kann nichts sparen


def test_trailing_shots_by_hand_for_one_shot_each():
    """R = 1, ABAB, p = 0,5, d = 0,1. Regelzeit: nur B liegt zurück, wenn A getroffen hat: 0,5. Sudden Death (nur bei Gleichstand, 0,45): B im Rückstand mit Wahrscheinlichkeit 0,5
    je Paar bei erwarteten 20/11 Paaren: 0,5 * 20/11. A liegt nie zurück."""
    e = A.exact_shootout("ABAB", 1, 0.5, 0.5, 0.1, 0.1)
    assert e.trailing_a == pytest.approx(0.0)
    assert e.trailing_b == pytest.approx(0.5 + 0.45 * 0.5 * 20 / 11)


def test_earliest_stop_with_five_shots_is_the_sixth_shot():
    """Mit fünf Schüssen je Mannschaft ist der früheste Abbruch nach dem 6. Schuss möglich (3 : 0 bei zwei verbleibenden Schüssen der anderen Seite, 3 > 0 + 2)."""
    for order in ("ABAB", "ABBA"):
        e = A.exact_shootout(order, 5, 0.75, 0.75, 0.05, 0.05)
        assert e.stop_probs[:5] == (0.0,) * 5
        assert e.stop_probs[5] > 0
        assert sum(e.stop_probs) + e.p_tie == pytest.approx(1.0)
        assert e.p_early_stop == pytest.approx(sum(e.stop_probs[:-1]))


def test_probabilities_add_up():
    for order in ("ABAB", "ABBA"):
        for r in (1, 3, 8):
            e = A.exact_shootout(order, r, 0.6, 0.6, 0.1, 0.1)
            assert e.win_a + e.win_b == pytest.approx(1.0)
            assert e.win_a_reg + e.win_b_reg + e.p_tie == pytest.approx(1.0)
            assert e.shots_reg <= 2 * r and e.shots_total >= e.shots_reg


def test_play_shootout_follows_the_script(scripted):
    """R = 1, ABAB, p = 0,5, d = 0,1. Werte: A 0,1 (trifft), B 0,1 (im Rückstand 0,4: trifft), Gleichstand 1 : 1; Sudden Death Paar 2: A 0,9 (verfehlt), B 0,1 (trifft): B gewinnt 1 : 2 nach 4 Schüssen."""
    shots = A.play_shootout(scripted([0.1, 0.1, 0.9, 0.1]), "ABAB", 1, 0.5, 0.5, 0.1, 0.1)
    assert [(s.team, s.phase, s.hit, s.score_a, s.score_b, s.decided) for s in shots] == [
        ("A", "Regelzeit", True, 1, 0, False), ("B", "Regelzeit", True, 1, 1, False),
        ("A", "Sudden Death", False, 1, 1, False), ("B", "Sudden Death", True, 1, 2, True),
    ]
    assert [s.probability for s in shots] == [0.5, pytest.approx(0.4), 0.5, 0.5] and [s.pair for s in shots] == [1, 1, 2, 2]


def test_play_shootout_abba_starts_the_even_pair_with_the_second_team(scripted):
    """R = 1 (ABBA): Paar 1 A, B; Paar 2 beginnt mit B, danach A; Paar 3 beginnt wieder mit A. Paar 1 und 2 verfehlen alle (0,9), im Paar 3 trifft A (0,1) und B verfehlt (0,9)."""
    values = [0.9, 0.9, 0.9, 0.9, 0.1, 0.9]
    shots = A.play_shootout(scripted(values), "ABBA", 1, 0.5, 0.5, 0.1, 0.1)
    assert [s.team for s in shots] == ["A", "B", "B", "A", "A", "B"]
    assert shots[-1].decided and (shots[-1].score_a, shots[-1].score_b) == (1, 0)


def test_play_shootout_stops_early(scripted):
    """R = 3, ABAB, p = 0,5, d = 0: A trifft, B verfehlt, A trifft, B verfehlt: nach Schuss 4 steht es 2 : 0, B hat noch einen Schuss, 2 > 0 + 1: Abbruch nach 4 Schüssen."""
    shots = A.play_shootout(scripted([0.1, 0.9, 0.1, 0.9]), "ABAB", 3, 0.5, 0.5, 0.0, 0.0)
    assert len(shots) == 4 and shots[-1].decided and (shots[-1].score_a, shots[-1].score_b) == (2, 0)
    assert not any(s.decided for s in shots[:-1])


def test_same_seed_gives_the_same_shootout():
    a = A.play_shootout(SplitMix64(11), "ABBA", 5, 0.7, 0.7, 0.1, 0.1)
    b = A.play_shootout(SplitMix64(11), "ABBA", 5, 0.7, 0.7, 0.1, 0.1)
    assert a == b


def test_simulate_counts_wins_and_shots():
    wins, shots = A.simulate("ABAB", 5, 0.75, 0.75, 0.05, 0.05, 50, 3)
    assert 0 <= wins <= 50 and 50 * 6 <= shots
    assert A.simulate("ABAB", 5, 0.75, 0.75, 0.05, 0.05, 50, 3) == (wins, shots)
