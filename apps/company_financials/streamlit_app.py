"""Company Financials: US and India quarterly results, UK and European company accounts, global earnings."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from common import ui
from common.data import load, meta

ui.setup("Company Financials Explorer: US & India quarterly results, UK & European accounts | Fliar BI",
         "Company Financials Explorer",
         "Revenue, profit and balance-sheet figures for US and Indian listed companies (quarterly), UK and European "
         "companies (annual accounts) and global earnings reports. Free samples of the Fliar BI financials datasets.",
         "📈")

CFG = {
    "US quarterly results": dict(
        key="us-quarterly-results", name="company_name", period="calendar_quarter", group="sector",
        geo="exchange", sort_period="period_end",
        metrics={"Revenue (US$)": ("revenue_usd", "$"), "Net income (US$)": ("net_income_usd", "$"),
                 "Operating income (US$)": ("operating_income_usd", "$"),
                 "Revenue growth YoY (%)": ("revenue_yoy_pct", "%")},
        extra=("ticker", "fiscal_year", "fiscal_quarter", "period_end", "fliar_profile_url")),
    "India quarterly results": dict(
        key="india-quarterly-results", name="company_name", period="quarter_end", group="sector", geo="basis",
        sort_period="quarter_end",
        metrics={"Revenue (INR)": ("revenue_inr", "₹"), "Net profit (INR)": ("net_profit_inr", "₹"),
                 "EBITDA (INR)": ("ebitda_inr", "₹"), "Revenue (US$)": ("revenue_usd", "$"),
                 "Revenue growth YoY (%)": ("revenue_yoy_pct", "%")},
        extra=("exchange_code", "fiscal_year", "quarter", "report_date", "fliar_profile_url")),
    "UK company accounts": dict(
        key="uk-company-financials-2019-2025", name="legal_name", period="fiscal_year", group="sic_section",
        geo="region", sort_period="fiscal_year",
        metrics={"Total assets (GBP)": ("total_assets", "£"), "Equity (GBP)": ("equity", "£"),
                 "Turnover (GBP)": ("turnover", "£"), "Profit (GBP)": ("profit", "£"), "Employees": ("employees", "")},
        extra=("company_number", "accounts_type", "company_status", "incorporation_year", "company_domain",
               "fliar_profile_url")),
    "European company accounts": dict(
        key="european-company-financials", name="legal_name", period="fiscal_year", group="country", geo="country",
        sort_period="fiscal_year",
        metrics={"Revenue (EUR)": ("revenue_eur", "€"), "Employees": ("employees", "")},
        extra=("registry_id", "currency", "revenue", "net_income", "equity", "total_assets", "company_domain",
               "fliar_profile_url")),
    "Global earnings reports": dict(
        key="company-earnings-results", name="company_name", period="fiscal_year", group="sector", geo="country",
        sort_period="report_date",
        metrics={"Revenue (US$)": ("revenue_usd", "$"), "Net income (US$)": ("net_income_usd", "$"),
                 "Revenue growth (%)": ("revenue_growth_pct", "%")},
        extra=("period_type", "period", "report_date", "beat_or_miss", "eps", "currency", "news_source", "news_url",
               "fliar_profile_url")),
}
label = st.sidebar.radio("Dataset", list(CFG))
c = CFG[label]
key, name, period, group, geo = c["key"], c["name"], c["period"], c["group"], c["geo"]
mcols = [v[0] for v in c["metrics"].values()]
cols = tuple(dict.fromkeys([name, period, group, geo, c["sort_period"], *mcols, *c["extra"]]))
m = meta(key)
df = load(key, cols)
st.sidebar.caption(f"{m['sample_rows']:,} of {m['full_rows']:,} {m['unit']} in this free sample.")

st.sidebar.header("Filters")
mlabel = st.sidebar.selectbox("Metric", list(c["metrics"]))
mcol, cur = c["metrics"][mlabel]
f = df
if "period_type" in f:
    f = ui.apply_multi(f, "period_type", ui.multi("Period type", f["period_type"]))
if period == "fiscal_year":
    f = ui.year_range(f, "fiscal_year", "Fiscal year")
f = ui.apply_multi(f, group, ui.multi(group.replace("sic_section", "Industry (SIC section)").title(), f[group]))
if geo != group:
    f = ui.apply_multi(f, geo, ui.multi(geo.title(), f[geo]))
f = ui.search(f, [name], "Search company")


def fmt(v):
    if cur == "%":
        return "–" if v is None or pd.isna(v) else f"{v:,.1f}%"
    return ui.money(v, cur) if cur else ui.num(v)


v = f[mcol].dropna()
ui.kpis([("Records", ui.num(len(f))), ("Companies", ui.num(f[name].nunique())),
         (f"Median {mlabel.split(' (')[0].lower()}", fmt(v.median() if len(v) else None)),
         ("Records with this metric", f"{(len(v) / max(1, len(f))):.0%}")])

if f.empty or v.empty:
    st.warning("No records with this metric match the filters.")
else:
    g = f[f[mcol].notna()].copy()
    g["_p"] = g[period].astype(str).str[:7] if period == "quarter_end" else g[period].astype(str)
    c1, c2 = st.columns(2)
    with c1:
        ui.time_bars(g.assign(_one=1), "_p", f"Records reporting {mlabel.split(' (')[0].lower()} by period")
    with c2:
        s = g.groupby("_p")[mcol].median().sort_index()
        fig = go.Figure(go.Scatter(x=s.index, y=s.values, mode="lines+markers", line=dict(width=2, color=ui.BLUE),
                                   marker=dict(size=8), hovertemplate="%{x}: %{y:,.2f}<extra></extra>"))
        fig.update_layout(title=f"Median {mlabel} by period (sample mix changes over time)", hovermode="x unified")
        fig.update_xaxes(type="category")
        ui.show(fig)
    c3, c4 = st.columns(2)
    with c3:
        gg = g[g[group].astype(str).str.strip() != ""]
        top = gg[group].astype(str).value_counts().head(12).index
        s = gg[gg[group].astype(str).isin(top)].groupby(gg[group].astype(str))[mcol].median().sort_values(ascending=False)
        ui.bar_series(s, f"Median {mlabel} by {group.replace('sic_section', 'industry')} (12 largest groups)",
                      money_axis=cur not in ("", "%"), prefix=cur, fmt=",.2f" if cur == "%" else ",.0f")
    with c4:
        latest = g.sort_values(c["sort_period"]).groupby(name, observed=True).tail(1)
        s = latest.set_index(latest[name].astype(str))[mcol].sort_values(ascending=False).head(15)
        ui.bar_series(s, f"Top companies by latest {mlabel}", money_axis=cur not in ("", "%"), prefix=cur,
                      fmt=",.2f" if cur == "%" else ",.0f")
    if "beat_or_miss" in g:
        ui.bar_top(g, "beat_or_miss", "Earnings vs expectations (where reported)")

    st.subheader("Company drill-down")
    names = g[name].astype(str).value_counts()
    pick = st.selectbox("Company (most reported first)", names.index[:500].tolist())
    one = f[f[name].astype(str) == pick].sort_values(c["sort_period"])
    one = one.assign(_p=one[period].astype(str).str[:7] if period == "quarter_end" else one[period].astype(str))
    fig = go.Figure()
    shown = [(lab, col) for lab, (col, cu) in c["metrics"].items() if cu == cur and one[col].notna().any()]
    for i, (lab, col) in enumerate(shown[:4]):
        fig.add_scatter(x=one["_p"], y=one[col], name=lab, mode="lines+markers", line=dict(width=2, color=ui.SERIES[i]),
                        marker=dict(size=8))
    fig.update_layout(title=f"{pick}: reported figures ({cur or 'count'})", hovermode="x unified")
    fig.update_xaxes(type="category")
    ui.show(fig)

ui.table(f.sort_values(c["sort_period"], ascending=False), list(cols), f"{key}_filtered",
         link_cols={"fliar_profile_url": "Profile", "news_url": "News"})
ui.about([key])
ui.footer()
