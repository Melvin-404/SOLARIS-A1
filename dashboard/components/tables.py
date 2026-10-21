"""Formatted table display helpers for SOLARIS-A1 dashboard (Stage 12)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import pandas as pd
import streamlit as st


def render_dataframe_with_status(
    df: pd.DataFrame,
    status_col: Optional[str] = "status",
    empty_message: str = "No records to display.",
) -> None:
    """Render a DataFrame with clear empty-state handling and standard formatting."""
    if df is None or df.empty:
        st.info(empty_message)
        return

    # Style status column if present
    st.dataframe(df, use_container_width=True)


def render_dict_as_metrics_cards(metrics_dict: Dict[str, Any], columns: int = 4) -> None:
    """Render dictionary items as Streamlit metric cards."""
    cols = st.columns(columns)
    for idx, (k, v) in enumerate(metrics_dict.items()):
        col = cols[idx % columns]
        val_str = f"{v:.4f}" if isinstance(v, float) else str(v)
        col.metric(label=k.replace("_", " ").title(), value=val_str)
