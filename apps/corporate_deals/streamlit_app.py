"""Corporate Deals and Events: M&A, IPOs, layoffs, contract wins, lawsuits and other corporate events, 2019–2026."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import streamlit as st

from common import ui
from common.data import load, meta

ui.setup("Corporate Deals & Events Tracker 2019–2026: M&A, IPOs, layoffs, contracts, lawsuits | Fliar BI",
         "Corporate Deals and Events Tracker",
         "Mergers and acquisitions, IPOs, layoffs, contract wins, lawsuits and 100,000 corporate events extracted "
         "from business news, 2019–2026. Free samples of the Fliar BI deals datasets.", "🤝")

CFG = {
    "Mergers & acquisitions": dict(
        key="mergers-acquisitions-2019-2026", date="announced_date", name="acquirer_name", value="deal_value_usd",
        vlabel="Disclosed deal value", cat="deal_type", geo="target_country", status="deal_status",
        cols=("announced_date", "year", "acquirer_name", "acquirer_country", "target_name", "target_country", "sector",
              "deal_type", "stake_pct", "deal_status", "deal_value_usd", "amount_status", "cross_border",
              "news_source", "news_url", "fliar_profile_url")),
    "IPOs": dict(
        key="ipo-tracker-2019-2026", date="listing_date", name="company_name", value="issue_size_usd",
        vlabel="Disclosed issue size", cat="exchange", geo="country", status="listing_status",
        cols=("listing_date", "first_report_date", "year", "company_name", "ticker", "exchange", "board", "country",
              "sector", "ipo_type", "listing_status", "issue_size_usd", "amount_status", "issue_price", "news_source",
              "news_url", "fliar_profile_url")),
    "Layoffs": dict(
        key="layoffs-2019-2026", date="date", name="company_name", value="headcount_cut", vlabel="Jobs cut (reported)",
        cat="sector", geo="company_country", status="headcount_status", people=True,
        cols=("date", "year", "company_name", "company_country", "company_state", "company_city", "sector",
              "headcount_cut", "headcount_status", "pct_workforce", "is_furlough", "news_source", "news_url",
              "fliar_profile_url")),
    "Contract wins": dict(
        key="contract-wins-2019-2026", date="date", name="contractor_name", value="value_usd",
        vlabel="Disclosed contract value", cat="contract_type", geo="contractor_country", status="client_type",
        cols=("date", "year", "contractor_name", "contractor_country", "sector", "client_name", "client_country",
              "client_type", "contract_type", "value_usd", "amount_status", "news_source", "news_url",
              "fliar_profile_url")),
    "Lawsuits": dict(
        key="lawsuits-2019-2026", date="date", name="company_name", value="claim_usd", vlabel="Disclosed claims",
        cat="case_type", geo="country", status="case_status",
        cols=("date", "year", "company_name", "company_role", "company_country", "sector", "opponent_name",
              "opponent_type", "case_type", "case_status", "country", "court", "claim_usd", "settlement_usd",
              "news_source", "news_url", "fliar_profile_url")),
    "All corporate events": dict(
        key="corporate-events-2019-2026", date="event_date", name="company_name", value=None, vlabel=None,
        cat="event_type", geo="country", status="role",
        cols=("event_date", "event_type", "role", "company_name", "country", "sector", "headline", "news_source",
              "news_url", "fliar_profile_url")),
}
label = st.sidebar.radio("Dataset", list(CFG))
c = CFG[label]
key, dcol, name, val, cat, geo = c["key"], c["date"], c["name"], c["value"], c["cat"], c["geo"]
m = meta(key)
df = load(key, c["cols"])
if "year" not in df:
    df["year"] = pd.to_numeric(df[dcol].astype(str).str[:4], errors="coerce")
df["year"] = pd.to_numeric(df["year"], errors="coerce").fillna(
    pd.to_numeric(df[dcol].astype(str).str[:4], errors="coerce"))
st.sidebar.caption(f"{m['sample_rows']:,} of {m['full_rows']:,} {m['unit']} in this free sample.")

st.sidebar.header("Filters")
f = ui.year_range(df[df["year"].notna()], "year")
f = ui.apply_multi(f, cat, ui.multi(cat.replace("_", " ").capitalize(), f[cat]))
f = ui.apply_multi(f, geo, ui.multi(geo.replace("_", " ").capitalize(), f[geo]))
if cat != "sector":
    f = ui.apply_multi(f, "sector", ui.multi("Sector", f["sector"]))
f = ui.search(f, [x for x in (name, "target_name", "client_name", "opponent_name", "headline") if x in f],
              "Search company or headline")

people = c.get("people", False)
k = [("Records", ui.num(len(f))), ("Companies", ui.num(f[name].nunique()))]
if val:
    v = f[val].dropna()
    k += [(c["vlabel"], ui.num(v.sum()) if people else ui.money(v.sum())),
          ("Median (where disclosed)", ui.num(v.median()) if people and len(v) else ui.money(v.median() if len(v) else None))]
else:
    k += [("Event types", ui.num(f[cat].nunique())), ("Countries", ui.num(f[geo].nunique()))]
ui.kpis(k)

if f.empty:
    st.warning("No records match these filters.")
else:
    c1, c2 = st.columns(2)
    with c1:
        ui.time_bars(f, "year", f"{label}: records by year")
    with c2:
        if val:
            ui.time_bars(f, "year", f"{c['vlabel']} by year" + ("" if people else " (US$)"), value=val, agg="sum",
                         money_axis=not people)
        else:
            ui.bar_top(f, geo, "Events by country")
    c3, c4 = st.columns(2)
    with c3:
        ui.bar_top(f, cat, f"Records by {cat.replace('_', ' ')}")
    with c4:
        if val:
            ui.bar_top(f, name, f"Top companies by {c['vlabel'].lower()}", value=val, agg="sum", money_axis=not people)
        else:
            ui.bar_top(f, name, "Companies with the most events")
    ui.heat(f.assign(year=f["year"].astype(int).astype(str)), cat if cat != "sector" else geo, "year",
            f"{(cat if cat != 'sector' else geo).replace('_', ' ').capitalize()} × year (records)", n_cols=8)

show_cols = list(c["cols"])
ui.table(f.sort_values(dcol, ascending=False), show_cols, f"{key}_filtered",
         link_cols={"news_url": "News", "fliar_profile_url": "Profile"})
ui.about([key])
ui.footer()
