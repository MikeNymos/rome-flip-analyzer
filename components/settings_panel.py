"""
Instellingenpagina voor het aanpassen van alle configureerbare parameters.
"""
from __future__ import annotations


import json
import streamlit as st

from config import DEFAULT_PARAMS, PARAM_DESCRIPTIONS


def render_settings(params: dict) -> dict:
    """
    Rendert de instellingenpagina en retourneert de bijgewerkte parameters.
    """
    st.subheader("Instellingen — Parameters Aanpassen")
    st.caption("Pas de onderliggende aannames aan voor de financiële berekeningen.")

    updated = params.copy()

    # === RENOVATIE ===
    st.markdown("#### Renovatiekosten")
    col1, col2, col3 = st.columns(3)
    with col1:
        updated["renovation_cost_min_per_m2"] = st.number_input(
            "Min. renovatie €/m² (optimistisch)",
            value=int(params["renovation_cost_min_per_m2"]),
            step=50,
            help=PARAM_DESCRIPTIONS["renovation_cost_min_per_m2"][1],
        )
    with col2:
        updated["renovation_cost_per_m2"] = st.number_input(
            "Gem. renovatie €/m²",
            value=int(params["renovation_cost_per_m2"]),
            step=50,
            help=PARAM_DESCRIPTIONS["renovation_cost_per_m2"][1],
        )
    with col3:
        updated["renovation_cost_max_per_m2"] = st.number_input(
            "Max. renovatie €/m² (conservatief)",
            value=int(params["renovation_cost_max_per_m2"]),
            step=50,
            help=PARAM_DESCRIPTIONS["renovation_cost_max_per_m2"][1],
        )

    # === AANKOOPKOSTEN ===
    st.markdown("#### Bijkomende Aankoopkosten")
    col1, col2 = st.columns(2)
    with col1:
        updated["registration_tax_seconda_casa"] = st.number_input(
            "Registratiebelasting seconda casa (%)",
            value=params["registration_tax_seconda_casa"] * 100,
            step=0.5,
            format="%.1f",
            help=PARAM_DESCRIPTIONS["registration_tax_seconda_casa"][1],
        ) / 100
        updated["registration_tax_prima_casa"] = st.number_input(
            "Registratiebelasting prima casa (%)",
            value=params["registration_tax_prima_casa"] * 100,
            step=0.5,
            format="%.1f",
            help=PARAM_DESCRIPTIONS["registration_tax_prima_casa"][1],
        ) / 100
        updated["notary_cost_fixed"] = st.number_input(
            "Notariskosten vast (€)",
            value=int(params["notary_cost_fixed"]),
            step=500,
            help=PARAM_DESCRIPTIONS["notary_cost_fixed"][1],
        )

    with col2:
        updated["notary_cost_percentage"] = st.number_input(
            "Notariskosten percentage (%)",
            value=params["notary_cost_percentage"] * 100,
            step=0.1,
            format="%.1f",
            help=PARAM_DESCRIPTIONS["notary_cost_percentage"][1],
        ) / 100
        updated["broker_buy_percentage"] = st.number_input(
            "Makelaar aankoop (%)",
            value=params["broker_buy_percentage"] * 100,
            step=0.5,
            format="%.1f",
            help=PARAM_DESCRIPTIONS["broker_buy_percentage"][1],
        ) / 100
        updated["broker_sell_percentage"] = st.number_input(
            "Makelaar verkoop (%)",
            value=params["broker_sell_percentage"] * 100,
            step=0.5,
            format="%.1f",
            help=PARAM_DESCRIPTIONS["broker_sell_percentage"][1],
        ) / 100

    # === ARCHITECT ===
    st.markdown("#### Architect & Vergunningen")
    col1, col2 = st.columns(2)
    with col1:
        updated["architect_geometra_cost"] = st.number_input(
            "Architect + geometra vast (€)",
            value=int(params["architect_geometra_cost"]),
            step=1000,
            help=PARAM_DESCRIPTIONS["architect_geometra_cost"][1],
        )
    with col2:
        updated["architect_cost_percentage"] = st.number_input(
            "Architect kosten percentage (%)",
            value=params["architect_cost_percentage"] * 100,
            step=0.5,
            format="%.1f",
            help=PARAM_DESCRIPTIONS["architect_cost_percentage"][1],
        ) / 100

    # === ONVOORZIEN & HOLDING ===
    st.markdown("#### Onvoorzien & Holding Costs")
    col1, col2, col3 = st.columns(3)
    with col1:
        updated["contingency_percentage"] = st.number_input(
            "Onvoorzien (%)",
            value=params["contingency_percentage"] * 100,
            step=1.0,
            format="%.0f",
            help=PARAM_DESCRIPTIONS["contingency_percentage"][1],
        ) / 100
    with col2:
        updated["holding_cost_monthly"] = st.number_input(
            "Holding costs per maand (€)",
            value=int(params["holding_cost_monthly"]),
            step=100,
            help=PARAM_DESCRIPTIONS["holding_cost_monthly"][1],
        )
    with col3:
        updated["project_duration_months"] = st.number_input(
            "Projectduur (maanden)",
            value=int(params["project_duration_months"]),
            step=1,
            min_value=1,
            help=PARAM_DESCRIPTIONS["project_duration_months"][1],
        )

    # === FISCAAL ===
    st.markdown("#### Fiscaal")
    col1, col2 = st.columns(2)
    with col1:
        updated["plusvalenza_rate"] = st.number_input(
            "Meerwaardebelasting (%)",
            value=params["plusvalenza_rate"] * 100,
            step=1.0,
            format="%.0f",
            help=PARAM_DESCRIPTIONS["plusvalenza_rate"][1],
        ) / 100
    with col2:
        updated["asking_price_discount"] = st.number_input(
            "Onderhandelingskorting (%)",
            value=params["asking_price_discount"] * 100,
            step=1.0,
            format="%.0f",
            help=PARAM_DESCRIPTIONS["asking_price_discount"][1],
        ) / 100

    # === FILTERS ===
    st.markdown("#### Filters")
    col1, col2 = st.columns(2)
    with col1:
        updated["min_roi_threshold"] = st.number_input(
            "Minimum ROI drempel (%)",
            value=params["min_roi_threshold"],
            step=1.0,
            format="%.1f",
            help=PARAM_DESCRIPTIONS["min_roi_threshold"][1],
        )
        updated["min_surface_m2"] = st.number_input(
            "Minimum oppervlakte (m²)",
            value=int(params["min_surface_m2"]),
            step=10,
        )
        updated["min_price"] = st.number_input(
            "Minimum prijs (€)",
            value=int(params["min_price"]),
            step=10000,
        )
    with col2:
        updated["max_surface_m2"] = st.number_input(
            "Maximum oppervlakte (m²)",
            value=int(params["max_surface_m2"]),
            step=10,
        )
        updated["max_price"] = st.number_input(
            "Maximum prijs (€)",
            value=int(params["max_price"]),
            step=10000,
        )

    # === ACTIES ===
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Reset naar defaults", use_container_width=True):
            updated = DEFAULT_PARAMS.copy()
            st.success("Parameters gereset naar standaardwaarden.")
            st.rerun()
    with col2:
        if st.button("Sla op als profiel", use_container_width=True):
            try:
                with open("saved_params.json", "w") as f:
                    json.dump(updated, f, indent=2)
                st.success("Parameters opgeslagen als saved_params.json")
            except Exception as e:
                st.error(f"Fout bij opslaan: {e}")
    with col3:
        uploaded_profile = st.file_uploader("Laad profiel", type=["json"], key="profile_upload")
        if uploaded_profile:
            try:
                loaded = json.loads(uploaded_profile.read().decode("utf-8"))
                updated.update(loaded)
                st.success("Profiel geladen!")
            except Exception as e:
                st.error(f"Fout bij laden profiel: {e}")

    return updated
