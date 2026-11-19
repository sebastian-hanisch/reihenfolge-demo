"""Gemeinsame Fixtures: die Mini-Instanzen, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class ScriptedRng:
    """Ersatz für den Zufallsgenerator: liefert nacheinander vorgegebene Werte (ein Schuss trifft, wenn der Wert unter der Trefferwahrscheinlichkeit liegt)."""

    def __init__(self, values):
        self.values = list(values)

    def random(self):
        return self.values.pop(0)


@pytest.fixture
def scripted():
    return ScriptedRng


@pytest.fixture
def mini_values():
    """Zwei Personen, drei Güter. Person 1 bewertet 0,9 / 0,5 / 0,1, Person 2 bewertet 0,8 / 0,7 / 0,2 (Handrechnung in tests/test_choice.py)."""
    return np.array([[0.9, 0.5, 0.1], [0.8, 0.7, 0.2]])
