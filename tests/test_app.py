"""End-to-end Rauchtests mit Streamlits AppTest: jeder Knopf, jeder Regler an beiden Grenzen, die Kombination aller Minima und aller Maxima, jede Auswahl, der Permalink,
die Verdikte der Seite gegen die Kernrechnung und die Übergabe der Reglerwerte an die richtigen Einstellungen (Schlüsselwörter, DEMO-PLAYBOOK §1d).

Laufzeit: Eine App für die ganze Datei, jeder Test stellt sie über das Standard-Preset zurück (ein frischer Start kostet etwa 3 Sekunden, ein Lauf nach einer Änderung meist weniger als eine)."""

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import rei_algorithm as A
import rei_constants as C
import rei_evaluation as ev
import rei_presets as P
from rei_rng import SplitMix64

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))      # unter Last (parallele Läufe) reichen 180 s nicht immer
STANDARD = next(iter(C.PRESETS))


@pytest.fixture(scope="module")
def app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


@pytest.fixture
def at(app):
    app.sidebar.button(key=f"preset_{STANDARD}").click().run(timeout=TIMEOUT)
    assert not app.exception, [str(e) for e in app.exception]
    return app


def _texts(at):
    return " ".join([m.value for m in at.markdown] + [s.value for s in at.success] + [i.value for i in at.info] + [w.value for w in at.warning] + [c.value for c in at.caption])


def _expander(at, label):
    return next(e for e in at.expander if e.label == label)               # nie per Index (DEMO-PLAYBOOK §2)


def _set(at, key, value):
    for art in ("slider", "selectbox", "number_input"):
        try:
            getattr(at.sidebar, art)(key=key).set_value(value)
            return
        except KeyError:
            continue
    raise AssertionError(key)


def _metric(at, label):
    return next(m for m in at.metric if m.label == label).value


def test_app_loads_without_exception_and_has_both_tabs(at):
    assert [t.label for t in at.tabs] == ["🥅 Elfmeterschießen", "🧺 Wahlreihenfolge"]
    assert at.title[0].value.startswith("🔀 Wann zählt die Reihenfolge?")
    assert "🚧 Wo die Annahmen enden" in " ".join(s.value for s in at.subheader)


def test_every_button_click_does_not_raise(at):
    labels = [b.label for b in at.sidebar.button]
    assert len(labels) == len(C.PRESETS) + 1 and "🎲 Neues Beispiel würfeln" in labels
    for key in [f"preset_{name}" for name in C.PRESETS]:
        at.sidebar.button(key=key).click().run(timeout=TIMEOUT)
        assert not at.exception, (key, [str(e) for e in at.exception])
    next(b for b in at.sidebar.button if b.label == "🎲 Neues Beispiel würfeln").click().run(timeout=TIMEOUT)
    assert not at.exception


@pytest.mark.parametrize("state_key", [k for k, s in P.SETTING_SPECS.items() if s.options is None])
def test_every_slider_and_input_at_its_min_and_max_does_not_raise(at, state_key):
    spec = P.SETTING_SPECS[state_key]
    for edge, value in (("min", spec.lo), ("max", spec.hi)):
        _set(at, state_key, spec.caster(value))
        at.run(timeout=TIMEOUT)
        assert not at.exception, (state_key, edge, [str(e) for e in at.exception])


@pytest.mark.parametrize("state_key", [k for k, s in P.SETTING_SPECS.items() if s.options is not None])
def test_every_option_of_every_selectbox_does_not_raise(at, state_key):
    for option in P.SETTING_SPECS[state_key].options:
        _set(at, state_key, option)
        at.run(timeout=TIMEOUT)
        assert not at.exception, (state_key, option, [str(e) for e in at.exception])


@pytest.mark.parametrize("edge", ["lo", "hi"])
def test_all_minima_and_all_maxima_together_do_not_raise(at, edge):
    for state_key, spec in P.SETTING_SPECS.items():
        if spec.options is not None:
            _set(at, state_key, spec.options[0 if edge == "lo" else -1])
        else:
            _set(at, state_key, spec.caster(spec.lo if edge == "lo" else spec.hi))
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]


def test_the_sidebar_values_reach_the_right_settings(at):
    """Die angezeigten Kennzahlen kommen aus den Reglerwerten (nicht aus den Standardwerten): feste, von den Voreinstellungen verschiedene Werte, Kennzahlen gegen die Kernrechnung."""
    for key, value in (("p_slider", 0.6), ("d_slider", 0.12), ("order_select", "ABBA"), ("r_slider", 3)):
        _set(at, key, value)
    at.run(timeout=TIMEOUT)
    assert not at.exception
    e = ev.exact_equal("ABBA", 3, 0.6, 0.12)
    assert _metric(at, "Erste Mannschaft (A) gewinnt") == f"{100 * e.win_a:.1f} %"
    assert _metric(at, "Zweite Mannschaft (B) gewinnt") == f"{100 * e.win_b:.1f} %"
    assert _metric(at, "Sudden Death nötig") == f"{100 * e.p_tie:.1f} %"
    assert _metric(at, "Erwartete Schüsse") == f"{e.shots_total:.1f}"
    kind, text = ev.verdict_shootout(0.12, "ABBA", e.win_a, ev.exact_equal("ABAB", 3, 0.6, 0.12).win_a, e.win_a)
    assert text in _texts(at)


def test_the_choice_values_reach_the_right_settings(at):
    for key, value in (("k_slider", 3), ("m_slider", 9), ("w_slider", 0.5), ("rule_select", "Schlange")):
        _set(at, key, value)
    at.run(timeout=TIMEOUT)
    assert not at.exception
    table = ev.choice_table(3, 9, 0.5)
    kind, text = ev.verdict_choice(table, 3, 9)
    assert text in _texts(at)
    assert "Folge bei k = 3, m = 9" in " ".join(str(c) for df in at.dataframe for c in df.value.columns)
    assert any(df.value.shape == (9, 4) and list(df.value.columns) == ["Schritt", "Wählt", "Nimmt", "Wert"] for df in at.dataframe)     # ein Schritt je Gut


def test_default_page_shows_the_expected_verdicts_and_figures(at):
    texts = _texts(at)
    s = ev.Settings()
    e, abab, abba = ev.exact_equal(s.order, s.r, s.p, s.d), ev.exact_equal("ABAB", s.r, s.p, s.d), ev.exact_equal("ABBA", s.r, s.p, s.d)
    assert ev.verdict_shootout(s.d, s.order, e.win_a, abab.win_a, abba.win_a)[1] in texts
    assert ev.verdict_sweep_d(ev.sweep_d(s.p, s.r))[1] in texts
    assert ev.verdict_sweep_r(ev.sweep_r(s.p, s.d))[1] in texts
    assert ev.verdict_probe(ev.probe(s))[1] in texts
    assert ev.verdict_sweep_w(ev.sweep_w(s.k, s.m))[1] in texts
    assert ev.verdict_sweep_m(ev.sweep_m(s.k, s.w))[1] in texts
    assert len(at.get("plotly_chart")) == 7             # Spielstand, Abbruch, Abschlag d, Schüsse je Mannschaft, Gesamtwerte, Geschmack w, Zahl der Güter


def test_independent_preset_reports_exactly_fifty_percent(at):
    at.sidebar.button(key="preset_Unabhängige Schüsse (d = 0)").click().run(timeout=TIMEOUT)
    assert not at.exception
    assert _metric(at, "Erste Mannschaft (A) gewinnt") == "50.0 %"
    assert any("Die Schüsse sind unabhängig (d = 0)" in i.value for i in at.info)
    assert any("genau zu 50 %" in s.value for s in at.success)


def test_every_preset_shows_the_verdict_of_its_own_settings(at):
    for name, preset in C.PRESETS.items():
        at.sidebar.button(key=f"preset_{name}").click().run(timeout=TIMEOUT)
        assert not at.exception, name
        s = ev.Settings(**preset)
        e = ev.exact_equal(s.order, s.r, s.p, s.d)
        expected = ev.verdict_shootout(s.d, s.order, e.win_a, ev.exact_equal("ABAB", s.r, s.p, s.d).win_a, ev.exact_equal("ABBA", s.r, s.p, s.d).win_a)[1]
        assert expected in _texts(at), name
        assert ev.verdict_choice(ev.choice_table(s.k, s.m, s.w), s.k, s.m)[1] in _texts(at), name


def test_the_explanation_of_each_named_choice_rule_and_order_is_on_the_page(at):
    tables = [df.value for df in at.dataframe if "So wählt man" in df.value.columns]
    assert len(tables) == 1 and list(tables[0]["Regel"]) == list(C.RULES)
    for name, text in (("Reihum", "Die Personen wählen der Reihe nach"), ("Schlange", "Jede zweite Runde läuft rückwärts"), ("Thue-Morse", "Stellensumme von t zur Basis k")):
        assert text in tables[0].set_index("Regel").loc[name, "So wählt man"], name
    assert tables[0].set_index("Regel").loc["Reihum", "Folge bei k = 2, m = 10"] == "ABABABABAB"
    assert "ABAB: Mannschaft A schießt in jedem Paar zuerst" in _texts(at)
    _set(at, "order_select", "ABBA")
    at.run(timeout=TIMEOUT)
    assert "ABBA: die Paare wechseln" in _texts(at)


def test_demarcation_and_assumption_texts_are_present(at):
    texts = _texts(at)
    assert "unteilbare-gueter-demo" in texts
    assert "Wo die Annahmen enden" in " ".join(s.value for s in at.subheader)
    assert _expander(at, "⚠️ Annahmen, Grenzen und bekannte Probleme")
    assert "nur aus Suchergebnissen, nicht im Volltext gelesen" in _expander(at, "⚠️ Annahmen, Grenzen und bekannte Probleme").markdown[0].value
    assert "Catch-Up" in _expander(at, "⚠️ Annahmen, Grenzen und bekannte Probleme").markdown[0].value


def test_math_blocks_have_no_inline_dollar_or_unescaped_percent(at):
    body = " ".join(m.value for m in _expander(at, "📐 Mathematische Formulierung").markdown)
    assert "%" not in body.replace("\\%", "")
    assert body.count("$$") % 2 == 0


def test_permalink_values_are_clamped_and_unknown_options_ignored():
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.query_params["p"] = "7"
    at.query_params["order"] = "XYZ"
    at.query_params["k"] = "99"
    at.run(timeout=TIMEOUT)
    assert not at.exception
    assert at.sidebar.slider(key="p_slider").value == pytest.approx(C.P_MAX)
    assert at.sidebar.selectbox(key="order_select").value == C.DEFAULT_ORDER
    assert at.sidebar.slider(key="k_slider").value == C.K_MAX


def test_shown_shootout_is_the_one_of_the_chosen_seed(at):
    _set(at, "seed_input", 7)
    at.run(timeout=TIMEOUT)
    assert not at.exception
    shots = A.play_shootout(SplitMix64(7), "ABAB", 5, 0.75, 0.75, 0.05, 0.05)
    shown = [df.value for df in at.dataframe if "Trefferchance (%)" in df.value.columns]
    assert len(shown) == 1 and len(shown[0]) == len(shots)
    assert list(shown[0]["Ergebnis"]) == ["Treffer" if sh.hit else "verfehlt" for sh in shots]
    assert shown[0]["Stand A : B"].iloc[-1] == f"{shots[-1].score_a} : {shots[-1].score_b}"
