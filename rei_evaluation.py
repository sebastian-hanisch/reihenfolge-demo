"""Kennzahlen, Verdikt-Logik und Messreihen: Elfmeterschießen (exakt) und Wahlreihenfolge (Messreihe über feste Zufalls-Seeds)."""

import math
from dataclasses import dataclass

import rei_algorithm as A
import rei_choice as H
import rei_constants as C
import rei_scenario as S


@dataclass(frozen=True)
class Settings:
    p: float = C.DEFAULT_P
    d: float = C.DEFAULT_D
    order: str = C.DEFAULT_ORDER
    r: int = C.DEFAULT_R
    k: int = C.DEFAULT_K
    m: int = C.DEFAULT_M
    w: float = C.DEFAULT_W
    rule: str = C.DEFAULT_RULE
    seed: int = C.DEFAULT_SEED


@dataclass(frozen=True)
class ShootoutAnalysis:
    exact: A.Exact              # für die gewählte Reihenfolge
    exact_abab: A.Exact
    exact_abba: A.Exact
    shots: list                 # das gezeigte Elfmeterschießen (Schuss für Schuss)


@dataclass(frozen=True)
class ChoiceExample:
    values: object              # (k, m) Bewertungsmatrix
    sequence: tuple
    owner: tuple
    steps: list                 # (Person, Gut) je Schritt der gewählten Wahlfolge
    totals: dict                # Regel -> Gesamtwert je Person im gezeigten Beispiel
    picks_per_person: tuple


def de_int(n: int) -> str:
    """Ganze Zahl mit Punkt als Tausendertrenner (10.000)."""
    return f"{n:,}".replace(",", ".")


def exact_equal(order: str, r: int, p: float, d: float) -> A.Exact:
    """Zwei gleich starke Mannschaften (gleiche p und d)."""
    return A.exact_shootout(order, r, p, p, d, d)


def analyse_shootout(s: Settings) -> ShootoutAnalysis:
    return ShootoutAnalysis(
        exact=exact_equal(s.order, s.r, s.p, s.d),
        exact_abab=exact_equal("ABAB", s.r, s.p, s.d),
        exact_abba=exact_equal("ABBA", s.r, s.p, s.d),
        shots=S.example_shootout(s.order, s.r, s.p, s.d, s.seed),
    )


def shot_rows(shots) -> list[dict]:
    """Das gezeigte Elfmeterschießen als Tabellenzeilen (Anzeigewerte; Prozent als Zahl mal 100)."""
    return [
        {
            "Schuss": sh.number, "Paar": sh.pair, "Phase": sh.phase, "Schütze": f"Mannschaft {sh.team}",
            "Trefferchance (%)": 100.0 * sh.probability, "Ergebnis": "Treffer" if sh.hit else "verfehlt",
            "Stand A : B": f"{sh.score_a} : {sh.score_b}", "Entschieden": "ja" if sh.decided else "",
        }
        for sh in shots
    ]


def sweep_d(p: float, r: int, ds=C.D_SWEEP) -> list[dict]:
    """Gewinnwahrscheinlichkeit der ersten Mannschaft über den Abschlag d, beide Reihenfolgen, exakt."""
    return [{"d": d, "abab": exact_equal("ABAB", r, p, d).win_a, "abba": exact_equal("ABBA", r, p, d).win_a} for d in ds]


def sweep_r(p: float, d: float, rs=range(C.R_MIN, C.R_MAX + 1)) -> list[dict]:
    """Gewinnwahrscheinlichkeit der ersten Mannschaft über die Schüsse je Mannschaft, beide Reihenfolgen, exakt."""
    return [{"r": r, "abab": exact_equal("ABAB", r, p, d).win_a, "abba": exact_equal("ABBA", r, p, d).win_a} for r in rs]


def table_independent(r: int, ps=C.P_TABLE) -> list[dict]:
    """Ohne Abhängigkeit (d = 0): erste Mannschaft, beide Reihenfolgen; dazu ein Paar ungleich starker Mannschaften (0,8 gegen 0,6)."""
    rows = [{"label": f"p = {p:.1f} für beide", "abab": exact_equal("ABAB", r, p, 0.0).win_a, "abba": exact_equal("ABBA", r, p, 0.0).win_a} for p in ps]
    rows.append({"label": "A mit 0,8 gegen B mit 0,6", "abab": A.exact_shootout("ABAB", r, 0.8, 0.6, 0.0, 0.0).win_a, "abba": A.exact_shootout("ABBA", r, 0.8, 0.6, 0.0, 0.0).win_a})
    return rows


def probe(s: Settings, n: int = C.MC_N, seed: int = C.MC_SEED) -> dict:
    """Probe: n Elfmeterschießen nachspielen und mit der exakten Wahrscheinlichkeit vergleichen (Standardfehler der Binomialverteilung)."""
    wins, shots = A.simulate(s.order, s.r, s.p, s.p, s.d, s.d, n, seed)
    exact = exact_equal(s.order, s.r, s.p, s.d)
    freq = wins / n
    se = math.sqrt(exact.win_a * (1.0 - exact.win_a) / n)
    return {"n": n, "wins": wins, "freq": freq, "exact": exact.win_a, "se": se, "mean_shots": shots / n, "exact_shots": exact.shots_total,
            "inside": abs(freq - exact.win_a) <= C.MC_SIGMAS * se}


# --- Wahlreihenfolge --------------------------------------------------------------------------------------------------------------------

def picks_per_person(rule: str, k: int, m: int) -> tuple[int, ...]:
    seq = H.pick_sequence(rule, k, m)
    return tuple(seq.count(i) for i in range(k))


def choice_example(s: Settings) -> ChoiceExample:
    values = S.example_values(s.k, s.m, s.w, s.seed)
    seq = H.pick_sequence(s.rule, s.k, s.m)
    owner = H.allocate(values, seq)
    totals = {rule: H.totals_of(values, H.allocate(values, H.pick_sequence(rule, s.k, s.m)), s.k) for rule in C.RULES}
    return ChoiceExample(values, seq, owner, H.pick_steps(values, seq), totals, picks_per_person(s.rule, s.k, s.m))


def get_draws(k: int, m: int, seeds=C.SWEEP_SEEDS, per_seed: int = C.INSTANCES_PER_SEED) -> dict:
    return {seed: H.base_draws(seed, per_seed, k, m) for seed in seeds}


def choice_table(k: int, m: int, w: float, draws=None) -> list[dict]:
    """Je Regel: mittlerer Gesamtwert der ersten und der letzten Person, Vorteil der ersten (erste minus letzte), Standardfehler, Wahlen je Person."""
    draws = draws if draws is not None else get_draws(k, m)
    rows = []
    for rule in C.RULES:
        res = H.measure(rule, k, m, w, draws=draws)
        rows.append({"rule": rule, "first": res["mean_totals"][0], "last": res["mean_totals"][k - 1], "advantage": res["advantage"], "se": res["advantage_se"],
                     "by_seed": res["advantage_by_seed"], "n": res["n"], "picks": picks_per_person(rule, k, m)})
    return rows


def sweep_w(k: int, m: int, draws=None, ws=C.W_SWEEP) -> list[dict]:
    """Vorteil der ersten gegenüber der letzten Person über die Geschmacksähnlichkeit w, je Regel."""
    draws = draws if draws is not None else get_draws(k, m)
    rows = []
    for w in ws:
        row = {"w": w}
        for rule in C.RULES:
            res = H.measure(rule, k, m, w, draws=draws)
            row[rule] = res["advantage"]
            row[rule + "_se"] = res["advantage_se"]
        rows.append(row)
    return rows


def m_sweep(k: int) -> tuple[int, ...]:
    """Gütermengen der Messreihe über m: nur Vielfache der Personenzahl (dann wählt jede Person gleich oft)."""
    return tuple(k * j for j in (2, 3, 4, 6, 8) if C.M_MIN <= k * j <= C.M_MAX)


def sweep_m(k: int, w: float) -> list[dict]:
    """Vorteil der ersten gegenüber der letzten Person über die Zahl der Güter (Vielfache von k), je Regel."""
    rows = []
    for m in m_sweep(k):
        draws = get_draws(k, m)
        row = {"m": m}
        for rule in C.RULES:
            res = H.measure(rule, k, m, w, draws=draws)
            row[rule] = res["advantage"]
            row[rule + "_se"] = res["advantage_se"]
        rows.append(row)
    return rows


# --- Verdikte (reine Funktionen: (Art, Text)) ------------------------------------------------------------------------------------------

def verdict_shootout(d: float, order: str, win_selected: float, win_abab: float, win_abba: float) -> tuple[str, str]:
    """Kernfrage 1: Hat die erste Mannschaft einen Vorteil? Nimmt Gewinnwahrscheinlichkeiten (0 bis 1) der ersten Mannschaft."""
    pct = lambda x: f"{100.0 * x:.1f} %"  # noqa: E731
    if d == 0.0:
        return "info", (f"Die Schüsse sind unabhängig (d = 0): Die erste Mannschaft gewinnt bei ABAB mit **{pct(win_abab)}** und bei ABBA mit **{pct(win_abba)}**. "
                        "Ohne Abhängigkeit vom Spielstand entscheidet die Reihenfolge nichts.")
    edge = win_selected - 0.5
    if abs(edge) < 0.01:
        return "success", (f"Bei Reihenfolge {order} gewinnt die erste Mannschaft mit **{pct(win_selected)}**: der Vorteil liegt unter einem Prozentpunkt "
                           f"(zum Vergleich ABAB {pct(win_abab)}, ABBA {pct(win_abba)}).")
    who = "erste" if edge > 0 else "zweite"
    return "warning", (f"Bei Reihenfolge {order} gewinnt die erste Mannschaft mit **{pct(win_selected)}**: ein Vorteil der {who}n Mannschaft von {100.0 * abs(edge):.1f} Prozentpunkten "
                       f"(zum Vergleich ABAB {pct(win_abab)}, ABBA {pct(win_abba)}).")


def verdict_sweep_d(rows: list[dict]) -> tuple[str, str]:
    """Experiment über d: nennt die Werte am größten d und zählt, bei wie vielen d > 0 ABBA näher an 50 % liegt als ABAB."""
    positive = [r for r in rows if r["d"] > 0]
    closer = sum(1 for r in positive if abs(r["abba"] - 0.5) < abs(r["abab"] - 0.5))
    last = rows[-1]
    return "info", (f"Bei d = {last['d']:.2f} gewinnt die erste Mannschaft mit {100 * last['abab']:.1f} % (ABAB) und {100 * last['abba']:.1f} % (ABBA). "
                    f"ABBA liegt in {closer} von {len(positive)} gemessenen Werten d > 0 näher an 50 % als ABAB.")


def verdict_sweep_r(rows: list[dict]) -> tuple[str, str]:
    """Experiment über die Schüsse je Mannschaft: Spanne der ABAB-Werte und Lauf der ABBA-Werte."""
    abab = [r["abab"] for r in rows]
    spread = 100.0 * (max(abab) - min(abab))
    return "info", (f"ABAB: {100 * abab[0]:.1f} % bei {rows[0]['r']} Schuss je Mannschaft, {100 * abab[-1]:.1f} % bei {rows[-1]['r']}; Spanne {spread:.2f} Prozentpunkte. "
                    f"ABBA: {100 * rows[0]['abba']:.1f} % bei {rows[0]['r']}, {100 * rows[-1]['abba']:.1f} % bei {rows[-1]['r']}.")


def verdict_probe(res: dict) -> tuple[str, str]:
    """Probe: liegt die Häufigkeit der nachgespielten Elfmeterschießen im Band um die exakte Wahrscheinlichkeit?"""
    text = (f"{de_int(res['n'])} nachgespielte Elfmeterschießen: erste Mannschaft gewinnt {100 * res['freq']:.1f} %, exakt {100 * res['exact']:.1f} % "
            f"(Band ±{C.MC_SIGMAS:.0f} Standardfehler = ±{100 * C.MC_SIGMAS * res['se']:.1f} Prozentpunkte).")
    return ("success", text + " Die Häufigkeit liegt im Band.") if res["inside"] else ("warning", text + " Die Häufigkeit liegt außerhalb des Bandes.")


def verdict_choice(rows: list[dict], k: int, m: int) -> tuple[str, str]:
    """Kernfrage 2: Vorteil der ersten gegenüber der letzten Person je Regel (Mittel über Bewertungsmatrizen); nennt die Regel mit dem kleinsten Betrag
    und den Abstand zur nächsten Regel. Liegt der Abstand unter zwei Standardfehlern (des größten Einzelwerts), gilt er als nicht unterscheidbar (kein Befund)."""
    ranked = sorted(rows, key=lambda r: abs(r["advantage"]))
    smallest, runner_up = ranked[0], ranked[1]
    se_max = max(r["se"] for r in rows)
    gap = abs(runner_up["advantage"]) - abs(smallest["advantage"])
    parts = ", ".join(f"{r['rule']} {r['advantage']:+.2f}" for r in rows)
    text = (f"Erste minus letzte Person, Mittel über {de_int(rows[0]['n'])} Bewertungsmatrizen: {parts} (Standardfehler je höchstens {se_max:.2f}). "
            f"Betragsmäßig am kleinsten ist {smallest['rule']}; der Abstand zu {runner_up['rule']} beträgt {gap:.2f}, zwei Standardfehler eines einzelnen Wertes sind {2 * se_max:.2f}. ")
    if gap < 2.0 * se_max:
        text += "Der Abstand der Beträge ist kleiner: die beiden Regeln sind hier nicht unterscheidbar."
    else:
        text += "Der Abstand der Beträge ist größer."
    if m % k != 0:
        extra = m % k
        who = "wählt die erste Person" if extra == 1 else f"wählen die ersten {extra} Personen"
        text += f" Bei {m} Gütern und {k} Personen {who} einmal öfter; das gehört zum Vorteil der Ersten."
        return "warning", text
    return "info", text


def verdict_sweep_w(rows: list[dict]) -> tuple[str, str]:
    """Experiment über die Geschmacksähnlichkeit w: Reihum am ersten und letzten Wert, dazu die anderen Regeln am letzten."""
    a, b = rows[0], rows[-1]
    return "info", (f"Reihum: {a['Reihum']:+.2f} bei w = {a['w']:.1f}, {b['Reihum']:+.2f} bei w = {b['w']:.1f}. Schlange: {a['Schlange']:+.2f} und {b['Schlange']:+.2f}. "
                    f"Thue-Morse: {a['Thue-Morse']:+.2f} und {b['Thue-Morse']:+.2f}.")


def verdict_sweep_m(rows: list[dict]) -> tuple[str, str]:
    """Experiment über die Zahl der Güter: Werte am kleinsten und größten m."""
    a, b = rows[0], rows[-1]
    return "info", (f"Bei m = {a['m']} Gütern: Reihum {a['Reihum']:+.2f}, Schlange {a['Schlange']:+.2f}, Thue-Morse {a['Thue-Morse']:+.2f}; "
                    f"bei m = {b['m']}: {b['Reihum']:+.2f}, {b['Schlange']:+.2f}, {b['Thue-Morse']:+.2f}.")
