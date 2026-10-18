"""Startup Funding Explorer: deal-level funding rounds (global, India, AI, US, UK samples)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import streamlit as st

from common import ui
from common.data import load, meta

ui.setup("Startup Funding Explorer 2019–2026: VC rounds by country, sector & stage | Fliar BI",
         "Startup Funding Explorer",
         "Explore deal-level venture funding rounds worldwide, in India, the US, the UK and in AI: stage, amount, "
         "lead investor and sector. Free samples of the Fliar BI funding datasets.", "💸")

DATASETS = {
    "Global startup funding": "global-startup-funding",
    "India startup funding": "india-startup-funding",
    "AI startup funding": "ai-startup-funding",
    "US startup funding": "us-startup-funding-2019-2026",
    "UK startup funding": "uk-startup-funding-2019-2026",
}
COLS = ("announced_date", "year", "company_name", "company_domain", "country", "state", "nation", "city", "sector",
        "stage", "amount_usd", "amount_status", "lead_investor", "investor_count", "news_source", "news_url",
        "fliar_profile_url")

key = ui.dataset_picker(DATASETS)
m = meta(key)
df = load(key, COLS)
st.sidebar.caption(f"{m['sample_rows']:,} of {m['full_rows']:,} {m['unit']} in this free sample.")

st.sidebar.header("Filters")
f = ui.year_range(df, "year")
region_col = "country" if df["country"].astype(str).nunique() > 3 else ("state" if "state" in df else ("nation" if "nation" in df else "city"))
f = ui.apply_multi(f, region_col, ui.multi(region_col.title(), f[region_col]))
f = ui.apply_multi(f, "sector", ui.multi("Sector", f["sector"]))
f = ui.apply_multi(f, "stage", ui.multi("Stage", f["stage"]))
min_m = st.sidebar.number_input("Minimum disclosed amount (US$ M)", 0.0, 100000.0, 0.0, step=1.0)
if min_m > 0:
    f = f[f["amount_usd"].fillna(0) >= min_m * 1e6]
f = ui.search(f, ["company_name", "lead_investor"], "Search company or lead investor")

amt = f["amount_usd"].dropna()
ui.kpis([
    ("Rounds", ui.num(len(f))),
    ("Companies", ui.num(f["company_name"].nunique())),
    ("Disclosed funding", ui.money(amt.sum())),
    ("Median disclosed round", ui.money(amt.median() if len(amt) else None)),
])
st.caption(f"Dataset: **{m['title']}**. Figures describe the filtered free sample, not the full dataset.")

if f.empty:
    st.warning("No rounds match these filters.")
else:
    c1, c2 = st.columns(2)
    with c1:
        ui.time_bars(f, "year", "Funding rounds by year")
    with c2:
        ui.time_bars(f, "year", "Disclosed funding by year (US$)", value="amount_usd", agg="sum", money_axis=True)
    c3, c4 = st.columns(2)
    with c3:
        ui.bar_top(f, "sector", "Top sectors by disclosed funding (US$)", value="amount_usd", agg="sum", money_axis=True)
    with c4:
        ui.box(f, "stage", "amount_usd", "Round size by stage (US$, log scale)", n=10, log=True)
    c5, c6 = st.columns(2)
    with c5:
        ui.bar_top(f, "lead_investor", "Most active lead investors (rounds)")
    with c6:
        geo = "city" if region_col != "city" and df["country"].astype(str).nunique() <= 3 else region_col
        ui.bar_top(f, geo, f"Rounds by {geo}")

ui.table(f.sort_values("announced_date", ascending=False),
         ["announced_date", "company_name", "company_domain", "country", "state", "nation", "city", "sector", "stage",
          "amount_usd", "amount_status", "lead_investor", "investor_count", "news_source", "news_url", "fliar_profile_url"],
         f"{key}_filtered", link_cols={"news_url": "News", "fliar_profile_url": "Profile"})
ui.about([key])
ui.footer()
