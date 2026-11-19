"""Orakel (anderer Rechenweg, ORACLE-PLAYBOOK §2 und §5, DEMO-PLAYBOOK §12).

Elfmeterschießen:
  1. Aufzählung aller 2^(2 R) Schussfolgen der Regelzeit mit eigener Abbruchlogik (Wahrscheinlichkeit der ganzen Folge, Entscheidung am ersten Zeitpunkt, an dem eine Seite uneinholbar vorn liegt)
     gegen die Vorwärtsrekursion des Kerns (Sieg, Gleichstand, erwartete Schüsse, Schüsse im Rückstand), auch für ungleich starke Mannschaften.
  2. Der Sudden Death in geschlossener Form mit Brüchen (`fractions`) gegen die Paar-für-Paar-Schleife des Kerns.
  3. Der Abbruch ändert den Sieger nie: auf allen 1.024 Schussfolgen gleicht der Sieger beim Abbruch dem Sieger nach allen zehn Schüssen.
  4. Das Nachspielen mit dem Zufallsgenerator der Demo gegen die exakte Wahrscheinlichkeit, in einem Band aus Standardfehlern (Sieg und mittlere Schusszahl).
Wahlreihenfolge:
  5. Bei unabhängigem Geschmack (w = 0) hängt der Ausgang nur an den Rangfolgen der Personen; der Erwartungswert des Gesamtwerts folgt aus der Aufzählung aller Rangprofile
     (Güter mit Rang r von unten haben den Erwartungswert r / (m + 1)) und wird mit der Messreihe des Kerns verglichen.
  6. Die vektorisierte Fassung gegen eine Schleife in reinem Python, die Wahlfolgen gegen die Definition (Popcount für Thue-Morse bei zwei Personen)."""

import itertools
import math
from fractions import Fraction

import numpy as np
import pytest

import rei_algorithm as A
import rei_choice as H
import rei_constants as C
from rei_rng import SplitMix64

SIGMAS = 4.5


# --- 1. Aufzählung der Regelzeit -----------------------------------------------------------------------------------------------------------------

def enumerate_regulation(order, r, pa, pb, da, db):
    """Alle Schussfolgen (Treffer/Fehlschuss je Schuss) mit dem Gewicht der ganzen Folge. Die Entscheidung gilt am ersten Schuss, nach dem eine Seite uneinholbar vorn liegt.
    Schüsse nach der Entscheidung ändern das Gewicht nicht (die Wahrscheinlichkeiten je Schuss summieren sich zu 1); gezählt werden nur Schüsse bis zur Entscheidung."""
    teams = []
    for pair in range(1, r + 1):
        first = "A" if (order == "ABAB" or pair % 2 == 1) else "B"
        teams += [first, "B" if first == "A" else "A"]
    n = len(teams)
    win_a = win_b = tie = shots = trail_a = trail_b = 0.0
    for outcome in itertools.product((0, 1), repeat=n):
        weight = 1.0
        goals = {"A": 0, "B": 0}
        decided_at = None
        winner = None
        played_trailing = {"A": 0, "B": 0}
        for i, (team, hit) in enumerate(zip(teams, outcome)):
            other = "B" if team == "A" else "A"
            p, d = (pa, da) if team == "A" else (pb, db)
            trailing = goals[team] < goals[other]
            q = max(0.0, p - d) if trailing else p
            weight *= q if hit else 1.0 - q
            if decided_at is None:
                played_trailing[team] += 1 if trailing else 0
            goals[team] += hit
            if decided_at is None:
                rest_a = sum(1 for t in teams[i + 1:] if t == "A")
                rest_b = sum(1 for t in teams[i + 1:] if t == "B")
                if goals["A"] - goals["B"] > rest_b:
                    decided_at, winner = i + 1, "A"
                elif goals["B"] - goals["A"] > rest_a:
                    decided_at, winner = i + 1, "B"
        if decided_at is None:
            decided_at = n
            winner = "A" if goals["A"] > goals["B"] else ("B" if goals["B"] > goals["A"] else None)
        shots += weight * decided_at
        trail_a += weight * played_trailing["A"]
        trail_b += weight * played_trailing["B"]
        if winner == "A":
            win_a += weight
        elif winner == "B":
            win_b += weight
        else:
            tie += weight
    return win_a, win_b, tie, shots, trail_a, trail_b


CASES = [
    (0.75, 0.75, 0.05, 0.05), (0.6, 0.6, 0.0, 0.0), (0.9, 0.9, 0.25, 0.25), (0.3, 0.3, 0.25, 0.25), (0.5, 0.5, 0.1, 0.1),
    (0.8, 0.6, 0.0, 0.0), (0.7, 0.55, 0.1, 0.2), (0.4, 0.95, 0.15, 0.05),
]


@pytest.mark.parametrize("order", ["ABAB", "ABBA"])
@pytest.mark.parametrize("r", [1, 2, 3, 4, 5])
def test_regulation_matches_the_enumeration_of_all_shot_sequences(order, r):
    for pa, pb, da, db in CASES:
        win_a, win_b, tie, shots, trail_a, trail_b = enumerate_regulation(order, r, pa, pb, da, db)
        k_win_a, k_win_b, k_tie, k_shots, _early, _stop, k_trail_a, k_trail_b = A.regulation(order, r, pa, pb, da, db)
        assert (k_win_a, k_win_b, k_tie) == pytest.approx((win_a, win_b, tie), abs=1e-12), (order, r, pa, pb, da, db)
        assert k_shots == pytest.approx(shots, abs=1e-12)
        assert (k_trail_a, k_trail_b) == pytest.approx((trail_a, trail_b), abs=1e-12)
        assert win_a + win_b + tie == pytest.approx(1.0, abs=1e-12)


def test_regulation_with_six_shots_each_also_matches():
    for order in ("ABAB", "ABBA"):
        win_a, win_b, tie, *_ = enumerate_regulation(order, 6, 0.65, 0.65, 0.1, 0.1)
        k = A.regulation(order, 6, 0.65, 0.65, 0.1, 0.1)
        assert (k[0], k[1], k[2]) == pytest.approx((win_a, win_b, tie), abs=1e-12)


# --- 2. Sudden Death in geschlossener Form -------------------------------------------------------------------------------------------------------

def closed_form_sudden_death(order, r, pa, pb, da, db):
    """P(A gewinnt den Sudden Death) mit Brüchen. Die Paar-Wahrscheinlichkeiten stammen aus der Aufzählung der vier Schussausgänge eines Paares (nicht aus dem Kern):
    Der Erste schießt im Gleichstand mit p, der Zweite nach einem Treffer des Ersten im Rückstand mit p - d."""
    pa, pb, da, db = (Fraction(str(x)) for x in (pa, pb, da, db))

    def pair_probs(first_is_a):
        pf, ps, ds = (pa, pb, db) if first_is_a else (pb, pa, da)
        first_wins = second_wins = cont = Fraction(0)
        for f_hit, s_hit in itertools.product((0, 1), repeat=2):
            pw = pf if f_hit else 1 - pf
            q = max(Fraction(0), ps - ds) if f_hit else ps      # der Zweite liegt nur nach einem Treffer des Ersten zurück
            pw *= q if s_hit else 1 - q
            if f_hit and not s_hit:
                first_wins += pw
            elif s_hit and not f_hit:
                second_wins += pw
            else:
                cont += pw
        return first_wins, second_wins, cont

    xa, ya, ca = pair_probs(True)       # Paar mit A zuerst: A gewinnt mit xa, B mit ya
    xb, yb, cb = pair_probs(False)      # Paar mit B zuerst: B gewinnt mit xb, A mit yb
    if order == "ABAB":
        return xa / (xa + ya)                     # A schießt in jedem Paar zuerst; ein Paar endet mit Wahrscheinlichkeit xa + ya
    # ABBA: abwechselnd; P_first = Sieg von A, wenn das nächste Paar mit A beginnt, P_second, wenn es mit B beginnt
    # P_first = xa + ca * P_second, P_second = yb + cb * P_first
    p_first = (xa + ca * yb) / (1 - ca * cb)
    p_second = yb + cb * p_first
    return p_first if (r + 1) % 2 == 1 else p_second


@pytest.mark.parametrize("order", ["ABAB", "ABBA"])
def test_sudden_death_matches_the_closed_form(order):
    for r in (1, 2, 4, 5, 7):
        for pa, pb, da, db in CASES:
            exact, _pairs, _ta, _tb = A.sudden_death(order, r, pa, pb, da, db)
            assert exact == pytest.approx(float(closed_form_sudden_death(order, r, pa, pb, da, db)), abs=1e-12), (order, r, pa, pb, da, db)


def test_closed_form_by_hand_for_the_default_case():
    """p = 0,75, d = 0,05 (ABAB): x = 0,75 * 0,30 = 0,225, y = 0,25 * 0,75 = 0,1875, also x / (x + y) = 6/11."""
    assert closed_form_sudden_death("ABAB", 5, 0.75, 0.75, 0.05, 0.05) == Fraction(6, 11)


def test_whole_shootout_equals_enumeration_plus_closed_form():
    for order in ("ABAB", "ABBA"):
        for r in (1, 3, 5):
            for pa, pb, da, db in CASES:
                win_a, _wb, tie, *_ = enumerate_regulation(order, r, pa, pb, da, db)
                expected = win_a + tie * float(closed_form_sudden_death(order, r, pa, pb, da, db))
                assert A.exact_shootout(order, r, pa, pb, da, db).win_a == pytest.approx(expected, abs=1e-12), (order, r, pa, pb, da, db)


# --- 3. Der Abbruch ändert den Sieger nie --------------------------------------------------------------------------------------------------------

def test_early_stop_never_changes_the_winner_on_all_1024_sequences():
    order = "ABBAABBAAB"
    counted = differing = early = 0
    for outcome in itertools.product((0, 1), repeat=10):
        goals = {"A": 0, "B": 0}
        stop_winner = None
        early_stop = False
        for i, (team, hit) in enumerate(zip(order, outcome)):
            goals[team] += hit
            rest_a, rest_b = order[i + 1:].count("A"), order[i + 1:].count("B")
            if stop_winner is None:
                if goals["A"] - goals["B"] > rest_b:
                    stop_winner, early_stop = "A", i + 1 < 10
                elif goals["B"] - goals["A"] > rest_a:
                    stop_winner, early_stop = "B", i + 1 < 10
        full = "A" if goals["A"] > goals["B"] else ("B" if goals["B"] > goals["A"] else None)
        counted += 1
        if stop_winner is not None:
            early += early_stop
            differing += stop_winner != full
    assert counted == 1024 and differing == 0 and early > 0


# --- 4. Nachspielen mit dem Zufallsgenerator der Demo --------------------------------------------------------------------------------------------

@pytest.mark.parametrize("order, p, d", [("ABAB", 0.75, 0.10), ("ABBA", 0.75, 0.10), ("ABAB", 0.6, 0.0), ("ABBA", 0.9, 0.2)])
def test_replay_stays_inside_the_band_around_the_exact_probability(order, p, d):
    n = 8000
    rng = SplitMix64(424242)
    wins = 0
    lengths = []
    for _ in range(n):
        shots = A.play_shootout(rng, order, 5, p, p, d, d)
        wins += shots[-1].score_a > shots[-1].score_b
        lengths.append(len(shots))
    exact = A.exact_shootout(order, 5, p, p, d, d)
    se = math.sqrt(exact.win_a * (1 - exact.win_a) / n)
    assert abs(wins / n - exact.win_a) <= SIGMAS * se
    arr = np.array(lengths, dtype=float)
    assert abs(arr.mean() - exact.shots_total) <= SIGMAS * arr.std(ddof=1) / math.sqrt(n)


def test_replay_helper_agrees_with_the_loop_above():
    wins, shots = A.simulate("ABAB", 5, 0.75, 0.75, 0.1, 0.1, 300, 424242)
    rng = SplitMix64(424242)
    ref_wins = ref_shots = 0
    for _ in range(300):
        s = A.play_shootout(rng, "ABAB", 5, 0.75, 0.75, 0.1, 0.1)
        ref_wins += s[-1].score_a > s[-1].score_b
        ref_shots += len(s)
    assert (wins, shots) == (ref_wins, ref_shots)


# --- 5. Wahlreihenfolge: Erwartungswert aus allen Rangprofilen -----------------------------------------------------------------------------------

def exact_expected_totals(rule, k, m):
    """Bei w = 0 entscheidet nur die Rangfolge der Güter je Person. Aufzählung aller (m!)^k Profile; ein Gut auf Platz pos (0 = bestes) hat den Erwartungswert (m - pos) / (m + 1)."""
    seq = H.pick_sequence(rule, k, m)
    perms = list(itertools.permutations(range(m)))      # eine Rangfolge: perms[j] = Güter von bestem bis schlechtestem
    total = [Fraction(0)] * k
    count = 0
    for profile in itertools.product(perms, repeat=k):
        taken = set()
        for person in seq:
            ranking = profile[person]
            good = next(g for g in ranking if g not in taken)
            taken.add(good)
            total[person] += Fraction(m - ranking.index(good), m + 1)
        count += 1
    return [t / count for t in total]


@pytest.mark.parametrize("rule", C.RULES)
@pytest.mark.parametrize("k, m", [(2, 4), (2, 5), (3, 4)])
def test_measured_means_stay_inside_the_band_around_the_exact_expectation(rule, k, m):
    exact = [float(x) for x in exact_expected_totals(rule, k, m)]
    seq = H.pick_sequence(rule, k, m)
    rows = []
    for seed in C.SWEEP_SEEDS:
        common, own = H.base_draws(seed, 400, k, m)
        rows.append(H.batch_totals(H.mix(common, own, 0.0), seq))
    tot = np.concatenate(rows)
    n = len(tot)
    for i in range(k):
        se = tot[:, i].std(ddof=1) / math.sqrt(n)
        assert abs(tot[:, i].mean() - exact[i]) <= SIGMAS * se, (rule, k, m, i)
    res = H.measure(rule, k, m, 0.0)
    assert res["advantage"] == pytest.approx(tot[:, 0].mean() - tot[:, k - 1].mean())
    assert abs(res["advantage"] - (exact[0] - exact[k - 1])) <= SIGMAS * res["advantage_se"]


def test_exact_expectation_by_hand_for_two_goods():
    """m = 2, zwei Personen: Person 1 nimmt ihr besseres Gut, Erwartungswert 2/3; Person 2 bekommt das andere Gut, das unabhängig von ihren Bewertungen bleibt: Erwartungswert 1/2."""
    first, second = exact_expected_totals("Reihum", 2, 2)
    assert first == Fraction(2, 3) and second == Fraction(1, 2)


def test_exact_expectation_by_hand_for_three_goods_with_reihum():
    """m = 3, Reihum ABA: Person 1 nimmt das beste Gut (Erwartung 3/4), Person 2 das beste der verbleibenden beiden (2/3), Person 1 das letzte; sein Wert ist der einer der beiden
    schlechteren Plätze, gleich wahrscheinlich: (1/2 + 1/4) / 2 = 3/8. Summe der Person 1: 3/4 + 3/8 = 9/8, Person 2: 2/3."""
    first, second = exact_expected_totals("Reihum", 2, 3)
    assert first == Fraction(9, 8) and second == Fraction(2, 3)


# --- 6. Vektorisiert gegen Schleife, Folgen gegen die Definition ----------------------------------------------------------------------------------

def loop_totals(values, seq):
    """Wahl in reinem Python ohne NumPy-Reihenfolgen: je Schritt wählt die Person das freie Gut mit dem größten Wert (Gleichstand: kleinerer Index)."""
    k, m = len(values), len(values[0])
    got = [0.0] * k
    taken = [False] * m
    for person in seq:
        best = None
        for g in range(m):
            if not taken[g] and (best is None or values[person][g] > values[person][best]):
                best = g
        taken[best] = True
        got[person] += values[person][best]
    return got


@pytest.mark.parametrize("rule", C.RULES)
@pytest.mark.parametrize("k, m", [(2, 6), (3, 9), (4, 8), (2, 7)])
def test_vectorised_totals_match_the_plain_loop(rule, k, m):
    seq = H.pick_sequence(rule, k, m)
    common, own = H.base_draws(777, 40, k, m)
    for w in (0.0, 0.5, 1.0):
        values = H.mix(common, own, w)
        batch = H.batch_totals(values, seq)
        for s in range(40):
            assert batch[s] == pytest.approx(loop_totals(values[s].tolist(), seq), abs=1e-12)
            assert H.totals_of(values[s], H.allocate(values[s], seq), k) == pytest.approx(batch[s], abs=1e-12)


def test_thue_morse_for_two_persons_equals_the_parity_of_the_binary_digit_count():
    assert H.pick_sequence("Thue-Morse", 2, 64) == tuple(bin(t).count("1") % 2 for t in range(64))


def test_schlange_equals_its_definition_by_reversing_every_second_round():
    for k in (2, 3, 4):
        expected = []
        for rnd in range(6):
            expected += list(range(k)) if rnd % 2 == 0 else list(reversed(range(k)))
        assert list(H.pick_sequence("Schlange", k, 6 * k)) == expected
