"""Data loading: published HF parquet samples and the small aggregate bundles committed under data/."""
from __future__ import annotations

import io
import json
import os
import urllib.request
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
META = json.loads((ROOT / "common" / "meta.json").read_text(encoding="utf-8"))
# For offline tests: a directory holding <key>.parquet copies of the published files.
LOCAL_DIR = os.environ.get("FLIAR_PARQUET_DIR")


def meta(key: str) -> dict:
    return META[key]


def _fetch(key: str) -> bytes | str:
    if LOCAL_DIR and (Path(LOCAL_DIR) / f"{key}.parquet").exists():
        return str(Path(LOCAL_DIR) / f"{key}.parquet")
    req = urllib.request.Request(META[key]["parquet"], headers={"User-Agent": "fliar-streamlit-apps/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def _shrink(df: pd.DataFrame) -> pd.DataFrame:
    """Low-cardinality text columns become categoricals to keep memory small."""
    for c in df.columns:
        if df[c].dtype == object or str(df[c].dtype).startswith("string"):
            if df[c].nunique(dropna=True) < max(50, len(df) // 4):
                df[c] = df[c].astype("category")
            else:
                df[c] = df[c].astype(object)
    return df


@st.cache_data(show_spinner="Loading the published sample from Hugging Face ...", ttl=24 * 3600, max_entries=8)
def load(key: str, columns: tuple[str, ...]) -> pd.DataFrame:
    """Read only the needed columns of a published dataset sample."""
    src = _fetch(key)
    f = io.BytesIO(src) if isinstance(src, bytes) else src
    pf = pq.ParquetFile(f)
    cols = [c for c in columns if c in pf.schema_arrow.names]
    df = pf.read(columns=cols).to_pandas()
    del src
    return _shrink(df)


@st.cache_data(show_spinner=False, max_entries=32)
def load_bundle(theme: str, name: str) -> pd.DataFrame:
    """Read an aggregate parquet committed under data/<theme>/<name>.parquet."""
    return pd.read_parquet(ROOT / "data" / theme / f"{name}.parquet")


def bundle_names(theme: str) -> list[str]:
    d = ROOT / "data" / theme
    return sorted(p.stem for p in d.glob("*.parquet")) if d.exists() else []
