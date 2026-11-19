"""Kern des Elfmeterschießens: Schussreihenfolge, exakte Rekursion (Regelzeit und Sudden Death) und das Nachspielen Schuss für Schuss.

Jede Regel ist eine eigene Funktion mit expliziten Ein- und Ausgaben (DEMO-PLAYBOOK §1b). Modell: Mannschaft A schießt als erste. Ein Schütze trifft mit der Wahrscheinlichkeit
p, wenn seine Mannschaft vor dem Schuss nicht zurückliegt, und mit p - d, wenn sie zurückliegt (Abhängigkeit vom Spielstand). Regelzeit: R Schüsse je Mannschaft, der Wettbewerb endet
vorzeitig, sobald eine Mannschaft auch dann nicht mehr einzuholen wäre, wenn sie alle ihre restlichen Schüsse trifft und die andere alle verfehlt. Bei Gleichstand nach der
Regelzeit folgt der Sudden Death in Paaren aus je einem Schuss je Mannschaft, bis ein Paar die Mannschaften trennt.

Reihenfolgen: ABAB (A schießt in jedem Paar zuerst, auch im Sudden Death). ABBA: das Paar mit ungerader Nummer beginnt mit A, das mit gerader Nummer mit B, auch im Sudden Death
(bei fünf Schüssen beginnt das Paar 6 also mit B)."""

from dataclasses import dataclass

import rei_constants as C
from rei_rng import SplitMix64


@dataclass(frozen=True)
class Exact:
    win_a: float            # Wahrscheinlichkeit, dass Mannschaft A (die erste) gewinnt
    win_b: float
    win_a_reg: float        # A gewinnt in der Regelzeit (nach dem vorzeitigen Abbruch oder nach allen Schüssen)
    win_b_reg: float
    p_tie: float            # Gleichstand nach der Regelzeit: Sudden Death folgt
    win_a_sd: float         # A gewinnt den Sudden Death, bedingt auf seinen Beginn
    shots_reg: float        # erwartete Zahl der Schüsse in der Regelzeit (mit vorzeitigem Abbruch)
    shots_total: float      # erwartete Gesamtzahl der Schüsse einschließlich Sudden Death
    shots_without_stop: float   # dasselbe ohne vorzeitigen Abbruch (alle 2 R Schüsse, dazu der Sudden Death)
    p_early_stop: float     # Wahrscheinlichkeit, dass die Regelzeit vor dem letzten Schuss endet
    stop_probs: tuple[float, ...]   # Wahrscheinlichkeit, dass die Entscheidung mit Schuss i + 1 fällt (i = 0 bis 2 R - 1)
    trailing_a: float       # erwartete Zahl der Schüsse von A, die im Rückstand fallen (Regelzeit und Sudden Death)
    trailing_b: float


@dataclass(frozen=True)
class Shot:
    number: int
    pair: int
    team: str
    phase: str              # "Regelzeit" oder "Sudden Death"
    probability: float      # Trefferwahrscheinlichkeit dieses Schusses (p oder p - d)
    hit: bool
    score_a: int
    score_b: int
    decided: bool           # nach diesem Schuss ist der Wettbewerb entschieden


def check_order(order: str) -> None:
    if order not in C.ORDERS:
        raise ValueError(f"unbekannte Reihenfolge {order!r}")


def pair_first(order: str, pair: int) -> str:
    """Wer im Paar mit der Nummer `pair` (ab 1, Regelzeit und Sudden Death durchgezählt) zuerst schießt."""
    check_order(order)
    if order == "ABAB":
        return "A"
    return "A" if pair % 2 == 1 else "B"


def shot_order(order: str, r: int) -> tuple[str, ...]:
    """Die 2 R Schüsse der Regelzeit als Folge der Mannschaften."""
    seq: list[str] = []
    for pair in range(1, r + 1):
        first = pair_first(order, pair)
        seq += [first, "B" if first == "A" else "A"]
    return tuple(seq)


def shot_probability(p: float, d: float, own: int, opp: int) -> float:
    """Trefferwahrscheinlichkeit: p, ohne Rückstand; p - d bei Rückstand (eigene Tore kleiner als die der anderen), nie unter 0."""
    return max(0.0, p - d) if own < opp else p


def decided(score_a: int, score_b: int, left_a: int, left_b: int) -> bool:
    """Vorzeitiger Abbruch: eine Mannschaft liegt um mehr Tore vorn, als die andere mit ihren restlichen Schüssen noch aufholen kann."""
    return score_a > score_b + left_b or score_b > score_a + left_a


def regulation(order: str, r: int, pa: float, pb: float, da: float, db: float):
    """Regelzeit exakt: Vorwärtsrekursion über die Spielstände (Wahrscheinlichkeitsverteilung je Schuss).

    Gibt (win_a, win_b, tie, erwartete Schüsse, Abbruch-Wahrscheinlichkeit, Entscheidung nach Schuss i + 1, erwartete Schüsse im Rückstand von A und von B) zurück."""
    seq = shot_order(order, r)
    dist = {(0, 0): 1.0}
    win_a = win_b = 0.0
    expected = 0.0
    trail = {"A": 0.0, "B": 0.0}
    stop = []
    for i, team in enumerate(seq):
        left_a = seq[i + 1:].count("A")
        left_b = seq[i + 1:].count("B")
        new: dict[tuple[int, int], float] = {}
        stopped = 0.0
        for (sa, sb), mass in dist.items():
            expected += mass                       # dieser Schuss wird gespielt
            p, d = (pa, da) if team == "A" else (pb, db)
            own, opp = (sa, sb) if team == "A" else (sb, sa)
            q = shot_probability(p, d, own, opp)
            if own < opp:
                trail[team] += mass                # dieser Schuss fällt im Rückstand
            for hit, weight in ((1, q), (0, 1.0 - q)):
                a = sa + (hit if team == "A" else 0)
                b = sb + (hit if team == "B" else 0)
                m = mass * weight
                if decided(a, b, left_a, left_b):
                    stopped += m
                    if a > b:
                        win_a += m
                    else:
                        win_b += m
                else:
                    new[(a, b)] = new.get((a, b), 0.0) + m
        stop.append(stopped)
        dist = new
    tie = sum(dist.values())
    early = sum(stop[:-1])
    return win_a, win_b, tie, expected, early, tuple(stop), trail["A"], trail["B"]


def sudden_death(order: str, r: int, pa: float, pb: float, da: float, db: float):
    """Sudden Death exakt, Paar für Paar: gibt (P(A gewinnt), erwartete Zahl der Paare, erwartete Schüsse im Rückstand von A und von B) zurück.

    In einem Paar schießt der Erste im Gleichstand (Wahrscheinlichkeit p), der Zweite liegt nach einem Treffer des Ersten zurück (p - d). Der Erste gewinnt das Paar mit
    Treffer und Fehlschuss des Zweiten, der Zweite mit Fehlschuss und Treffer; sonst folgt das nächste Paar."""
    mass = 1.0
    win_a = 0.0
    pairs = 0.0
    trail_a = trail_b = 0.0
    for pair in range(r + 1, r + 1 + C.MAX_SD_PAIRS):
        a_first = pair_first(order, pair) == "A"
        pf, ps, ds = (pa, pb, db) if a_first else (pb, pa, da)
        second_after_hit = shot_probability(ps, ds, 0, 1)      # der Erste hat getroffen: der Zweite liegt zurück
        first_wins = pf * (1.0 - second_after_hit)
        second_wins = (1.0 - pf) * ps
        cont = pf * second_after_hit + (1.0 - pf) * (1.0 - ps)
        pairs += mass
        if a_first:
            trail_b += mass * pf                    # der Zweite liegt nach einem Treffer des Ersten zurück
        else:
            trail_a += mass * pf
        win_a += mass * (first_wins if a_first else second_wins)
        mass *= cont
        if mass < 1e-18:
            break
    else:
        raise RuntimeError("Sudden Death konvergiert nicht")
    return win_a, pairs, trail_a, trail_b


def exact_shootout(order: str, r: int, pa: float, pb: float, da: float, db: float) -> Exact:
    """Gesamtwahrscheinlichkeiten des Elfmeterschießens aus Regelzeit und Sudden Death."""
    if not 1 <= r:
        raise ValueError("mindestens ein Schuss je Mannschaft")
    reg_a, reg_b, tie, shots_reg, early, stop, reg_trail_a, reg_trail_b = regulation(order, r, pa, pb, da, db)
    sd_a, sd_pairs, sd_trail_a, sd_trail_b = sudden_death(order, r, pa, pb, da, db)
    win_a = reg_a + tie * sd_a
    return Exact(
        win_a=win_a, win_b=1.0 - win_a, win_a_reg=reg_a, win_b_reg=reg_b, p_tie=tie, win_a_sd=sd_a,
        shots_reg=shots_reg, shots_total=shots_reg + tie * 2.0 * sd_pairs,
        shots_without_stop=2.0 * r + tie * 2.0 * sd_pairs, p_early_stop=early, stop_probs=stop,
        trailing_a=reg_trail_a + tie * sd_trail_a, trailing_b=reg_trail_b + tie * sd_trail_b,
    )


def play_shootout(rng: SplitMix64, order: str, r: int, pa: float, pb: float, da: float, db: float) -> list[Shot]:
    """Ein Elfmeterschießen Schuss für Schuss mit dem Zufallsgenerator der Demo; endet mit der Entscheidung (Regelzeit, danach Sudden Death)."""
    seq = shot_order(order, r)
    sa = sb = 0
    shots: list[Shot] = []
    for i, team in enumerate(seq):
        left_a = seq[i + 1:].count("A")
        left_b = seq[i + 1:].count("B")
        sa, sb, done = _take_shot(rng, shots, team, "Regelzeit", i // 2 + 1, sa, sb, left_a, left_b, pa, pb, da, db)
        if done:
            return shots
    pair = r + 1
    while pair <= r + C.MAX_SD_PAIRS:
        first = pair_first(order, pair)
        second = "B" if first == "A" else "A"
        sa, sb, done = _take_shot(rng, shots, first, "Sudden Death", pair, sa, sb, 1 if first == "B" else 0, 1 if first == "A" else 0, pa, pb, da, db)
        sa, sb, done = _take_shot(rng, shots, second, "Sudden Death", pair, sa, sb, 0, 0, pa, pb, da, db)
        if done:
            return shots
        pair += 1
    raise RuntimeError("Sudden Death endet nicht")


def _take_shot(rng, shots, team, phase, pair, sa, sb, left_a, left_b, pa, pb, da, db):
    p, d = (pa, da) if team == "A" else (pb, db)
    own, opp = (sa, sb) if team == "A" else (sb, sa)
    q = shot_probability(p, d, own, opp)
    hit = rng.random() < q
    sa += 1 if (hit and team == "A") else 0
    sb += 1 if (hit and team == "B") else 0
    done = decided(sa, sb, left_a, left_b)
    shots.append(Shot(len(shots) + 1, pair, team, phase, q, hit, sa, sb, done))
    return sa, sb, done


def simulate(order: str, r: int, pa: float, pb: float, da: float, db: float, n: int, seed: int) -> tuple[int, int]:
    """Spielt n Elfmeterschießen nach und gibt (Siege von A, Zahl aller Schüsse) zurück."""
    rng = SplitMix64(seed)
    wins = shots_total = 0
    for _ in range(n):
        shots = play_shootout(rng, order, r, pa, pb, da, db)
        shots_total += len(shots)
        wins += shots[-1].score_a > shots[-1].score_b
    return wins, shots_total
