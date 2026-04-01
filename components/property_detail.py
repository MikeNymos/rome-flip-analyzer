"""
Individuele pand-analyse view met foto's, interactieve sliders,
onderbouwde verkoopprijsschatting, locatieanalyse en volledige P&L.
"""
from __future__ import annotations

import json
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go

from utils.helpers import format_eur, format_pct, format_m2, format_eur_per_m2, score_color
from config import get_score_label
from data.constants import CONDITION_MAP
from models.financial import calculate_investment_analysis, calculate_sensitivity
from models.scoring import calculate_flip_score
from models.risk import analyze_description


def render_property_detail(listing: dict, analysis: dict, score_data: dict, params: dict):
    """Rendert de volledige analyse voor een individueel pand."""

    # === 1. FOTO'S + HEADER ===
    _render_photo_gallery(listing)
    _render_header(listing, score_data)

    st.divider()

    # === 2. INTERACTIEVE SLIDERS ===
    # Sliders use the ORIGINAL analysis for defaults, return current overrides
    overrides = _render_parameter_sliders(listing, analysis, params)

    # Recalculate with current slider values so P&L etc. update immediately
    if overrides:
        analysis = calculate_investment_analysis(listing, params, overrides)
        score_data = calculate_flip_score(listing, analysis, params)

    st.divider()

    # === 3. VERKOOPPRIJSONDERBOUWING ===
    st.subheader("Verkoopprijsschatting -- Onderbouwing")
    _render_sale_price_justification(listing, analysis)

    st.divider()

    # === 4. LOCATIEANALYSE ===
    st.subheader("Locatieanalyse")
    _render_location_analysis(listing, analysis)

    st.divider()

    # === 5. P&L TABEL ===
    st.subheader("Winst & Verliesrekening")
    _render_pnl_table(analysis)

    st.divider()

    # === 6. SCORE BREAKDOWN MET TOELICHTINGEN ===
    _render_score_breakdown(score_data)

    st.divider()

    # === 7. BESCHRIJVINGSANALYSE ===
    _render_description_analysis(listing)

    st.divider()

    # === 8. GEVOELIGHEIDSANALYSE ===
    st.subheader("Gevoeligheidsanalyse")
    _render_sensitivity(listing, params, overrides or None)

    st.divider()

    # === 9. ACTIES ===
    _render_actions(listing, analysis, score_data, params)


# ============================================================
# FOTO GALERIJ
# ============================================================

def _render_photo_gallery(listing: dict):
    """Toont een interactieve fotogalerij met pijlnavigatie en thumbnail-strip."""
    images = listing.get("images", [])
    if not images:
        return

    # Cap at 30 for performance
    imgs = images[:30]
    total = len(images)
    imgs_json = json.dumps(imgs)

    html = f"""
    <style>
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      .gallery {{ position:relative; width:100%; background:#111; border-radius:8px; overflow:hidden; }}
      .main-img {{ width:100%; height:480px; object-fit:contain; display:block; }}
      .arrow {{ position:absolute; top:50%; transform:translateY(-50%); width:48px; height:48px;
                background:rgba(0,0,0,0.45); border:none; color:#fff; font-size:28px;
                cursor:pointer; border-radius:50%; opacity:0; transition:opacity .2s; z-index:2; }}
      .gallery:hover .arrow {{ opacity:1; }}
      .arrow:hover {{ background:rgba(0,0,0,0.7); }}
      .arrow-l {{ left:12px; }}
      .arrow-r {{ right:12px; }}
      .counter {{ position:absolute; bottom:12px; right:12px; background:rgba(0,0,0,0.6);
                  color:#fff; padding:4px 12px; border-radius:16px; font-size:13px; z-index:2; }}
      .thumbs {{ display:flex; gap:6px; overflow-x:auto; padding:8px 0; scrollbar-width:thin; }}
      .thumbs::-webkit-scrollbar {{ height:6px; }}
      .thumbs::-webkit-scrollbar-thumb {{ background:#ccc; border-radius:3px; }}
      .thumb {{ min-width:100px; height:70px; object-fit:cover; border-radius:4px;
                cursor:pointer; opacity:0.5; transition:opacity .2s; border:2px solid transparent; }}
      .thumb:hover {{ opacity:0.85; }}
      .thumb.active {{ opacity:1; border-color:#1a365d; }}
    </style>
    <div class="gallery" id="gal">
      <img class="main-img" id="main" src="{imgs[0]}">
      <button class="arrow arrow-l" onclick="nav(-1)">&lsaquo;</button>
      <button class="arrow arrow-r" onclick="nav(1)">&rsaquo;</button>
      <span class="counter" id="ctr">1 / {total}</span>
    </div>
    <div class="thumbs" id="thumbs"></div>
    <script>
      var imgs = {imgs_json};
      var total = {total};
      var cur = 0;
      var thumbsEl = document.getElementById('thumbs');
      imgs.forEach(function(src, i) {{
        var t = document.createElement('img');
        t.src = src;
        t.className = 'thumb' + (i === 0 ? ' active' : '');
        t.onclick = function() {{ goTo(i); }};
        thumbsEl.appendChild(t);
      }});
      function nav(dir) {{
        goTo((cur + dir + imgs.length) % imgs.length);
      }}
      function goTo(i) {{
        cur = i;
        document.getElementById('main').src = imgs[cur];
        document.getElementById('ctr').textContent = (cur+1) + ' / ' + total;
        var ts = thumbsEl.querySelectorAll('.thumb');
        ts.forEach(function(t, j) {{ t.className = 'thumb' + (j===cur?' active':''); }});
        ts[cur].scrollIntoView({{ behavior:'smooth', inline:'center', block:'nearest' }});
      }}
      document.addEventListener('keydown', function(e) {{
        if (e.key === 'ArrowLeft') nav(-1);
        if (e.key === 'ArrowRight') nav(1);
      }});
    </script>
    """
    components.html(html, height=590)


# ============================================================
# HEADER
# ============================================================

def _render_header(listing: dict, score_data: dict):
    """Toont pand-header met score en kerngetallen."""
    score = score_data["flip_score"]
    label, color, meaning = get_score_label(score)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        st.markdown(
            f"<div style='text-align:center; padding:20px; background-color:{color}20; "
            f"border-radius:12px; border: 2px solid {color};'>"
            f"<h1 style='color:{color}; margin:0;'>{score}</h1>"
            f"<p style='color:{color}; margin:0; font-weight:bold;'>{label}</p>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(f"### {listing.get('title', 'Onbekend pand')}")
        condition_label = CONDITION_MAP.get(listing.get("condition", ""), listing.get("condition", ""))

        info_parts = []
        if listing.get("zone"):
            info_parts.append(f"**Wijk:** {listing['zone']}")
        if listing.get("address"):
            info_parts.append(f"**Adres:** {listing['address']}")
        if listing.get("floor") is not None:
            floor_text = "Begane grond" if listing["floor"] == 0 else f"Verdieping {listing['floor']}"
            if listing.get("has_elevator") is not None:
                floor_text += " (met lift)" if listing["has_elevator"] else " (zonder lift)"
            info_parts.append(f"**Verdieping:** {floor_text}")
        if condition_label:
            info_parts.append(f"**Staat:** {condition_label}")
        if listing.get("energy_class"):
            info_parts.append(f"**Energieklasse:** {listing['energy_class']}")

        st.markdown(" | ".join(info_parts))

    with col3:
        st.metric("Vraagprijs", format_eur(listing["price"]))
        st.metric("Oppervlakte", format_m2(listing["surface_m2"]))
        st.metric("Prijs/m2", format_eur_per_m2(listing["price_per_m2"]))


# ============================================================
# INTERACTIEVE PARAMETER SLIDERS
# ============================================================

def _render_parameter_sliders(listing: dict, analysis: dict, params: dict) -> dict | None:
    """
    Interactieve sliders voor per-pand parameter aanpassing.
    Returns overrides dict if sliders differ from defaults, else None.
    """
    sale_estimate = analysis.get("sale_price_estimate", {})
    final_prices = sale_estimate.get("final_price_per_m2", {})

    # Defaults from original analysis
    default_reno = params["renovation_cost_min_per_m2"]
    default_sale = int(final_prices.get("mid", 6000))
    default_discount = int(params["asking_price_discount"] * 100)

    with st.expander("Parameters aanpassen (dit pand)", expanded=False):
        st.caption("Pas de sliders aan om de berekeningen voor dit specifieke pand te wijzigen.")
        col1, col2, col3 = st.columns(3)

        with col1:
            reno_cost = st.slider(
                "Renovatiekosten (EUR/m2)",
                min_value=800, max_value=2500,
                value=default_reno,
                step=50,
                key=f"slider_reno_{listing.get('url', '')}",
            )

        with col2:
            sale_price = st.slider(
                "Verkoopprijs (EUR/m2)",
                min_value=3000, max_value=15000,
                value=default_sale,
                step=100,
                key=f"slider_sale_{listing.get('url', '')}",
            )

        with col3:
            discount = st.slider(
                "Onderhandelingskorting (%)",
                min_value=0, max_value=20,
                value=default_discount,
                step=1,
                key=f"slider_discount_{listing.get('url', '')}",
            )

    # Check if any slider was changed from defaults
    changed = (reno_cost != default_reno or sale_price != default_sale or discount != default_discount)

    if not changed:
        return None

    overrides = {
        "renovation_cost_per_m2": reno_cost,
        "sale_price_per_m2_mid": sale_price,
        "sale_price_per_m2_low": int(sale_price * 0.88),
        "sale_price_per_m2_high": int(sale_price * 1.12),
        "asking_price_discount": discount / 100,
    }

    # Sla op in session state
    key = listing.get("url", str(id(listing)))
    st.session_state.setdefault("property_overrides", {})[key] = overrides
    return overrides


# ============================================================
# VERKOOPPRIJSONDERBOUWING
# ============================================================

def _render_sale_price_justification(listing: dict, analysis: dict):
    """Toont WAAROM de geschatte verkoopprijs is wat het is."""
    sale_estimate = analysis.get("sale_price_estimate", {})
    if not sale_estimate:
        st.warning("Geen verkoopprijsschatting beschikbaar.")
        return

    neighborhood_name = sale_estimate.get("neighborhood_name", "Onbekend")
    base_prices = sale_estimate.get("base_price_per_m2", {})
    adjustments = sale_estimate.get("adjustments", [])
    final_prices = sale_estimate.get("final_price_per_m2", {})
    surface = listing["surface_m2"]

    # Basisprijs uitleg
    st.info(
        f"**Wijkbenchmark: {neighborhood_name}**\n\n"
        f"Gerenoveerde woningen in {neighborhood_name} worden verkocht voor "
        f"**{format_eur_per_m2(base_prices.get('low', 0))}** (laag) tot "
        f"**{format_eur_per_m2(base_prices.get('high', 0))}** (hoog), "
        f"met een middenprijs van **{format_eur_per_m2(base_prices.get('mid', 0))}**.\n\n"
        f"_Bron: marktanalyse vergelijkbare transacties in {neighborhood_name}_"
    )

    # Correcties
    if adjustments:
        st.markdown("**Correcties op basis van dit pand:**")
        for adj in adjustments:
            pct = adj["adjustment_pct"]
            eur = adj.get("adjustment_eur_per_m2", 0)
            sign = "+" if pct > 0 else ""
            icon = ":green[+]" if pct > 0 else ":red[-]"
            st.markdown(
                f"- {icon} **{adj['name']}**: {sign}{pct*100:.0f}% "
                f"({sign}{eur} EUR/m2) -- {adj['explanation']}"
            )

    # Geschatte verkoopprijs
    st.markdown("**Geschatte verkoopprijs na renovatie:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Laag",
            format_eur(final_prices.get("low", 0) * surface),
            help=format_eur_per_m2(final_prices.get("low", 0)),
        )
    with col2:
        st.metric(
            "Verwacht",
            format_eur(final_prices.get("mid", 0) * surface),
            help=format_eur_per_m2(final_prices.get("mid", 0)),
        )
    with col3:
        st.metric(
            "Hoog",
            format_eur(final_prices.get("high", 0) * surface),
            help=format_eur_per_m2(final_prices.get("high", 0)),
        )


# ============================================================
# LOCATIEANALYSE
# ============================================================

def _render_location_analysis(listing: dict, analysis: dict):
    """Rendert de multi-factor locatiekwaliteitsanalyse."""
    location = analysis.get("location_quality", {})
    if not location:
        st.info("Geen locatieanalyse beschikbaar.")
        return

    overall = location.get("overall_score", 50)
    color = score_color(overall)

    st.markdown(
        f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">'
        f'<span style="background:{color};color:white;padding:8px 16px;border-radius:8px;'
        f'font-size:1.3em;font-weight:bold;">{overall}/100</span>'
        f'<span style="font-size:1.1em;">{location.get("summary", "")}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    factors = location.get("factors", [])
    positive = [f for f in factors if f["category"] == "positief"]
    negative = [f for f in factors if f["category"] == "negatief"]
    neutral = [f for f in factors if f["category"] == "neutraal"]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Positieve factoren:**")
        if positive:
            for f in positive:
                st.markdown(f"- :green[+{f['impact']}] **{f['name']}**: {f['explanation']}")
        else:
            st.caption("Geen positieve locatiefactoren geidentificeerd.")

    with col2:
        st.markdown("**Negatieve factoren:**")
        if negative:
            for f in negative:
                st.markdown(f"- :red[{f['impact']}] **{f['name']}**: {f['explanation']}")
        else:
            st.caption("Geen negatieve locatiefactoren geidentificeerd.")

    if neutral:
        for f in neutral:
            st.markdown(f"- **{f['name']}**: {f['explanation']}")


# ============================================================
# P&L TABEL
# ============================================================

def _render_pnl_table(analysis: dict):
    """Rendert de P&L tabel met prima casa als hoofdscenario."""
    prima = analysis.get("prima_casa", analysis.get("optimistic", {}))
    seconda = analysis.get("seconda_casa", analysis.get("conservative", {}))

    st.info(
        "**Prima casa** is het hoofdscenario: aankoop als eerste woning (2% registratiebelasting, "
        "geen meerwaardebelasting). **Seconda casa** ter vergelijking (9% belasting, 26% plusvalenza)."
    )

    rows = [
        ("**AANKOOPZIJDE**", "", ""),
        ("Aankoopprijs", format_eur(prima.get("purchase_price", 0)), format_eur(seconda.get("purchase_price", 0))),
        ("Registratiebelasting", format_eur(prima.get("registration_tax", 0)), format_eur(seconda.get("registration_tax", 0))),
        ("Notaris + kadaster", format_eur(prima.get("notary", 0)), format_eur(seconda.get("notary", 0))),
        ("Makelaar aankoop", format_eur(prima.get("broker_buy", 0)), format_eur(seconda.get("broker_buy", 0))),
        ("Renovatiekosten", format_eur(prima.get("renovation", 0)), format_eur(seconda.get("renovation", 0))),
        ("Architect + vergunningen", format_eur(prima.get("architect", 0)), format_eur(seconda.get("architect", 0))),
        ("Onvoorzien", format_eur(prima.get("contingency", 0)), format_eur(seconda.get("contingency", 0))),
        ("Holding costs", format_eur(prima.get("holding_costs", 0)), format_eur(seconda.get("holding_costs", 0))),
        ("**TOTALE INVESTERING**", f"**{format_eur(prima.get('total_investment', 0))}**", f"**{format_eur(seconda.get('total_investment', 0))}**"),
        ("---", "---", "---"),
        ("**VERKOOPZIJDE**", "", ""),
        ("Geschatte verkoopprijs", format_eur(prima.get("sale_price", 0)), format_eur(seconda.get("sale_price", 0))),
        ("Verkoopprijs/m2", format_eur_per_m2(prima.get("sale_price_per_m2", 0)), format_eur_per_m2(seconda.get("sale_price_per_m2", 0))),
        ("Makelaar verkoop", format_eur(prima.get("broker_sell", 0)), format_eur(seconda.get("broker_sell", 0))),
        ("Plusvalenza (26%)", format_eur(prima.get("plusvalenza_tax", 0)), format_eur(seconda.get("plusvalenza_tax", 0))),
        ("**NETTO OPBRENGST**", f"**{format_eur(prima.get('net_revenue', 0))}**", f"**{format_eur(seconda.get('net_revenue', 0))}**"),
        ("---", "---", "---"),
        ("**NETTO WINST**", f"**{format_eur(prima.get('net_profit', 0))}**", f"**{format_eur(seconda.get('net_profit', 0))}**"),
        ("**ROI**", f"**{format_pct(prima.get('roi', 0))}**", f"**{format_pct(seconda.get('roi', 0))}**"),
    ]

    md = "| Kostenpost | Prima Casa (2%) | Seconda Casa (9%) |\n"
    md += "|:-----------|---------------------------:|----------------------------:|\n"
    for label, prima_val, seconda_val in rows:
        if label == "---":
            md += "| | | |\n"
        else:
            md += f"| {label} | {prima_val} | {seconda_val} |\n"

    st.markdown(md)


# ============================================================
# SCORE BREAKDOWN MET TOELICHTINGEN
# ============================================================

def _render_score_breakdown(score_data: dict):
    """Rendert de score breakdown met uitklapbare toelichtingen."""
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Flip Score Breakdown")
        _render_score_radar(score_data)

        # Uitklapbare toelichtingen per component
        explanations = score_data.get("score_explanations", {})
        categories = ["ROI", "Marge", "Locatie", "Risico", "Liquiditeit", "Oppervlakte"]
        keys = ["roi", "margin", "neighborhood", "risk", "liquidity", "surface"]

        for cat, key in zip(categories, keys):
            val = score_data["component_scores"].get(key, 0)
            weight_pct = score_data["weights"][key] * 100
            with st.expander(f"{cat}: {val}/100 (gewicht: {weight_pct:.0f}%)"):
                st.markdown(explanations.get(key, "Geen toelichting beschikbaar."))

    with col2:
        st.subheader("Risicovlaggen")
        _render_risk_flags(score_data)


def _render_score_radar(score_data: dict):
    """Radar chart met de 6 score-componenten."""
    scores = score_data["component_scores"]
    categories = ["ROI", "Marge", "Locatie", "Risico", "Liquiditeit", "Oppervlakte"]
    keys = ["roi", "margin", "neighborhood", "risk", "liquidity", "surface"]
    values = [scores.get(k, 0) for k in keys]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill="toself",
        name="Score",
        line_color="#1a365d",
        fillcolor="rgba(26, 54, 93, 0.2)",
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False, height=350,
        margin=dict(l=40, r=40, t=40, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_risk_flags(score_data: dict):
    """Toont risicovlaggen."""
    risk_flags = score_data.get("risk_flags", [])
    if not risk_flags:
        st.success("Geen risicovlaggen gevonden.")
    else:
        for flag in risk_flags:
            st.warning(flag)


# ============================================================
# BESCHRIJVINGSANALYSE
# ============================================================

def _render_description_analysis(listing: dict):
    """Analyseert en toont beschrijvings-keywords."""
    description = listing.get("description", "")
    if not description:
        return

    st.subheader("Beschrijvingsanalyse")
    result = analyze_description(description)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Positieve indicatoren:**")
        if result["positive"]:
            for item in result["positive"]:
                st.markdown(f"- :green[{item['label']}] (`{item['keyword']}`)")
        else:
            st.caption("Geen positieve keywords gevonden")

    with col2:
        st.markdown("**Negatieve indicatoren:**")
        if result["negative"]:
            for item in result["negative"]:
                st.markdown(f"- :red[{item['label']}] (`{item['keyword']}`)")
        else:
            st.caption("Geen negatieve keywords gevonden")

    if result["red_flags"]:
        st.error("**Red flags gevonden in beschrijving:**")
        for rf in result["red_flags"]:
            st.error(f"- {rf['keyword']} (impact: {rf['penalty']} punten)")


# ============================================================
# GEVOELIGHEIDSANALYSE
# ============================================================

def _render_sensitivity(listing: dict, params: dict, overrides: dict | None = None):
    """Toont gevoeligheidsanalyse tabel."""
    scenarios = calculate_sensitivity(listing, params, overrides)

    md = "| Scenario | Midpoint ROI | Winst Prima Casa | Winst Seconda Casa | Delta ROI |\n"
    md += "|:---------|------------:|-----------------:|-------------------:|----------:|\n"
    for s in scenarios:
        delta_sign = "+" if s["delta_roi"] >= 0 else ""
        md += (
            f"| {s['scenario']} | {format_pct(s['midpoint_roi'])} | "
            f"{format_eur(s.get('prima_profit', s.get('cons_profit', 0)))} | "
            f"{format_eur(s.get('seconda_profit', s.get('opti_profit', 0)))} | "
            f"{delta_sign}{format_pct(s['delta_roi'])} |\n"
        )

    st.markdown(md)


# ============================================================
# ACTIES
# ============================================================

def _render_actions(listing: dict, analysis: dict, score_data: dict, params: dict):
    """Rendert actieknoppen met directe PDF export."""
    from services.pdf_export import generate_property_report

    col1, col2 = st.columns(2)
    with col1:
        if listing.get("url"):
            st.link_button("Open op Immobiliare.it", listing["url"], use_container_width=True)
    with col2:
        pdf_state_key = f"pdf_{listing.get('url', 'unknown')}"
        if st.button("Genereer PDF", key="pdf_export_btn", use_container_width=True):
            with st.spinner("PDF genereren..."):
                pdf_bytes = generate_property_report(listing, analysis, score_data, params)
            st.session_state[pdf_state_key] = pdf_bytes

        if pdf_state_key in st.session_state:
            st.download_button(
                label="Download PDF Rapport",
                data=st.session_state[pdf_state_key],
                file_name=f"flip_analyse_{listing.get('zone', 'pand')}_{listing.get('price', 0):.0f}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
