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
from services.auth import is_logged_in, get_current_user
from services.database import toggle_favorite, is_favorite


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

    # === 3b. MARKT VERGELIJKBARE PANDEN (live van Immobiliare.it) ===
    _render_market_comparables(listing, analysis)

    st.divider()

    # === 4. LOCATIEANALYSE ===
    st.subheader("Locatieanalyse")
    _render_location_analysis(listing, analysis)

    st.divider()

    # === 5. VERKOOPSNELHEID + BETROUWBAARHEID ===
    _render_speed_and_confidence(listing)

    st.divider()

    # === 6. P&L TABEL ===
    st.subheader("Winst & Verliesrekening")
    _render_pnl_table(analysis)

    st.divider()

    # === 7. VERGELIJKBARE PANDEN (BATCH) ===
    _render_comparables(listing)

    st.divider()

    # === 8. SCORE BREAKDOWN MET TOELICHTINGEN ===
    _render_score_breakdown(score_data)

    st.divider()

    # === 9. BESCHRIJVINGSANALYSE ===
    _render_description_analysis(listing)

    st.divider()

    # === 10. GEVOELIGHEIDSANALYSE ===
    st.subheader("Gevoeligheidsanalyse")
    _render_sensitivity(listing, params, overrides or None)

    st.divider()

    # === 11. ACTIES ===
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
      .main-img {{ width:100%; height:480px; object-fit:contain; display:block; cursor:pointer; }}
      .arrow {{ position:absolute; top:50%; transform:translateY(-50%); width:48px; height:48px;
                background:rgba(0,0,0,0.45); border:none; color:#fff; font-size:28px;
                cursor:pointer; border-radius:50%; opacity:0; transition:opacity .2s; z-index:2; }}
      .gallery:hover .arrow {{ opacity:1; }}
      .arrow:hover {{ background:rgba(0,0,0,0.7); }}
      .arrow-l {{ left:12px; }}
      .arrow-r {{ right:12px; }}
      .counter {{ position:absolute; bottom:12px; right:12px; background:rgba(0,0,0,0.6);
                  color:#fff; padding:4px 12px; border-radius:16px; font-size:13px; z-index:2; }}
      .zoom-hint {{ position:absolute; bottom:12px; left:12px; background:rgba(0,0,0,0.6);
                    color:#fff; padding:4px 12px; border-radius:16px; font-size:12px; z-index:2;
                    opacity:0; transition:opacity .2s; pointer-events:none; }}
      .gallery:hover .zoom-hint {{ opacity:0.7; }}
      .thumbs {{ display:flex; gap:6px; overflow-x:auto; padding:8px 0; scrollbar-width:thin; }}
      .thumbs::-webkit-scrollbar {{ height:6px; }}
      .thumbs::-webkit-scrollbar-thumb {{ background:#ccc; border-radius:3px; }}
      .thumb {{ min-width:100px; height:70px; object-fit:cover; border-radius:4px;
                cursor:pointer; opacity:0.5; transition:opacity .2s; border:2px solid transparent; }}
      .thumb:hover {{ opacity:0.85; }}
      .thumb.active {{ opacity:1; border-color:#1a365d; }}

      /* Lightbox overlay */
      .lightbox {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%;
                   background:rgba(0,0,0,0.95); z-index:9999; align-items:center;
                   justify-content:center; flex-direction:column; }}
      .lightbox.open {{ display:flex; }}
      .lightbox-img {{ max-width:90%; max-height:75%; object-fit:contain;
                       border-radius:4px; user-select:none; }}
      .lightbox-close {{ position:absolute; top:16px; right:24px; background:none;
                         border:none; color:#fff; font-size:36px; cursor:pointer;
                         width:48px; height:48px; display:flex; align-items:center;
                         justify-content:center; border-radius:50%; transition:background .2s; z-index:10001; }}
      .lightbox-close:hover {{ background:rgba(255,255,255,0.15); }}
      .lb-arrow {{ position:absolute; top:50%; transform:translateY(-50%); width:56px; height:56px;
                   background:rgba(255,255,255,0.1); border:none; color:#fff; font-size:32px;
                   cursor:pointer; border-radius:50%; transition:background .2s; z-index:10001; }}
      .lb-arrow:hover {{ background:rgba(255,255,255,0.25); }}
      .lb-arrow-l {{ left:20px; }}
      .lb-arrow-r {{ right:20px; }}
      .lb-counter {{ position:absolute; bottom:20px; color:#fff; font-size:14px;
                     background:rgba(0,0,0,0.5); padding:6px 16px; border-radius:20px; }}
      .lb-thumbs {{ position:absolute; bottom:56px; display:flex; gap:6px; max-width:90%;
                    overflow-x:auto; padding:6px; scrollbar-width:thin; }}
      .lb-thumbs::-webkit-scrollbar {{ height:4px; }}
      .lb-thumbs::-webkit-scrollbar-thumb {{ background:rgba(255,255,255,0.3); border-radius:2px; }}
      .lb-thumb {{ width:64px; height:44px; object-fit:cover; border-radius:3px;
                   cursor:pointer; opacity:0.4; transition:opacity .2s; border:2px solid transparent;
                   flex-shrink:0; }}
      .lb-thumb:hover {{ opacity:0.75; }}
      .lb-thumb.active {{ opacity:1; border-color:#fff; }}
    </style>

    <div class="gallery" id="gal">
      <img class="main-img" id="main" src="{imgs[0]}" onclick="openLightbox()">
      <button class="arrow arrow-l" onclick="nav(-1)">&lsaquo;</button>
      <button class="arrow arrow-r" onclick="nav(1)">&rsaquo;</button>
      <span class="counter" id="ctr">1 / {total}</span>
      <span class="zoom-hint">🔍 Klik om te vergroten</span>
    </div>
    <div class="thumbs" id="thumbs"></div>

    <!-- Lightbox overlay -->
    <div class="lightbox" id="lightbox" onclick="closeLightboxBg(event)">
      <button class="lightbox-close" onclick="closeLightbox()">&times;</button>
      <button class="lb-arrow lb-arrow-l" onclick="lbNav(-1)">&lsaquo;</button>
      <img class="lightbox-img" id="lb-img" src="">
      <button class="lb-arrow lb-arrow-r" onclick="lbNav(1)">&rsaquo;</button>
      <div class="lb-thumbs" id="lb-thumbs"></div>
      <span class="lb-counter" id="lb-ctr"></span>
    </div>

    <script>
      var imgs = {imgs_json};
      var total = {total};
      var cur = 0;
      var lbOpen = false;
      var frameOrigStyle = '';

      /* ---- Thumbnail strip (gallery) ---- */
      var thumbsEl = document.getElementById('thumbs');
      imgs.forEach(function(src, i) {{
        var t = document.createElement('img');
        t.src = src;
        t.className = 'thumb' + (i === 0 ? ' active' : '');
        t.onclick = function() {{ goTo(i); }};
        thumbsEl.appendChild(t);
      }});

      /* ---- Lightbox thumbnail strip ---- */
      var lbThumbsEl = document.getElementById('lb-thumbs');
      imgs.forEach(function(src, i) {{
        var t = document.createElement('img');
        t.src = src;
        t.className = 'lb-thumb' + (i === 0 ? ' active' : '');
        t.onclick = function(e) {{ e.stopPropagation(); lbGoTo(i); }};
        lbThumbsEl.appendChild(t);
      }});

      /* ---- Gallery navigation ---- */
      function nav(dir) {{ goTo((cur + dir + imgs.length) % imgs.length); }}
      function goTo(i) {{
        cur = i;
        document.getElementById('main').src = imgs[cur];
        document.getElementById('ctr').textContent = (cur+1) + ' / ' + total;
        var ts = thumbsEl.querySelectorAll('.thumb');
        ts.forEach(function(t, j) {{ t.className = 'thumb' + (j===cur?' active':''); }});
        ts[cur].scrollIntoView({{ behavior:'smooth', inline:'center', block:'nearest' }});
      }}

      /* ---- iframe fullscreen helper ---- */
      function expandIframe() {{
        try {{
          var frame = window.frameElement;
          if (frame) {{
            frameOrigStyle = frame.style.cssText;
            frame.style.cssText = 'position:fixed!important;top:0!important;left:0!important;' +
              'width:100vw!important;height:100vh!important;z-index:99999!important;' +
              'border:none!important;max-width:100vw!important;';
          }}
        }} catch(e) {{}}
      }}
      function restoreIframe() {{
        try {{
          var frame = window.frameElement;
          if (frame) {{
            frame.style.cssText = frameOrigStyle;
          }}
        }} catch(e) {{}}
      }}

      /* ---- Lightbox ---- */
      function openLightbox() {{
        lbOpen = true;
        expandIframe();
        var lb = document.getElementById('lightbox');
        lb.classList.add('open');
        lbGoTo(cur);
      }}
      function closeLightbox() {{
        lbOpen = false;
        document.getElementById('lightbox').classList.remove('open');
        restoreIframe();
      }}
      function closeLightboxBg(e) {{
        if (e.target === document.getElementById('lightbox')) closeLightbox();
      }}
      function lbNav(dir) {{ lbGoTo((cur + dir + imgs.length) % imgs.length); }}
      function lbGoTo(i) {{
        cur = i;
        document.getElementById('lb-img').src = imgs[cur];
        document.getElementById('lb-ctr').textContent = (cur+1) + ' / ' + total;
        /* sync gallery */
        document.getElementById('main').src = imgs[cur];
        document.getElementById('ctr').textContent = (cur+1) + ' / ' + total;
        var ts = thumbsEl.querySelectorAll('.thumb');
        ts.forEach(function(t, j) {{ t.className = 'thumb' + (j===cur?' active':''); }});
        /* lightbox thumbs */
        var lts = lbThumbsEl.querySelectorAll('.lb-thumb');
        lts.forEach(function(t, j) {{ t.className = 'lb-thumb' + (j===cur?' active':''); }});
        lts[cur].scrollIntoView({{ behavior:'smooth', inline:'center', block:'nearest' }});
      }}

      /* ---- Keyboard navigation ---- */
      document.addEventListener('keydown', function(e) {{
        if (e.key === 'Escape' && lbOpen) {{ closeLightbox(); return; }}
        if (e.key === 'ArrowLeft') {{ if (lbOpen) lbNav(-1); else nav(-1); }}
        if (e.key === 'ArrowRight') {{ if (lbOpen) lbNav(1); else nav(1); }}
      }});

      /* ---- Touch swipe support for lightbox ---- */
      var touchStartX = 0;
      var lbEl = document.getElementById('lightbox');
      lbEl.addEventListener('touchstart', function(e) {{
        touchStartX = e.changedTouches[0].screenX;
      }}, {{ passive: true }});
      lbEl.addEventListener('touchend', function(e) {{
        var dx = e.changedTouches[0].screenX - touchStartX;
        if (Math.abs(dx) > 50) {{ lbNav(dx < 0 ? 1 : -1); }}
      }}, {{ passive: true }});
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
        # Titel + favorieten knop
        title_col, fav_col = st.columns([5, 1])
        with title_col:
            st.markdown(f"### {listing.get('title', 'Onbekend pand')}")
        with fav_col:
            user = get_current_user() if is_logged_in() else None
            listing_url = listing.get("url", "")
            if user and listing_url:
                fav_cache_key = f"fav_{user['id']}_{listing_url}"
                if fav_cache_key not in st.session_state:
                    st.session_state[fav_cache_key] = is_favorite(user["id"], listing_url)
                is_fav = st.session_state[fav_cache_key]
                fav_label = "❤️ Favoriet" if is_fav else "🤍 Favoriet"
                if st.button(fav_label, key="detail_fav_btn", use_container_width=True):
                    new_state = toggle_favorite(user["id"], listing)
                    st.session_state[fav_cache_key] = new_state
                    st.rerun()

        condition_label = CONDITION_MAP.get(listing.get("condition", ""), listing.get("condition", ""))

        info_parts = []
        if listing.get("zone"):
            info_parts.append(f"**Wijk:** {listing['zone']}")

        # Adres met Google Maps link
        if listing.get("address"):
            address = listing["address"]
            lat = listing.get("latitude")
            lng = listing.get("longitude")
            if lat and lng:
                maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"
            else:
                from urllib.parse import quote as url_quote
                maps_query = f"{address}, {listing.get('zone', '')}, Roma, Italia"
                maps_url = f"https://www.google.com/maps/search/?api=1&query={url_quote(maps_query)}"
            info_parts.append(f"**Adres:** [{address}]({maps_url})")

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
    """Toont WAAROM de geschatte verkoopprijs is wat het is, met bronnen en voorbeelden."""
    sale_estimate = analysis.get("sale_price_estimate", {})
    if not sale_estimate:
        st.warning("Geen verkoopprijsschatting beschikbaar.")
        return

    neighborhood_name = sale_estimate.get("neighborhood_name", "Onbekend")
    base_prices = sale_estimate.get("base_price_per_m2", {})
    adjustments = sale_estimate.get("adjustments", [])
    final_prices = sale_estimate.get("final_price_per_m2", {})
    surface = listing["surface_m2"]
    data_period = sale_estimate.get("data_period", "")
    sources = sale_estimate.get("sources", [])
    transactions = sale_estimate.get("recent_transactions", [])
    comparable_url = sale_estimate.get("comparable_search_url", "")

    # Basisprijs uitleg met bronverwijzingen
    source_text = ""
    if data_period:
        source_text += f"Periode: **{data_period}**. "
    if sources:
        source_links = ", ".join(
            f"[{s['name']}]({s['url']})" for s in sources
        )
        source_text += f"Bronnen: {source_links}"

    st.info(
        f"**Wijkbenchmark: {neighborhood_name}**\n\n"
        f"Gerenoveerde woningen in {neighborhood_name} worden verkocht voor "
        f"**{format_eur_per_m2(base_prices.get('low', 0))}** (laag) tot "
        f"**{format_eur_per_m2(base_prices.get('high', 0))}** (hoog), "
        f"met een middenprijs van **{format_eur_per_m2(base_prices.get('mid', 0))}**.\n\n"
        + (f"{source_text}" if source_text else "")
    )

    # Recente transacties als onderbouwing
    if transactions:
        with st.expander(f"Recente vergelijkbare verkopen in {neighborhood_name} ({len(transactions)} voorbeelden)", expanded=False):
            tx_md = "| Adres | Type | Prijs/m² | Opp. | Datum |\n"
            tx_md += "|:------|:-----|----------:|-----:|------:|\n"
            for tx in transactions:
                tx_md += (
                    f"| {tx['address']} | {tx['type']} | "
                    f"€{tx['price_m2']:,.0f}/m² | {tx['surface']}m² | "
                    f"{tx['date']} |\n"
                )
            st.markdown(tx_md)
            st.caption(
                "Deze transacties zijn representatieve referenties voor gerenoveerde "
                "woningen in deze wijk. Exacte prijzen kunnen variëren op basis van "
                "specifieke pandkenmerken."
            )
            if comparable_url:
                st.markdown(
                    f"[Bekijk vergelijkbare woningen op Immobiliare.it]({comparable_url})"
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
# MARKT VERGELIJKBARE PANDEN (LIVE IMMOBILIARE.IT)
# ============================================================

def _render_market_comparables(listing: dict, analysis: dict):
    """
    Haalt vergelijkbare gerenoveerde panden op van Immobiliare.it
    en toont ze als kaartjes met foto, prijs, afstand en link.

    Wordt gecacht in session state per pand-URL zodat we niet
    bij elke rerender opnieuw scrapen.
    """
    from services.apify_client import fetch_market_comparables

    sale_estimate = analysis.get("sale_price_estimate", {})
    final_prices = sale_estimate.get("final_price_per_m2", {})
    comparable_url = sale_estimate.get("comparable_search_url", "")
    surface = listing.get("surface_m2", 0)

    if not comparable_url or not surface:
        return

    # Bereken doelverkoopprijs (mid-scenario)
    sale_price_mid = final_prices.get("mid", 0) * surface
    if sale_price_mid <= 0:
        return

    st.subheader("Marktvalidatie — Vergelijkbare Te Koop")
    st.caption(
        "Panden momenteel te koop in dezelfde wijk en prijsklasse. "
        "Vergelijk deze met je geschatte verkoopprijs om te valideren of je inschatting klopt."
    )

    # Cache key per pand + verkoopprijs (zodat wijzigen van slider ook herlaadt)
    price_bucket = int(sale_price_mid / 25000) * 25000  # Afronden op 25k blokken
    cache_key = f"market_comps_{listing.get('url', '')}_{price_bucket}"

    if cache_key not in st.session_state:
        # Haal op met spinner
        with st.spinner("Vergelijkbare panden ophalen van Immobiliare.it..."):
            try:
                comps = fetch_market_comparables(
                    comparable_search_url=comparable_url,
                    target_price=sale_price_mid,
                    target_surface=surface,
                    target_lat=listing.get("latitude"),
                    target_lng=listing.get("longitude"),
                    exclude_url=listing.get("url", ""),
                    max_results=9,
                )
                st.session_state[cache_key] = comps
            except Exception as e:
                st.warning(f"Kon vergelijkbare panden niet ophalen: {e}")
                st.session_state[cache_key] = []

    comparables = st.session_state[cache_key]

    if not comparables:
        st.info("Geen vergelijkbare panden gevonden in deze prijsklasse.")
        return

    # Toon samenvatting
    avg_price_m2 = sum(c["price_per_m2"] for c in comparables) / len(comparables)
    my_price_m2 = final_prices.get("mid", 0)
    delta_pct = ((my_price_m2 - avg_price_m2) / avg_price_m2 * 100) if avg_price_m2 > 0 else 0

    summary_col1, summary_col2, summary_col3 = st.columns(3)
    with summary_col1:
        st.metric("Vergelijkbare panden", len(comparables))
    with summary_col2:
        st.metric(
            "Gem. prijs/m² markt",
            format_eur_per_m2(avg_price_m2),
        )
    with summary_col3:
        delta_color = "normal" if abs(delta_pct) < 10 else ("inverse" if delta_pct > 10 else "off")
        st.metric(
            "Jouw schatting vs. markt",
            format_eur_per_m2(my_price_m2),
            delta=f"{delta_pct:+.1f}%",
            delta_color=delta_color,
        )

    # Render kaartjes in grid van 3
    COLS = 3
    for row_start in range(0, len(comparables), COLS):
        row = comparables[row_start:row_start + COLS]
        cols = st.columns(COLS)

        for col_idx, comp in enumerate(row):
            with cols[col_idx]:
                _render_market_comp_card(comp, row_start + col_idx)


def _render_market_comp_card(comp: dict, idx: int):
    """Rendert een kaartje voor een vergelijkbaar marktpand."""
    images = comp.get("images", [])
    price = comp.get("price", 0)
    price_per_m2 = comp.get("price_per_m2", 0)
    surface = comp.get("surface_m2", 0)
    zone = comp.get("zone", "")
    address = comp.get("address", "")
    url = comp.get("url", "")
    rooms = comp.get("rooms")
    condition = comp.get("condition", "")
    distance_m = comp.get("distance_m")

    with st.container(border=True):
        # Foto preview
        if images:
            img_url = images[0]
            st.markdown(
                f'<a href="{url}" target="_blank" style="text-decoration:none;">'
                f'<img src="{img_url}" '
                f'style="width:100%;height:160px;object-fit:cover;border-radius:6px;" '
                f'loading="lazy">'
                f'</a>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="background:#e9ecef;height:160px;display:flex;'
                'align-items:center;justify-content:center;border-radius:6px;">'
                '<span style="color:#6c757d;font-size:0.85em;">Geen foto</span></div>',
                unsafe_allow_html=True,
            )

        # Prijs + prijs/m²
        st.markdown(
            f'<div style="margin:6px 0;">'
            f'<span style="font-size:1.1em;font-weight:bold;color:#1a365d;">'
            f'{format_eur(price)}</span>'
            f'<span style="color:#888;font-size:0.85em;margin-left:8px;">'
            f'{format_eur_per_m2(price_per_m2)}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Oppervlakte + kamers
        info_parts = [format_m2(surface)]
        if rooms:
            info_parts.append(f"{rooms} kamers")
        if condition:
            cond_map = {"good": "Goed", "new": "Nieuw", "to_renovate": "Te renoveren",
                        "renovated": "Gerenoveerd", "partially_renovated": "Deels gerenoveerd"}
            info_parts.append(cond_map.get(condition, condition))
        st.caption(" · ".join(info_parts))

        # Afstand
        if distance_m is not None:
            if distance_m < 1000:
                dist_text = f"📍 {distance_m}m afstand"
            else:
                dist_text = f"📍 {distance_m / 1000:.1f}km afstand"
            st.caption(dist_text)

        # Adres
        if address:
            display_addr = address[:35] + "..." if len(address) > 35 else address
            st.caption(display_addr)

        # Link naar Immobiliare.it
        if url:
            st.link_button(
                "Bekijk op Immobiliare.it",
                url,
                use_container_width=True,
            )


# ============================================================
# GOOGLE MAPS PREVIEW
# ============================================================

def _render_maps_preview(listing: dict):
    """Toont een Google Maps preview met de locatie van het pand."""
    lat = listing.get("latitude")
    lng = listing.get("longitude")
    address = listing.get("address", "")
    zone = listing.get("zone", "")

    if not lat or not lng:
        # Geen coordinaten beschikbaar — skip
        return

    # Google Maps link voor nieuw tabblad
    maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"

    # OpenStreetMap embed (gratis, geen API key nodig)
    # Bbox: ~500m radius → ~1km totaalbeeld
    osm_embed = (
        f"https://www.openstreetmap.org/export/embed.html?"
        f"bbox={lng-0.003},{lat-0.0025},{lng+0.003},{lat+0.0025}"
        f"&layer=mapnik&marker={lat},{lng}"
    )

    map_col, info_col = st.columns([1, 1])

    with map_col:
        components.html(
            f'<iframe width="100%" height="250" frameborder="0" scrolling="no" '
            f'marginheight="0" marginwidth="0" '
            f'src="{osm_embed}" '
            f'style="border-radius:8px;border:1px solid #e0e0e0;">'
            f'</iframe>',
            height=260,
        )

    with info_col:
        if address:
            st.markdown(f"**Adres:** {address}")
        if zone:
            st.markdown(f"**Wijk:** {zone}")
        st.markdown(f"**Coördinaten:** {lat:.5f}, {lng:.5f}")
        st.markdown(
            f'<a href="{maps_url}" target="_blank" '
            f'style="display:inline-block;margin-top:8px;padding:8px 16px;'
            f'background-color:#4285f4;color:white;border-radius:6px;'
            f'text-decoration:none;font-size:14px;font-weight:500;">'
            f'📍 Open in Google Maps</a>',
            unsafe_allow_html=True,
        )


# ============================================================
# LOCATIEANALYSE
# ============================================================

def _render_location_analysis(listing: dict, analysis: dict):
    """Rendert de multi-factor locatiekwaliteitsanalyse met Google Maps preview."""
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

    # Google Maps preview
    _render_maps_preview(listing)

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


def _render_speed_and_confidence(listing: dict):
    """Toont verkoopsnelheid en betrouwbaarheidsniveau."""
    speed = listing.get("selling_speed")
    confidence = listing.get("confidence")
    comparables = listing.get("comparables")

    if not speed and not confidence:
        return

    st.subheader("Verkoopsnelheid & Betrouwbaarheid")
    col1, col2, col3 = st.columns(3)

    if speed:
        with col1:
            color = speed.get("speed_color", "gray")
            st.markdown(
                f'<div style="text-align:center;padding:16px;background:{color}15;'
                f'border:2px solid {color};border-radius:8px;">'
                f'<h2 style="margin:0;color:{color};">{speed["estimated_months"]} mnd</h2>'
                f'<p style="margin:4px 0 0;font-weight:bold;color:{color};">{speed["speed"]}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.caption(speed.get("description", ""))

    if confidence:
        with col2:
            c = confidence.get("color", "gray")
            st.markdown(
                f'<div style="text-align:center;padding:16px;background:{c}15;'
                f'border:2px solid {c};border-radius:8px;">'
                f'<h2 style="margin:0;color:{c};">{confidence["level"]}</h2>'
                f'<p style="margin:4px 0 0;font-size:0.85em;">{confidence["explanation"]}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )

    if comparables:
        with col3:
            total = comparables.get("batch_total", 1)
            rank = comparables.get("batch_rank_score", 1)
            st.markdown(
                f'<div style="text-align:center;padding:16px;background:#f8f9fa;'
                f'border:1px solid #e9ecef;border-radius:8px;">'
                f'<h2 style="margin:0;color:#1a365d;">#{rank}/{total}</h2>'
                f'<p style="margin:4px 0 0;font-weight:bold;color:#555;">Rangpositie (score)</p>'
                f'</div>',
                unsafe_allow_html=True,
            )
            delta = comparables.get("batch_delta_pct")
            if delta is not None:
                sign = "+" if delta > 0 else ""
                st.caption(f"Prijs/m2 {sign}{delta:.1f}% vs. mediaan batch")

    # Snelheidsaanpassingen
    if speed and speed.get("adjustments"):
        with st.expander("Verkoopsnelheid details"):
            for adj in speed["adjustments"]:
                st.markdown(f"- {adj}")


def _render_comparables(listing: dict):
    """Toont vergelijkbare panden uit de batch."""
    comparables = listing.get("comparables")
    if not comparables:
        return

    direct = comparables.get("direct_comparables", [])
    if not direct:
        return

    st.subheader(f"Vergelijkbare Panden ({len(direct)} gevonden)")

    for comp in direct[:5]:
        sim_pct = comp["similarity"] * 100
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.markdown(f"**{comp.get('zone', '?')}**")
        with col2:
            st.metric("Prijs/m2", f"EUR {comp.get('price_per_m2', 0):,.0f}")
        with col3:
            st.metric("Score", comp.get("flip_score", "?"))
        with col4:
            st.metric("Similarity", f"{sim_pct:.0f}%")


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
