"""
Authenticatiepagina met login, registratie en wachtwoord-reset formulieren.
"""
from __future__ import annotations

import streamlit as st
from services.auth import login, register, forgot_password


def render_auth_page():
    """Rendert de authenticatiepagina wanneer niet ingelogd."""

    # Gecentreerde layout
    _, col, _ = st.columns([1, 2, 1])

    with col:
        st.markdown(
            "<h1 style='text-align: center; color: #1a365d;'>Rome Flip Analyzer</h1>"
            "<p style='text-align: center; color: #c9a026; font-size: 1.1em; "
            "margin-bottom: 2em;'>Vastgoed Investeringsanalyse</p>",
            unsafe_allow_html=True,
        )

        tab_login, tab_register, tab_forgot = st.tabs([
            "Inloggen", "Registreren", "Wachtwoord Vergeten"
        ])

        # === TAB: INLOGGEN ===
        with tab_login:
            with st.form("login_form"):
                st.subheader("Inloggen")
                email = st.text_input("E-mailadres", key="login_email")
                password = st.text_input(
                    "Wachtwoord", type="password", key="login_password"
                )
                submitted = st.form_submit_button(
                    "Inloggen", use_container_width=True
                )

                if submitted:
                    if not email or not password:
                        st.error("Vul zowel e-mailadres als wachtwoord in.")
                    else:
                        success, msg = login(email.strip(), password)
                        if success:
                            st.rerun()
                        else:
                            st.error(msg)

        # === TAB: REGISTREREN ===
        with tab_register:
            with st.form("register_form"):
                st.subheader("Account Aanmaken")
                reg_email = st.text_input("E-mailadres", key="register_email")
                reg_password = st.text_input(
                    "Wachtwoord", type="password", key="register_password",
                    help="Minimaal 6 tekens",
                )
                reg_password_confirm = st.text_input(
                    "Bevestig Wachtwoord", type="password",
                    key="register_password_confirm",
                )
                submitted = st.form_submit_button(
                    "Registreren", use_container_width=True
                )

                if submitted:
                    if not reg_email or not reg_password:
                        st.error("Vul alle velden in.")
                    elif reg_password != reg_password_confirm:
                        st.error("Wachtwoorden komen niet overeen.")
                    elif len(reg_password) < 6:
                        st.error("Wachtwoord moet minimaal 6 tekens zijn.")
                    else:
                        success, msg = register(reg_email.strip(), reg_password)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)

        # === TAB: WACHTWOORD VERGETEN ===
        with tab_forgot:
            with st.form("forgot_form"):
                st.subheader("Wachtwoord Vergeten")
                st.caption(
                    "Voer je e-mailadres in. Je ontvangt een link om je "
                    "wachtwoord te resetten."
                )
                forgot_email = st.text_input("E-mailadres", key="forgot_email")
                submitted = st.form_submit_button(
                    "Verstuur Reset Link", use_container_width=True
                )

                if submitted:
                    if not forgot_email:
                        st.error("Vul je e-mailadres in.")
                    else:
                        success, msg = forgot_password(forgot_email.strip())
                        st.info(msg)
