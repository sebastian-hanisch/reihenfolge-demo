"""Szenario: das gezeigte Beispiel (ein Elfmeterschießen, eine Bewertungsmatrix) aus den Reglerwerten und dem Zufalls-Seed der Seitenleiste.

Alles mit dem Zufallsgenerator der Demo (SplitMix64, `rei_rng.py`): gleiche Reglerwerte und gleicher Zufalls-Seed, gleiches Beispiel auf jeder Plattform."""

import numpy as np

import rei_algorithm as A
import rei_choice as H
from rei_rng import SplitMix64


def example_shootout(order: str, r: int, p: float, d: float, seed: int) -> list[A.Shot]:
    """Das gezeigte Elfmeterschießen: beide Mannschaften gleich stark (p, d), Schuss für Schuss."""
    return A.play_shootout(SplitMix64(seed), order, r, p, p, d, d)


def example_values(k: int, m: int, w: float, seed: int) -> np.ndarray:
    """Die gezeigte Bewertungsmatrix (k Personen, m Güter) nach dem Geschmacksmodell mit dem Geschmacksähnlichkeits-Regler w."""
    return H.make_values(SplitMix64(seed), k, m, w)
