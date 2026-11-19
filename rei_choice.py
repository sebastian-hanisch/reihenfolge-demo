"""Kern der Wahlreihenfolge: k Personen wählen abwechselnd je ein unteilbares Gut, jede Person nimmt das ihr wertvollste noch freie.

Regeln der Wahlfolge (wer im Schritt t wählt, t = 0, 1, ..., m - 1):
  Reihum:      t mod k, also 0, 1, ..., k-1, 0, 1, ... (bei zwei Personen ABAB...).
  Schlange:    in Runde 0 die Personen 0 bis k-1, in Runde 1 rückwärts k-1 bis 0, dann wieder vorwärts (bei zwei Personen ABBAABBA...).
  Thue-Morse:  Stellensumme von t zur Basis k, modulo k (bei zwei Personen ABBABAABBAABBABAAB..., die Thue-Morse-Folge; für k > 2 die Prouhet-Verallgemeinerung).
Bewertungen sind additiv: der Wert einer Person ist die Summe der Werte ihrer Güter. Geschmack: v[i, g] = w * c[g] + (1 - w) * e[i, g] mit gleichverteilten c und e in [0, 1)
(w = 0: jede Person bewertet unabhängig, w = 1: alle bewerten gleich)."""

import numpy as np

import rei_constants as C
from rei_rng import MASK, SplitMix64


def digit_sum(t: int, base: int) -> int:
    total = 0
    while t:
        total += t % base
        t //= base
    return total


def pick_sequence(rule: str, k: int, m: int) -> tuple[int, ...]:
    """Wer im Schritt t wählt (0-basiert), für m Güter und k Personen."""
    if k < 1 or m < 0:
        raise ValueError("k >= 1 und m >= 0 verlangt")
    if rule == "Reihum":
        return tuple(t % k for t in range(m))
    if rule == "Schlange":
        return tuple((t % k) if (t // k) % 2 == 0 else (k - 1 - t % k) for t in range(m))
    if rule == "Thue-Morse":
        return tuple(digit_sum(t, k) % k for t in range(m))
    raise ValueError(f"unbekannte Regel {rule!r}")


def make_values(rng: SplitMix64, k: int, m: int, w: float):
    """Bewertungsmatrix (k, m) nach dem Geschmacksmodell; Reihenfolge der Ziehungen: erst c[0..m-1], dann e zeilenweise."""
    common = np.array([rng.random() for _ in range(m)])
    own = np.array([[rng.random() for _ in range(m)] for _ in range(k)])
    return w * common[None, :] + (1.0 - w) * own


def random_stream(seed: int, n: int):
    """Die ersten n Zahlen von `SplitMix64(seed).random()` auf einmal (vektorisiert): der Zustand nach i Schritten ist seed + i * Goldener Schnitt modulo 2^64,
    danach die beiden Mischschritte. Gleiche Zahlen wie die Schleife über den Generator der Demo (tests/test_choice.py prüft das)."""
    idx = np.arange(1, n + 1, dtype=np.uint64)
    with np.errstate(over="ignore"):
        z = np.uint64(seed & MASK) + idx * np.uint64(0x9E3779B97F4A7C15)
        z = (z ^ (z >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
        z = (z ^ (z >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
        z = z ^ (z >> np.uint64(31))
    return (z >> np.uint64(11)).astype(np.float64) / float(1 << 53)


def base_draws(seed: int, n: int, k: int, m: int):
    """n Bewertungsmatrizen als Rohziehungen (c: n x m, e: n x k x m) aus einem Zufalls-Seed; w wird erst beim Mischen angewendet.

    Reihenfolge der Ziehungen je Matrix wie in `make_values`: erst die gemeinsamen Werte c[0..m-1], dann e zeilenweise."""
    block = random_stream(seed, n * (m + k * m)).reshape(n, m + k * m)
    return block[:, :m].copy(), block[:, m:].reshape(n, k, m).copy()


def mix(common, own, w: float):
    """v = w * c + (1 - w) * e für alle Matrizen zugleich: Form (n, k, m)."""
    return w * common[:, None, :] + (1.0 - w) * own


def pick_steps(values, seq) -> list[tuple[int, int]]:
    """Schritt für Schritt (Person, Gut): im Schritt t nimmt die Person seq[t] das ihr wertvollste freie Gut (Gleichstand: kleinerer Gutindex)."""
    m = values.shape[1]
    free = list(range(m))
    steps = []
    for person in seq:
        best = max(free, key=lambda g: (values[person, g], -g))
        free.remove(best)
        steps.append((person, best))
    return steps


def allocate(values, seq) -> tuple[int, ...]:
    """Besitzer jedes Guts (Index der Person) nach den Schritten von `pick_steps`."""
    owner = [-1] * values.shape[1]
    for person, good in pick_steps(values, seq):
        owner[good] = person
    return tuple(owner)


def totals_of(values, owner, k: int):
    """Gesamtwert je Person bei der Zuteilung `owner`."""
    return [float(sum(values[i, g] for g in range(len(owner)) if owner[g] == i)) for i in range(k)]


def batch_totals(values, seq):
    """Gesamtwerte (n, k) für n Matrizen (n, k, m) zugleich, vektorisiert über die Matrizen; dieselbe Regel wie `allocate`."""
    n, k, m = values.shape
    free = np.ones((n, m), dtype=bool)
    totals = np.zeros((n, k))
    rows = np.arange(n)
    for person in seq:
        masked = np.where(free, values[:, person, :], -np.inf)
        best = np.argmax(masked, axis=1)          # argmax nimmt bei Gleichstand den kleinsten Index
        totals[:, person] += values[rows, person, best]
        free[rows, best] = False
    return totals


def measure(rule: str, k: int, m: int, w: float, seeds=C.SWEEP_SEEDS, per_seed: int = C.INSTANCES_PER_SEED, draws=None):
    """Messreihe über mehrere feste Zufalls-Seeds: mittlerer Gesamtwert je Wahlposition, Vorteil der ersten gegenüber der letzten Person samt Streuung.

    `draws`: optional {seed: (common, own)} (zwischengespeicherte Rohziehungen). Gibt ein Dict mit Mittelwerten je Position, mittlerem Vorteil (erste minus letzte Person),
    Standardfehler über alle Matrizen und Vorteil je Zufalls-Seed zurück."""
    seq = pick_sequence(rule, k, m)
    per_seed_adv = []
    all_adv = []
    all_tot = []
    for seed in seeds:
        common, own = draws[seed] if draws is not None else base_draws(seed, per_seed, k, m)
        tot = batch_totals(mix(common, own, w), seq)
        adv = tot[:, 0] - tot[:, k - 1]
        per_seed_adv.append(float(adv.mean()))
        all_adv.append(adv)
        all_tot.append(tot)
    adv = np.concatenate(all_adv)
    tot = np.concatenate(all_tot)
    return {
        "mean_totals": tuple(float(x) for x in tot.mean(axis=0)),
        "advantage": float(adv.mean()),
        "advantage_se": float(adv.std(ddof=1) / np.sqrt(len(adv))),
        "advantage_by_seed": tuple(per_seed_adv),
        "n": int(len(adv)),
    }
