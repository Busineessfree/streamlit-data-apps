"""Jobs Market Monitor: 100,000 job postings from 2026 (US and India) by role, skill, city and salary."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from common import ui
from common.data import load, meta

ui.setup("Jobs Market Monitor 2026: job postings by role, skill, city & salary | Fliar BI",
         "Jobs Market Monitor",
         "Track 2026 job postings in the United States and India: hiring by month, category, seniority, city, "
         "in-demand skills and posted salaries. Free sample of the Fliar BI job postings dataset.", "🧭")

key = "job-postings-2026"
cols = ("posted_date", "title", "company", "role", "seniority", "category", "city", "region", "country", "remote",
        "experience_years", "education", "skills", "salary_annual_usd", "company_domain", "fliar_profile_url")
m = meta(key)
df = load(key, cols)
df["month"] = df["posted_date"].astype(str).str[:7]
st.sidebar.caption(f"{m['sample_rows']:,} of {m['full_rows']:,} {m['unit']} in this free sample.")

st.sidebar.header("Filters")
months = sorted(x for x in df["month"].unique() if x and x != "nan")
a, b = st.sidebar.select_slider("Posted month", months, (months[0], months[-1])) if len(months) > 1 else (months[0], months[0])
f = df[(df["month"] >= a) & (df["month"] <= b)]
f = ui.apply_multi(f, "country", ui.multi("Country", f["country"]))
f = ui.apply_multi(f, "category", ui.multi("Job category", f["category"]))
f = ui.apply_multi(f, "seniority", ui.multi("Seniority", f["seniority"]))
f = ui.apply_multi(f, "remote", ui.multi("Work mode", f["remote"]))
f = ui.apply_multi(f, "region", ui.multi("State / region", f["region"]))
sk = st.sidebar.text_input("Skill contains (e.g. python)").strip().lower()
if sk:
    f = f[f["skills"].astype(str).str.lower().str.contains(sk, regex=False)]
f = ui.search(f, ["title", "company"], "Search job title or employer")

sal = f["salary_annual_usd"].dropna()
ui.kpis([("Postings", ui.num(len(f))), ("Employers", ui.num(f["company"].nunique())),
         ("Postings with salary", f"{len(sal) / max(1, len(f)):.0%}"),
         ("Median posted salary (US$/yr)", ui.money(sal.median() if len(sal) else None))])
st.caption("Monthly counts reflect collection as well as hiring (see Limitations in About the data).")

if f.empty:
    st.warning("No postings match these filters.")
else:
    t = f.groupby(["month", f["country"].astype(str)]).size().unstack(fill_value=0).sort_index()
    fig = go.Figure()
    for i, cc in enumerate(t.sum().sort_values(ascending=False).index[:8]):
        fig.add_bar(x=t.index, y=t[cc], name=cc, marker_color=ui.SERIES[i], marker_line_width=2,
                    marker_line_color="rgba(0,0,0,0)", hovertemplate=f"{cc} %{{x}}: %{{y:,}}<extra></extra>")
    fig.update_layout(barmode="stack", title="Postings by month and country")
    fig.update_xaxes(type="category")
    ui.show(fig)
    c1, c2 = st.columns(2)
    with c1:
        ui.bar_top(f, "category", "Postings by job category")
    with c2:
        ui.bar_series(ui.explode_counts(f["skills"], n=20), "Most requested skills (postings)")
    c3, c4 = st.columns(2)
    with c3:
        ui.bar_top(f, "city", "Top cities")
    with c4:
        ui.box(f[f["seniority"].astype(str).str.strip() != ""], "seniority", "salary_annual_usd",
               "Posted salary by seniority (US$/yr)", n=8)

ui.table(f.sort_values("posted_date", ascending=False), [c for c in cols], f"{key}_filtered",
         link_cols={"fliar_profile_url": "Profile"})
ui.about([key])
ui.footer()
