"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

# --- Elfmeterschießen ------------------------------------------------------------------------------------------------------------------
P_MIN, P_MAX, DEFAULT_P = 0.30, 0.95, 0.75     # Trefferwahrscheinlichkeit, wenn der Schütze nicht zurückliegt
D_MIN, D_MAX, DEFAULT_D = 0.0, 0.25, 0.05      # Abschlag im Rückstand: p - d; P_MIN - D_MAX = 0,05, die Wahrscheinlichkeit bleibt positiv
ORDERS = ("ABAB", "ABBA")                      # Schussreihenfolge; Namen der Auswahlbox
DEFAULT_ORDER = "ABAB"
R_MIN, R_MAX, DEFAULT_R = 1, 8, 5              # Schüsse je Mannschaft in der Regelzeit (Aufzählung: 2^(2 R) = 65.536 Schussfolgen bei R = 8)
MAX_SD_PAIRS = 5000                            # Sicherung der Sudden-Death-Schleife: bei p <= 0,95 bleibt nach 5.000 Paaren weniger als 1e-200 übrig
MC_N = 10000                                   # nachgespielte Elfmeterschießen der Probe
MC_SEED = 100000                               # fester Zufalls-Seed der Probe (unabhängig vom Seed der Seitenleiste)
MC_SIGMAS = 3.0                                # Breite des Bandes der Probe in Standardfehlern (App); die Tests nehmen 4,5
D_SWEEP = tuple(round(0.01 * i, 2) for i in range(0, 26))   # d von 0 bis 0,25
P_TABLE = (0.3, 0.5, 0.7, 0.9)                 # Trefferwahrscheinlichkeiten der Tabelle ohne Abhängigkeit

# --- Wahlreihenfolge -------------------------------------------------------------------------------------------------------------------
K_MIN, K_MAX, DEFAULT_K = 2, 4, 2              # Personen
M_MIN, M_MAX, DEFAULT_M = 4, 24, 10            # Güter
W_MIN, W_MAX, DEFAULT_W = 0.0, 1.0, 0.0        # Geschmacksähnlichkeit: 0 = jede Person bewertet unabhängig, 1 = alle bewerten gleich
RULES = ("Reihum", "Schlange", "Thue-Morse")   # Namen der Auswahlbox
DEFAULT_RULE = "Reihum"
SWEEP_SEEDS = tuple(range(100000, 100005))     # feste Zufalls-Seeds aller Messreihen: nie ein einzelner Seed als Befund
INSTANCES_PER_SEED = 400                       # Bewertungsmatrizen je Zufalls-Seed (5 x 400 = 2.000 je Zelle)
W_SWEEP = tuple(round(0.1 * i, 1) for i in range(0, 11))
M_SWEEP = (4, 6, 8, 10, 14, 18, 24)

SEED_MAX, DEFAULT_SEED = 999999, 35

COLOR_A = "#2F6B65"
COLOR_B = "#C0602A"
COLOR_LINE_A = "#4c78a8"
COLOR_LINE_B = "#e45756"
COLOR_LINE_C = "#54a24b"
COLOR_BAND = "rgba(150,150,150,0.35)"

PRESETS = {
    "Standardfall (Voreinstellung)": dict(p=DEFAULT_P, d=DEFAULT_D, order="ABAB", r=DEFAULT_R, k=DEFAULT_K, m=DEFAULT_M, w=DEFAULT_W, rule="Reihum", seed=DEFAULT_SEED),
    "Unabhängige Schüsse (d = 0)": dict(p=DEFAULT_P, d=0.0, order="ABAB", r=DEFAULT_R, k=DEFAULT_K, m=DEFAULT_M, w=DEFAULT_W, rule="Reihum", seed=DEFAULT_SEED),
    "Starker Druck, ABAB (d = 0,15)": dict(p=DEFAULT_P, d=0.15, order="ABAB", r=DEFAULT_R, k=DEFAULT_K, m=DEFAULT_M, w=DEFAULT_W, rule="Reihum", seed=DEFAULT_SEED),
    "Starker Druck, ABBA (d = 0,15)": dict(p=DEFAULT_P, d=0.15, order="ABBA", r=DEFAULT_R, k=DEFAULT_K, m=DEFAULT_M, w=DEFAULT_W, rule="Reihum", seed=DEFAULT_SEED),
    "Wahl: ähnlicher Geschmack": dict(p=DEFAULT_P, d=DEFAULT_D, order="ABAB", r=DEFAULT_R, k=DEFAULT_K, m=DEFAULT_M, w=0.8, rule="Reihum", seed=DEFAULT_SEED),
    "Wahl: drei Personen, Thue-Morse": dict(p=DEFAULT_P, d=DEFAULT_D, order="ABAB", r=DEFAULT_R, k=3, m=12, w=0.5, rule="Thue-Morse", seed=DEFAULT_SEED),
}
PRESET_HELP = {
    "Standardfall (Voreinstellung)": "Elfmeterschießen mit fünf Schüssen je Mannschaft, Trefferwahrscheinlichkeit 0,75, Abschlag 0,05 im Rückstand, Reihenfolge ABAB; Wahl: zwei Personen, zehn Güter, unabhängiger Geschmack, Reihum.",
    "Unabhängige Schüsse (d = 0)": "Kein Abschlag im Rückstand: die Schüsse sind unabhängig. Beide Reihenfolgen geben der ersten Mannschaft genau 50 %.",
    "Starker Druck, ABAB (d = 0,15)": "Im Rückstand trifft der Schütze mit p − 0,15. Bei ABAB schießt die zweite Mannschaft im Mittel öfter im Rückstand als die erste.",
    "Starker Druck, ABBA (d = 0,15)": "Derselbe Druck, aber die Reihenfolge ABBA: die Paare wechseln, wer zuerst schießt. Der Vorteil der ersten Mannschaft ist hier kleiner als bei ABAB.",
    "Wahl: ähnlicher Geschmack": "Zwei Personen bewerten die zehn Güter mit dem Gewicht 0,8 auf einen gemeinsamen Wert je Gut. Bei Reihum ist der Vorteil der ersten Person hier größer als bei unabhängigem Geschmack.",
    "Wahl: drei Personen, Thue-Morse": "Drei Personen, zwölf Güter, halb ähnlicher Geschmack, Wahlfolge Thue-Morse (Stellensumme zur Basis 3 modulo 3).",
}
