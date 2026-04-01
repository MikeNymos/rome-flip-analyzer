"""
Hoofd-dashboard view met samenvattingskaarten, visuele property cards en charts.
"""
from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.helpers import format_eur, format_pct, format_m2, format_eur_per_m2, score_color
from config import get_score_label


def render_dashboard(analyzed_listings: list[dict]):
    """Rendert het hoofddashboard met samenvatting, kaarten en charts."""
    if not analyzed_listings:
        st.info("Geen geanalyseerde panden beschikbaar. Gebruik de zijbalk om data te laden.")
        return

    _render_summary_cards(analyzed_listings)
    st.divider()

    st.subheader("Alle Panden")
    selected_idx = _render_property_cards(analyzed_listings)

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        _render_roi_scatter(analyzed_listings)
    with col2:
        _render_score_distribution(analyzed_listings)

    return selected_idx


def _render_summary_cards(listings: list[dict]):
    """Toont samenvattingskaarten bovenaan het dashboard."""
    total = len(listings)
    good_deals = sum(1 for l in listings if l.get("flip_score", 0) >= 65)
    avg_roi = sum(l.get("roi_prima_casa", l.get("midpoint_roi", 0)) for l in listings) / total if total > 0 else 0

    best = max(listings, key=lambda l: l.get("flip_score", 0))
    best_label = f"{best.get('zone', 'Onbekend')} -- {format_eur(best['price'])}"

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Panden geanalyseerd", total)
    with col2:
        st.metric("Flip Score >= 65", good_deals)
    with col3:
        st.metric("Gem. ROI (prima casa)", format_pct(avg_roi))
    with col4:
        st.metric("Beste deal", f"Score: {best.get('flip_score', 0)}", help=best_label)


def _render_property_cards(listings: list[dict]) -> int | None:
    """Rendert een grid van visuele property cards."""
    selected_idx = None
    COLS = 3

    for row_start in range(0, len(listings), COLS):
        row_listings = listings[row_start:row_start + COLS]
        cols = st.columns(COLS)

        for col_idx, listing in enumerate(row_listings):
            global_idx = row_start + col_idx
            with cols[col_idx]:
                if _render_single_card(listing, global_idx):
                    selected_idx = global_idx

    return selected_idx


def _render_single_card(listing: dict, idx: int) -> bool:
    """Rendert een enkele property card. Retourneert True als geselecteerd."""
    score = listing.get("flip_score", 0)
    label, color, _ = get_score_label(score)
    images = listing.get("images", [])
    roi = listing.get("roi_prima_casa", listing.get("midpoint_roi", 0))
    zone = listing.get("zone", "Onbekend")
    address = listing.get("address", "")
    price = listing.get("price", 0)
    surface = listing.get("surface_m2", 0)
    price_per_m2 = listing.get("price_per_m2", 0)
    risk_count = len(listing.get("risk_flags", []))
    loc_score = listing.get("location_quality", {}).get("overall_score", "?")

    selected = False

    with st.container(border=True):
        # Thumbnail
        if images:
            st.markdown(
                f'<img src="{images[0]}" style="width:100%;height:200px;object-fit:cover;'
                f'border-radius:6px;" loading="lazy">',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="background:#e9ecef;height:200px;display:flex;'
                'align-items:center;justify-content:center;border-radius:6px;">'
                '<span style="color:#6c757d;font-size:0.9em;">Geen foto</span></div>',
                unsafe_allow_html=True,
            )

        # Score badge
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;margin:8px 0 4px 0;">'
            f'<span style="background:{color};color:white;padding:4px 14px;'
            f'border-radius:20px;font-weight:bold;font-size:1.1em;">{score}</span>'
            f'<span style="color:#555;font-size:0.85em;">{label}</span>'
            f'<span style="color:#888;font-size:0.8em;margin-left:auto;">'
            f'Locatie: {loc_score}/100</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Zone + adres
        display_zone = zone[:40] if len(zone) > 40 else zone
        st.markdown(f"**{display_zone}**")
        if address:
            st.caption(address)

        # Kerngetallen
        st.markdown(f"{format_eur(price)} | {format_m2(surface)} | {format_eur_per_m2(price_per_m2)}")

        # ROI
        roi_color = "green" if roi > 15 else "orange" if roi > 5 else "red"
        st.markdown(f"**ROI (prima casa):** :{roi_color}[{format_pct(roi)}]")

        if risk_count > 0:
            st.caption(f"{risk_count} risicovlag(gen)")

        # Knoppen
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Bekijk detail", key=f"card_detail_{idx}", use_container_width=True):
                selected = True
        with col_b:
            url = listing.get("url", "")
            if url:
                st.link_button("Immobiliare", url, use_container_width=True)

    return selected


def _render_roi_scatter(listings: list[dict]):
    """Scatter chart: ROI vs. Aankoopprijs."""
    st.subheader("ROI vs. Aankoopprijs")
    data = [{
        "Aankoopprijs": l.get("price", 0),
        "ROI Prima Casa (%)": l.get("roi_prima_casa", l.get("midpoint_roi", 0)),
        "Wijk": (l.get("zone", "Onbekend"))[:30],
        "Flip Score": l.get("flip_score", 0),
        "m2": l.get("surface_m2", 0),
    } for l in listings]

    df = pd.DataFrame(data)
    if df.empty:
        return

    fig = px.scatter(
        df, x="Aankoopprijs", y="ROI Prima Casa (%)", color="Wijk",
        size="Flip Score", hover_data=["m2", "Flip Score"],
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(height=400, margin=dict(l=20, r=20, t=30, b=20))
    fig.add_hline(y=15, line_dash="dash", line_color="gray", annotation_text="Min. ROI 15%")
    st.plotly_chart(fig, use_container_width=True)


def _render_score_distribution(listings: list[dict]):
    """Bar chart: Flip Score verdeling."""
    st.subheader("Flip Score Verdeling")
    scores = [l.get("flip_score", 0) for l in listings]
    buckets = {"0-34": 0, "35-49": 0, "50-64": 0, "65-79": 0, "80-100": 0}
    colors_list = ["#c0392b", "#e07c24", "#d4a017", "#3da55d", "#2d8a4e"]

    for s in scores:
        if s >= 80: buckets["80-100"] += 1
        elif s >= 65: buckets["65-79"] += 1
        elif s >= 50: buckets["50-64"] += 1
        elif s >= 35: buckets["35-49"] += 1
        else: buckets["0-34"] += 1

    fig = go.Figure(data=[go.Bar(
        x=list(buckets.keys()), y=list(buckets.values()), marker_color=colors_list,
    )])
    fig.update_layout(height=400, margin=dict(l=20, r=20, t=30, b=20), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
