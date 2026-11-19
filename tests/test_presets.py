"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, jede Aussage der Preset-Hilfe gegen die Rechnung (DEMO-PLAYBOOK §11a Punkt 7)."""

import pytest

import rei_choice as H
import rei_constants as C
import rei_evaluation as ev
import rei_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds_and_options():
    for name, preset in C.PRESETS.items():
        for key, state_key in P.PRESET_KEYS.items():
            spec = P.SETTING_SPECS[state_key]
            value = preset[key]
            if spec.options is not None:
                assert value in spec.options, (name, key)
            else:
                assert spec.lo <= value <= spec.hi, (name, key)
                assert isinstance(value, (int, float)), (name, key)


def test_the_choice_always_fits_into_the_instance():
    assert C.K_MAX <= C.M_MIN
    for preset in C.PRESETS.values():
        assert preset["k"] <= preset["m"]


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS["Standardfall (Voreinstellung)"]) == ev.Settings()


def test_presets_are_pairwise_different():
    settings = [ev.Settings(**p) for p in C.PRESETS.values()]
    assert len(set(settings)) == len(settings)


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_help_of_the_independent_preset_says_fifty_percent_and_it_is():
    s = ev.Settings(**C.PRESETS["Unabhängige Schüsse (d = 0)"])
    assert s.d == 0.0
    for order in C.ORDERS:
        assert ev.exact_equal(order, s.r, s.p, 0.0).win_a == pytest.approx(0.5, abs=1e-12)
    assert "genau 50 %" in C.PRESET_HELP["Unabhängige Schüsse (d = 0)"]


def test_help_of_the_pressure_presets_matches_the_numbers():
    abab = ev.Settings(**C.PRESETS["Starker Druck, ABAB (d = 0,15)"])
    abba = ev.Settings(**C.PRESETS["Starker Druck, ABBA (d = 0,15)"])
    assert (abab.d, abba.d) == (0.15, 0.15) and (abab.order, abba.order) == ("ABAB", "ABBA")
    e_abab, e_abba = ev.exact_equal("ABAB", abab.r, abab.p, 0.15), ev.exact_equal("ABBA", abba.r, abba.p, 0.15)
    assert e_abab.trailing_b > e_abab.trailing_a                       # „schießt die zweite Mannschaft im Mittel öfter im Rückstand“
    assert e_abba.win_a - 0.5 < e_abab.win_a - 0.5                     # „Vorteil ist bei ABBA kleiner“


def test_help_of_the_similar_taste_preset_matches_the_measurement():
    s = ev.Settings(**C.PRESETS["Wahl: ähnlicher Geschmack"])
    assert (s.k, s.w, s.rule) == (2, 0.8, "Reihum")
    draws = ev.get_draws(s.k, s.m)
    similar = ev.choice_table(s.k, s.m, s.w, draws)[0]
    independent = ev.choice_table(s.k, s.m, 0.0, draws)[0]
    assert similar["rule"] == "Reihum" and similar["advantage"] > independent["advantage"]


def test_the_three_person_preset_uses_thue_morse_with_base_three():
    s = ev.Settings(**C.PRESETS["Wahl: drei Personen, Thue-Morse"])
    assert (s.k, s.m, s.rule) == (3, 12, "Thue-Morse")
    assert "".join("ABC"[i] for i in H.pick_sequence("Thue-Morse", 3, 9)) == "ABCBCACAB"
