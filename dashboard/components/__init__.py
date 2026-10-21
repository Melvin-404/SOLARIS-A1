"""Dashboard presentation components package for SOLARIS-A1 (Stage 12)."""

from dashboard.components.banner import (
    PERSISTENT_SIDEBAR_DISCLAIMER,
    get_banner_text,
    render_sidebar_disclaimer,
    render_status_banner,
)
from dashboard.components.figures import (
    build_feature_histogram,
    build_light_curve_figure,
)
from dashboard.components.tables import (
    render_dataframe_with_status,
    render_dict_as_metrics_cards,
)

__all__ = [
    "PERSISTENT_SIDEBAR_DISCLAIMER",
    "get_banner_text",
    "render_sidebar_disclaimer",
    "render_status_banner",
    "build_light_curve_figure",
    "build_feature_histogram",
    "render_dataframe_with_status",
    "render_dict_as_metrics_cards",
]
