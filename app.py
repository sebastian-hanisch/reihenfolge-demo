"""Wann zählt die Reihenfolge? Elfmeterschießen und Wahlreihenfolge - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Wurzel der Linie „Wettbewerbsverzerrung erklärt“: bei gleich starken Seiten entscheidet die Reihenfolge nur, wenn Schüsse (oder Wahlen) voneinander abhängen.
Aufbau nach DEMO-PLAYBOOK.md (§2). Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import rei_algorithm as A
import rei_choice as H
import rei_constants as C
import rei_evaluation as E
from rei_layout import dunkles_design, kopf_css
from rei_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from rei_visualization import (
    build_choice_sweep,
    build_progress,
    build_stop_probs,
    build_sweep_d,
    build_sweep_r,
    build_totals,
)

st.set_page_config(page_title="Wann zählt die Reihenfolge? Elfmeterschießen und Wahlreihenfolge – Sebastian Hanisch", layout="wide")

ORDER_HELP = {
    "ABAB": "ABAB: Mannschaft A schießt in jedem Paar zuerst (A B A B …), auch im Sudden Death. Das ist die heutige Regel.",
    "ABBA": "ABBA: die Paare wechseln, wer zuerst schießt (A B | B A | A B | B A | A B …); das Paar 6 beginnt mit B, danach wechselt es weiter.",
}
RULE_TEXT = {
    "Reihum": "Die Personen wählen der Reihe nach 1, 2, …, k, dann wieder 1, 2, … (bei zwei Personen ABAB…).",
    "Schlange": "Jede zweite Runde läuft rückwärts: 1, 2, …, k, dann k, …, 2, 1, dann wieder vorwärts (bei zwei Personen ABBAABBA…).",
    "Thue-Morse": "Wer im Schritt t wählt, steht in der Stellensumme von t zur Basis k modulo k (bei zwei Personen ABBABAABBAABBABAAB…; für mehr als zwei Personen die Verallgemeinerung nach Prouhet).",
}
LETTERS = "ABCD"


@st.cache_data(show_spinner=False)
def _shootout(settings):
    return E.analyse_shootout(settings)


@st.cache_data(show_spinner=False)
def _sweep_d(p, r):
    return E.sweep_d(p, r)


@st.cache_data(show_spinner=False)
def _sweep_r(p, d):
    return E.sweep_r(p, d)


@st.cache_data(show_spinner=False)
def _table_independent(r):
    return E.table_independent(r)


@st.cache_data(show_spinner=False)
def _probe(order, r, p, d):
    return E.probe(E.Settings(p=p, d=d, order=order, r=r))


@st.cache_data(show_spinner=False)
def _choice_table(k, m, w):
    return E.choice_table(k, m, w)


@st.cache_data(show_spinner=False)
def _sweep_w(k, m):
    return E.sweep_w(k, m)


@st.cache_data(show_spinner=False)
def _sweep_m(k, w):
    return E.sweep_m(k, w)


@st.cache_data(show_spinner=False)
def _choice_example(settings):
    return E.choice_example(settings)


def pct(x: float) -> str:
    return f"{100.0 * x:.1f} %"


de_int = E.de_int


def letters(seq) -> str:
    return "".join(LETTERS[i] for i in seq)


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in rei_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🔀 Wann zählt die Reihenfolge? Elfmeterschießen und Wahlreihenfolge")
st.markdown(
    """
**Bei gleich starken Seiten: wann entscheidet die Reihenfolge überhaupt?** Beim **Elfmeterschießen** schießt eine Mannschaft zuerst. Sind die Schüsse **unabhängig**, ist das für den Sieg gleichgültig:
die erste Mannschaft gewinnt bei gleich starken Mannschaften genau zu 50 %, in der Reihenfolge ABAB wie in ABBA, mit und ohne vorzeitigen Abbruch. In diesem Modell erzeugt erst eine **Abhängigkeit vom Spielstand**
(wer zurückliegt, trifft seltener) einen Startvorteil, und die Reihenfolge ABBA dämpft ihn. Der Reiter **Wahlreihenfolge** fragt dasselbe für das abwechselnde Wählen unteilbarer Güter
(reihum, Schlange, Thue-Morse). Beides sind Modelle mit erfundenen Mannschaften und Zufallsbewertungen, keine Aussagen über echte Spiele.

Wer die Frage zuerst ohne Fachbegriffe verstehen will, öffnet „💬 In einfachen Worten“. Weiter unten: die **🔬 Experimente** in beiden Reitern, **🚧 Wo die Annahmen enden**, **⚠️ Annahmen, Grenzen und bekannte Probleme** und der Expander **📐 Mathematische Formulierung**.
"""
)

# erklaerseite:einfach:start (erzeugt von tools/set_demo_explainer.py (Website-Repo) aus tools/content/explainers/elfmeter-reihenfolge-erklaert.json, nicht von Hand ändern)
with st.expander("💬 In einfachen Worten"):
    st.markdown(
        """
Beim Elfmeterschießen schießt eine Mannschaft zuerst. Die Demo fragt, ob das bei zwei gleich starken Mannschaften einen Vorteil bringt. Im Rechenbild lautet die Antwort: Treffen alle Schützen unabhängig davon, wie es gerade steht, bringt die Reihenfolge keinen Vorteil. Erst wenn Schützen im Rückstand schlechter treffen, gewinnt die Mannschaft, die zuerst schießt, öfter. Wechselt der Beginn von Paar zu Paar, wird dieser Vorteil kleiner.

Der zweite Reiter stellt dieselbe Frage für das abwechselnde Wählen von Gegenständen: Wie viel hat die Person, die zuerst wählt, am Ende mehr als die letzte? Das hängt von der Wahlfolge ab, auch ohne jede Abhängigkeit. Alles ist erfunden und zeigt, wie sich eine Annahme auswirkt, nicht, wie es in echten Spielen ist.

[Ausführlich und verständlich erklärt, mit Fachteil](https://sebastianhanisch.net/elfmeter-reihenfolge-erklaert.html)
        """
    )
# erklaerseite:einfach:end

with st.expander("So funktioniert ein Elfmeterschießen mit Reihenfolge", expanded=True):
    st.markdown(
        """
1. **Regelzeit:** Beide Mannschaften schießen abwechselnd je *R* Mal. Bei **ABAB** beginnt Mannschaft A in jedem Paar; bei **ABBA** beginnt A in den Paaren 1, 3, 5, B in den Paaren 2, 4.
2. **Vorzeitiger Abbruch:** Sobald eine Mannschaft auch dann nicht mehr einzuholen wäre, wenn sie alle ihre restlichen Schüsse trifft und die andere alle verfehlt, endet die Regelzeit.
3. **Sudden Death:** Steht es nach allen Schüssen unentschieden, schießen beide Mannschaften paarweise weiter, bis ein Paar sie trennt (ein Treffer, ein Fehlschuss). Bei ABAB beginnt A immer; bei ABBA wechselt der Beginn von Paar zu Paar, bei fünf Schüssen beginnt das Paar 6 mit B.
4. **Trefferwahrscheinlichkeit:** *p*, solange die schießende Mannschaft nicht zurückliegt; *p − d* im Rückstand. Mit *d = 0* sind die Schüsse unabhängig.
5. **Was gemessen wird:** die Wahrscheinlichkeit, dass die erste Mannschaft (A) gewinnt, exakt aus einer Rekursion über alle Spielstände, nachgeprüft durch Aufzählung aller Schussfolgen, die geschlossene Form des Sudden Death und ein Nachspielen mit dem Zufallsgenerator der Demo.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**🥅 Elfmeterschießen** (gilt für den ersten Reiter)")
    p = st.slider("Trefferwahrscheinlichkeit p", *bounds("p_slider"), key="p_slider", step=0.01, format="%.2f",
                  help="Trefferwahrscheinlichkeit eines Schützen, dessen Mannschaft nicht zurückliegt. Beide Mannschaften sind gleich stark.")
    d = st.slider("Abschlag im Rückstand d", *bounds("d_slider"), key="d_slider", step=0.01, format="%.2f",
                  help="Wer zurückliegt, trifft mit p − d. Bei d = 0 sind die Schüsse unabhängig vom Spielstand.")
    order = st.selectbox("Schussreihenfolge", C.ORDERS, key="order_select", help="ABAB (heutige Regel) oder ABBA (die Paare wechseln, wer zuerst schießt).")
    st.caption(ORDER_HELP[order])
    r = st.slider("Schüsse je Mannschaft (Regelzeit)", *bounds("r_slider"), key="r_slider", help="Danach folgt bei Gleichstand der Sudden Death.")
    st.markdown("**🧺 Wahlreihenfolge** (gilt für den zweiten Reiter)")
    k = st.slider("Personen k", *bounds("k_slider"), key="k_slider", help="Wie viele Personen abwechselnd wählen.")
    m = st.slider("Güter m", *bounds("m_slider"), key="m_slider", help="Wie viele unteilbare Güter verteilt werden; jedes Gut wählt genau eine Person.")
    w = st.slider("Geschmacksähnlichkeit w", *bounds("w_slider"), key="w_slider", step=0.1, format="%.1f",
                  help="0: jede Person bewertet jedes Gut unabhängig. 1: alle bewerten gleich. Dazwischen: Wert = w · gemeinsamer Wert + (1 − w) · eigener Wert.")
    rule = st.selectbox("Wahlfolge im Beispiel", C.RULES, key="rule_select", help="Wer in welchem Schritt wählt (Beispiel oben im Reiter; die Messreihen vergleichen immer alle drei).")
    st.caption(RULE_TEXT[rule])
    st.markdown("**🎲 Zufall**")
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1, help="Bestimmt das gezeigte Elfmeterschießen und die gezeigten Bewertungen; die Messreihen haben feste Zufalls-Seeds.")
    st.button("🎲 Neues Beispiel würfeln", width="stretch", on_click=randomize_seed)

sync_query_params({"p_slider": float(p), "d_slider": float(d), "order_select": order, "r_slider": int(r), "k_slider": int(k), "m_slider": int(m),
                   "w_slider": float(w), "rule_select": rule, "seed_input": int(seed)})

settings = E.Settings(p=float(p), d=float(d), order=order, r=int(r), k=int(k), m=int(m), w=float(w), rule=rule, seed=int(seed))

tab_shoot, tab_choice = st.tabs(["🥅 Elfmeterschießen", "🧺 Wahlreihenfolge"])

# =================================================================================================================================================
# Reiter 1: Elfmeterschießen
# =================================================================================================================================================
with tab_shoot:
    a = _shootout(settings)
    ex = a.exact

    st.markdown("## 🎯 Ergebnis")
    st.caption("Zwei gleich starke Mannschaften, exakte Wahrscheinlichkeiten aus der Rekursion über alle Spielstände.")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Erste Mannschaft (A) gewinnt", pct(ex.win_a), delta=f"{100.0 * (ex.win_a - 0.5):+.1f} Prozentpunkte gegen 50 %", delta_color="off")
    m2.metric("Zweite Mannschaft (B) gewinnt", pct(ex.win_b), delta=f"{100.0 * (ex.win_b - 0.5):+.1f} Prozentpunkte gegen 50 %", delta_color="off")
    m3.metric("Sudden Death nötig", pct(ex.p_tie), delta="Gleichstand nach der Regelzeit", delta_color="off")
    m4.metric("Erwartete Schüsse", f"{ex.shots_total:.1f}", delta=f"ohne Abbruch {ex.shots_without_stop:.1f}", delta_color="off")

    st.markdown("### Ein Elfmeterschießen Schuss für Schuss")
    st.caption(f"Gespielt mit dem Zufalls-Seed {seed}, Reihenfolge {order}. Ein einzelnes Schießen sagt nichts über die Wahrscheinlichkeiten; es zeigt, wie ein Durchgang abläuft.")
    st.plotly_chart(build_progress(a.shots), width="stretch", key="progress_chart")
    st.dataframe(
        E.shot_rows(a.shots), hide_index=True, width="stretch",
        column_config={"Trefferchance (%)": st.column_config.NumberColumn(format="%.0f %%")},
    )
    last = a.shots[-1]
    winner = "A (die erste Mannschaft)" if last.score_a > last.score_b else "B (die zweite Mannschaft)"
    st.caption(f"Ausgang: Mannschaft {winner} gewinnt {last.score_a} : {last.score_b} nach {len(a.shots)} Schüssen.")

    st.markdown("### Beide Reihenfolgen nebeneinander")
    rows = []
    for label, e in (("ABAB", a.exact_abab), ("ABBA", a.exact_abba)):
        rows.append({
            "Reihenfolge": label,
            "A gewinnt (%)": 100.0 * e.win_a,
            "davon in der Regelzeit (%)": 100.0 * e.win_a_reg,
            "B gewinnt in der Regelzeit (%)": 100.0 * e.win_b_reg,
            "Sudden Death (%)": 100.0 * e.p_tie,
            "A gewinnt den Sudden Death (%)": 100.0 * e.win_a_sd,
            "Schüsse im Rückstand, A": e.trailing_a,
            "Schüsse im Rückstand, B": e.trailing_b,
        })
    st.dataframe(
        rows, hide_index=True, width="stretch",
        column_config={
            **{c: st.column_config.NumberColumn(format="%.1f %%") for c in ("A gewinnt (%)", "davon in der Regelzeit (%)", "B gewinnt in der Regelzeit (%)", "Sudden Death (%)", "A gewinnt den Sudden Death (%)")},
            "Schüsse im Rückstand, A": st.column_config.NumberColumn(format="%.2f"),
            "Schüsse im Rückstand, B": st.column_config.NumberColumn(format="%.2f"),
        },
    )
    st.caption("„Schüsse im Rückstand“: erwartete Zahl der Schüsse einer Mannschaft, die fallen, während sie zurückliegt (Regelzeit und Sudden Death), bei den gewählten Reglerwerten. Das ist die Stelle, an der der Abschlag d wirkt: wer öfter im Rückstand schießt, verliert öfter Wahrscheinlichkeit.")

    st.markdown("## ❓ Kernfrage: Hat die erste Mannschaft einen Vorteil, und was ändert ABBA?")
    kind, text = E.verdict_shootout(settings.d, order, ex.win_a, a.exact_abab.win_a, a.exact_abba.win_a)
    getattr(st, kind)(text)

    st.markdown("---")

    st.subheader("🔬 Experiment 1: Ohne Abhängigkeit zählt die Reihenfolge nicht")
    st.caption(f"d = 0, {settings.r} Schüsse je Mannschaft, exakt. Die letzte Zeile: Mannschaft A mit p = 0,8, Mannschaft B mit p = 0,6, ebenfalls ohne Abhängigkeit.")
    rows_ind = _table_independent(settings.r)
    st.dataframe(
        [{"Fall": x["label"], "A gewinnt bei ABAB (%)": 100.0 * x["abab"], "A gewinnt bei ABBA (%)": 100.0 * x["abba"]} for x in rows_ind],
        hide_index=True, width="stretch",
        column_config={"A gewinnt bei ABAB (%)": st.column_config.NumberColumn(format="%.2f %%"), "A gewinnt bei ABBA (%)": st.column_config.NumberColumn(format="%.2f %%")},
    )
    equal_rows = rows_ind[:-1]
    if all(abs(x["abab"] - 0.5) < 1e-9 and abs(x["abba"] - 0.5) < 1e-9 for x in equal_rows):
        st.success(f"Bei gleich starken Mannschaften und d = 0 gewinnt A in allen {len(equal_rows)} gerechneten Zeilen genau zu 50 % (Abweichung unter 1e-9), in beiden Reihenfolgen. "
                   f"Bei ungleich starken Mannschaften sind beide Reihenfolgen gleich ({100 * rows_ind[-1]['abab']:.2f} % und {100 * rows_ind[-1]['abba']:.2f} %): ohne Abhängigkeit bringt die Reihenfolge keinen Vorteil, nur die Stärke zählt.")
    else:
        st.warning("Die Tabelle zeigt Abweichungen von 50 %: das widerspricht der Annahme unabhängiger Schüsse und gehört gemeldet.")
    st.markdown("**Der vorzeitige Abbruch ändert den Sieger nie, nur die Länge.** Wer nach einem Abbruch vorn liegt, bleibt auch nach allen restlichen Schüssen vorn; deshalb ist die Gewinnwahrscheinlichkeit mit und ohne Abbruch dieselbe.")
    st.plotly_chart(build_stop_probs(ex.stop_probs), width="stretch", key="stop_chart")
    st.caption(f"Reihenfolge {order}, d = {settings.d:.2f}: Die Regelzeit endet mit Wahrscheinlichkeit {pct(ex.p_early_stop)} vor dem letzten Schuss; die erwartete Zahl der Schüsse in der Regelzeit ist {ex.shots_reg:.2f}" + f" statt {2 * settings.r}.")

    st.subheader("🔬 Experiment 2: Abhängigkeit erzeugt den Vorteil, ABBA dämpft ihn")
    st.caption(f"Gewinnwahrscheinlichkeit der ersten Mannschaft über den Abschlag d von 0 bis 0,25 bei p = {settings.p:.2f} und {settings.r} Schüssen je Mannschaft, exakt.")
    rows_d = _sweep_d(settings.p, settings.r)
    st.plotly_chart(build_sweep_d(rows_d, settings.d), width="stretch", key="sweep_d_chart")
    kind, text = E.verdict_sweep_d(rows_d)
    getattr(st, kind)(text)

    st.subheader("🔬 Experiment 3: Wie viele Schüsse je Mannschaft?")
    st.caption(f"Gewinnwahrscheinlichkeit der ersten Mannschaft über die Zahl der Schüsse je Mannschaft bei p = {settings.p:.2f} und d = {settings.d:.2f}, exakt.")
    rows_r = _sweep_r(settings.p, settings.d)
    st.plotly_chart(build_sweep_r(rows_r, settings.r), width="stretch", key="sweep_r_chart")
    kind, text = E.verdict_sweep_r(rows_r)
    getattr(st, kind)(text)

    st.subheader("🔬 Experiment 4: Probe durch Nachspielen")
    st.caption(f"{de_int(C.MC_N)} Elfmeterschießen mit dem Zufallsgenerator der Demo (fester Zufalls-Seed {C.MC_SEED}), Reihenfolge {order}, gegen die exakte Wahrscheinlichkeit.")
    with st.spinner(f"Spiele {de_int(C.MC_N)} Elfmeterschießen nach (dauert etwa eine Sekunde) …"):
        res = _probe(order, settings.r, settings.p, settings.d)
    kind, text = E.verdict_probe(res)
    getattr(st, kind)(text)
    st.caption(f"Mittlere Schusszahl im Nachspielen {res['mean_shots']:.2f}, exakt {res['exact_shots']:.2f}.")

# =================================================================================================================================================
# Reiter 2: Wahlreihenfolge
# =================================================================================================================================================
with tab_choice:
    ce = _choice_example(settings)
    st.markdown("## 🎯 Ergebnis")
    st.caption(
        "Abgrenzung: `unteilbare-gueter-demo` vergleicht fünf Verteilungsregeln auf denselben Bewertungen (dort ist „Reihum“ eine davon) nach Neidfreiheit, EF1, EFX und Pareto-Optimalität. "
        "Hier geht es nur um die **Reihenfolge des Wählens**: wie viel hängt daran, wer zuerst wählt?"
    )
    st.markdown("### Drei Wahlfolgen")
    st.dataframe(
        [{"Regel": name, "So wählt man": RULE_TEXT[name], f"Folge bei k = {settings.k}, m = {settings.m}": letters(H.pick_sequence(name, settings.k, settings.m)),
          "Wahlen je Person": " / ".join(str(c) for c in E.picks_per_person(name, settings.k, settings.m))} for name in C.RULES],
        hide_index=True, width="stretch",
    )
    st.caption("Jede Person nimmt im eigenen Schritt das ihr wertvollste noch freie Gut (Gleichstand: das mit der kleineren Nummer). Bewertungen sind additiv; der Wert einer Person ist die Summe ihrer Güter.")

    st.markdown("### Ein Beispiel Schritt für Schritt")
    st.caption(f"Bewertungen mit dem Zufalls-Seed {seed}, Geschmacksähnlichkeit w = {settings.w:.1f}, Wahlfolge {rule}. Ein einzelnes Beispiel ist kein Befund.")
    st.dataframe(
        [{"Person": f"Person {i + 1}", **{f"Gut {g + 1}": round(float(ce.values[i, g]), 2) for g in range(settings.m)}} for i in range(settings.k)],
        hide_index=True, width="stretch",
    )
    st.dataframe(
        [{"Schritt": t + 1, "Wählt": f"Person {person + 1}", "Nimmt": f"Gut {g + 1}", "Wert": round(float(ce.values[person, g]), 2)} for t, (person, g) in enumerate(ce.steps)],
        hide_index=True, width="stretch",
    )
    st.plotly_chart(build_totals(ce.totals, settings.k), width="stretch", key="totals_chart")
    st.caption("Gesamtwert je Person in diesem Beispiel bei jeder der drei Wahlfolgen (dieselben Bewertungen).")

    with st.spinner("Rechne die Messreihe über 5 feste Zufalls-Seeds mit je 400 Bewertungsmatrizen (beim ersten Aufruf einige Sekunden) …"):
        table = _choice_table(settings.k, settings.m, settings.w)
    st.markdown("## ❓ Kernfrage: Wie viel Vorteil hat, wer zuerst wählt, und was ändert die Wahlfolge?")
    kind, text = E.verdict_choice(table, settings.k, settings.m)
    getattr(st, kind)(text)

    st.markdown("---")
    st.subheader("🔬 Experiment 1: Die drei Wahlfolgen im Vergleich")
    st.caption(f"k = {settings.k} Personen, m = {settings.m} Güter, w = {settings.w:.1f}; Mittel über {de_int(table[0]['n'])} Bewertungsmatrizen (5 feste Zufalls-Seeds zu je {C.INSTANCES_PER_SEED}).")
    st.dataframe(
        [{"Regel": t["rule"], "Wahlen je Person": " / ".join(str(c) for c in t["picks"]), "Gesamtwert der ersten Person": t["first"], "Gesamtwert der letzten Person": t["last"],
          "Erste minus letzte": t["advantage"], "Standardfehler": t["se"], "Je Zufalls-Seed (kleinster)": min(t["by_seed"]), "Je Zufalls-Seed (größter)": max(t["by_seed"])} for t in table],
        hide_index=True, width="stretch",
        column_config={c: st.column_config.NumberColumn(format="%.3f") for c in ("Gesamtwert der ersten Person", "Gesamtwert der letzten Person", "Erste minus letzte", "Standardfehler", "Je Zufalls-Seed (kleinster)", "Je Zufalls-Seed (größter)")},
    )
    st.caption("Positiv heißt: Die erste Person erreicht im Mittel mehr als die letzte. Der Standardfehler gilt für das Mittel über alle Bewertungsmatrizen; die Spalten je Zufalls-Seed zeigen die Streuung zwischen den fünf Messreihen.")

    st.subheader("🔬 Experiment 2: Wie hängt der Vorteil vom Geschmack ab?")
    st.caption(f"Vorteil (erste minus letzte Person) über die Geschmacksähnlichkeit w bei k = {settings.k}, m = {settings.m}; Balken: ±2 Standardfehler.")
    rows_w = _sweep_w(settings.k, settings.m)
    st.plotly_chart(build_choice_sweep(rows_w, "w", "Geschmacksähnlichkeit w"), width="stretch", key="sweep_w_chart")
    kind, text = E.verdict_sweep_w(rows_w)
    getattr(st, kind)(text)

    st.subheader("🔬 Experiment 3: Wie viele Güter?")
    ms = E.m_sweep(settings.k)
    st.caption(f"Vorteil über die Zahl der Güter ({', '.join(str(x) for x in ms)}; nur Vielfache von k = {settings.k}, damit jede Person gleich oft wählt) bei w = {settings.w:.1f}; Balken: ±2 Standardfehler.")
    with st.spinner("Rechne die Messreihe über die Zahl der Güter (beim ersten Aufruf einige Sekunden) …"):
        rows_m = _sweep_m(settings.k, settings.w)
    st.plotly_chart(build_choice_sweep(rows_m, "m", "Zahl der Güter m"), width="stretch", key="sweep_m_chart")
    kind, text = E.verdict_sweep_m(rows_m)
    getattr(st, kind)(text)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Der Schuss hängt nur davon ab, ob die eigene Mannschaft zurückliegt** (p oder p − d) | Andere Abhängigkeiten (Müdigkeit, Hot Hand, Spielstand nahe der Entscheidung) liefern andere Vorteile; ob es den Abschlag im echten Elfmeterschießen gibt, ist hier nicht gemessen | Hot-Hand-Messfehler |
| **Beide Mannschaften gleich stark** | Ohne Abhängigkeit sind beide Reihenfolgen auch bei ungleicher Stärke gleich (Experiment 1); die Gewinnchance selbst folgt der Stärke | – |
| **Ein einzelnes Elfmeterschießen ohne Vorgeschichte** | Läuft ein Zustand („Form“) über mehrere Spiele mit, kann der Spielplan selbst verzerren | Spielplanreihenfolge |
| **Reihenfolge der Spiele wirkt über den Zustand, nicht über den Ort** | Hin- und Rückspiel tauschen den Ort, nicht die Reihenfolge der Schüsse | Hin- und Rückspiel |
| **Wählende bewerten ehrlich, additiv und zufällig (Geschmack w)** | Strategisches Bewerten und nicht additive Bewertungen sind nicht modelliert | `unteilbare-gueter-demo` (Neid, EF1, EFX) |
| **Die Reihenfolge wirkt auf das Spiel, nicht auf die Bewertung** | Wirkt sie auf die Bewertung einer Darbietung (Noten, Anker), ist das ein anderes Modell | Auftrittsreihenfolge |
| **Mehrere Verzerrungen gleichzeitig** | Die Demo betrachtet eine Verzerrung je Experiment; wie groß sie neben dem Zufall in einer Tabelle ist, bleibt offen | Rauschen oder Verzerrung? |
"""
)

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(
        """
**Annahmen.** Elfmeterschießen: zwei gleich stark simulierte Mannschaften, Trefferwahrscheinlichkeit *p*, im Rückstand *p − d*, ein Rückstand zählt nur im Spielstand vor dem Schuss. Wahlreihenfolge: additive Bewertungen, Geschmack
*v = w · c + (1 − w) · e* mit gleichverteilten Zufallszahlen, jede Person nimmt das ihr wertvollste freie Gut. Alles mit synthetischen Daten und festen Zufalls-Seeds, keine Felddaten.

**Grenzen.** Die Gewinnwahrscheinlichkeiten des Elfmeterschießens sind **exakt**, aber für dieses Modell; sie sagen nichts darüber, wie stark die Abhängigkeit im echten Spiel ist. Die Messreihen der Wahlreihenfolge sind
**Stichproben** (2.000 Bewertungsmatrizen je Zelle); Unterschiede unterhalb von etwa zwei Standardfehlern sind kein Befund. Der Abschlag *d* ist ein Regler, keine geschätzte Größe.
Zur Wirklichkeit (nur aus Suchergebnissen, nicht im Volltext gelesen): Die IFAB hat ABBA im Elfmeterschießen 2018 verworfen, die Evidenz zu einem Startvorteil ist uneinheitlich und in Daten umstritten.
Eine „Catch-Up“-Wahlfolge ist nicht umgesetzt.

**Bekannte Probleme.** Nur mit dem Streamlit-Testrahmen (AppTest) geprüft, nicht mit echten Mausklicks in verschiedenen Browsern. Die Messreihen der Wahlreihenfolge brauchen beim ersten Aufruf einige Sekunden.
        """
    )

with st.expander("📐 Mathematische Formulierung"):
    # erklaerseite:lesehilfe:start (erzeugt von tools/set_demo_explainer.py (Website-Repo) aus tools/content/explainers/elfmeter-reihenfolge-erklaert.json, nicht von Hand ändern)
    st.markdown(
        r"""
**Lesehilfe.** Gegeben sind zwei gleich starke Mannschaften mit der Trefferwahrscheinlichkeit $p$, die im Rückstand auf $p - d$ sinkt, und eine Reihenfolge der Schüsse. Gesucht ist die Wahrscheinlichkeit, dass die Mannschaft A gewinnt, die zuerst schießt. Im zweiten Reiter sind $k$ Personen, $m$ Güter und die Bewertungen $v_{ig}$ gegeben; gesucht ist der Vorteil der ersten gegenüber der letzten Person.

| Symbol | Bedeutung |
|---|---|
| $R$ | Zahl der Schüsse je Mannschaft in der Regelzeit |
| $p$ | Trefferwahrscheinlichkeit, solange die schießende Mannschaft nicht zurückliegt |
| $d$ | Abschlag im Rückstand (Regler, keine Schätzung); $d = 0$ heißt unabhängige Schüsse |
| $q$ | Trefferwahrscheinlichkeit des nächsten Schusses |
| $s_A$, $s_B$ | Tore von A bzw. B |
| $s_{\text{eigen}}$, $s_{\text{fremd}}$ | Tore der schießenden bzw. der anderen Mannschaft vor dem Schuss |
| $\ell_A$, $\ell_B$ | restliche Schüsse von A bzw. B in der Regelzeit |
| $P_A^{\text{reg}}$, $P_B^{\text{reg}}$, $P_{\text{tie}}$ | Wahrscheinlichkeit, dass A bzw. B in der Regelzeit gewinnt, bzw. dass es danach unentschieden steht |
| $x$, $y$ | Wahrscheinlichkeit, dass im Sudden Death der Erste bzw. der Zweite eines Paares das Paar gewinnt |
| $c$ (ohne Index) | Wahrscheinlichkeit, dass ein Paar im Sudden Death nicht trennt und ein weiteres folgt |
| $P_A^{\text{SD}}$, $P_1$, $P_2$ | Wahrscheinlichkeit, dass A den Sudden Death gewinnt: bei ABAB bzw. bei ABBA mit A (bzw. B) als Erstem im nächsten Paar |
| $P_A$ | Wahrscheinlichkeit, dass A insgesamt gewinnt |
| $k$, $m$ | Zahl der Personen bzw. der Güter |
| $\pi(t)$ | Person, die im Schritt $t$ wählt |
| $v_{ig}$ | Wert des Guts $g$ für Person $i$ (zwischen 0 und 1) |
| $w$ | Gewicht des gemeinsamen Geschmacks; $w = 0$ heißt unabhängiger Geschmack, $w = 1$ gleiche Bewertung aller |
| $c_g$ (mit Index) | gemeinsamer Wert von Gut $g$, für alle Personen gleich (nicht zu verwechseln mit $c$ oben) |
| $e_{ig}$ | persönlicher Wert von Person $i$ für Gut $g$ |
| $\Delta$, $V_i$ | Vorteil der ersten gegenüber der letzten Person, gemessen in den Werten der Güter; Gesamtwert der Güter von Person $i$ |

[Schritt für Schritt erklärt, mit Herleitung und Literatur](https://sebastianhanisch.net/elfmeter-reihenfolge-erklaert.html#fachleute)
        """
    )
    # erklaerseite:lesehilfe:end
    st.markdown(
        r"""
**Elfmeterschießen.** Mannschaften A (zuerst) und B schießen je $R$ Mal. Vor jedem Schuss gilt für die schießende Mannschaft mit Toren $s_{\text{eigen}}$ gegen $s_{\text{fremd}}$ die Trefferwahrscheinlichkeit:
        """
    )
    st.markdown(r"$$q = \begin{cases} p - d & \text{falls } s_{\text{eigen}} < s_{\text{fremd}} \\ p & \text{sonst} \end{cases}$$")
    st.markdown(r"Abbruch nach einem Schuss, wenn mit den restlichen Schüssen $\ell_A$ und $\ell_B$ gilt:")
    st.markdown(r"$$s_A > s_B + \ell_B \quad\text{oder}\quad s_B > s_A + \ell_A$$")
    st.markdown(r"Die Rekursion über die Spielstände $(s_A, s_B)$ gibt die Wahrscheinlichkeiten $P_A^{\text{reg}}$, $P_B^{\text{reg}}$ und den Gleichstand $P_{\text{tie}}$. Im Sudden Death schießt der Erste eines Paares mit $p$, der Zweite mit $p - d$, wenn der Erste getroffen hat, sonst mit $p$. Der Erste gewinnt das Paar mit:")
    st.markdown(r"$$x = p\,(1 - p + d)$$")
    st.markdown(r"der Zweite mit:")
    st.markdown(r"$$y = (1 - p)\,p$$")
    st.markdown(r"und mit Wahrscheinlichkeit $c = 1 - x - y$ folgt ein weiteres Paar. Bei ABAB (A immer zuerst) gilt für den Sudden Death:")
    st.markdown(r"$$P_A^{\text{SD}} = \frac{x}{x + y} = \frac{1 - p + d}{2(1 - p) + d}$$")
    st.markdown(r"Bei ABBA beginnt A in Paaren mit ungerader Nummer, B in Paaren mit gerader. Beginnt das nächste Paar mit A, gilt mit $P_1$ für diesen Fall und $P_2$ für den Beginn mit B:")
    st.markdown(r"$$P_1 = \frac{x + c\,y}{1 - c^2}, \qquad P_2 = \frac{y + c\,x}{1 - c^2}$$")
    st.markdown(r"Insgesamt gewinnt A mit $P_A = P_A^{\text{reg}} + P_{\text{tie}}\,P_A^{\text{SD}}$. Gemessen (nicht bewiesen): bei ABAB, gleich starken Mannschaften ist $P_A$ in den geprüften Fällen unabhängig von $R$ und gleich $P_A^{\text{SD}}$.")
    st.markdown(
        r"""
**Wahlreihenfolge.** $k$ Personen, $m$ Güter, Bewertung $v_{ig}$. Wahlfolge $\pi(t)$ (wer im Schritt $t = 0, \dots, m-1$ wählt): Reihum $t \bmod k$; Schlange: vorwärts, rückwärts, vorwärts, …; Thue-Morse: die Stellensumme von $t$ zur Basis $k$ modulo $k$. Geschmack:
        """
    )
    st.markdown(r"$$v_{ig} = w\,c_g + (1 - w)\,e_{ig}, \qquad c_g, e_{ig} \sim \mathrm{U}[0, 1)$$")
    st.markdown(r"Gemessen wird der Vorteil der ersten gegenüber der letzten Person, gemittelt über die Bewertungsmatrizen:")
    st.markdown(r"$$\Delta = \mathbb{E}\big[V_1 - V_k\big], \qquad V_i = \sum_{g \text{ von } i \text{ gewählt}} v_{ig}$$")
    st.markdown(
        r"""
**Literatur (nur Hinweise, nicht im Volltext gelesen).** Apesteguia und Palacios-Huerta (2010, American Economic Review) zum Startvorteil im Elfmeterschießen (aus dem Gedächtnis, ungeprüft); Prouhet (1851) und Thue (1912) zur Thue-Morse-Folge (aus dem Gedächtnis, ungeprüft);
IFAB-Entscheidung zu ABBA 2018 (aus Suchergebnissen, nicht gelesen).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Wettbewerbsverzerrung: Reihenfolge und Anreize](https://sebastianhanisch.net/konzepte-wettbewerbsverzerrung.html)."
)
