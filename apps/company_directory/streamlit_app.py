"""Company Directory and Web Tech: open company database, website technology stacks and Google Play apps."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import plotly.express as px
import streamlit as st

from common import ui
from common.data import load, meta

ui.setup("Open Company Database & Website Technology Stack Explorer | Fliar BI",
         "Company Directory and Web Tech",
         "Browse an open company database by country, sector and size, see which technologies company websites run "
         "on, and explore Google Play apps by developer. Free samples of the Fliar BI company datasets.", "🏢")

view = st.sidebar.radio("View", ["Company directory", "Website technology", "Google Play apps"])
st.sidebar.header("Filters")

if view == "Company directory":
    key = "open-company-database"
    cols = ("company_name", "company_domain", "country", "region", "city", "founded_year", "sector", "industry",
            "business_model", "status", "is_funded", "employees_range", "web_rank_bucket", "fliar_profile_url")
    df = load(key, cols)
    f = ui.apply_multi(df, "country", ui.multi("Country", df["country"]))
    f = ui.apply_multi(f, "sector", ui.multi("Sector", f["sector"]))
    f = ui.apply_multi(f, "status", ui.multi("Status / stage", f["status"]))
    f = ui.apply_multi(f, "employees_range", ui.multi("Employees", f["employees_range"]))
    if st.sidebar.checkbox("Funded companies only"):
        f = f[f["is_funded"] == True]  # noqa: E712
    fy = pd.to_numeric(f["founded_year"], errors="coerce")
    if fy.notna().any():
        lo, hi = int(max(1900, fy.min())), int(fy.max())
        a, b = st.sidebar.slider("Founded", lo, hi, (lo, hi))
        if (a, b) != (lo, hi):
            f = f[(fy >= a) & (fy <= b)]
    f = ui.search(f, ["company_name", "company_domain", "business_model"], "Search name, domain or business model")
    ui.kpis([("Companies", ui.num(len(f))), ("Countries", ui.num(f["country"].nunique())),
             ("Funded", f"{f['is_funded'].fillna(False).astype(bool).mean():.0%}" if len(f) else "–"),
             ("Median founded year", (lambda v: "–" if pd.isna(v) else str(int(v)))(pd.to_numeric(f["founded_year"], errors="coerce").median()))])
    if f.empty:
        st.warning("No companies match these filters.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            ui.bar_top(f, "country", "Companies by country")
        with c2:
            ui.bar_top(f, "sector", "Companies by sector")
        c3, c4 = st.columns(2)
        with c3:
            y = pd.to_numeric(f["founded_year"], errors="coerce")
            ui.time_bars(f[(y >= 1990)].assign(founded_year=y[(y >= 1990)].astype("Int64")), "founded_year",
                         "Companies by founding year (1990+)")
        with c4:
            order = ["1-10", "11-50", "51-200", "201-500", "501-1000", "1001-5000", "5001-10000", "10001+"]
            s = f["employees_range"].astype(str).value_counts()
            s = s.reindex([o for o in order if o in s.index] + [i for i in s.index if i not in order and i.strip()])
            s = s.dropna()
            ui.bar_series(s[::-1], "Companies by employee range")
        ui.bar_series(ui.explode_counts(f["business_model"], n=20), "Most common business-model tags")
    ui.table(f, list(cols), "open_company_database_filtered", link_cols={"fliar_profile_url": "Profile"})
    ui.about([key])

elif view == "Website technology":
    key = "website-technology-stack"
    cols = ("company_domain", "company_name", "country", "sector", "technologies", "technology_count", "cdn",
            "web_rank_bucket", "web_speed", "seo_maturity", "fliar_profile_url")
    df = load(key, cols)
    f = ui.apply_multi(df, "country", ui.multi("Country", df["country"]))
    f = ui.apply_multi(f, "sector", ui.multi("Sector", f["sector"]))
    f = ui.apply_multi(f, "web_rank_bucket", ui.multi("Web rank", f["web_rank_bucket"]))
    tech = st.sidebar.text_input("Uses technology (e.g. wordpress, react)").strip().lower()
    if tech:
        f = f[f["technologies"].astype(str).str.lower().str.split("|").apply(lambda xs: tech in xs)]
    f = ui.search(f, ["company_name", "company_domain"], "Search company or domain")
    has_cdn = (f["cdn"].astype(str).str.strip() != "").mean() if len(f) else None
    ui.kpis([("Websites", ui.num(len(f))), ("Median technologies per site", ui.num(f["technology_count"].median())),
             ("Sites behind a CDN", f"{has_cdn:.0%}" if has_cdn is not None else "–"),
             ("Distinct technologies", ui.num(ui.explode_counts(f["technologies"], n=100000).size))])
    if f.empty:
        st.warning("No websites match these filters.")
    else:
        top = ui.explode_counts(f["technologies"], n=25)
        ui.bar_series((top / len(f) * 100).round(1), "Most used technologies (% of sites)", fmt=".1f")
        c1, c2 = st.columns(2)
        with c1:
            ui.bar_top(f, "cdn", "CDN used")
        with c2:
            h = f[f["technology_count"] <= f["technology_count"].quantile(0.99)]
            fig = px.histogram(h, x="technology_count", nbins=40, color_discrete_sequence=[ui.BLUE])
            fig.update_layout(title="Technologies detected per website", bargap=0.05, xaxis_title=None,
                              yaxis_title="websites")
            ui.show(fig)
        c3, c4 = st.columns(2)
        with c3:
            ui.heat(f, "seo_maturity", "web_speed", "SEO maturity × page speed (websites)", n_rows=6, n_cols=6)
        with c4:
            ui.bar_top(f, "sector", "Websites by sector")
    ui.table(f, list(cols), "website_technology_stack_filtered", link_cols={"fliar_profile_url": "Profile"})
    ui.about([key])

else:
    key = "google-play-apps-2026"
    cols = ("title", "developer", "developer_domain", "genre", "is_game", "installs", "score", "ratings", "reviews",
            "free", "price", "contains_ads", "offers_iap", "content_rating", "released", "last_updated",
            "fliar_profile_url")
    df = load(key, cols)
    df["_inst"] = pd.to_numeric(df["installs"].astype(str).str.replace(r"[^0-9]", "", regex=True), errors="coerce")
    f = ui.apply_multi(df, "genre", ui.multi("Genre", df["genre"]))
    kind = st.sidebar.selectbox("Type", ["All", "Games", "Non-game apps"])
    if kind != "All":
        f = f[f["is_game"] == (kind == "Games")]
    mins = st.sidebar.slider("Minimum rating", 0.0, 5.0, 0.0, 0.1)
    if mins > 0:
        f = f[f["score"].fillna(0) >= mins]
    mi = st.sidebar.selectbox("Minimum installs", [0, 1_000, 100_000, 1_000_000, 10_000_000, 100_000_000],
                              format_func=lambda x: f"{x:,}+")
    if mi:
        f = f[f["_inst"].fillna(0) >= mi]
    f = ui.search(f, ["title", "developer"], "Search app or developer")
    ui.kpis([("Apps", ui.num(len(f))), ("Developers", ui.num(f["developer"].nunique())),
             ("Median rating", f"{f['score'].median():.2f}" if f["score"].notna().any() else "–"),
             ("Contain ads", f"{f['contains_ads'].fillna(False).astype(bool).mean():.0%}" if len(f) else "–")])
    if f.empty:
        st.warning("No apps match these filters.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            ui.bar_top(f, "genre", "Apps by genre")
        with c2:
            s = f.groupby(f["installs"].astype(str))["_inst"].first().sort_values()
            cnt = f["installs"].astype(str).value_counts().reindex(s.index)
            ui.bar_series(cnt[::-1], "Apps by install bracket")
        c3, c4 = st.columns(2)
        with c3:
            fig = px.histogram(f[f["score"] > 0], x="score", nbins=40, color_discrete_sequence=[ui.BLUE])
            fig.update_layout(title="Rating distribution (rated apps)", bargap=0.05, xaxis_title=None,
                              yaxis_title="apps")
            ui.show(fig)
        with c4:
            ui.bar_top(f, "developer", "Developers with the most apps")
        g = f[f["genre"].astype(str).isin(ui.top_values(f["genre"], 12))]
        s = (g.groupby(g["genre"].astype(str))["offers_iap"].mean() * 100).sort_values(ascending=False)
        ui.bar_series(s.round(1), "Share offering in-app purchases by genre (12 largest, %)", fmt=".1f")
    ui.table(f.sort_values("_inst", ascending=False), [c for c in cols], "google_play_apps_filtered",
             link_cols={"fliar_profile_url": "Profile"})
    ui.about([key])
ui.footer()
