"""Web Technology Trends: technology adoption, Core Web Vitals and structured data across ~14.5M websites (HTTP Archive)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from common import ui
from common.data import load_bundle

ui.setup("Web Technology Trends 2025–2026: CMS, frameworks, Core Web Vitals across 14.5M sites | Fliar BI",
         "Web Technology Trends",
         "Which technologies websites run, how adoption changed from May 2025 to May 2026, Core Web Vitals pass rates "
         "by platform and structured-data use. Aggregates built by Fliar BI from HTTP Archive crawl data.", "🌐")

T = "webtech"
top = load_bundle(T, "technologies_top300")
byrank = load_bundle(T, "technology_by_rank")
bytld = load_bundle(T, "technology_by_tld")
cwv = load_bundle(T, "cwv_by_platform")
ov = load_bundle(T, "overview_by_rank")
sd = load_bundle(T, "structured_data_types")
tlds = load_bundle(T, "tlds")
stack = load_bundle(T, "stack_size")
C_NEW, C_OLD = sorted(ov["crawl"].unique())[-1], sorted(ov["crawl"].unique())[0]
Y_NEW, Y_OLD = C_NEW[:7], C_OLD[:7]

st.sidebar.header("Filters")
cats = st.sidebar.multiselect("Technology category", ui.top_values(top["category"], 100), help="Leave empty for all")
q = st.sidebar.text_input("Technology name contains").strip().lower()
min_share = st.sidebar.slider("Minimum share of sites (%)", 0.0, 10.0, 0.0, 0.5)
f = top.copy()
if cats:
    f = f[f["category"].isin(cats)]
if q:
    f = f[f["technology"].str.lower().str.contains(q, regex=False)]
f = f[f["share"] * 100 >= min_share]

o_new = ov[ov["crawl"] == C_NEW]
o_old = ov[ov["crawl"] == C_OLD]
pass_new = o_new["cwv_good"].sum() / o_new["cwv_pages"].sum()
pass_old = o_old["cwv_good"].sum() / o_old["cwv_pages"].sum()
sn = stack[stack["crawl"] == C_NEW].sort_values("n_tech")
med = sn.loc[sn["pages"].cumsum() >= sn["pages"].sum() / 2, "n_tech"].iloc[0]
ui.kpis([(f"Sites crawled ({Y_NEW})", ui.num(o_new["pages"].sum())),
         (f"Core Web Vitals pass ({Y_NEW})", f"{pass_new:.1%}"),
         ("Change vs a year earlier", f"{(pass_new - pass_old) * 100:+.1f} pp"),
         ("Median technologies per site", ui.num(med))])
st.caption("Shares and rates are unbiased; absolute site counts cover about 93% of each crawl (see About the data).")

t1, t2, t3, t4 = st.tabs(["Technologies", "Core Web Vitals", "Structured data", "Domains (TLD)"])
with t1:
    if f.empty:
        st.warning("No technologies match these filters.")
    else:
        s = f.set_index("technology")["share"].nlargest(25) * 100
        ui.bar_series(s.round(2), f"Most used technologies, share of sites in {Y_NEW} (%)", fmt=".2f")
        c1, c2 = st.columns(2)
        g = f[f["share"] >= 0.02]
        with c1:
            ui.bar_series(g.set_index("technology")["change_pp"].nlargest(15).round(2),
                          f"Largest gains {Y_OLD} → {Y_NEW} (pp, on 2%+ of sites)", fmt=".2f")
        with c2:
            ui.bar_series(g.set_index("technology")["change_pp"].nsmallest(15).round(2)[::-1],
                          f"Largest losses {Y_OLD} → {Y_NEW} (pp, on 2%+ of sites)", fmt=".2f")
        st.subheader("Technology detail")
        pick = st.selectbox("Technology", f.sort_values("share", ascending=False)["technology"].tolist())
        r = byrank[byrank["technology"] == pick]
        fig = go.Figure()
        for i, cr in enumerate([C_OLD, C_NEW]):
            x = r[r["crawl"] == cr].sort_values("rank_bucket")
            fig.add_bar(x=x["rank_bucket"], y=x["share_in_bucket"] * 100, name=cr[:7], marker_color=ui.SERIES[i],
                        marker_line_width=2, marker_line_color="rgba(0,0,0,0)",
                        hovertemplate=f"{cr[:7]} · %{{x}}: %{{y:.2f}}%<extra></extra>")
        fig.update_layout(barmode="group", title=f"{pick}: share of sites by popularity bucket (%)")
        c3, c4 = st.columns(2)
        with c3:
            ui.show(fig)
        with c4:
            tt = bytld[(bytld["technology"] == pick) & (bytld["tld_pages"] >= 50000)]
            ui.bar_series((tt.set_index("tld")["share_in_tld"].nlargest(15) * 100).round(2),
                          f"{pick}: share of sites by TLD (TLDs with 50k+ sites, %)", fmt=".2f")
    ui.table(f.sort_values("share", ascending=False),
             ["rank", "technology", "category", "share", "share_2025", "change_pp", "share_top1m", "share_company_sites",
              "cwv_pass_rate", "lcp_good_rate", "cls_good_rate", "inp_good_rate", "pages"], "web_technologies_top300")
with t2:
    c = cwv[(cwv["crawl"] == C_NEW) & (cwv["cwv_pages"] >= 50000)]
    if cats:
        c = c[c["category"].isin(cats)]
    ui.bar_series((c.set_index("technology")["cwv_pass_rate"].sort_values(ascending=False).head(25) * 100).round(1),
                  f"Core Web Vitals pass rate by platform, {Y_NEW} (platforms with 50k+ field-data sites, %)", fmt=".1f")
    fig = go.Figure()
    for i, cr in enumerate([C_OLD, C_NEW]):
        x = ov[ov["crawl"] == cr].sort_values("rank_bucket")
        fig.add_bar(x=x["rank_bucket"], y=x["cwv_pass_rate"] * 100, name=cr[:7], marker_color=ui.SERIES[i],
                    marker_line_width=2, marker_line_color="rgba(0,0,0,0)",
                    hovertemplate=f"{cr[:7]} · %{{x}}: %{{y:.1f}}%<extra></extra>")
    fig.update_layout(barmode="group", title="Core Web Vitals pass rate by site popularity (%)")
    ui.show(fig)
    st.dataframe(c.sort_values("cwv_pages", ascending=False), use_container_width=True, hide_index=True)
with t3:
    s = sd.set_index("sd_type")["share"].nlargest(25) * 100
    ui.bar_series(s.round(2), f"Most declared schema.org types, share of sites {Y_NEW} (%)", fmt=".2f")
    ui.bar_series(sd[sd["share"] >= 0.01].set_index("sd_type")["change_pp"].nlargest(15).round(2),
                  f"Fastest-growing structured-data types {Y_OLD} → {Y_NEW} (pp, on 1%+ of sites)", fmt=".2f")
with t4:
    d = tlds[(tlds["crawl"] == C_NEW) & (tlds["tld"] != "other")]
    c1, c2 = st.columns(2)
    with c1:
        ui.bar_series((d.set_index("tld")["share"].nlargest(20) * 100).round(2), f"Largest TLDs, share of sites {Y_NEW} (%)",
                      fmt=".2f")
    with c2:
        dd = d[d["cwv_pages"] >= 20000]
        ui.bar_series((dd.set_index("tld")["cwv_pass_rate"].sort_values(ascending=False).head(20) * 100).round(1),
                      "Highest Core Web Vitals pass rate by TLD (20k+ field-data sites, %)", fmt=".1f")
    st.dataframe(d.sort_values("pages", ascending=False), use_container_width=True, hide_index=True)
ui.about_bundle(T, {"Aggregates on Hugging Face": "https://huggingface.co/datasets/fliarbi/web-technology-trends-aggregates"},
                related=["website-technology-stack"])
ui.footer()
