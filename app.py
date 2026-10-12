import base64
import logging
import os
import random

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from simulation import SCENARIOS, calculate_mission


st.set_page_config(
    page_title="ASTRA-TRACE",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

logger = logging.getLogger(__name__)


def load_background_base64():
    asset_path = os.path.join(os.path.dirname(__file__), "assets", "space-background.svg")
    with open(asset_path, "rb") as handle:
        return base64.b64encode(handle.read()).decode("utf-8")


BACKGROUND_B64 = load_background_base64()

_space_rng = random.Random(2026)


def build_space_overlay():
    star_layers = []
    for layer_name, count in (("stars-far", 28), ("stars-mid", 22), ("stars-near", 14)):
        stars = []
        for _ in range(count):
            size = _space_rng.choice((1, 1, 1.5, 2))
            duration = _space_rng.randint(3, 8)
            delay = _space_rng.randint(-8, 0)
            stars.append(
                f'<i class="space-star" style="left:{_space_rng.randint(0, 100)}%;'
                f'top:{_space_rng.randint(0, 100)}%;width:{size}px;height:{size}px;'
                f'--twinkle-duration:{duration}s;--twinkle-delay:{delay}s"></i>'
            )
        star_layers.append(f'<div class="star-layer {layer_name}">{"".join(stars)}</div>')

    asteroid_specs = (
        ("asteroid-one", 15, 32, 10, 86, -35),
        ("asteroid-two", 64, 21, 7, 112, -82),
        ("asteroid-three", 39, 78, 14, 138, -116),
        ("asteroid-four", 81, 63, 6, 96, -51),
        ("asteroid-five", 24, 91, 9, 124, -101),
    )
    asteroids = "".join(
        f'<div class="asteroid {name}" style="left:{left}%;top:{top}%;width:{size}px;'
        f'height:{size}px;--drift-duration:{duration}s;--drift-delay:{delay}s">'
        '<i class="asteroid-body"></i></div>'
        for name, left, top, size, duration, delay in asteroid_specs
    )

    meteor_specs = (
        ("meteor-one", 12, 7, 23, 16, 13),
        ("meteor-two", 70, 4, 17, 23, 9),
        ("meteor-three", 46, 48, 27, 29, 19),
    )
    meteors = "".join(
        f'<i class="meteor {name}" style="left:{left}%;top:{top}%;'
        f'--meteor-duration:{duration}s;--meteor-delay:-{delay}s;'
        f'--meteor-x:{travel}vw;--meteor-y:{travel * 0.62}vh"></i>'
        for name, left, top, duration, delay, travel in meteor_specs
    )

    return (
        '<div class="space-animation" aria-hidden="true">'
        '<div class="nebula-drift nebula-drift-one"></div>'
        '<div class="nebula-drift nebula-drift-two"></div>'
        + "".join(star_layers)
        + asteroids
        + meteors
        + '<div class="black-hole"><div class="black-hole-glow"></div>'
        '<div class="accretion-disk"></div><div class="black-hole-core"></div>'
        '<div class="lensing-halo"></div></div></div>'
    )


SPACE_OVERLAY_HTML = build_space_overlay()


st.markdown(
    f"""
    <style>
    .stApp {{
        background: linear-gradient(180deg, rgba(2, 3, 8, 0.82), rgba(8, 10, 16, 0.88));
    }}

    .stApp > div:before {{
        content: "";
        position: fixed;
        inset: 0;
        z-index: -2;
        background-image: url("data:image/svg+xml;base64,{BACKGROUND_B64}");
        background-size: cover;
        background-position: center center;
        background-repeat: no-repeat;
        opacity: 0.96;
    }}

    .stApp > div:after {{
        content: "";
        position: fixed;
        inset: 0;
        z-index: -1;
        background: linear-gradient(90deg, rgba(3, 3, 5, 0.72) 0%, rgba(5, 8, 15, 0.36) 40%, rgba(3, 3, 5, 0.76) 100%);
        pointer-events: none;
    }}

    .space-animation {{
        position: fixed;
        inset: 0;
        z-index: 0;
        overflow: hidden;
        pointer-events: none;
        contain: layout paint;
    }}

    div[data-testid="stElementContainer"] {{
        position: relative;
        z-index: 1;
    }}

    div[data-testid="stElementContainer"]:has(.space-animation) {{
        position: static;
        z-index: auto;
    }}

    div[data-testid="stMain"], section[data-testid="stSidebar"] {{
        position: relative;
        z-index: 1;
    }}

    section[data-testid="stSidebar"] {{
        z-index: 2;
    }}

    .star-layer, .nebula-drift, .asteroid, .meteor, .black-hole {{
        position: absolute;
        pointer-events: none;
    }}

    .star-layer {{
        inset: -5%;
        will-change: transform;
    }}

    .stars-far {{
        animation: star-parallax-far 180s linear infinite;
        opacity: 0.52;
    }}

    .stars-mid {{
        animation: star-parallax-mid 115s linear infinite;
        opacity: 0.72;
    }}

    .stars-near {{
        animation: star-parallax-near 78s linear infinite;
        opacity: 0.82;
    }}

    .space-star {{
        position: absolute;
        display: block;
        border-radius: 50%;
        background: #f4f2ff;
        box-shadow: 0 0 5px rgba(205, 202, 255, 0.55);
        animation: star-twinkle var(--twinkle-duration) ease-in-out var(--twinkle-delay) infinite;
        will-change: opacity, transform;
    }}

    .nebula-drift {{
        width: 70vw;
        height: 55vh;
        border-radius: 50%;
        filter: blur(70px);
        opacity: 0.12;
        will-change: transform, opacity;
    }}

    .nebula-drift-one {{
        left: -24vw;
        top: 12vh;
        background: radial-gradient(ellipse, rgba(148, 109, 255, 0.55), transparent 68%);
        animation: nebula-float-one 72s ease-in-out infinite alternate;
    }}

    .nebula-drift-two {{
        right: -24vw;
        bottom: -12vh;
        background: radial-gradient(ellipse, rgba(137, 164, 231, 0.42), transparent 68%);
        animation: nebula-float-two 94s ease-in-out infinite alternate;
    }}

    .asteroid {{
        display: grid;
        place-items: center;
        border-radius: 50%;
        animation: asteroid-drift var(--drift-duration) linear var(--drift-delay) infinite;
        will-change: transform;
    }}

    .asteroid-body {{
        display: block;
        width: 100%;
        height: 100%;
        border-radius: 38% 62% 53% 47% / 57% 42% 58% 43%;
        background:
            radial-gradient(circle at 32% 27%, rgba(197, 190, 181, 0.55) 0 5%, transparent 7%),
            radial-gradient(circle at 68% 64%, rgba(10, 11, 14, 0.8) 0 9%, transparent 11%),
            radial-gradient(ellipse at 36% 30%, #727078 0%, #35343b 40%, #111217 78%);
        box-shadow: inset -2px -2px 4px rgba(0,0,0,0.8), 0 0 10px rgba(167, 164, 185, 0.1);
        animation: asteroid-rotate 24s linear infinite;
    }}

    .asteroid-two .asteroid-body, .asteroid-four .asteroid-body {{
        animation-duration: 38s;
        animation-direction: reverse;
    }}

    .asteroid-three {{ opacity: 0.52; filter: blur(0.6px); }}
    .asteroid-four {{ opacity: 0.6; }}
    .asteroid-five {{ opacity: 0.7; filter: blur(0.3px); }}

    .meteor {{
        width: clamp(90px, 12vw, 180px);
        height: 2px;
        z-index: 1;
        opacity: 0;
        background: linear-gradient(90deg, transparent, rgba(213, 211, 255, 0.16) 35%, rgba(240, 239, 255, 0.95));
        box-shadow: 0 0 9px rgba(196, 189, 255, 0.6);
        transform: rotate(-34deg);
        transform-origin: left center;
        animation: meteor-flight var(--meteor-duration) ease-out var(--meteor-delay) infinite;
        will-change: transform, opacity;
    }}

    .meteor::after {{
        content: "";
        position: absolute;
        right: -2px;
        top: -2px;
        width: 5px;
        height: 5px;
        border-radius: 50%;
        background: #fff;
        box-shadow: 0 0 9px 2px rgba(226, 219, 255, 0.9);
    }}

    .black-hole {{
        width: clamp(160px, 20vw, 290px);
        height: clamp(95px, 12vw, 170px);
        top: 22vh;
        right: 5vw;
        z-index: 0;
        filter: drop-shadow(0 0 22px rgba(180, 146, 255, 0.2));
    }}

    .black-hole-glow, .accretion-disk, .black-hole-core, .lensing-halo {{
        position: absolute;
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);
        border-radius: 50%;
    }}

    .black-hole-glow {{
        width: 115%;
        height: 150%;
        background: radial-gradient(ellipse, rgba(232, 163, 255, 0.26), rgba(119, 137, 255, 0.12) 34%, transparent 70%);
        animation: black-hole-pulse 8s ease-in-out infinite alternate;
    }}

    .accretion-disk {{
        width: 100%;
        height: 55%;
        border: 7px solid transparent;
        background:
            linear-gradient(#05050a, #05050a) padding-box,
            conic-gradient(from 0deg, #554975, #d9a6ff, #f5d9a2, #889df0, #4d395d, #d9a6ff) border-box;
        box-shadow: 0 0 14px rgba(211, 159, 255, 0.7), 0 0 34px rgba(138, 157, 255, 0.28);
        animation: disk-rotation 34s linear infinite;
    }}

    .black-hole-core {{
        width: 37%;
        height: 62%;
        z-index: 2;
        background: radial-gradient(circle at 38% 35%, #171722 0%, #030306 44%, #000 75%);
        box-shadow: 0 0 18px 7px rgba(0, 0, 0, 0.95);
    }}

    .lensing-halo {{
        width: 64%;
        height: 98%;
        border: 1px solid rgba(208, 197, 255, 0.5);
        box-shadow: 0 0 12px rgba(164, 155, 255, 0.28), inset 0 0 9px rgba(164, 155, 255, 0.18);
        animation: lensing-pulse 6s ease-in-out infinite alternate;
    }}

    @keyframes star-twinkle {{
        0%, 100% {{ opacity: 0.35; transform: scale(0.78); }}
        50% {{ opacity: 1; transform: scale(1.15); }}
    }}
    @keyframes star-parallax-far {{
        from {{ transform: translate3d(0, 0, 0); }}
        to {{ transform: translate3d(-1.2vw, 0.6vh, 0); }}
    }}
    @keyframes star-parallax-mid {{
        from {{ transform: translate3d(0, 0, 0); }}
        to {{ transform: translate3d(-2.8vw, 1.2vh, 0); }}
    }}
    @keyframes star-parallax-near {{
        from {{ transform: translate3d(0, 0, 0); }}
        to {{ transform: translate3d(-4.5vw, 1.8vh, 0); }}
    }}
    @keyframes nebula-float-one {{
        from {{ transform: translate3d(0, 0, 0) scale(0.96); opacity: 0.08; }}
        to {{ transform: translate3d(8vw, -3vh, 0) scale(1.08); opacity: 0.17; }}
    }}
    @keyframes nebula-float-two {{
        from {{ transform: translate3d(0, 0, 0) scale(1.04); opacity: 0.07; }}
        to {{ transform: translate3d(-7vw, 4vh, 0) scale(0.94); opacity: 0.15; }}
    }}
    @keyframes asteroid-drift {{
        from {{ transform: translate3d(-12vw, 0, 0); }}
        to {{ transform: translate3d(112vw, -8vh, 0); }}
    }}
    @keyframes asteroid-rotate {{
        from {{ transform: rotate(0deg); }}
        to {{ transform: rotate(360deg); }}
    }}
    @keyframes meteor-flight {{
        0%, 78% {{ opacity: 0; transform: translate3d(0, 0, 0) rotate(-34deg); }}
        80% {{ opacity: 0.95; }}
        88% {{ opacity: 0.72; transform: translate3d(var(--meteor-x), var(--meteor-y), 0) rotate(-34deg); }}
        91%, 100% {{ opacity: 0; transform: translate3d(var(--meteor-x), var(--meteor-y), 0) rotate(-34deg); }}
    }}
    @keyframes disk-rotation {{
        from {{ rotate: 0deg; }}
        to {{ rotate: 360deg; }}
    }}
    @keyframes black-hole-pulse {{
        from {{ opacity: 0.48; scale: 0.96; }}
        to {{ opacity: 0.9; scale: 1.06; }}
    }}
    @keyframes lensing-pulse {{
        from {{ opacity: 0.45; scale: 0.98; }}
        to {{ opacity: 0.85; scale: 1.03; }}
    }}

    @media (max-width: 700px) {{
        .black-hole {{ top: 16vh; right: -8vw; opacity: 0.55; }}
        .asteroid-five, .asteroid-four {{ display: none; }}
        .nebula-drift {{ filter: blur(48px); }}
    }}

    @media (prefers-reduced-motion: reduce) {{
        .space-animation *, .space-animation *::before, .space-animation *::after {{
            animation: none !important;
            scroll-behavior: auto !important;
        }}
        .meteor {{ display: none; }}
        .space-star {{ opacity: 0.72; transform: none; }}
        .black-hole-glow, .lensing-halo {{ opacity: 0.65; }}
    }}

    header[data-testid="stHeader"] {{
        background: transparent !important;
        box-shadow: none !important;
    }}

    section[data-testid="stSidebar"] {{
        background: rgba(10, 12, 18, 0.72) !important;
        backdrop-filter: blur(18px);
        border-right: 1px solid rgba(181, 192, 255, 0.15);
        box-shadow: inset -1px 0 0 rgba(255,255,255,0.04);
    }}

    section[data-testid="stSidebar"] * {{
        color: #f5f7ff !important;
    }}

    .block-container {{
        max-width: 1480px !important;
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }}

    .space-panel {{
        background: rgba(9, 11, 16, 0.44);
        border: 1px solid rgba(170, 180, 255, 0.18);
        border-radius: 20px;
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        box-shadow: 0 18px 40px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.06);
    }}

    .topbar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        padding: 0.4rem 0 0.8rem;
    }}

    .brand-block {{
        display: flex;
        flex-direction: column;
        gap: 0.1rem;
    }}

    .brand-title {{
        margin: 0;
        font-size: clamp(2.5rem, 3vw, 4.1rem);
        line-height: 1;
        color: #f5f5fa !important;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        font-weight: 800;
    }}

    .brand-subtitle {{
        margin: 0;
        color: #b8bfdc !important;
        letter-spacing: 0.34em;
        text-transform: uppercase;
        font-size: 0.78rem;
        font-weight: 600;
    }}

    .status-chip {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.45rem 0.9rem;
        border-radius: 999px;
        border: 1px solid rgba(122, 224, 164, 0.5);
        background: rgba(17, 27, 29, 0.7);
        color: #94f0c3 !important;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        font-size: 0.72rem;
        box-shadow: 0 0 18px rgba(94, 245, 180, 0.18);
    }}

    .metric-card {{
        background: rgba(10, 13, 18, 0.62);
        border: 1px solid rgba(154, 166, 214, 0.18);
        border-radius: 18px;
        padding: 1.1rem 1.15rem;
        min-height: 150px;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.08), 0 12px 25px rgba(0,0,0,0.22);
    }}

    .metric-title {{
        font-size: 0.8rem;
        letter-spacing: 0.12em;
        color: #b7bdd6 !important;
        text-transform: uppercase;
        margin-bottom: 0.75rem;
        font-weight: 600;
    }}

    .metric-value {{
        font-size: clamp(1.8rem, 2.3vw, 2.75rem);
        font-weight: 800;
        letter-spacing: -0.04em;
        color: #f6f7fb !important;
        line-height: 1.05;
    }}

    .metric-detail {{
        margin-top: 0.75rem;
        color: #a9b3d2 !important;
        font-size: 0.9rem;
    }}

    .safe {{ color: #8ef2bf !important; }}
    .warning {{ color: #f7c66b !important; }}
    .critical {{ color: #ff8d8d !important; }}

    .chart-panel {{
        padding: 0.6rem 0.6rem 0.2rem;
        margin-top: 1.2rem;
    }}

    .section-heading {{
        color: #dfe7ff !important;
        font-size: 0.9rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin: 0 0 0.8rem;
        font-weight: 700;
    }}

    .data-table {{
        background: rgba(9, 12, 18, 0.6);
        border: 1px solid rgba(177, 182, 214, 0.15);
        border-radius: 16px;
        overflow: hidden;
    }}

    [data-testid="stDataFrame"] {{
        background: transparent;
    }}

    table, th, td {{
        background: transparent !important;
        border-color: rgba(177, 182, 214, 0.12) !important;
        color: #edf1ff !important;
    }}

    th {{
        color: #d1d8f0 !important;
        background: rgba(16, 18, 24, 0.9) !important;
        font-size: 0.78rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
    }}

    td {{
        font-size: 0.9rem !important;
    }}

    div[data-baseweb="select"] > div, div[role="listbox"] {{
        background: rgba(14, 17, 26, 0.9) !important;
        border: 1px solid rgba(162, 169, 216, 0.2) !important;
        color: #f1f3ff !important;
    }}

    .stSlider [data-testid="stSliderThumb"] {{
        background: #dfe6ff !important;
        border: 2px solid #b0b8ff !important;
    }}

    .stSlider [data-testid="stMarkdownContainer"] p {{
        color: #f5f7ff !important;
    }}

    .stButton > button {{
        border: 1px solid rgba(177, 181, 255, 0.28);
        border-radius: 12px;
        background: linear-gradient(135deg, rgba(14, 18, 32, 0.95), rgba(24, 32, 48, 0.92));
        color: #f5f7ff !important;
        font-weight: 700;
        letter-spacing: 0.04em;
        box-shadow: 0 10px 24px rgba(0,0,0,0.24);
    }}

    .stButton > button:hover {{
        border-color: rgba(174, 179, 255, 0.5);
        box-shadow: 0 14px 26px rgba(47, 75, 200, 0.14);
    }}

    .stRadio > div > label, .stCheckbox > label, .stSelectbox label, .stSlider label {{
        color: #e5ebff !important;
        font-weight: 600 !important;
        letter-spacing: 0.04em;
    }}

    .stSelectbox div[data-baseweb="select"] span {{
        color: #f6f8ff !important;
    }}

    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown(SPACE_OVERLAY_HTML, unsafe_allow_html=True)


with st.sidebar:
    st.markdown('<div class="space-panel" style="padding: 1.1rem 1rem 0.8rem; margin-bottom: 1rem;">', unsafe_allow_html=True)
    st.markdown('<div style="font-size: 1.15rem; letter-spacing: 0.18em; text-transform: uppercase; color: #dfe6ff; font-weight: 700; margin-bottom: 0.8rem;">Mission Control</div>', unsafe_allow_html=True)

    scenario = st.selectbox(
        "Mission Scenario",
        list(SCENARIOS),
        index=0,
        help="Mission operations profile",
    )

    reserve_target = st.slider("Battery Reserve Target", min_value=20, max_value=80, value=45, step=1)

    mode = st.radio("Monitoring Mode", ["Autonomous", "Manual", "Safe Hold"], index=0)

    st.checkbox("Telemetry lock", value=True)
    predictive_analytics = st.checkbox("Predictive analytics", value=True)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="display: flex; flex-direction: column; gap: 0.85rem; margin-top: 1.1rem;">', unsafe_allow_html=True)
    sync_telemetry_clicked = st.button("Sync Telemetry")
    run_diagnostic_clicked = st.button(
        "Run Diagnostic",
        disabled=not predictive_analytics,
    )
    st.markdown('</div>', unsafe_allow_html=True)

if sync_telemetry_clicked:
    st.info("Telemetry synchronization is not connected to a telemetry source.")

try:
    metrics = calculate_mission(scenario, reserve_target, mode)
except Exception:
    logger.exception("Mission forecast failed for scenario %r", scenario)
    st.error("Mission forecast failed. See the VS Code terminal for details.")
    st.stop()

if run_diagnostic_clicked:
    try:
        st.session_state["diagnostic_report"] = calculate_mission(
            scenario,
            reserve_target,
            mode,
        )
        st.session_state["diagnostic_inputs"] = (scenario, reserve_target, mode)
        st.session_state.pop("diagnostic_error", None)
    except Exception as error:
        logger.exception("Mission diagnostic failed for scenario %r", scenario)
        st.session_state["diagnostic_error"] = str(error)

status_class = {
    "SAFE": "safe",
    "WATCH": "warning",
    "CRITICAL": "critical",
}[metrics["status"]]


with st.container():
    st.markdown(
        """
        <div class="topbar">
            <div class="brand-block">
                <h1 class="brand-title">ASTRA-TRACE</h1>
                <p class="brand-subtitle">PREDICTIVE SATELLITE MISSION SAFETY MONITOR</p>
            </div>
            <div class="status-chip">System nominal</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Mission Status</div>
                <div class="metric-value {status_class}">{metrics['status']}</div>
                <div class="metric-detail">{len(metrics['violations'])} forecast reserve violations</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with metric_cols[1]:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Minimum Forecast Reserve</div>
                <div class="metric-value">{metrics['minimum_reserve']}%</div>
                <div class="metric-detail">At hour {metrics['minimum_reserve_hour']} / target {reserve_target}%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with metric_cols[2]:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Mission Intent Drift</div>
                <div class="metric-value">{metrics['drift_score']}</div>
                <div class="metric-detail">{len(metrics['threatened_objectives'])} threatened objectives</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with metric_cols[3]:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Risk Exposure</div>
                <div class="metric-value {status_class}">{metrics['risk']}</div>
                <div class="metric-detail">Risk classification follows mission status</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=metrics["hours"], y=metrics["battery"], mode="lines+markers", line=dict(color="#b8b8ff", width=3), marker=dict(size=8, color="#e1e3ff"), name="Battery reserve"))
    fig.add_trace(go.Scatter(x=metrics["hours"], y=metrics["required_reserve"], mode="lines", line=dict(color="#f5c56b", width=2, dash="dash"), name="Required reserve"))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(10,12,18,0.0)",
        plot_bgcolor="rgba(10,12,18,0.0)",
        margin=dict(l=35, r=20, t=15, b=35),
        font=dict(color="#edf1ff", family="Inter, Arial, sans-serif"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
        xaxis=dict(title=dict(text="Mission hours", font=dict(size=11)), tickfont=dict(size=11), gridcolor="rgba(255,255,255,0.08)", zeroline=False),
        yaxis=dict(title=dict(text="Reserve (%)", font=dict(size=11)), tickfont=dict(size=11), gridcolor="rgba(255,255,255,0.08)", zeroline=False, range=[0, 100]),
    )

    st.markdown('<div class="section-heading">Battery reserve forecast</div>', unsafe_allow_html=True)
    st.caption(
        f"SAFE: no forecast breaches · WATCH: breach up to 5 pp · "
        f"CRITICAL: breach over 5 pp. Drift score = cumulative shortfall + "
        f"5 per threatened objective."
    )
    st.caption(
        "Scenario energy costs and solar recovery are locally modeled inputs, "
        "not live telemetry. Monitoring mode scales modeled energy use."
    )
    st.markdown('<div class="space-panel chart-panel">', unsafe_allow_html=True)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

    mission_activity = pd.DataFrame(
        {
            "Hour": metrics["hours"][1:],
            "Mission phase": metrics["schedule"],
            "Energy cost (pp)": metrics["energy_costs"],
            "Solar recovery (pp)": metrics["solar_recovery"],
            "Battery reserve (%)": metrics["battery"][1:],
            "Required reserve (%)": metrics["required_reserve"][1:],
        }
    )

    st.markdown('<div class="section-heading" style="margin-top: 1.35rem;">Mission activity</div>', unsafe_allow_html=True)
    st.markdown('<div class="space-panel data-table" style="padding: 0.2rem;">', unsafe_allow_html=True)
    st.dataframe(mission_activity, width="stretch", hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.caption(f"Scenario: {scenario} · Mode: {mode}")

    diagnostic_report = st.session_state.get("diagnostic_report")
    diagnostic_inputs = st.session_state.get("diagnostic_inputs")
    if st.session_state.get("diagnostic_error"):
        st.error(
            "Diagnostic failed: "
            + st.session_state["diagnostic_error"]
            + " (details are logged in the VS Code terminal)"
        )
    elif diagnostic_report and diagnostic_inputs == (scenario, reserve_target, mode):
        st.success(
            f"Diagnostic complete: {diagnostic_report['status']} · "
            f"{len(diagnostic_report['violations'])} reserve violations · "
            f"{len(diagnostic_report['threatened_objectives'])} threatened objectives."
        )
        for objective in diagnostic_report["threatened_objectives"]:
            st.warning(
                f"Threatened objective: {objective['name']} at hour "
                f"{objective['hour']} ({objective['reserve']}% reserve)."
            )
    elif diagnostic_report:
        st.info("Inputs changed since the last diagnostic. Run Diagnostic to refresh the report.")
