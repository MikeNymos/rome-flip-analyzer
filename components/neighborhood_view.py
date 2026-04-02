"""
Wijkdata overzicht en vergelijkingstool.
"""
from __future__ import annotations


import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from data.neighborhoods import NEIGHBORHOOD_BENCHMARKS, DEFAULT_BENCHMARK
from utils.helpers import format_eur_per_m2, format_pct, get_plotly_layout


def render_neighborhood_view():
    """Rendert het wijkdata-overzicht met tabel en vergelijkingschart."""

    st.subheader("Wijkbenchmarks — Overzicht")
    st.caption("Prijzen per m² en kenmerken per wijk. Deze data wordt gebruikt voor de financiële analyse.")

    # === TABEL ===
    _render_benchmark_table()

    st.divider()

    # === VERGELIJKINGSCHART ===
    st.subheader("Wijkvergelijking — Prijzen per m²")
    _render_comparison_chart()

    st.divider()

    # === GROEI CHART ===
    st.subheader("Jaar-op-jaar Prijsgroei")
    _render_growth_chart()


def _render_benchmark_table():
    """Toont alle wijkbenchmarks in tabelformaat."""
    rows = []
    for zone_name, data in NEIGHBORHOOD_BENCHMARKS.items():
        priority_stars = "★" * data["priority"]
        rows.append({
            "Wijk": zone_name,
            "Prioriteit": priority_stars,
            "Te renoveren (laag)": format_eur_per_m2(data["unrenovated_price_low"]),
            "Te renoveren (hoog)": format_eur_per_m2(data["unrenovated_price_high"]),
            "Gerenoveerd (laag)": format_eur_per_m2(data["renovated_price_low"]),
            "Gerenoveerd (mid)": format_eur_per_m2(data["renovated_price_mid"]),
            "Gerenoveerd (hoog)": format_eur_per_m2(data["renovated_price_high"]),
            "Groei (j-o-j)": format_pct(data["yoy_growth"] * 100),
            "Verkooptijd": f"{data['avg_selling_time_months']} mnd",
            "Risico": data["risk_level"].capitalize(),
            "Opmerkingen": data["notes"],
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_comparison_chart():
    """Bar chart: wijken naast elkaar (aankoop vs. verkoop per m²)."""
    zones = list(NEIGHBORHOOD_BENCHMARKS.keys())
    unrenovated_mid = [
        (d["unrenovated_price_low"] + d["unrenovated_price_high"]) / 2
        for d in NEIGHBORHOOD_BENCHMARKS.values()
    ]
    renovated_mid = [d["renovated_price_mid"] for d in NEIGHBORHOOD_BENCHMARKS.values()]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Te renoveren (gem. €/m²)",
        x=zones,
        y=unrenovated_mid,
        marker_color="#F97316",
    ))
    fig.add_trace(go.Bar(
        name="Gerenoveerd (gem. €/m²)",
        x=zones,
        y=renovated_mid,
        marker_color="#10B981",
    ))

    dark = st.session_state.get("dark_mode", False)
    fig.update_layout(
        barmode="group",
        height=400,
        margin=dict(l=20, r=20, t=30, b=20),
        yaxis_title="€/m²",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        **get_plotly_layout(dark),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Spread berekening
    st.markdown("**Spread (verschil aankoop → verkoop):**")
    for zone_name, data in NEIGHBORHOOD_BENCHMARKS.items():
        unreno_mid = (data["unrenovated_price_low"] + data["unrenovated_price_high"]) / 2
        reno_mid = data["renovated_price_mid"]
        spread = ((reno_mid - unreno_mid) / unreno_mid) * 100
        st.markdown(f"- **{zone_name}**: {spread:.0f}% spread")


def _render_growth_chart():
    """Bar chart: jaar-op-jaar groei per wijk."""
    zones = list(NEIGHBORHOOD_BENCHMARKS.keys())
    growth = [d["yoy_growth"] * 100 for d in NEIGHBORHOOD_BENCHMARKS.values()]

    fig = go.Figure(data=[
        go.Bar(
            x=zones,
            y=growth,
            marker_color=["#E8956A" if g >= 7 else "#818CF8" for g in growth],
            text=[f"{g:.1f}%" for g in growth],
            textposition="auto",
        )
    ])

    dark = st.session_state.get("dark_mode", False)
    fig.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=30, b=20),
        yaxis_title="Groei (%)",
        showlegend=False,
        **get_plotly_layout(dark),
    )

    st.plotly_chart(fig, use_container_width=True)
