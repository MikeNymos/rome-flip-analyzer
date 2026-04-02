"""
Hoofd-dashboard view met samenvattingskaarten, visuele property cards en charts.
"""
from __future__ import annotations

import json
from urllib.parse import quote
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.helpers import format_eur, format_pct, format_m2, format_eur_per_m2, score_color, get_plotly_layout
from config import get_score_label, DESIGN
from services.auth import is_logged_in, get_current_user
from services.database import toggle_favorite, is_favorite


SORT_OPTIONS = {
    "Flip Score (hoog → laag)": ("flip_score", True),
    "Flip Score (laag → hoog)": ("flip_score", False),
    "Prijs (laag → hoog)": ("price", False),
    "Prijs (hoog → laag)": ("price", True),
    "Prijs/m² (laag → hoog)": ("price_per_m2", False),
    "Prijs/m² (hoog → laag)": ("price_per_m2", True),
    "ROI (hoog → laag)": ("roi_prima_casa", True),
    "ROI (laag → hoog)": ("roi_prima_casa", False),
    "Nieuwste eerst": ("listing_id", True),
    "Oudste eerst": ("listing_id", False),
}


def _sort_listings(listings: list[dict], sort_key: str, reverse: bool) -> list[dict]:
    """Sorteer listings op een gegeven key, None-waarden komen altijd achteraan."""
    def sort_val(item):
        val = item.get(sort_key)
        if val is None:
            return (1, 0)  # Altijd achteraan
        if reverse:
            return (0, -val)  # Negeer waarde voor aflopende sortering
        return (0, val)

    return sorted(listings, key=sort_val)


def render_dashboard(analyzed_listings: list[dict]):
    """Rendert het hoofddashboard met samenvatting, kaarten en charts."""
    if not analyzed_listings:
        st.info("Geen geanalyseerde panden beschikbaar. Gebruik de zijbalk om data te laden.")
        return

    _render_summary_cards(analyzed_listings)
    st.divider()

    # Sorteeroptie + header
    sort_col, header_col = st.columns([1, 2])
    with header_col:
        st.subheader("Alle Panden")
    with sort_col:
        sort_label = st.selectbox(
            "Sorteren op",
            list(SORT_OPTIONS.keys()),
            index=0,
            key="dashboard_sort",
        )
    sort_field, sort_reverse = SORT_OPTIONS[sort_label]

    # Check of listing_id beschikbaar is voor nieuwste/oudste sortering
    has_ids = any(l.get("listing_id") is not None for l in analyzed_listings)
    if sort_field == "listing_id" and not has_ids:
        st.caption("Publicatievolgorde niet beschikbaar voor deze dataset. Fallback naar Flip Score.")
        sort_field, sort_reverse = "flip_score", True

    sorted_listings = _sort_listings(analyzed_listings, sort_field, sort_reverse)
    selected_idx = _render_property_cards(sorted_listings, analyzed_listings)

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


def _render_property_cards(sorted_listings: list[dict], original_listings: list[dict]) -> int | None:
    """Rendert een grid van visuele property cards.

    Args:
        sorted_listings: Listings in de huidige sorteervolgorde (voor weergave).
        original_listings: Originele (ongesorteerde) lijst (voor index-mapping).

    Returns:
        Index in original_listings van het geselecteerde pand, of None.
    """
    selected_idx = None
    COLS = 3

    # Bouw een lookup van url → originele index
    url_to_orig_idx: dict[str, int] = {}
    for i, l in enumerate(original_listings):
        url = l.get("url", "")
        if url:
            url_to_orig_idx[url] = i

    for row_start in range(0, len(sorted_listings), COLS):
        row_listings = sorted_listings[row_start:row_start + COLS]
        cols = st.columns(COLS)

        for col_idx, listing in enumerate(row_listings):
            display_idx = row_start + col_idx
            with cols[col_idx]:
                if _render_single_card(listing, display_idx):
                    # Map terug naar originele index
                    url = listing.get("url", "")
                    selected_idx = url_to_orig_idx.get(url, display_idx)

    return selected_idx


def _render_image_carousel(images: list[str], idx: int):
    """Render an interactive image carousel with arrow navigation."""
    imgs = images[:15]  # Cap for performance
    total = len(images)
    imgs_json = json.dumps(imgs)

    html = f"""
    <div id="carousel-{idx}" style="position:relative;width:100%;height:200px;
         border-radius:12px;overflow:hidden;background:#EDE7E0;">
      <img id="img-{idx}" src="{imgs[0]}"
           style="width:100%;height:200px;object-fit:cover;" loading="lazy">
      <button onclick="nav({idx},-1)" style="position:absolute;left:0;top:0;width:36px;
              height:100%;background:rgba(0,0,0,0.25);border:none;color:#fff;
              font-size:22px;cursor:pointer;opacity:0;transition:opacity .2s;"
              onmouseenter="this.style.opacity='1'"
              onmouseleave="this.style.opacity='0'"
              id="prev-{idx}">&lsaquo;</button>
      <button onclick="nav({idx},1)" style="position:absolute;right:0;top:0;width:36px;
              height:100%;background:rgba(0,0,0,0.25);border:none;color:#fff;
              font-size:22px;cursor:pointer;opacity:0;transition:opacity .2s;"
              onmouseenter="this.style.opacity='1'"
              onmouseleave="this.style.opacity='0'"
              id="next-{idx}">&rsaquo;</button>
      <span id="counter-{idx}" style="position:absolute;bottom:6px;right:8px;
            background:rgba(0,0,0,0.55);color:#fff;padding:2px 8px;border-radius:10px;
            font-size:12px;">1 / {total}</span>
    </div>
    <script>
      var imgs_{idx} = {imgs_json};
      var cur_{idx} = 0;
      var total_{idx} = {total};
      function nav(id, dir) {{
        cur_{idx} = (cur_{idx} + dir + imgs_{idx}.length) % imgs_{idx}.length;
        document.getElementById('img-'+id).src = imgs_{idx}[cur_{idx}];
        document.getElementById('counter-'+id).textContent =
          (cur_{idx}+1) + ' / ' + total_{idx};
      }}
      // Show arrows on hover over the container
      var c = document.getElementById('carousel-{idx}');
      c.addEventListener('mouseenter', function() {{
        document.getElementById('prev-{idx}').style.opacity = '1';
        document.getElementById('next-{idx}').style.opacity = '1';
      }});
      c.addEventListener('mouseleave', function() {{
        document.getElementById('prev-{idx}').style.opacity = '0';
        document.getElementById('next-{idx}').style.opacity = '0';
      }});
    </script>
    """
    components.html(html, height=210)


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
        # Photo carousel or placeholder
        if images:
            _render_image_carousel(images, idx)
        else:
            st.markdown(
                '<div style="background:#EDE7E0;height:200px;display:flex;'
                'align-items:center;justify-content:center;border-radius:12px;">'
                '<span style="color:#B0AAA3;font-size:0.9em;">Geen foto</span></div>',
                unsafe_allow_html=True,
            )

        # Score badge + favoriet hart
        listing_url = listing.get("url", "")
        user = get_current_user() if is_logged_in() else None
        is_fav = False
        if user and listing_url:
            fav_cache_key = f"fav_{user['id']}_{listing_url}"
            if fav_cache_key not in st.session_state:
                st.session_state[fav_cache_key] = is_favorite(user["id"], listing_url)
            is_fav = st.session_state[fav_cache_key]

        heart_html = ""
        if user:
            heart_icon = "&#10084;" if is_fav else "&#9825;"
            heart_color = "#e53e3e" if is_fav else "#a0aec0"
            heart_html = (
                f'<span style="color:{heart_color};font-size:1.3em;cursor:pointer;" '
                f'title="{"Verwijder uit favorieten" if is_fav else "Toevoegen aan favorieten"}">'
                f'{heart_icon}</span>'
            )

        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;margin:8px 0 4px 0;">'
            f'<span style="background:linear-gradient(135deg,{color},{color}dd);color:white;padding:5px 14px;'
            f'border-radius:12px;font-weight:700;font-size:1.05em;font-family:Inter,sans-serif;'
            f'box-shadow:0 2px 6px {color}40;">{score}</span>'
            f'<span style="color:#7A7672;font-size:0.82em;font-weight:500;">{label}</span>'
            f'<span style="color:#B0AAA3;font-size:0.75em;margin-left:auto;'
            f'font-weight:500;text-transform:uppercase;letter-spacing:0.04em;">'
            f'Locatie {loc_score}/100</span>'
            f'{heart_html}'
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
        if user:
            col_a, col_b, col_fav = st.columns([2, 2, 1])
        else:
            col_a, col_b = st.columns(2)
            col_fav = None

        with col_a:
            search_id = st.session_state.get("last_search_id")
            if search_id and listing_url:
                encoded_url = quote(listing_url, safe="")
                st.markdown(
                    f'<a href="?sid={search_id}&url={encoded_url}" target="_blank" '
                    f'style="display:block;text-align:center;padding:0.5rem 0.75rem;'
                    f'background:linear-gradient(135deg,#C9A24E,#B8913D);'
                    f'border-radius:12px;color:white;font-size:14px;'
                    f'text-decoration:none;line-height:1.6;font-weight:600;'
                    f'font-family:Inter,sans-serif;box-shadow:0 2px 6px rgba(201,162,78,0.2);"'
                    f'>Bekijk detail</a>',
                    unsafe_allow_html=True,
                )
            else:
                if st.button("Bekijk detail", key=f"card_detail_{idx}", use_container_width=True):
                    selected = True
        with col_b:
            url = listing.get("url", "")
            if url:
                st.link_button("Immobiliare", url, use_container_width=True)

        if col_fav and user and listing_url:
            with col_fav:
                fav_label = "❤️" if is_fav else "🤍"
                if st.button(fav_label, key=f"fav_{idx}", help="Favoriet", use_container_width=True):
                    new_state = toggle_favorite(user["id"], listing)
                    fav_cache_key = f"fav_{user['id']}_{listing_url}"
                    st.session_state[fav_cache_key] = new_state
                    st.rerun()

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

    dark = st.session_state.get("dark_mode", False)
    fig = px.scatter(
        df, x="Aankoopprijs", y="ROI Prima Casa (%)", color="Wijk",
        size="Flip Score", hover_data=["m2", "Flip Score"],
        color_discrete_sequence=DESIGN["plotly_colorway"],
    )
    fig.update_layout(height=400, margin=dict(l=20, r=20, t=30, b=20), **get_plotly_layout(dark))
    fig.add_hline(y=15, line_dash="dash", line_color="#B0AAA3", annotation_text="Min. ROI 15%")
    st.plotly_chart(fig, use_container_width=True)


def _render_score_distribution(listings: list[dict]):
    """Bar chart: Flip Score verdeling."""
    st.subheader("Flip Score Verdeling")
    scores = [l.get("flip_score", 0) for l in listings]
    buckets = {"0-34": 0, "35-49": 0, "50-64": 0, "65-79": 0, "80-100": 0}
    colors_list = ["#D4766C", "#D4916A", "#C9A24E", "#7D9B8A", "#5B8A72"]

    for s in scores:
        if s >= 80: buckets["80-100"] += 1
        elif s >= 65: buckets["65-79"] += 1
        elif s >= 50: buckets["50-64"] += 1
        elif s >= 35: buckets["35-49"] += 1
        else: buckets["0-34"] += 1

    fig = go.Figure(data=[go.Bar(
        x=list(buckets.keys()), y=list(buckets.values()), marker_color=colors_list,
    )])
    dark = st.session_state.get("dark_mode", False)
    fig.update_layout(height=400, margin=dict(l=20, r=20, t=30, b=20), showlegend=False, **get_plotly_layout(dark))
    st.plotly_chart(fig, use_container_width=True)
