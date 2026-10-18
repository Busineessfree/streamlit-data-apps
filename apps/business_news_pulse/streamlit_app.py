"""Business News Pulse: monthly volume, sentiment and topics of 17.4M business & financial news articles, 2019–2026."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from common import ui
from common.data import ROOT, load_bundle

ui.setup("Business News Pulse 2019–2026: business news volume, sentiment & rising topics | Fliar BI",
         "Business News Pulse",
         "Monthly volume, sentiment and topics of business and financial news from January 2019 to June 2026, "
         "plus monthly corporate-event counts. Aggregates only, built by Fliar BI.", "📰")

T = "news"
cov = json.loads((ROOT / "data" / T / "coverage.json").read_text())
partial = set(cov.get("partial_months", []))

tc = load_bundle(T, "monthly_topic_country")
sec = load_bundle(T, "monthly_sector")
sub = load_bundle(T, "monthly_subtopic")
rise = load_bundle(T, "rising_topics")
ev_c = load_bundle(T, "monthly_events_country")
ev_s = load_bundle(T, "monthly_events_sector")
tot = load_bundle(T, "monthly_totals")

st.sidebar.header("Filters")
months = sorted(tot["month"].unique())
a, b = st.sidebar.select_slider("Months", months, (months[0], months[-1]))
drop_partial = st.sidebar.checkbox(f"Hide partial months ({', '.join(sorted(partial)) or 'none'})", value=True)
groups = st.sidebar.multiselect("Topic group", sorted(tc["topic_group"].unique()), help="Leave empty for all")
countries = st.sidebar.multiselect("Country", ui.top_values(tc["country"], 40), help="Leave empty for all")
topics = st.sidebar.multiselect("Topic", sorted(tc["topic"].unique()), help="Leave empty for all")


def window(d):
    d = d[(d["month"] >= a) & (d["month"] <= b)]
    return d[~d["month"].isin(partial)] if drop_partial else d


f = window(tc)
if groups:
    f = f[f["topic_group"].isin(groups)]
if countries:
    f = f[f["country"].isin(countries)]
if topics:
    f = f[f["topic"].isin(topics)]


def net(d):
    n = d["articles"].sum()
    return (d["positive"].sum() - d["negative"].sum()) / n * 100 if n else float("nan")


ui.kpis([("Articles in view", ui.num(f["articles"].sum())), ("Months", ui.num(f["month"].nunique())),
         ("Net sentiment", f"{net(f):+.1f}" if len(f) else "–"),
         ("Avg tone", f"{f['tone_sum'].sum() / max(1, f['articles'].sum()) * 100:+.1f}" if len(f) else "–")])
st.caption("Net sentiment = (positive − negative) / all articles × 100. Monthly volume follows crawler capacity "
           "as much as the news cycle, so compare shares and sentiment rather than raw counts.")

tab1, tab2, tab3, tab4 = st.tabs(["Volume & sentiment", "Topics & sectors", "Rising topics", "Corporate events"])
with tab1:
    if f.empty:
        st.warning("Nothing matches these filters.")
    else:
        mth = f.groupby("month")[["articles", "positive", "negative"]].sum()
        mth["net"] = (mth["positive"] - mth["negative"]) / mth["articles"] * 100
        ui.time_bars(mth.reset_index(), "month", "Articles per month", value="articles", agg="sum")
        fig = go.Figure(go.Scatter(x=mth.index, y=mth["net"], mode="lines", line=dict(width=2, color=ui.BLUE),
                                   hovertemplate="%{x}: %{y:+.1f}<extra></extra>"))
        fig.add_hline(y=0, line_width=1, line_color="rgba(137,135,129,0.6)")
        fig.update_layout(title="Net sentiment per month", hovermode="x unified")
        ui.show(fig)
with tab2:
    if not f.empty:
        c1, c2 = st.columns(2)
        with c1:
            ui.bar_top(f, "topic", "Topics by articles", value="articles", agg="sum")
        with c2:
            g = f[f["country"] != "Unspecified"]
            ui.bar_top(g, "country", "Countries by articles (where detected)", value="articles", agg="sum")
        s = window(sec).groupby("sector")[["articles", "positive", "negative"]].sum()
        s = s[s["articles"] >= 1000]
        s["net"] = (s["positive"] - s["negative"]) / s["articles"] * 100
        s = s.sort_values("net")
        pick = pd.concat([s.head(10), s.tail(10)])
        fig = go.Figure(go.Bar(x=pick["net"], y=pick.index, orientation="h",
                               marker_color=ui.BLUE,
                               hovertemplate="%{y}: %{x:+.1f}<extra></extra>"))
        fig.update_layout(title="Sectors with the lowest and highest net sentiment (sectors with 1,000+ articles)")
        ui.show(fig, height=640)
        top_t = f.groupby("topic")["articles"].sum().nlargest(8).index
        sh = f[f["topic"].isin(top_t)].groupby(["month", "topic"])["articles"].sum().unstack(fill_value=0)
        allm = f.groupby("month")["articles"].sum()
        sh = sh.div(allm, axis=0) * 100
        fig = go.Figure()
        for i, t in enumerate(top_t):
            fig.add_scatter(x=sh.index, y=sh[t], name=t, mode="lines", line=dict(width=2, color=ui.SERIES[i]))
        fig.update_layout(title="Share of articles by topic (8 largest topics, %)", hovermode="x unified")
        ui.show(fig, height=440)
with tab3:
    r = rise.copy()
    w6, w12 = r["window_last6"].iloc[0], r["window_prev12"].iloc[0]
    st.caption(f"Share of business news in {w6} vs {w12}. Minimum 300 articles in the last 6 months and 100 before.")
    c1, c2 = st.columns(2)
    with c1:
        up = r[r["direction"] == "rising"].nlargest(20, "growth_x").set_index("subtopic")["growth_x"]
        ui.bar_series(up, "Fastest-rising sub-topics (share growth ×)", fmt=".2f")
    with c2:
        dn = r[r["direction"] != "rising"].nsmallest(20, "growth_x").set_index("subtopic")["growth_x"]
        ui.bar_series(dn, "Fastest-falling sub-topics (share growth ×)", fmt=".2f")
    q = st.selectbox("Sub-topic trend", r.sort_values("growth_x", ascending=False)["subtopic"].tolist())
    one = window(sub[sub["subtopic"] == q]).groupby("month")["articles"].sum()
    share = (one / window(tot).set_index("month")["articles"] * 100).dropna()
    fig = go.Figure(go.Scatter(x=share.index, y=share.values, mode="lines+markers", line=dict(width=2, color=ui.BLUE),
                               marker=dict(size=8), hovertemplate="%{x}: %{y:.3f}%<extra></extra>"))
    fig.update_layout(title=f"“{q}”: share of business news per month (%)")
    ui.show(fig)
    ui.table(r, list(r.columns), "rising_falling_topics")
with tab4:
    e = window(ev_c)
    if countries:
        e = e[e["country"].isin(countries)]
    c1, c2 = st.columns(2)
    with c1:
        ui.bar_top(e, "event_label", "Corporate events by type", value="events", agg="sum")
    with c2:
        ui.bar_top(e, "country", "Corporate events by company country", value="events", agg="sum")
    es = window(ev_s)
    ui.bar_top(es, "sector", "Corporate events by company sector", value="events", agg="sum", n=20)

st.subheader("Monthly topic × country table")
ui.table(f.sort_values(["month", "articles"], ascending=[False, False]),
         ["month", "topic_group", "topic", "country", "articles", "positive", "negative", "neutral"],
         "business_news_monthly_topic_country")
ui.about_bundle(T, {"Aggregates on Hugging Face": "https://huggingface.co/datasets/fliarbi/business-news-pulse-aggregates"},
                related=["corporate-events-2019-2026"])
ui.footer()
