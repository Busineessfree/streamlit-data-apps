"""Patent Trends: patent publications by year, office, CPC technology class and assignee (aggregates)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from common import ui
from common.data import load_bundle

ui.setup("Patent Trends 2006–2026: patent filings by technology class, country & company | Fliar BI",
         "Patent Trends",
         "Patent publications and grants by year, patent office, CPC technology class and top assignee, 2006 to "
         "April 2026. Aggregates built by Fliar BI from a 108-million-record patent corpus.", "🔬")

T = "patents"


def ints(d):
    for c in d.columns:
        if str(d[c].dtype).startswith("uint"):
            d[c] = d[c].astype("int64")
    return d


yo = ints(load_bundle(T, "by_year_office").copy())
cyo = ints(load_bundle(T, "by_class_year_office").copy())
cls = load_bundle(T, "cpc_classes")
summ = ints(load_bundle(T, "class_summary").copy())
ay = ints(load_bundle(T, "top_assignees_by_year").copy())
acy = ints(load_bundle(T, "top_assignees_by_class_year").copy())
label = (cls["cpc_class"] + " · " + cls["cpc_title_short"]).tolist()
lab_map = dict(zip(cls["cpc_class"], cls["cpc_title_short"]))

st.sidebar.header("Filters")
ymin, ymax = int(yo["year"].min()), int(yo["year"].max())
a, b = st.sidebar.slider("Publication year", ymin, ymax, (ymin, ymax))
st.sidebar.caption(f"{ymax} is partial (publications to April). Counts cover the answering share of the corpus.")
offices = yo.groupby("office_name")["publications"].sum().sort_values(ascending=False)
pick_off = st.sidebar.multiselect("Patent office", offices.index.tolist(), help="Leave empty for all")
code_of = dict(zip(yo["office_name"], yo["country_code"]))
sections = cls.drop_duplicates("section").set_index("section")["section_title"]
pick_sec = st.sidebar.multiselect("CPC section", [f"{k} · {v}" for k, v in sections.items()], help="Leave empty for all")
pick_cls = st.sidebar.multiselect("CPC class", label, help="Leave empty for all")
q = st.sidebar.text_input("Assignee contains (e.g. SAMSUNG)").strip().upper()

classes = None
if pick_cls:
    classes = {x.split(" · ")[0] for x in pick_cls}
elif pick_sec:
    secs = {x.split(" · ")[0] for x in pick_sec}
    classes = set(cls.loc[cls["section"].isin(secs), "cpc_class"])
codes = {code_of[o] for o in pick_off} if pick_off else None

if classes is None:
    f = yo[(yo["year"] >= a) & (yo["year"] <= b)]
    if codes:
        f = f[f["country_code"].isin(codes)]
    f = f.rename(columns={"office_name": "office_label"})
    st.caption("Totals count every publication; class views count publications with a CPC class.")
else:
    f = cyo[(cyo["year"] >= a) & (cyo["year"] <= b) & cyo["cpc_class"].isin(classes)]
    if codes:
        f = f[f["office"].isin(codes)]
    name_of = {v: k for k, v in code_of.items()}
    f = f.assign(office_label=f["office"].map(name_of).fillna(f["office"]))
    st.caption("Class filters count publications per CPC class; a patent with several classes counts in each.")

pubs, gr, cit = f["publications"].sum(), f["granted"].sum(), f["sum_citations"].sum()
ui.kpis([("Publications", ui.num(pubs)), ("Granted", ui.num(gr)),
         ("Grant share", f"{gr / pubs:.0%}" if pubs else "–"),
         ("Citations per publication", f"{cit / pubs:.1f}" if pubs else "–")])

if f.empty:
    st.warning("Nothing matches these filters.")
else:
    c1, c2 = st.columns(2)
    with c1:
        ui.time_bars(f, "year", "Patent publications by year", value="publications", agg="sum")
    with c2:
        ui.bar_top(f, "office_label", "Publications by patent office", value="publications", agg="sum")
    c3, c4 = st.columns(2)
    with c3:
        g = cyo[(cyo["year"] >= a) & (cyo["year"] <= b)]
        if codes:
            g = g[g["office"].isin(codes)]
        if classes is not None:
            g = g[g["cpc_class"].isin(classes)]
        s = g.groupby("cpc_class")["publications"].sum().nlargest(15)
        s.index = [f"{c} · {lab_map.get(c, '')}"[:60] for c in s.index]
        ui.bar_series(s, "Largest technology classes (publications)")
    with c4:
        sm = summ[summ["pub_2020"] >= 2000]
        if classes is not None:
            sm = sm[sm["cpc_class"].isin(classes)]
        s = sm.set_index("cpc_class")["cagr_2020_2025"].nlargest(15) * 100
        s.index = [f"{c} · {lab_map.get(c, '')}"[:60] for c in s.index]
        ui.bar_series(s.round(1), "Fastest-growing classes: CAGR 2020–2025 (%)", fmt=".1f")
    if classes is None:
        ta = ay[(ay["year"] >= a) & (ay["year"] <= b)]
    else:
        ta = acy[(acy["year"] >= a) & (acy["year"] <= b) & acy["cpc_class"].isin(classes)]
    if codes:
        ta = ta[ta["assignee_country"].isin(codes)]
    if q:
        ta = ta[ta["assignee"].str.contains(q, regex=False, na=False)]
    c5, c6 = st.columns(2)
    with c5:
        ui.bar_top(ta, "assignee", "Top assignees (publications)", value="publications", agg="sum")
    with c6:
        top5 = ta.groupby("assignee")["publications"].sum().nlargest(5).index
        tt = ta[ta["assignee"].isin(top5)].groupby(["year", "assignee"])["publications"].sum().unstack(fill_value=0)
        fig = go.Figure()
        for i, n in enumerate(top5):
            fig.add_scatter(x=tt.index, y=tt[n], name=n.title()[:30], mode="lines+markers",
                            line=dict(width=2, color=ui.SERIES[i]), marker=dict(size=8))
        fig.update_layout(title="Top 5 assignees: publications per year", hovermode="x unified")
        ui.show(fig, height=420)

st.subheader("Technology class summary")
st.caption("One row per CPC class over the whole window (all offices).")
show = summ.copy()
if classes is not None:
    show = show[show["cpc_class"].isin(classes)]
ui.table(show.sort_values("publications", ascending=False),
         ["cpc_class", "section_title", "cpc_title_short", "publications", "granted", "grant_share", "avg_citations",
          "pub_2015", "pub_2020", "pub_2025", "cagr_2015_2025", "cagr_2020_2025", "share_2025",
          "share_change_pp_2020_2025", "cn_share_2025"], "patent_class_summary")
ui.about_bundle(T)
ui.footer()
