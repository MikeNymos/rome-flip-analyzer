"""
Authenticatie service met Supabase Auth.
Beheert login, registratie, wachtwoord reset en sessie-state.
"""
from __future__ import annotations

import streamlit as st
from services.database import get_supabase_client

_AUTH_USER_KEY = "auth_user"
_AUTH_SESSION_KEY = "auth_session"

# Nederlandse vertalingen van veelvoorkomende Supabase Auth fouten
_ERROR_TRANSLATIONS = {
    "Invalid login credentials": "Ongeldige inloggegevens.",
    "User already registered": "Dit e-mailadres is al geregistreerd.",
    "Email not confirmed": "E-mailadres is nog niet bevestigd. Controleer je inbox.",
    "Password should be at least 6 characters": "Wachtwoord moet minimaal 6 tekens zijn.",
    "Unable to validate email address: invalid format": "Ongeldig e-mailadres.",
}


def _translate_error(msg: str) -> str:
    """Vertaalt een Supabase foutmelding naar het Nederlands."""
    for en, nl in _ERROR_TRANSLATIONS.items():
        if en.lower() in msg.lower():
            return nl
    return msg


def get_current_user() -> dict | None:
    """Retourneert de huidige ingelogde gebruiker, of None."""
    return st.session_state.get(_AUTH_USER_KEY)


def is_logged_in() -> bool:
    """Controleert of een gebruiker is ingelogd."""
    return get_current_user() is not None


def login(email: str, password: str) -> tuple[bool, str]:
    """Logt een gebruiker in met email en wachtwoord."""
    try:
        client = get_supabase_client()
        response = client.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })
        user = response.user
        session = response.session

        st.session_state[_AUTH_USER_KEY] = {
            "id": user.id,
            "email": user.email,
        }
        st.session_state[_AUTH_SESSION_KEY] = {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
        }
        return True, "Succesvol ingelogd!"

    except Exception as e:
        msg = str(e)
        return False, _translate_error(msg)


def register(email: str, password: str) -> tuple[bool, str]:
    """Registreert een nieuwe gebruiker."""
    if len(password) < 6:
        return False, "Wachtwoord moet minimaal 6 tekens zijn."

    try:
        client = get_supabase_client()
        response = client.auth.sign_up({
            "email": email,
            "password": password,
        })

        if response.user and response.user.identities:
            return True, "Registratie succesvol! Controleer je e-mail voor bevestiging."

        # Supabase returns user without identities if already registered
        if response.user and not response.user.identities:
            return False, "Dit e-mailadres is al geregistreerd."

        return True, "Registratie succesvol! Controleer je e-mail voor bevestiging."

    except Exception as e:
        msg = str(e)
        return False, _translate_error(msg)


def forgot_password(email: str) -> tuple[bool, str]:
    """Stuurt een wachtwoord-reset email."""
    try:
        client = get_supabase_client()
        client.auth.reset_password_email(email)
        # Altijd success teruggeven om email-enumeratie te voorkomen
        return True, "Als dit e-mailadres bekend is, ontvang je een reset-link."
    except Exception:
        return True, "Als dit e-mailadres bekend is, ontvang je een reset-link."


def logout():
    """Logt de gebruiker uit en wist de sessie."""
    try:
        client = get_supabase_client()
        client.auth.sign_out()
    except Exception:
        pass

    # Wis auth state
    st.session_state.pop(_AUTH_USER_KEY, None)
    st.session_state.pop(_AUTH_SESSION_KEY, None)

    # Wis app data om gegevenslekkage te voorkomen
    st.session_state.pop("analyzed_listings", None)
    st.session_state.pop("raw_listings", None)
    st.session_state.pop("property_overrides", None)


def restore_session() -> bool:
    """
    Herstelt een bestaande sessie na een Streamlit rerun.
    Wordt aangeroepen bij elke app-start.
    """
    session_data = st.session_state.get(_AUTH_SESSION_KEY)
    if not session_data:
        return False

    try:
        client = get_supabase_client()
        response = client.auth.set_session(
            access_token=session_data["access_token"],
            refresh_token=session_data["refresh_token"],
        )

        if response and response.user:
            # Update tokens (ze kunnen vernieuwd zijn)
            st.session_state[_AUTH_USER_KEY] = {
                "id": response.user.id,
                "email": response.user.email,
            }
            if response.session:
                st.session_state[_AUTH_SESSION_KEY] = {
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                }
            return True

    except Exception:
        # Sessie verlopen of ongeldig — wis alles
        st.session_state.pop(_AUTH_USER_KEY, None)
        st.session_state.pop(_AUTH_SESSION_KEY, None)

    return False
