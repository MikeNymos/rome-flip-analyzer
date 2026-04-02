"""
Favorieten-overzicht: toont opgeslagen panden met kaartjes en verwijderoptie.
"""
from __future__ import annotations

import json
from urllib.parse import quote

import streamlit as st
import streamlit.components.v1 as components

from utils.helpers import format_eur, format_pct, format_m2, format_eur_per_m2, score_color
from config import get_score_label
from services.auth import get_current_user
from services.database import get_favorites, remove_favorite


def render_favorites() -> dict | None:
    """
    Rendert het favorieten-overzicht.

    Returns:
        Een listing dict als de gebruiker een favoriet wil bekijken, anders None.
    """
    user = get_current_user()
    if not user:
        st.info("Log in om je favorieten te bekijken.")
        return None

    favorites = get_favorites(user["id"])

    if not favorites:
        st.markdown(
            """
            ### Geen favorieten

            Je hebt nog geen panden opgeslagen als favoriet.
            Gebruik het ❤️ icoon op het dashboard of de detailpagina
            om interessante panden op te slaan.
            """
        )
        return None

    st.subheader(f"Mijn Favorieten ({len(favorites)})")
    st.caption("Klik op een pand om de volledige analyse te bekijken.")

    selected_listing = None
    COLS = 3

    for row_start in range(0, len(favorites), COLS):
        row_favs = favorites[row_start:row_start + COLS]
        cols = st.columns(COLS)

        for col_idx, fav in enumerate(row_favs):
            listing = fav.get("listing_data", {})
            with cols[col_idx]:
                result = _render_favorite_card(listing, fav, row_start + col_idx, user["id"])
                if result == "view":
                    selected_listing = listing
                elif result == "removed":
                    st.rerun()

    return selected_listing


def _render_favorite_card(listing: dict, fav_record: dict, idx: int, user_id: str) -> str | None:
    """
    Rendert een enkele favorietenkaart.

    Returns:
        "view" als de gebruiker het pand wil bekijken,
        "removed" als het verwijderd is,
        None anders.
    """
    score = listing.get("flip_score", 0)
    label, color, _ = get_score_label(score)
    images = listing.get("images", [])
    roi = listing.get("roi_prima_casa", listing.get("midpoint_roi", 0))
    zone = listing.get("zone", "Onbekend")
    address = listing.get("address", "")
    price = listing.get("price", 0)
    surface = listing.get("surface_m2", 0)
    price_per_m2 = listing.get("price_per_m2", 0)
    listing_url = listing.get("url", "")

    with st.container(border=True):
        # Foto
        if images:
            _render_fav_image(images, idx)
        else:
            st.markdown(
                '<div style="background:#EDE7E0;height:180px;display:flex;'
                'align-items:center;justify-content:center;border-radius:12px;">'
                '<span style="color:#B0AAA3;font-size:0.9em;">Geen foto</span></div>',
                unsafe_allow_html=True,
            )

        # Score badge
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;margin:8px 0 4px 0;">'
            f'<span style="background:linear-gradient(135deg,{color},{color}cc);color:white;padding:5px 14px;'
            f'border-radius:10px;font-weight:700;font-size:1.05em;font-family:Inter,sans-serif;'
            f'box-shadow:0 3px 10px {color}35;">{score}</span>'
            f'<span style="color:#64748B;font-size:0.82em;font-weight:500;">{label}</span>'
            f'<span style="color:#EF4444;font-size:1.2em;margin-left:auto;">&#10084;</span>'
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

        # Opgeslagen datum
        created = fav_record.get("created_at", "")
        if created:
            date_str = created[:10]
            st.caption(f"Opgeslagen op {date_str}")

        # Knoppen
        col_a, col_b, col_c = st.columns(3)
        result = None

        with col_a:
            if st.button("Bekijk detail", key=f"fav_detail_{idx}", use_container_width=True):
                result = "view"
        with col_b:
            if listing_url:
                st.link_button("Immobiliare", listing_url, use_container_width=True)
        with col_c:
            if st.button("🗑️", key=f"fav_remove_{idx}", help="Verwijder uit favorieten", use_container_width=True):
                remove_favorite(user_id, listing_url)
                # Clear cache
                fav_cache_key = f"fav_{user_id}_{listing_url}"
                if fav_cache_key in st.session_state:
                    del st.session_state[fav_cache_key]
                st.toast("Verwijderd uit favorieten", icon="🗑️")
                result = "removed"

        return result


def _render_fav_image(images: list[str], idx: int):
    """Render favoriet image met carousel."""
    imgs = images[:10]
    total = len(images)

    if len(imgs) <= 1:
        # Enkele afbeelding
        st.markdown(
            f'<img src="{imgs[0]}" '
            f'style="width:100%;height:180px;object-fit:cover;border-radius:12px;" loading="lazy">',
            unsafe_allow_html=True,
        )
        return

    imgs_json = json.dumps(imgs)
    html = f"""
    <div id="fav-carousel-{idx}" style="position:relative;width:100%;height:180px;
         border-radius:12px;overflow:hidden;background:#EDE7E0;">
      <img id="fav-img-{idx}" src="{imgs[0]}"
           style="width:100%;height:180px;object-fit:cover;" loading="lazy">
      <button onclick="favNav({idx},-1)" style="position:absolute;left:0;top:0;width:32px;
              height:100%;background:rgba(0,0,0,0.25);border:none;color:#fff;
              font-size:20px;cursor:pointer;opacity:0;transition:opacity .2s;"
              id="fav-prev-{idx}">&lsaquo;</button>
      <button onclick="favNav({idx},1)" style="position:absolute;right:0;top:0;width:32px;
              height:100%;background:rgba(0,0,0,0.25);border:none;color:#fff;
              font-size:20px;cursor:pointer;opacity:0;transition:opacity .2s;"
              id="fav-next-{idx}">&rsaquo;</button>
      <span id="fav-ctr-{idx}" style="position:absolute;bottom:6px;right:8px;
            background:rgba(0,0,0,0.55);color:#fff;padding:2px 8px;border-radius:10px;
            font-size:11px;">1 / {total}</span>
    </div>
    <script>
      var fav_imgs_{idx} = {imgs_json};
      var fav_cur_{idx} = 0;
      var fav_total_{idx} = {total};
      function favNav(id, dir) {{
        fav_cur_{idx} = (fav_cur_{idx} + dir + fav_imgs_{idx}.length) % fav_imgs_{idx}.length;
        document.getElementById('fav-img-'+id).src = fav_imgs_{idx}[fav_cur_{idx}];
        document.getElementById('fav-ctr-'+id).textContent =
          (fav_cur_{idx}+1) + ' / ' + fav_total_{idx};
      }}
      var fc = document.getElementById('fav-carousel-{idx}');
      fc.addEventListener('mouseenter', function() {{
        document.getElementById('fav-prev-{idx}').style.opacity = '1';
        document.getElementById('fav-next-{idx}').style.opacity = '1';
      }});
      fc.addEventListener('mouseleave', function() {{
        document.getElementById('fav-prev-{idx}').style.opacity = '0';
        document.getElementById('fav-next-{idx}').style.opacity = '0';
      }});
    </script>
    """
    components.html(html, height=190)
