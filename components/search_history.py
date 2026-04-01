"""
Zoekgeschiedenis component in de sidebar.
"""
from __future__ import annotations

from datetime import datetime
import streamlit as st

from services.auth import get_current_user
from services.database import get_search_history, get_saved_listings, delete_search


_TYPE_LABELS = {
    "url": "Zoek-URL",
    "single": "Enkel Pand",
    "upload": "Upload",
    "test": "Testdata",
}

_TYPE_ICONS = {
    "url": "🔍",
    "single": "🏠",
    "upload": "📁",
    "test": "🧪",
}


def _format_timestamp(ts_str: str) -> str:
    """Formatteert een ISO timestamp naar leesbaar formaat."""
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        months_nl = [
            "", "jan", "feb", "mrt", "apr", "mei", "jun",
            "jul", "aug", "sep", "okt", "nov", "dec",
        ]
        return f"{dt.day} {months_nl[dt.month]} {dt.year}, {dt.hour:02d}:{dt.minute:02d}"
    except (ValueError, IndexError):
        return ts_str[:16] if ts_str else ""


def render_search_history() -> list[dict] | None:
    """
    Rendert de zoekgeschiedenis in de sidebar.

    Returns:
        Lijst van geanalyseerde listings als gebruiker een item laadt,
        anders None.
    """
    user = get_current_user()
    if not user:
        return None

    history = get_search_history(user["id"])
    if not history:
        return None

    st.sidebar.divider()

    with st.sidebar.expander(f"Geschiedenis ({len(history)})", expanded=False):
        for item in history:
            search_id = item["id"]
            stype = item.get("search_type", "url")
            icon = _TYPE_ICONS.get(stype, "📋")
            label = _TYPE_LABELS.get(stype, stype)
            query = item.get("search_query", "")
            count = item.get("listing_count", 0)
            avg_score = item.get("avg_flip_score", 0) or 0
            ts = _format_timestamp(item.get("created_at", ""))

            # Verkort query voor weergave
            display_query = query
            if len(display_query) > 40:
                display_query = display_query[:37] + "..."

            st.markdown(
                f"**{icon} {label}**  \n"
                f"<small>{display_query}</small>  \n"
                f"<small>{ts} | {count} panden | Score: {avg_score:.0f}</small>",
                unsafe_allow_html=True,
            )

            col_load, col_del = st.columns([3, 1])

            with col_load:
                if st.button("Laden", key=f"load_{search_id}", use_container_width=True):
                    listings = get_saved_listings(search_id)
                    if listings:
                        return listings
                    else:
                        st.error("Geen listings gevonden.")

            with col_del:
                if st.button("🗑️", key=f"del_{search_id}", use_container_width=True):
                    # Bewaar in session state voor bevestiging
                    confirm_key = f"confirm_del_{search_id}"
                    if st.session_state.get(confirm_key):
                        delete_search(search_id)
                        st.session_state.pop(confirm_key, None)
                        st.rerun()
                    else:
                        st.session_state[confirm_key] = True
                        st.rerun()

            # Toon bevestigingsvraag als nodig
            confirm_key = f"confirm_del_{search_id}"
            if st.session_state.get(confirm_key):
                st.warning("Zeker weten?")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Ja", key=f"yes_{search_id}", use_container_width=True):
                        delete_search(search_id)
                        st.session_state.pop(confirm_key, None)
                        st.rerun()
                with c2:
                    if st.button("Nee", key=f"no_{search_id}", use_container_width=True):
                        st.session_state.pop(confirm_key, None)
                        st.rerun()

            st.divider()

    return None
