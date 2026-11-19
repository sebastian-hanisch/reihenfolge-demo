"""Die kopierte Datei rei_rng.py (wörtlich, Quelle im Kopf der Datei): Vergleich mit der Vorlage, solange sie im Portfolio-Ordner liegt."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SOURCES = {"rei_rng.py": ("sebastianhanisch-website", "tools/templates/rng_splitmix64_exact.py")}


@pytest.mark.parametrize("copy", list(SOURCES))
def test_copy_is_verbatim_apart_from_the_header(copy):
    folder, original = SOURCES[copy]
    source = ROOT.parent / folder / original
    if not source.exists():
        pytest.skip("Vorlage liegt nicht im Portfolio-Ordner")
    mine = (ROOT / copy).read_text(encoding="utf-8").splitlines()
    assert mine[0].startswith(f"# Wörtliche Kopie von {folder}/{original}")
    assert mine[1:] == source.read_text(encoding="utf-8").splitlines(), "die Kopie weicht von der Vorlage ab: Änderungen gehören in die Vorlage, danach neu kopieren"


def test_the_copy_runs_on_its_own():
    from rei_rng import SplitMix64
    assert SplitMix64(0).next_u64() == 16294208416658607535
    assert SplitMix64(1).below(10) in range(10)
    assert 0.0 <= SplitMix64(7).random() < 1.0
