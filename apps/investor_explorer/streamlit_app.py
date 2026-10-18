"""Investor Explorer: VC investor directory and co-investment network."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from common import ui
from common.data import load, meta

ui.setup("VC Investor Directory & Co-investment Network Explorer | Fliar BI",
         "Investor Explorer",
         "Find startup investors by country, type and activity, and see who invests alongside whom. "
         "Free samples of the Fliar BI VC investor directory and co-investment network.", "🕸️")

DIR, NET = "vc-investor-directory", "investor-coinvestment-network"
view = st.sidebar.radio("View", ["Investor directory", "Co-investment network"])
st.sidebar.header("Filters")

if view == "Investor directory":
    m = meta(DIR)
    df = load(DIR, ("investor_name", "investor_domain", "hq_country", "hq_city", "investor_type", "deals", "lead_deals",
                    "portfolio_companies", "first_deal_year", "last_deal_year", "deals_2025_2026", "top_sectors",
                    "top_countries", "seed_share", "early_share", "growth_share", "median_round_usd", "fliar_profile_url"))
    st.sidebar.caption(f"{m['sample_rows']:,} of {m['full_rows']:,} {m['unit']} in this free sample.")
    f = ui.apply_multi(df, "hq_country", ui.multi("HQ country", df["hq_country"]))
    f = ui.apply_multi(f, "investor_type", ui.multi("Investor type", f["investor_type"]))
    sec = st.sidebar.text_input("Sector focus contains (e.g. Fintech)").strip().lower()
    if sec:
        f = f[f["top_sectors"].astype(str).str.lower().str.contains(sec, regex=False)]
    mind = st.sidebar.slider("Minimum deals", 1, int(max(2, min(100, df["deals"].max()))), 1)
    f = f[f["deals"] >= mind]
    f = ui.search(f, ["investor_name", "investor_domain"], "Search investor")

    ui.kpis([("Investors", ui.num(len(f))), ("Deals (sum)", ui.num(f["deals"].sum())),
             ("Lead deals (sum)", ui.num(f["lead_deals"].sum())),
             ("Median of median round", ui.money(f["median_round_usd"].median() if len(f) else None))])
    if f.empty:
        st.warning("No investors match these filters.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            ui.bar_top(f, "investor_name", "Most active investors (deals)", value="deals", agg="sum")
        with c2:
            ui.bar_top(f, "hq_country", "Investors by HQ country")
        c3, c4 = st.columns(2)
        with c3:
            ui.bar_top(f, "investor_type", "Investors by type", n=12)
        with c4:
            g = f[f["deals"] >= 3].copy()
            g["investor_type"] = g["investor_type"].astype(str)
            mix = g.groupby("investor_type")[["seed_share", "early_share", "growth_share"]].mean()
            mix = mix.loc[g["investor_type"].value_counts().head(8).index] if len(mix) else mix
            fig = go.Figure()
            for i, (c, lab) in enumerate([("seed_share", "Seed"), ("early_share", "Early"), ("growth_share", "Growth")]):
                fig.add_bar(y=mix.index, x=mix[c] * 100, name=lab, orientation="h", marker_color=ui.SERIES[i],
                            marker_line_width=2, marker_line_color="rgba(0,0,0,0)",
                            hovertemplate=f"%{{y}} · {lab}: %{{x:.0f}}%<extra></extra>")
            fig.update_layout(barmode="group", title="Average stage mix by investor type (investors with 3+ deals, %)")
            ui.show(fig, height=420)
        ui.bar_top(f[f["deals_2025_2026"] > 0], "investor_name", "Most active in 2025–2026 (deals)",
                   value="deals_2025_2026", agg="sum")
    ui.table(f.sort_values("deals", ascending=False),
             ["investor_name", "investor_domain", "hq_country", "hq_city", "investor_type", "deals", "lead_deals",
              "portfolio_companies", "first_deal_year", "last_deal_year", "deals_2025_2026", "top_sectors",
              "top_countries", "seed_share", "early_share", "growth_share", "median_round_usd", "fliar_profile_url"],
             "vc_investor_directory_filtered", link_cols={"fliar_profile_url": "Profile"})
    ui.about([DIR, NET])
else:
    m = meta(NET)
    df = load(NET, ("investor_a", "investor_a_type", "investor_b", "investor_b_type", "shared_deals", "first_year",
                    "last_year", "top_shared_sector", "top_shared_country", "fliar_profile_url"))
    st.sidebar.caption(f"{m['sample_rows']:,} of {m['full_rows']:,} {m['unit']} in this free sample.")
    f = ui.year_range(df, "last_year", "Last shared deal year")
    f = ui.apply_multi(f, "top_shared_country", ui.multi("Shared-deal country", f["top_shared_country"]))
    f = ui.apply_multi(f, "top_shared_sector", ui.multi("Shared-deal sector", f["top_shared_sector"]))
    mins = st.sidebar.slider("Minimum shared deals", 1, 10, 2)
    f = f[f["shared_deals"] >= mins]
    q = st.sidebar.text_input("Focus on investor (name contains)").strip().lower()
    if q:
        f = f[f["investor_a"].astype(str).str.lower().str.contains(q, regex=False)
              | f["investor_b"].astype(str).str.lower().str.contains(q, regex=False)]
    max_edges = st.sidebar.slider("Edges drawn in the graph", 50, 400, 200, step=50)

    inv = pd.concat([f["investor_a"].astype(str), f["investor_b"].astype(str)])
    ui.kpis([("Investor pairs", ui.num(len(f))), ("Investors", ui.num(inv.nunique())),
             ("Shared deals (sum)", ui.num(f["shared_deals"].sum())),
             ("Most deals by one pair", ui.num(f["shared_deals"].max() if len(f) else None))])
    if f.empty:
        st.warning("No pairs match these filters. Lower the minimum shared deals.")
    else:
        e = f.nlargest(max_edges, "shared_deals")
        G = nx.Graph()
        for a, b, w in zip(e["investor_a"].astype(str), e["investor_b"].astype(str), e["shared_deals"]):
            G.add_edge(a, b, weight=float(w))
        pos = nx.spring_layout(G, seed=7, k=1.2 / max(1, len(G) ** 0.5), iterations=60, weight="weight")
        ex, ey = [], []
        for a, b in G.edges():
            ex += [pos[a][0], pos[b][0], None]
            ey += [pos[a][1], pos[b][1], None]
        deg = dict(G.degree(weight="weight"))
        nodes = list(G.nodes())
        top_lab = set(sorted(nodes, key=lambda n: -deg[n])[:15])
        fig = go.Figure()
        fig.add_scatter(x=ex, y=ey, mode="lines", line=dict(width=1, color="rgba(137,135,129,0.45)"), hoverinfo="skip",
                        showlegend=False)
        fig.add_scatter(x=[pos[n][0] for n in nodes], y=[pos[n][1] for n in nodes], mode="markers+text",
                        text=[n if n in top_lab else "" for n in nodes], textposition="top center",
                        textfont=dict(size=10),
                        marker=dict(size=[8 + min(30, deg[n] * 1.5) for n in nodes], color=ui.BLUE,
                                    line=dict(width=2, color="rgba(255,255,255,0.9)")),
                        customdata=[[n, deg[n], G.degree(n)] for n in nodes],
                        hovertemplate="%{customdata[0]}<br>shared deals in view: %{customdata[1]:,.0f}"
                                      "<br>co-investors in view: %{customdata[2]}<extra></extra>", showlegend=False)
        fig.update_layout(title=f"Co-investment network: the {len(e):,} strongest pairs (node size = shared deals)")
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        ui.show(fig, height=640)
        c1, c2 = st.columns(2)
        with c1:
            p = e.head(15).copy()
            p["pair"] = p["investor_a"].astype(str) + " + " + p["investor_b"].astype(str)
            ui.bar_top(p, "pair", "Strongest pairs (shared deals)", value="shared_deals", agg="sum")
        with c2:
            ui.bar_top(f, "top_shared_sector", "Pairs by main shared sector")
        hub = pd.DataFrame({"investor": inv})
        ui.bar_top(hub, "investor", "Investors with the most co-investors in view")
    ui.table(f.sort_values("shared_deals", ascending=False),
             ["investor_a", "investor_a_type", "investor_b", "investor_b_type", "shared_deals", "first_year", "last_year",
              "top_shared_sector", "top_shared_country", "fliar_profile_url"],
             "vc_coinvestment_pairs_filtered", link_cols={"fliar_profile_url": "Profile"})
    ui.about([NET, DIR])
ui.footer()
