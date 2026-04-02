"""
Supabase database service voor search history en saved listings.
"""
from __future__ import annotations

import math
import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def get_supabase_client() -> Client:
    """Retourneert een gecachete Supabase client."""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)


def _sanitize_for_json(obj):
    """Vervangt float('inf') en NaN met None voor JSONB compatibiliteit."""
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_for_json(v) for v in obj]
    if isinstance(obj, float):
        if math.isinf(obj) or math.isnan(obj):
            return None
    return obj


def save_search(
    user_id: str,
    search_type: str,
    search_query: str,
    analyzed_listings: list[dict],
) -> str | None:
    """
    Slaat een zoekactie en alle geanalyseerde listings op in de database.

    Returns:
        De UUID van de search_history record, of None bij fout.
    """
    try:
        client = get_supabase_client()

        listing_count = len(analyzed_listings)
        scores = [l.get("flip_score", 0) for l in analyzed_listings]
        rois = [l.get("roi_prima_casa", 0) or 0 for l in analyzed_listings]
        avg_score = sum(scores) / max(listing_count, 1)
        best_roi = max(rois) if rois else 0

        # Insert search_history
        result = client.table("search_history").insert({
            "user_id": user_id,
            "search_type": search_type,
            "search_query": search_query[:500],
            "listing_count": listing_count,
            "avg_flip_score": round(avg_score, 1),
            "best_roi": round(best_roi, 1),
        }).execute()

        search_id = result.data[0]["id"]

        # Insert saved_listings in batches
        rows = []
        for listing in analyzed_listings:
            sanitized = _sanitize_for_json(listing)
            rows.append({
                "search_id": search_id,
                "listing_data": sanitized,
                "flip_score": listing.get("flip_score", 0),
                "zone": listing.get("zone", ""),
                "price": listing.get("price", 0),
            })

        if rows:
            # Insert in batches of 50 to avoid payload limits
            for i in range(0, len(rows), 50):
                batch = rows[i:i + 50]
                client.table("saved_listings").insert(batch).execute()

        return search_id

    except Exception as e:
        st.toast(f"Opslaan mislukt: {e}", icon="⚠️")
        return None


def get_search_history(user_id: str, limit: int = 20) -> list[dict]:
    """Haalt de zoekgeschiedenis op, meest recent eerst."""
    try:
        client = get_supabase_client()
        result = (
            client.table("search_history")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


def get_saved_listings(search_id: str) -> list[dict]:
    """Haalt alle opgeslagen listings op voor een zoekactie."""
    try:
        client = get_supabase_client()
        result = (
            client.table("saved_listings")
            .select("listing_data")
            .eq("search_id", search_id)
            .execute()
        )
        return [row["listing_data"] for row in (result.data or [])]
    except Exception:
        return []


def delete_search(search_id: str) -> bool:
    """Verwijdert een zoekactie en alle gekoppelde listings (CASCADE)."""
    try:
        client = get_supabase_client()
        client.table("search_history").delete().eq("id", search_id).execute()
        return True
    except Exception:
        return False


# ============================================================
# FAVORIETEN
# ============================================================

def toggle_favorite(user_id: str, listing: dict) -> bool:
    """
    Voegt een pand toe aan favorieten of verwijdert het als het al bestaat.

    Returns:
        True als het pand nu een favoriet is, False als het verwijderd is.
    """
    listing_url = listing.get("url", "")
    if not listing_url:
        return False

    try:
        client = get_supabase_client()

        # Check of het al een favoriet is
        result = (
            client.table("favorites")
            .select("id")
            .eq("user_id", user_id)
            .eq("listing_url", listing_url)
            .execute()
        )

        if result.data:
            # Verwijder favoriet
            client.table("favorites").delete().eq("id", result.data[0]["id"]).execute()
            return False
        else:
            # Voeg toe als favoriet
            sanitized = _sanitize_for_json(listing)
            client.table("favorites").insert({
                "user_id": user_id,
                "listing_url": listing_url,
                "listing_data": sanitized,
                "flip_score": listing.get("flip_score", 0),
                "zone": listing.get("zone", ""),
                "price": listing.get("price", 0),
            }).execute()
            return True
    except Exception as e:
        st.toast(f"Favoriet opslaan mislukt: {e}", icon="⚠️")
        return False


def get_favorites(user_id: str) -> list[dict]:
    """Haalt alle favoriete panden op voor een gebruiker, nieuwste eerst."""
    try:
        client = get_supabase_client()
        result = (
            client.table("favorites")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


def is_favorite(user_id: str, listing_url: str) -> bool:
    """Controleert of een pand al een favoriet is."""
    if not listing_url:
        return False
    try:
        client = get_supabase_client()
        result = (
            client.table("favorites")
            .select("id")
            .eq("user_id", user_id)
            .eq("listing_url", listing_url)
            .execute()
        )
        return bool(result.data)
    except Exception:
        return False


def remove_favorite(user_id: str, listing_url: str) -> bool:
    """Verwijdert een pand uit favorieten."""
    try:
        client = get_supabase_client()
        client.table("favorites").delete().eq("user_id", user_id).eq("listing_url", listing_url).execute()
        return True
    except Exception:
        return False
