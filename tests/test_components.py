"""Unit tests for dashboard presentation components (Stage 12).

Tests:
1. Status banner text and formatting for PROVISIONAL, PILOT, UNVERIFIED, MISSING, ERROR, OK.
2. Persistent sidebar governance disclaimer contents.
3. Light-curve and feature histogram Plotly figure generators.
"""

import pandas as pd
import pytest
from dashboard.components.banner import (
    PERSISTENT_SIDEBAR_DISCLAIMER,
    get_banner_text,
)
from dashboard.components.figures import (
    build_feature_histogram,
    build_light_curve_figure,
)


def test_status_banner_text_mapping():
    """Verify standard status banner text across all status codes."""
    assert "PROVISIONAL STATUS" in get_banner_text("PROVISIONAL", "Awaiting approval")
    assert "PILOT EXPERIMENT" in get_banner_text("PILOT", "Single-day run")
    assert "CANDIDATE — UNVERIFIED" in get_banner_text("UNVERIFIED", "Heuristic bursts")
    assert "ARTIFACT MISSING" in get_banner_text("MISSING", "File not found")
    assert "ARTIFACT PARSING ERROR" in get_banner_text("ERROR", "Corrupt file")
    assert "CONFIRMED" in get_banner_text("OK", "Approved records")


def test_sidebar_disclaimer_content():
    """Verify persistent sidebar disclaimer contains mandatory scientific warnings."""
    assert "not verified solar flares" in PERSISTENT_SIDEBAR_DISCLAIMER
    assert "Pilot and provisional results are not validated detector performance" in PERSISTENT_SIDEBAR_DISCLAIMER


def test_figure_builders():
    """Verify Plotly figure generation for light curves and histograms."""
    # Synthetic light curve
    df_lc = pd.DataFrame({
        "time": [10.0, 20.0, 30.0, 40.0],
        "counts": [5.0, 15.0, 25.0, 0.0],
    })
    fig_lc, downsampled = build_light_curve_figure(df_lc, show_flagged=True)
    assert fig_lc is not None
    assert downsampled is False
    assert len(fig_lc.data) >= 1  # Contains at least primary scatter line

    # Synthetic histogram
    df_feat = pd.DataFrame({"ratio_to_base": [1.0, 1.5, 2.0, 4.0, 5.0]})
    fig_hist = build_feature_histogram(df_feat, "ratio_to_base", nbins=5)
    assert fig_hist is not None
    assert len(fig_hist.data) >= 1
