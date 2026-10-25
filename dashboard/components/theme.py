"""Solar-science dark observatory design system for SOLARIS-A1 dashboard."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional
import streamlit as st


def get_solar_hero_image_b64() -> str:
    """Return base64 encoded string of authentic NASA SDO AIA 171 solar observation image."""
    asset_dir = Path(__file__).resolve().parent.parent / "assets"
    for name in ["solar_sdo_aia_171.png", "solar_sdo_aia_171.jpg"]:
        asset_path = asset_dir / name
        if asset_path.is_file():
            return base64.b64encode(asset_path.read_bytes()).decode("ascii")
    return ""


def find_sun_4k_video_file() -> Optional[Path]:
    """Locate the authentic SUN 4k video file in Downloads or project assets."""
    downloads_dir = Path.home() / "Downloads"
    if downloads_dir.is_dir():
        target = downloads_dir / "sun-4k-video-ytmp4.savetube.vip.mp4"
        if target.is_file() and target.stat().st_size > 0:
            return target
        for p in downloads_dir.glob("*[Ss][Uu][Nn]*4[Kk]*.mp4"):
            if p.is_file() and p.stat().st_size > 0:
                return p

    base_dir = Path(__file__).resolve().parent.parent
    for candidate in [
        base_dir / "static" / "sun_4k_video.mp4",
        base_dir / "assets" / "sun_4k_video.mp4",
        base_dir / "static" / "sun-4k-video-ytmp4.savetube.vip.mp4",
        base_dir / "assets" / "sun-4k-video-ytmp4.savetube.vip.mp4",
    ]:
        if candidate.is_file() and candidate.stat().st_size > 0:
            return candidate
    return None


@st.cache_data
def get_solar_hero_video_b64() -> Optional[str]:
    """Return base64 encoded string of authentic SUN 4k video file."""
    vid_path = find_sun_4k_video_file()
    if vid_path and vid_path.is_file() and vid_path.stat().st_size > 0:
        return base64.b64encode(vid_path.read_bytes()).decode("ascii")
    return None


def get_solar_hero_video_url() -> Optional[str]:
    """Return static URL path of authentic SUN 4k video if present."""
    base_dir = Path(__file__).resolve().parent.parent
    for p in [
        base_dir / "static" / "sun_4k_video.mp4",
        base_dir / "assets" / "sun_4k_video.mp4",
    ]:
        if p.is_file() and p.stat().st_size > 0:
            return f"app/static/{p.name}"
    return None


def get_solar_hero_image_url() -> Optional[str]:
    """Return static URL path of authentic NASA SDO solar image if present."""
    base_dir = Path(__file__).resolve().parent.parent
    for p in [
        base_dir / "static" / "solar_sdo_aia_171.png",
        base_dir / "static" / "solar_sdo_aia_171.jpg",
        base_dir / "assets" / "solar_sdo_aia_171.png",
        base_dir / "assets" / "solar_sdo_aia_171.jpg",
    ]:
        if p.is_file() and p.stat().st_size > 0:
            return f"app/static/{p.name}"
    return None



def apply_space_weather_theme() -> None:
    """Inject refined solar observatory CSS styling into Streamlit page."""
    custom_css = """
    <style>
    /* SOLARIS-A1 Dark Solar Observatory Design System */
    :root {
        --space-deep: #070B14;
        --space-surface: #0E1526;
        --space-surface-hover: #151F36;
        --border-subtle: #1E293B;
        --border-accent: rgba(245, 158, 11, 0.35);
        
        /* Solar Spectrum Accents */
        --solar-gold: #F59E0B;
        --solar-gold-light: #FBBF24;
        --solar-amber: #D97706;
        --solar-orange: #EA580C;
        --solar-corona: rgba(245, 158, 11, 0.45);
        
        /* Scientific Status Colors */
        --science-blue: #38BDF8;
        --status-ok: #10B981;
        --status-warning: #F59E0B;
        --status-danger: #EF4444;
        
        /* Text Hierarchy */
        --text-primary: #F8FAFC;
        --text-secondary: #CBD5E1;
        --text-muted: #94A3B8;
        --text-faint: #64748B;
    }

    /* Overall page background and base text with ambient solar illumination */
    .stApp {
        background-color: var(--space-deep);
        background-image: 
            radial-gradient(circle 800px at 78% 230px, rgba(245, 158, 11, 0.13) 0%, rgba(217, 119, 6, 0.07) 32%, rgba(234, 88, 12, 0.025) 55%, transparent 80%),
            radial-gradient(circle 1000px at 82% 280px, rgba(245, 158, 11, 0.05) 0%, transparent 70%);
        background-repeat: no-repeat;
        color: var(--text-primary);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }

    /* Typography — Comfortable & Hierarchical (Desktop Target: ~17px body, 36px H1, 25px H2) */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary);
        font-weight: 700;
        letter-spacing: -0.015em;
    }

    h1 {
        font-size: 2.25rem !important; /* ~36px */
        font-weight: 700 !important;
        border-bottom: none !important;
        padding-bottom: 0 !important;
        margin: 0 0 0.50rem 0 !important;
        line-height: 1.26 !important;
    }

    h2 {
        font-size: 1.55rem !important; /* ~24.8px */
        font-weight: 600 !important;
        margin-top: 1.30rem !important;
        margin-bottom: 0.45rem !important;
        line-height: 1.30 !important;
    }

    h3 {
        font-size: 1.28rem !important; /* ~20.5px */
        font-weight: 600 !important;
        color: var(--solar-gold-light) !important;
        margin-top: 1.05rem !important;
        margin-bottom: 0.35rem !important;
        line-height: 1.32 !important;
    }

    h4 {
        font-size: 1.10rem !important; /* ~17.6px */
        font-weight: 600 !important;
        margin-top: 0.80rem !important;
        margin-bottom: 0.25rem !important;
        line-height: 1.40 !important;
    }

    p, .stMarkdown p, .stText {
        font-size: 1.05rem !important; /* ~16.8px desktop body */
        margin-bottom: 0.65rem !important;
        line-height: 1.62 !important;
        color: var(--text-primary);
    }

    div[data-testid="stCaptionContainer"], .stCaption {
        margin-top: 0.25rem !important;
        margin-bottom: 0.60rem !important;
        font-size: 0.92rem !important; /* ~14.7px */
        color: var(--text-muted) !important;
        line-height: 1.52 !important;
    }

    /* Widget Labels (Selectbox, Slider, Radio, Text Input) */
    label[data-testid="stWidgetLabel"],
    div[data-testid="stWidgetLabel"] p,
    .stSelectbox label,
    .stSlider label,
    .stRadio label {
        font-size: 1.0rem !important; /* ~16px */
        font-weight: 600 !important;
        color: #F1F5F9 !important;
        margin-bottom: 5px !important;
    }

    /* Radio button options text */
    div[data-testid="stRadio"] label p,
    div[data-testid="stCheckbox"] label p {
        font-size: 0.98rem !important;
        line-height: 1.45 !important;
    }

    /* Header Horizontal Divider */
    .header-divider,
    hr.header-divider {
        margin: 12px 0 20px 0 !important;
        border: 0 !important;
        border-top: 1px solid var(--border-subtle) !important;
        width: 100% !important;
    }

    /* Section Horizontal Rules */
    hr {
        margin: 16px 0 18px 0 !important;
        border: 0 !important;
        border-top: 1px solid rgba(30, 41, 59, 0.6) !important;
    }

    /* Scientific Safeguard Callout Box (Restrained Dark Navy) */
    .scientific-safeguard-card {
        background-color: #0B1322 !important;
        border: 1px solid #1E293B !important;
        border-left: 3px solid #EF4444 !important;
        border-radius: 6px !important;
        padding: 14px 18px !important;
        margin-bottom: 18px !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25) !important;
    }
    .scientific-safeguard-card .safeguard-title {
        color: #F87171 !important;
        font-size: 0.92rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.03em !important;
        margin-bottom: 6px !important;
        line-height: 1.35 !important;
    }
    .scientific-safeguard-card .safeguard-text {
        margin: 0 !important;
        color: #CBD5E1 !important;
        font-size: 0.92rem !important;
        line-height: 1.60 !important;
    }
    .scientific-safeguard-card .safeguard-text strong {
        color: #F1F5F9 !important;
    }

    /* Alert Banners — Comfortable Observatory Style */
    div[data-testid="stAlert"] {
        padding: 10px 16px !important;
        border-radius: 6px !important;
        margin: 6px 0 12px 0 !important;
    }
    div[data-testid="stAlert"] div[role="alert"] {
        font-size: 0.92rem !important;
        line-height: 1.50 !important;
    }

    /* Global Block Spacing */
    [data-testid="stVerticalBlock"] {
        gap: 0.75rem !important;
    }
    [data-testid="stHorizontalBlock"] {
        gap: 0.90rem !important;
        align-items: stretch !important;
    }

    /* Metric Cards — Anti-Truncation & Clear Responsive Typography */
    div[data-testid="stMetric"] {
        background: var(--space-surface) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 8px !important;
        padding: 14px 18px !important;
        min-height: 104px !important;
        height: auto !important;
        overflow: visible !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25) !important;
        transition: border-color 0.2s ease, transform 0.15s ease !important;
    }

    div[data-testid="stMetric"]:hover {
        border-color: var(--border-accent) !important;
        transform: translateY(-1px) !important;
    }

    div[data-testid="stMetricValue"] {
        font-weight: 700 !important;
        color: var(--solar-gold-light) !important;
        font-family: "SF Mono", Monaco, "Cascadia Code", monospace !important;
        font-size: 1.70rem !important; /* ~27px */
        white-space: normal !important;
        overflow: visible !important;
        word-break: break-word !important;
        line-height: 1.22 !important;
    }
    div[data-testid="stMetricValue"] > div {
        overflow: visible !important;
        white-space: normal !important;
    }

    div[data-testid="stMetricLabel"] {
        color: var(--text-muted) !important;
        font-size: 0.88rem !important; /* ~14px */
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.04em !important;
        white-space: normal !important;
        overflow: visible !important;
        word-break: break-word !important;
        line-height: 1.30 !important;
        margin-bottom: 2px !important;
    }
    div[data-testid="stMetricLabel"] > div,
    div[data-testid="stMetricLabel"] span {
        overflow: visible !important;
        white-space: normal !important;
        text-overflow: clip !important;
        word-break: break-word !important;
    }

    div[data-testid="stMetricDelta"] {
        font-size: 0.84rem !important; /* ~13.5px */
        white-space: normal !important;
        overflow: visible !important;
        word-break: break-word !important;
        line-height: 1.30 !important;
        margin-top: 3px !important;
        display: flex !important;
        align-items: flex-start !important;
    }
    div[data-testid="stMetricDelta"] svg {
        flex-shrink: 0 !important;
        margin-top: 2px !important;
    }
    div[data-testid="stMetricDelta"] > div,
    div[data-testid="stMetricDelta"] span,
    div[data-testid="stMetricDelta"] * {
        overflow: visible !important;
        white-space: normal !important;
        text-overflow: unset !important;
        word-break: break-word !important;
    }

    /* Data Status Badges */
    .badge-simulation {
        background-color: rgba(245, 158, 11, 0.12);
        color: #F59E0B;
        border: 1px solid rgba(245, 158, 11, 0.40);
        border-radius: 4px;
        padding: 3px 9px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        display: inline-block;
    }
    .badge-historical {
        background-color: rgba(56, 189, 248, 0.12);
        color: #38BDF8;
        border: 1px solid rgba(56, 189, 248, 0.35);
        border-radius: 4px;
        padding: 3px 9px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        display: inline-block;
    }

    .badge-verified {
        background-color: rgba(16, 185, 129, 0.12);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.35);
        border-radius: 4px;
        padding: 3px 9px;
        font-size: 0.78rem;
        font-weight: 600;
        display: inline-block;
    }

    .badge-unverified {
        background-color: rgba(245, 158, 11, 0.12);
        color: #FBBF24;
        border: 1px solid rgba(245, 158, 11, 0.35);
        border-radius: 4px;
        padding: 3px 9px;
        font-size: 0.78rem;
        font-weight: 600;
        display: inline-block;
    }

    /* Top block container padding ensuring complete visibility beneath Streamlit header */
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 2.875rem !important;
        z-index: 99 !important;
    }

    [data-testid="stMain"] .block-container,
    .stMain .block-container,
    .block-container {
        padding-top: 2.2rem !important;
        padding-bottom: 2.8rem !important;
        padding-left: 2.0rem !important;
        padding-right: 2.0rem !important;
        max-width: 1460px !important;
        width: 100% !important;
    }

    /* Scientific Card Containers */
    .scientific-card {
        background: var(--space-surface);
        border: 1px solid var(--border-subtle);
        border-radius: 6px;
        padding: 12px 15px;
        margin-bottom: 10px;
    }

    .scientific-card-accent {
        background: var(--space-surface);
        border: 1px solid var(--border-subtle);
        border-left: 3px solid var(--solar-gold);
        border-radius: 6px;
        padding: 12px 15px;
        margin-bottom: 10px;
    }

    /* DataFrames & Expanders Compact Design */
    div[data-testid="stDataFrame"],
    div[data-testid="stTable"] {
        border: 1px solid var(--border-subtle) !important;
        border-radius: 6px !important;
        overflow-x: auto !important;
    }
    div[data-testid="stExpander"] {
        border: 1px solid var(--border-subtle) !important;
        border-radius: 6px !important;
        background: rgba(14, 21, 38, 0.5) !important;
        margin-bottom: 8px !important;
    }
    div[data-testid="stExpander"] details summary {
        padding: 8px 12px !important;
        font-size: 0.96rem !important;
        font-weight: 600 !important;
    }

    /* Solar Hero Styles */
    .hero-left-content {
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding-top: 8px;
        overflow: visible !important;
    }

    .hero-eyebrow {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: #38BDF8;
        margin-bottom: 8px;
        display: inline-block;
        line-height: 1.3;
    }

    .hero-main-title {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 3.30rem !important; /* ~15% increase */
        font-weight: 800;
        letter-spacing: -0.035em;
        background: linear-gradient(135deg, #FFFFFF 35%, #FDE68A 80%, #F59E0B 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.15 !important;
        margin: 0 0 10px 0;
        border: none !important;
        padding-top: 6px !important;
        padding-bottom: 4px !important;
        overflow: visible !important;
        filter: drop-shadow(0 2px 20px rgba(245, 158, 11, 0.20));
    }

    .hero-headline {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 1.30rem;
        font-weight: 600;
        color: var(--solar-gold-light);
        letter-spacing: -0.015em;
        margin: 0 0 14px 0;
        line-height: 1.35;
        border: none !important;
    }

    .hero-summary {
        font-size: 1.02rem;
        color: #CBD5E1;
        line-height: 1.58;
        margin: 0 0 6px 0;
        max-width: 620px;
    }

    .hero-button-spacer {
        height: 22px;
        width: 100%;
    }

    /* Solar Hero Animated Sun Integration */
    .hero-sun-wrapper {
        width: 100%;
        max-width: 385px;
        aspect-ratio: 1 / 1;
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto;
    }

    /* Diffuse Ambient Golden Solar Glow extending into the page */
    .hero-sun-glow-ambient {
        position: absolute;
        width: 490px;
        height: 490px;
        border-radius: 50%;
        background: radial-gradient(
            circle,
            rgba(245, 158, 11, 0.13) 0%,
            rgba(217, 119, 6, 0.07) 35%,
            rgba(234, 88, 12, 0.02) 60%,
            transparent 80%
        );
        filter: blur(42px);
        pointer-events: none;
        z-index: 0;
    }

    /* Warm Solar Coronal Core Glow with gentle breathing pulsation */
    .hero-sun-glow-core {
        position: absolute;
        width: 350px;
        height: 350px;
        border-radius: 50%;
        background: radial-gradient(
            circle,
            rgba(251, 191, 36, 0.28) 0%,
            rgba(245, 158, 11, 0.20) 25%,
            rgba(217, 119, 6, 0.10) 48%,
            rgba(234, 88, 12, 0.035) 68%,
            transparent 82%
        );
        filter: blur(20px);
        pointer-events: none;
        z-index: 1;
        animation: solarGlowBreathe 7s ease-in-out infinite;
    }

    @keyframes solarGlowBreathe {
        0%, 100% {
            transform: scale(0.97);
            opacity: 0.85;
            filter: blur(20px);
        }
        50% {
            transform: scale(1.05);
            opacity: 1.0;
            filter: blur(24px);
        }
    }

    /* Seamless Blend Animated Sun Video */
    .hero-sun-video {
        position: relative;
        z-index: 2;
        width: 100%;
        max-width: 350px;
        height: auto;
        aspect-ratio: 1 / 1;
        object-fit: contain;
        mix-blend-mode: screen;
        filter: drop-shadow(0 0 28px rgba(245, 158, 11, 0.45));
        pointer-events: none;
        mask-image: radial-gradient(circle at 50% 50%, #000 60%, rgba(0, 0, 0, 0.85) 76%, transparent 97%);
        -webkit-mask-image: radial-gradient(circle at 50% 50%, #000 60%, rgba(0, 0, 0, 0.85) 76%, transparent 97%);
        border: none !important;
        outline: none !important;
        background: transparent !important;
        display: block;
    }

    /* Compact Metadata Strip below hero */
    .hero-metadata-strip {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: flex-start;
        gap: 16px;
        padding: 9px 16px;
        margin-top: 10px;
        margin-bottom: 16px;
        background: rgba(14, 21, 38, 0.7);
        border: 1px solid rgba(30, 41, 59, 0.8);
        border-top: 1px solid rgba(245, 158, 11, 0.25);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25), 0 -2px 12px rgba(245, 158, 11, 0.04);
        border-radius: 6px;
        font-size: 0.86rem;
        color: #94A3B8;
    }

    .hero-metadata-strip .meta-item {
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }

    .hero-metadata-strip .meta-item strong {
        color: #E2E8F0;
    }

    .hero-metadata-strip .meta-dot {
        color: #F59E0B;
        font-size: 0.70rem;
    }

    .hero-metadata-strip .meta-sep {
        color: #475569;
    }

    /* Accessible and prominent action buttons in hero */
    [data-testid="stMain"] div[data-testid="stPageLink"] a[href*="Light_Curves"],
    [data-testid="stMain"] div[data-testid="stPageLink"] a[href*="Model_Results"],
    [data-testid="stMain"] a[href*="Light_Curves"],
    [data-testid="stMain"] a[href*="Model_Results"] {
        border-radius: 8px !important;
        padding: 10px 14px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
        text-decoration: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 8px !important;
    }
    [data-testid="stMain"] div[data-testid="stPageLink"] a[href*="Light_Curves"],
    [data-testid="stMain"] a[href*="Light_Curves"] {
        background: linear-gradient(135deg, rgba(56, 189, 248, 0.12) 0%, #0E1526 100%) !important;
        border: 1px solid rgba(56, 189, 248, 0.45) !important;
    }
    [data-testid="stMain"] div[data-testid="stPageLink"] a[href*="Light_Curves"]:hover,
    [data-testid="stMain"] a[href*="Light_Curves"]:hover {
        background: linear-gradient(135deg, rgba(56, 189, 248, 0.22) 0%, #151F36 100%) !important;
        border-color: #38BDF8 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 14px rgba(56, 189, 248, 0.25) !important;
    }
    [data-testid="stMain"] div[data-testid="stPageLink"] a[href*="Model_Results"],
    [data-testid="stMain"] a[href*="Model_Results"] {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.12) 0%, #0E1526 100%) !important;
        border: 1px solid rgba(245, 158, 11, 0.45) !important;
    }
    [data-testid="stMain"] div[data-testid="stPageLink"] a[href*="Model_Results"]:hover,
    [data-testid="stMain"] a[href*="Model_Results"]:hover {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.22) 0%, #151F36 100%) !important;
        border-color: #F59E0B !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 14px rgba(245, 158, 11, 0.25) !important;
    }
    [data-testid="stMain"] div[data-testid="stPageLink"] a[href*="Light_Curves"] p,
    [data-testid="stMain"] div[data-testid="stPageLink"] a[href*="Model_Results"] p,
    [data-testid="stMain"] a[href*="Light_Curves"] p,
    [data-testid="stMain"] a[href*="Model_Results"] p {
        color: #F8FAFC !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        margin: 0 !important;
        text-decoration: none !important;
        white-space: nowrap !important;
    }
    [data-testid="stMain"] div[data-testid="stPageLink"] a[href*="Light_Curves"]:hover p,
    [data-testid="stMain"] a[href*="Light_Curves"]:hover p {
        color: #38BDF8 !important;
    }
    [data-testid="stMain"] div[data-testid="stPageLink"] a[href*="Model_Results"]:hover p,
    [data-testid="stMain"] a[href*="Model_Results"]:hover p {
        color: #FBBF24 !important;
    }

    /* SOLARIS-A1 OBSERVATORY LEFT SIDEBAR DESIGN */
    [data-testid="stSidebar"] {
        background-color: #0A0F1D !important;
        border-right: 1px solid #1E293B !important;
        min-width: 250px !important;
        max-width: 285px !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        background-color: #0A0F1D !important;
        padding-top: 0.8rem !important;
    }
    [data-testid="stSidebarNav"] {
        padding-top: 0.3rem !important;
        padding-bottom: 0.4rem !important;
    }
    [data-testid="stSidebarNav"] ul {
        gap: 3px !important;
        padding-left: 0 !important;
    }

    /* Sidebar Navigation Links */
    [data-testid="stSidebarNavLink"] {
        border-radius: 6px !important;
        padding: 7px 12px !important;
        margin: 2px 0 !important;
        color: #94A3B8 !important;
        font-size: 0.92rem !important;
        font-weight: 500 !important;
        border-left: 3px solid transparent !important;
        transition: all 0.15s ease !important;
        display: flex !important;
        align-items: center !important;
    }
    [data-testid="stSidebarNavLink"]:hover {
        background: #111A2E !important;
        color: #F1F5F9 !important;
        border-left-color: rgba(56, 189, 248, 0.4) !important;
    }
    [data-testid="stSidebarNavLink"][aria-current="page"] {
        background: #131E38 !important;
        color: #F8FAFC !important;
        font-weight: 600 !important;
        border-left: 3px solid #38BDF8 !important;
        box-shadow: inset 0 0 10px rgba(56, 189, 248, 0.08) !important;
    }
    [data-testid="stSidebarNavLink"][aria-current="page"] span {
        color: #F8FAFC !important;
    }

    /* Streamlit Root App Label Clean Name */
    [data-testid="stSidebarNavLink"][href$="/"] {
        overflow: visible !important;
    }
    [data-testid="stSidebarNavLink"][href$="/"] span {
        visibility: hidden !important;
        position: relative !important;
        display: inline-block !important;
        overflow: visible !important;
        width: 150px !important;
    }
    [data-testid="stSidebarNavLink"][href$="/"] span::after {
        visibility: visible !important;
        position: absolute !important;
        left: 0 !important;
        top: 0 !important;
        content: "Observatory Home" !important;
        font-size: 0.92rem !important;
        font-weight: inherit !important;
        white-space: nowrap !important;
        overflow: visible !important;
    }

    /* Clean Scientific Monochrome SVG Icons for Navigation Items */
    [data-testid="stSidebarNavLink"]::before {
        content: "";
        display: inline-block;
        width: 15px;
        height: 15px;
        margin-right: 10px;
        vertical-align: middle;
        background-color: currentColor;
        -webkit-mask-size: contain;
        mask-size: contain;
        -webkit-mask-repeat: no-repeat;
        mask-repeat: no-repeat;
        -webkit-mask-position: center;
        mask-position: center;
        flex-shrink: 0;
    }

    /* Home / App: Solar Starburst */
    [data-testid="stSidebarNavLink"][href$="/"]::before {
        -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='4'/%3E%3Cpath d='M12 2v2'/%3E%3Cpath d='M12 20v2'/%3E%3Cpath d='m4.93 4.93 1.41 1.41'/%3E%3Cpath d='m17.66 17.66 1.41 1.41'/%3E%3Cpath d='M2 12h2'/%3E%3Cpath d='M20 12h2'/%3E%3Cpath d='m6.34 17.66-1.41 1.41'/%3E%3Cpath d='m19.07 4.93-1.41 1.41'/%3E%3C/svg%3E");
        mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='4'/%3E%3Cpath d='M12 2v2'/%3E%3Cpath d='M12 20v2'/%3E%3Cpath d='m4.93 4.93 1.41 1.41'/%3E%3Cpath d='m17.66 17.66 1.41 1.41'/%3E%3Cpath d='M2 12h2'/%3E%3Cpath d='M20 12h2'/%3E%3Cpath d='m6.34 17.66-1.41 1.41'/%3E%3Cpath d='m19.07 4.93-1.41 1.41'/%3E%3C/svg%3E");
    }

    /* Overview: Compass / Scope */
    [data-testid="stSidebarNavLink"][href*="Overview"]::before {
        -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'/%3E%3Cpolygon points='16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76'/%3E%3C/svg%3E");
        mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'/%3E%3Cpolygon points='16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76'/%3E%3C/svg%3E");
    }

    /* Dataset: Database / Archives */
    [data-testid="stSidebarNavLink"][href*="Dataset"]::before {
        -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cellipse cx='12' cy='5' rx='9' ry='3'/%3E%3Cpath d='M21 12c0 1.66-4 3-9 3s-9-1.34-9-3'/%3E%3Cpath d='M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5'/%3E%3C/svg%3E");
        mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cellipse cx='12' cy='5' rx='9' ry='3'/%3E%3Cpath d='M21 12c0 1.66-4 3-9 3s-9-1.34-9-3'/%3E%3Cpath d='M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5'/%3E%3C/svg%3E");
    }

    /* Data Quality: Shield Check */
    [data-testid="stSidebarNavLink"][href*="Data_Quality"]::before {
        -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z'/%3E%3Cpath d='m9 12 2 2 4-4'/%3E%3C/svg%3E");
        mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z'/%3E%3Cpath d='m9 12 2 2 4-4'/%3E%3C/svg%3E");
    }

    /* Light Curves: Activity Waveform */
    [data-testid="stSidebarNavLink"][href*="Light_Curves"]::before {
        -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='22 12 18 12 15 21 9 3 6 12 2 12'/%3E%3C/svg%3E");
        mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='22 12 18 12 15 21 9 3 6 12 2 12'/%3E%3C/svg%3E");
    }

    /* Events: Flare Flash */
    [data-testid="stSidebarNavLink"][href*="Events"]::before {
        -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolygon points='13 2 3 14 12 14 11 22 21 10 12 10 13 2'/%3E%3C/svg%3E");
        mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolygon points='13 2 3 14 12 14 11 22 21 10 12 10 13 2'/%3E%3C/svg%3E");
    }

    /* Features: Causal Matrix */
    [data-testid="stSidebarNavLink"][href*="Features"]::before {
        -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='3' width='7' height='7' rx='1'/%3E%3Crect x='14' y='3' width='7' height='7' rx='1'/%3E%3Crect x='14' y='14' width='7' height='7' rx='1'/%3E%3Crect x='3' y='14' width='7' height='7' rx='1'/%3E%3C/svg%3E");
        mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='3' width='7' height='7' rx='1'/%3E%3Crect x='14' y='3' width='7' height='7' rx='1'/%3E%3Crect x='14' y='14' width='7' height='7' rx='1'/%3E%3Crect x='3' y='14' width='7' height='7' rx='1'/%3E%3C/svg%3E");
    }

    /* Model Results: Neural Circuit Chip */
    [data-testid="stSidebarNavLink"][href*="Model_Results"]::before {
        -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='4' y='4' width='16' height='16' rx='2'/%3E%3Crect x='9' y='9' width='6' height='6'/%3E%3Cline x1='9' y1='1' x2='9' y2='4'/%3E%3Cline x1='15' y1='1' x2='15' y2='4'/%3E%3Cline x1='9' y1='20' x2='9' y2='23'/%3E%3Cline x1='15' y1='20' x2='15' y2='23'/%3E%3Cline x1='20' y1='9' x2='23' y2='9'/%3E%3Cline x1='20' y1='15' x2='23' y2='15'/%3E%3Cline x1='1' y1='9' x2='4' y2='9'/%3E%3Cline x1='1' y1='15' x2='4' y2='15'/%3E%3C/svg%3E");
        mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='4' y='4' width='16' height='16' rx='2'/%3E%3Crect x='9' y='9' width='6' height='6'/%3E%3Cline x1='9' y1='1' x2='9' y2='4'/%3E%3Cline x1='15' y1='1' x2='15' y2='4'/%3E%3Cline x1='9' y1='20' x2='9' y2='23'/%3E%3Cline x1='15' y1='20' x2='15' y2='23'/%3E%3Cline x1='20' y1='9' x2='23' y2='9'/%3E%3Cline x1='20' y1='15' x2='23' y2='15'/%3E%3Cline x1='1' y1='9' x2='4' y2='9'/%3E%3Cline x1='1' y1='15' x2='4' y2='15'/%3E%3C/svg%3E");
    }

    /* Live Inference: Radar Telemetry */
    [data-testid="stSidebarNavLink"][href*="Live_Inference"]::before {
        -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='2'/%3E%3Cpath d='M16.24 7.76a6 6 0 0 1 0 8.49m-8.48-.01a6 6 0 0 1 0-8.49'/%3E%3Cpath d='M19.07 4.93a10 10 0 0 1 0 14.14m-14.14 0a10 10 0 0 1 0-14.14'/%3E%3C/svg%3E");
        mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='2'/%3E%3Cpath d='M16.24 7.76a6 6 0 0 1 0 8.49m-8.48-.01a6 6 0 0 1 0-8.49'/%3E%3Cpath d='M19.07 4.93a10 10 0 0 1 0 14.14m-14.14 0a10 10 0 0 1 0-14.14'/%3E%3C/svg%3E");
    }

    /* Spectral Analysis: Energy Waves */
    [data-testid="stSidebarNavLink"][href*="Spectral_Analysis"]::before {
        -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M2 12h3l3 8 4-16 4 11 3-5h3'/%3E%3C/svg%3E");
        mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M2 12h3l3 8 4-16 4 11 3-5h3'/%3E%3C/svg%3E");
    }

    /* Sidebar Model Status Panel */
    .sidebar-model-panel {
        background: #0E1526;
        border: 1px solid #1E293B;
        border-radius: 6px;
        padding: 9px 12px;
        margin-top: 8px;
        margin-bottom: 6px;
    }
    .sidebar-panel-header {
        display: flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 5px;
    }
    .sidebar-panel-indicator {
        color: #F59E0B;
        font-size: 0.80rem;
    }
    .sidebar-panel-title {
        color: #F8FAFC;
        font-weight: 700;
        font-size: 0.88rem;
        flex: 1;
    }
    .sidebar-panel-badge {
        font-size: 0.72rem;
        font-weight: 600;
        color: #38BDF8;
        background: rgba(56, 189, 248, 0.1);
        border: 1px solid rgba(56, 189, 248, 0.25);
        border-radius: 4px;
        padding: 2px 6px;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    .sidebar-panel-body {
        display: flex;
        flex-direction: column;
        gap: 3px;
    }
    .sidebar-panel-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.80rem;
        color: #94A3B8;
    }
    .sidebar-panel-row code {
        background: rgba(15, 23, 42, 0.6);
        color: #E2E8F0;
        padding: 2px 4px;
        border-radius: 3px;
        font-size: 0.78rem;
    }
    .sidebar-panel-footer {
        font-size: 0.75rem;
        color: #10B981;
        margin-top: 5px;
        padding-top: 5px;
        border-top: 1px solid rgba(30, 41, 59, 0.6);
    }

    /* Sidebar Governance Disclaimer */
    .sidebar-disclaimer {
        padding: 8px 10px;
        margin-top: 8px;
        border-radius: 6px;
        background: rgba(15, 23, 42, 0.4);
        border: 1px solid rgba(30, 41, 59, 0.5);
    }
    .sidebar-disclaimer-title {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748B;
        margin-bottom: 3px;
    }
    .sidebar-disclaimer-text {
        font-size: 0.76rem;
        line-height: 1.45;
        color: #64748B;
    }

    /* Reduced motion preference accessibility */
    @media (prefers-reduced-motion: reduce) {
        .hero-sun-glow-core {
            animation: none !important;
            transform: none !important;
        }
    }

    /* Responsive tablet / mobile layout */
    @media (max-width: 900px) {
        .hero-sun-wrapper {
            max-width: 280px;
            margin: 14px auto;
        }
        .hero-sun-video {
            max-width: 270px;
        }
        .hero-sun-glow-core {
            width: 270px;
            height: 270px;
        }
        .hero-sun-glow-ambient {
            width: 380px;
            height: 380px;
        }
        .hero-main-title {
            font-size: 2.5rem;
        }
        .hero-headline {
            font-size: 1.15rem;
        }
        .hero-metadata-strip {
            justify-content: center;
            text-align: center;
            gap: 12px;
            padding: 10px 12px;
            font-size: 0.78rem;
        }
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


def render_source_badge(data_status: str = "HISTORICAL") -> None:
    """Render a restrained scientific badge distinguishing data provenance."""
    st_up = data_status.upper()
    if "LIVE" in st_up:
        badge = '<span class="badge-verified">● Live Stream</span>'
    elif "SAMPLE" in st_up or "SYNTHETIC" in st_up:
        badge = '<span class="badge-unverified">Synthetic Test Input</span>'
    else:
        badge = '<span class="badge-historical">Archived Level-1 Science Data (ISRO PRADAN)</span>'
    st.markdown(f'<div style="text-align: right; margin-top: 6px;">{badge}</div>', unsafe_allow_html=True)
