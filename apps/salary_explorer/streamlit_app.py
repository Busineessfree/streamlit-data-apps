"""Salary Explorer: posted salary benchmarks for India, the US and 100k global postings."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import plotly.express as px
import streamlit as st

from common import ui
from common.data import load, meta

ui.setup("Salary Explorer 2026: India, US & global salary benchmarks by role and city | Fliar BI",
         "Salary Explorer",
         "Posted salary ranges by role family, seniority, city and industry for India (INR), the United States (USD) "
         "and 100,000 global postings (USD). Free samples of the Fliar BI salary datasets.", "💼")

CFG = {
    "India salaries (INR)": dict(key="india-salary-benchmarks-2026", pay="salary_mid_inr", cur="₹", loc="city",
                                  cols=("posted_month", "company", "job_title", "role_family", "seniority",
                                        "experience_band", "city", "industry_category", "salary_min_inr",
                                        "salary_max_inr", "salary_mid_inr", "fliar_profile_url")),
    "US salaries (USD)": dict(key="us-salary-benchmarks-2026", pay="salary_mid_usd", cur="$", loc="state",
                              cols=("posted_month", "company", "job_title", "role_family", "seniority",
                                    "experience_band", "city", "state", "metro", "industry_category", "remote",
                                    "pay_period", "salary_min_usd", "salary_max_usd", "salary_mid_usd",
                                    "fliar_profile_url")),
    "Global salaries by skill (USD)": dict(key="skill-salary-percentiles-global", pay="salary_mid_usd", cur="$",
                                           loc="country_name",
                                           cols=("posted_month", "country_name", "region_group", "company", "job_title",
                                                 "role_family", "seniority", "industry_category", "skills", "currency",
                                                 "salary_mid_local", "salary_min_usd", "salary_max_usd",
                                                 "salary_mid_usd", "fliar_profile_url")),
}
label = st.sidebar.radio("Dataset", list(CFG))
c = CFG[label]
key, pay, cur, loc = c["key"], c["pay"], c["cur"], c["loc"]
m = meta(key)
df = load(key, c["cols"])
st.sidebar.caption(f"{m['sample_rows']:,} of {m['full_rows']:,} {m['unit']} in this free sample.")

st.sidebar.header("Filters")
f = ui.apply_multi(df, "role_family", ui.multi("Role family", df["role_family"]))
f = ui.apply_multi(f, "seniority", ui.multi("Seniority", f["seniority"]))
f = ui.apply_multi(f, loc, ui.multi(loc.replace("_name", "").replace("_", " ").title(), f[loc]))
f = ui.apply_multi(f, "industry_category", ui.multi("Industry", f["industry_category"]))
if "skills" in f:
    sk = st.sidebar.text_input("Skill contains (e.g. python)").strip().lower()
    if sk:
        f = f[f["skills"].astype(str).str.lower().str.contains(sk, regex=False)]
f = ui.search(f, ["job_title", "company"], "Search job title or company")

p = f[pay].dropna()
ui.kpis([("Postings", ui.num(len(f))), ("Median salary (mid)", ui.money(p.median() if len(p) else None, cur)),
         ("25th percentile", ui.money(p.quantile(.25) if len(p) else None, cur)),
         ("75th percentile", ui.money(p.quantile(.75) if len(p) else None, cur))])
st.caption("Salary = midpoint of the posted annual range. Figures describe the filtered free sample.")

if f.empty:
    st.warning("No postings match these filters.")
else:
    c1, c2 = st.columns(2)
    with c1:
        g = f[f["role_family"].astype(str).str.strip() != ""]
        s = g.groupby(g["role_family"].astype(str))[pay].median().dropna()
        cnt = g["role_family"].astype(str).value_counts()
        s = s[cnt.reindex(s.index).fillna(0) >= 20].sort_values(ascending=False).head(15)
        ui.bar_series(s, "Median salary by role family (20+ postings)", money_axis=True, prefix=cur)
    with c2:
        ui.box(f[f["seniority"].astype(str).str.strip() != ""], "seniority", pay, "Salary by seniority", n=8)
    c3, c4 = st.columns(2)
    with c3:
        g = f[f[loc].astype(str).str.strip() != ""]
        top = g[loc].astype(str).value_counts().head(15).index
        s = g[g[loc].astype(str).isin(top)].groupby(g[loc].astype(str))[pay].median().sort_values(ascending=False)
        ui.bar_series(s, f"Median salary in the 15 {loc.replace('_name', '')}s with most postings", money_axis=True,
                      prefix=cur)
    with c4:
        h = f[f[pay].notna()]
        h = h[h[pay] <= h[pay].quantile(0.99)]
        fig = px.histogram(h, x=pay, nbins=40, color_discrete_sequence=[ui.BLUE])
        fig.update_layout(title="Salary distribution (top 1% trimmed)", bargap=0.05, xaxis_title=None,
                          yaxis_title="postings")
        fig.update_xaxes(tickprefix=cur)
        ui.show(fig)
    if "skills" in f:
        g = f[f["skills"].astype(str).str.strip() != ""]
        top = ui.explode_counts(g["skills"], n=40).index
        ex = g[["skills", pay]].assign(skill=g["skills"].astype(str).str.split("|")).explode("skill")
        ex = ex[ex["skill"].isin(top)]
        s = ex.groupby("skill")[pay].median().sort_values(ascending=False).head(20)
        ui.bar_series(s, "Median salary by skill (40 most common skills, top 20 shown)", money_axis=True, prefix=cur)

ui.table(f.sort_values(pay, ascending=False), list(c["cols"]), f"{key}_filtered",
         link_cols={"fliar_profile_url": "Profile"})
ui.about([key])
ui.footer()
