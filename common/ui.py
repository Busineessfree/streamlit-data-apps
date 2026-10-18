"""Page scaffolding shared by every app: config, KPIs, filters, charts, table, download, About-the-data."""
from __future__ import annotations

from typing import Iterable

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from common.data import meta

GITHUB_INDEX = "https://github.com/Busineessfree/open-company-datasets"
REPO = "https://github.com/Busineessfree/streamlit-data-apps"
CONTACT = "b2b@fliarbi.com"
LICENCE = "CC BY-NC 4.0"
LICENCE_URL = "https://creativecommons.org/licenses/by-nc/4.0/"

# Validated categorical order (fixed, never cycled) and a single-hue sequential blue ramp.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
BLUE = "#2a78d6"
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]


def setup(title: str, h1: str, description: str, icon: str = "📊") -> None:
    st.set_page_config(page_title=title, page_icon=icon, layout="wide",
                       menu_items={"About": f"{h1}. Data by Fliar BI, licence {LICENCE}. Contact {CONTACT}."})
    st.title(h1)
    st.caption(description)


# ---------- formatting ----------
def money(v: float | int | None, cur: str = "$") -> str:
    if v is None or pd.isna(v):
        return "–"
    a = abs(float(v))
    if cur == "₹":  # Indian units: lakh and crore
        for div, suf in ((1e7, " Cr"), (1e5, " L")):
            if a >= div:
                return f"{'-' if v < 0 else ''}₹{a / div:,.1f}{suf}"
        return f"{'-' if v < 0 else ''}₹{a:,.0f}"
    for div, suf in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if a >= div:
            return f"{'-' if v < 0 else ''}{cur}{a / div:,.1f}{suf}"
    return f"{'-' if v < 0 else ''}{cur}{a:,.0f}"


def num(v) -> str:
    return "–" if v is None or pd.isna(v) else f"{v:,.0f}"


def kpis(items: Iterable[tuple[str, str]]) -> None:
    items = list(items)
    cols = st.columns(len(items))
    for c, (label, value) in zip(cols, items):
        c.metric(label, value)


# ---------- filters ----------
def top_values(s: pd.Series, n: int = 200) -> list:
    vc = s.dropna().astype(str)
    vc = vc[vc.str.strip() != ""].value_counts()
    return vc.index[:n].tolist()


def multi(label: str, s: pd.Series, n: int = 200, key: str | None = None, help: str | None = None) -> list:
    return st.sidebar.multiselect(label, top_values(s, n), key=key, help=help or "Leave empty for all")


def apply_multi(df: pd.DataFrame, col: str, picked: list) -> pd.DataFrame:
    return df[df[col].astype(str).isin(picked)] if picked else df


def year_range(df: pd.DataFrame, col: str, label: str = "Year", key: str | None = None) -> pd.DataFrame:
    y = pd.to_numeric(df[col], errors="coerce")
    lo, hi = int(y.min()), int(y.max())
    if lo == hi:
        return df
    a, b = st.sidebar.slider(label, lo, hi, (lo, hi), key=key)
    return df[(y >= a) & (y <= b)]


def search(df: pd.DataFrame, cols: list[str], label: str = "Search name", key: str | None = None) -> pd.DataFrame:
    q = st.sidebar.text_input(label, key=key).strip().lower()
    if not q:
        return df
    m = pd.Series(False, index=df.index)
    for c in cols:
        m |= df[c].astype(str).str.lower().str.contains(q, regex=False, na=False)
    return df[m]


# ---------- charts ----------
def _style(fig: go.Figure, height: int = 380) -> go.Figure:
    fig.update_layout(height=height, margin=dict(l=8, r=8, t=76, b=8), colorway=SERIES,
                      legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0), hoverlabel=dict(namelength=-1))
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridwidth=1)
    return fig


def show(fig: go.Figure, height: int = 380) -> None:
    st.plotly_chart(_style(fig, height), use_container_width=True, theme="streamlit")


def bar_top(df: pd.DataFrame, col: str, title: str, n: int = 15, value: str | None = None, agg: str = "count",
            money_axis: bool = False) -> None:
    d = df[df[col].notna() & (df[col].astype(str).str.strip() != "")]
    if d.empty:
        st.info(f"No data for: {title}")
        return
    if value is None:
        s = d[col].astype(str).value_counts().head(n)
    else:
        s = d.groupby(d[col].astype(str), observed=True)[value].agg(agg).sort_values(ascending=False).head(n)
    s = s[::-1]
    fig = go.Figure(go.Bar(x=s.values, y=s.index, orientation="h", marker_color=BLUE,
                           hovertemplate="%{y}: %{x:,.0f}<extra></extra>"))
    fig.update_layout(title=title, bargap=0.25)
    if money_axis:
        fig.update_xaxes(tickprefix="$")
    show(fig, height=max(320, 26 * len(s) + 90))


def time_bars(df: pd.DataFrame, col: str, title: str, value: str | None = None, agg: str = "count",
              money_axis: bool = False) -> None:
    d = df[df[col].notna()]
    if d.empty:
        st.info(f"No data for: {title}")
        return
    if value is None:
        s = d.groupby(col, observed=True).size()
    else:
        s = d.groupby(col, observed=True)[value].agg(agg)
    s = s.sort_index()
    fig = go.Figure(go.Bar(x=s.index.astype(str), y=s.values, marker_color=BLUE,
                           hovertemplate="%{x}: %{y:,.0f}<extra></extra>"))
    fig.update_layout(title=title, bargap=0.2)
    fig.update_xaxes(type="category")
    if money_axis:
        fig.update_yaxes(tickprefix="$")
    show(fig)


def box(df: pd.DataFrame, x: str, y: str, title: str, n: int = 10, log: bool = False) -> None:
    d = df[df[y].notna() & df[x].notna()]
    if d.empty:
        st.info(f"No data for: {title}")
        return
    keep = d[x].astype(str).value_counts().head(n).index
    d = d[d[x].astype(str).isin(keep)].copy()
    d[x] = d[x].astype(str)
    order = d.groupby(x)[y].median().sort_values(ascending=False).index.tolist()
    fig = px.box(d, x=x, y=y, points=False, category_orders={x: order}, log_y=log, color_discrete_sequence=[BLUE])
    fig.update_layout(title=title, xaxis_title=None)
    show(fig)


def heat(df: pd.DataFrame, rows: str, cols: str, title: str, n_rows: int = 12, n_cols: int = 10) -> None:
    d = df[df[rows].notna() & df[cols].notna()]
    d = d[(d[rows].astype(str).str.strip() != "") & (d[cols].astype(str).str.strip() != "")]
    if d.empty:
        st.info(f"No data for: {title}")
        return
    r = d[rows].astype(str).value_counts().head(n_rows).index
    c = d[cols].astype(str).value_counts().head(n_cols).index
    d = d[d[rows].astype(str).isin(r) & d[cols].astype(str).isin(c)]
    t = pd.crosstab(d[rows].astype(str), d[cols].astype(str)).reindex(index=r, columns=c, fill_value=0)
    fig = go.Figure(go.Heatmap(z=t.values, x=t.columns, y=t.index, colorscale=[[i / 6, s] for i, s in enumerate(SEQ)],
                               hovertemplate="%{y} × %{x}: %{z:,}<extra></extra>", xgap=2, ygap=2))
    fig.update_layout(title=title)
    fig.update_yaxes(autorange="reversed")
    show(fig, height=max(340, 28 * len(r) + 120))


# ---------- table + download ----------
def table(df: pd.DataFrame, cols: list[str], filename: str, link_cols: dict[str, str] | None = None,
          max_rows: int = 5000) -> None:
    cols = [c for c in cols if c in df.columns]
    view = df[cols]
    st.subheader("Data table")
    st.caption(f"{len(view):,} rows match the filters. Click a column header to sort."
               + (f" Showing the first {max_rows:,}; the CSV holds them all." if len(view) > max_rows else ""))
    cfg = {}
    for c, label in (link_cols or {}).items():
        if c in cols:
            cfg[c] = st.column_config.LinkColumn(label, display_text="open")
    st.dataframe(view.head(max_rows), use_container_width=True, hide_index=True, column_config=cfg, height=420)
    st.download_button("Download filtered view as CSV", view.to_csv(index=False).encode("utf-8"),
                       file_name=f"{filename}.csv", mime="text/csv", type="primary")


# ---------- about ----------
def about(keys: list[str], extra: str | None = None) -> None:
    with st.expander("About the data", expanded=False):
        if extra:
            st.markdown(extra)
        for k in keys:
            m = meta(k)
            st.markdown(f"### {m['title']}")
            links = " · ".join(f"[{n}]({u})" for n, u in m["links"].items() if u)
            st.markdown(links + f" · [All datasets (GitHub index)]({GITHUB_INDEX})")
            if m.get("acquisition"):
                st.markdown(m["acquisition"])
            if m.get("sample_note"):
                st.markdown("**Coverage.** " + m["sample_note"])
            if m.get("findings"):
                st.markdown("**Key findings (computed on the full data)**")
                st.markdown(m["findings"])
            if m.get("method"):
                st.markdown("**Method**")
                st.markdown(m["method"])
            if m.get("limitations"):
                st.markdown("**Limitations**")
                st.markdown(m["limitations"])
            if m.get("withheld"):
                st.markdown("**Not in the free sample:** " + "; ".join(m["withheld"]) + ".")
        st.markdown(f"**Licence** [{LICENCE}]({LICENCE_URL}), attribution *Fliar BI*. "
                    f"Questions, full data or API access: [{CONTACT}](mailto:{CONTACT}).")


def footer() -> None:
    st.divider()
    st.caption(f"Data by [Fliar BI](https://fliarbi.com) · licence [{LICENCE}]({LICENCE_URL}) · "
               f"[All datasets]({GITHUB_INDEX}) · [App source]({REPO}) · contact {CONTACT}")


def dataset_picker(options: dict[str, str], label: str = "Dataset") -> str:
    """options: display label -> dataset key. Returns the key."""
    lab = st.sidebar.radio(label, list(options.keys()))
    return options[lab]


def explode_counts(s: pd.Series, sep: str = "|", n: int = 20) -> pd.Series:
    """Count items in a delimiter-separated text column (skills, technologies)."""
    t = s.dropna().astype(str)
    t = t[t.str.strip() != ""]
    if t.empty:
        return pd.Series(dtype="int64")
    return t.str.split(sep, regex=False).explode().str.strip().loc[lambda x: x != ""].value_counts().head(n)


def bar_series(s: pd.Series, title: str, money_axis: bool = False, prefix: str = "$", fmt: str = ",.0f") -> None:
    if s.empty:
        st.info(f"No data for: {title}")
        return
    s = s[::-1]
    fig = go.Figure(go.Bar(x=s.values, y=s.index.astype(str), orientation="h", marker_color=BLUE,
                           hovertemplate=f"%{{y}}: %{{x:{fmt}}}<extra></extra>"))
    fig.update_layout(title=title, bargap=0.25)
    if money_axis:
        fig.update_xaxes(tickprefix=prefix)
    show(fig, height=max(320, 26 * len(s) + 90))


def about_bundle(theme: str, links: dict[str, str] | None = None, related: list[str] | None = None) -> None:
    """About-the-data for an aggregate bundle: its README (method, coverage, caveats) plus links."""
    from common.data import ROOT
    p = ROOT / "data" / theme / "README.md"
    with st.expander("About the data", expanded=False):
        if p.exists():
            txt = p.read_text(encoding="utf-8")
            txt = "\n".join(l for l in txt.splitlines() if not l.startswith("# "))
            st.markdown(txt)
        if links:
            st.markdown(" · ".join(f"[{n}]({u})" for n, u in links.items() if u))
        if related:
            st.markdown("**Related free datasets:** " + " · ".join(
                f"[{meta(k)['title']}](https://fliarbi.com/datasets/{k}/)" for k in related))
        st.markdown(f"[All datasets (GitHub index)]({GITHUB_INDEX}) · [Fliar dataset hub](https://fliarbi.com/datasets/)")
        st.markdown(f"**Licence** [{LICENCE}]({LICENCE_URL}), attribution *Fliar BI*. "
                    f"Questions, full data or API access: [{CONTACT}](mailto:{CONTACT}).")
