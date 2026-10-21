"""Reusable status banners and scientific disclaimers for SOLARIS-A1 dashboard (Stage 12)."""

from __future__ import annotations

from typing import Optional
import streamlit as st


PERSISTENT_SIDEBAR_DISCLAIMER = (
    "Candidate bursts are not verified solar flares. "
    "Pilot and provisional results are not validated detector performance."
)


def get_banner_text(status: str, message: str, context: Optional[str] = None) -> str:
    """Format standard banner text based on artifact status code."""
    status_upper = status.upper()
    prefix = f"[{context}] " if context else ""

    if status_upper == "PROVISIONAL":
        return f"{prefix}⚠️ **PROVISIONAL STATUS**: {message} (Pending human researcher approval at designated gate)."
    elif status_upper == "PILOT":
        return f"{prefix}🔬 **PILOT EXPERIMENT**: {message} (Single-day dataset; does not establish general detector performance)."
    elif status_upper == "UNVERIFIED":
        return f"{prefix}🔍 **CANDIDATE — UNVERIFIED**: {message} (Heuristic statistical detections are NOT ground-truth labels)."
    elif status_upper == "MISSING":
        return f"{prefix}ℹ️ **ARTIFACT MISSING**: {message}"
    elif status_upper == "STALE":
        return f"{prefix}⏳ **STALE ARTIFACT**: {message} (Upstream pipeline changes detected)."
    elif status_upper == "ERROR":
        return f"{prefix}❌ **ARTIFACT PARSING ERROR**: {message}"
    elif status_upper == "EMPTY":
        return f"{prefix}ℹ️ **EMPTY ARTIFACT**: {message}"
    elif status_upper == "OK":
        return f"{prefix}✅ **CONFIRMED**: {message}"
    else:
        return f"{prefix}ℹ️ **{status_upper}**: {message}"


def render_status_banner(status: str, message: str, context: Optional[str] = None) -> None:
    """Render an appropriate Streamlit alert box matching the scientific status code."""
    text = get_banner_text(status, message, context)
    status_upper = status.upper()

    if status_upper in {"PROVISIONAL", "UNVERIFIED", "STALE"}:
        st.warning(text)
    elif status_upper in {"PILOT", "MISSING", "EMPTY"}:
        st.info(text)
    elif status_upper == "ERROR":
        st.error(text)
    elif status_upper == "OK":
        st.success(text)
    else:
        st.info(text)


def render_sidebar_disclaimer() -> None:
    """Render persistent scientific governance disclaimer in Streamlit sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.caption(PERSISTENT_SIDEBAR_DISCLAIMER)
