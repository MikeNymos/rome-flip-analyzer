"""
Authenticatiepagina met login, registratie en wachtwoord-reset formulieren.
Inclusief password-manager compatibility fix en dark-mode toggle.
"""
from __future__ import annotations

import streamlit as st
from services.auth import login, register, forgot_password


def _inject_password_manager_fix():
    """
    Injecteert JavaScript dat de juiste autocomplete, name, id en type
    attributen op Streamlit text-inputs zet, zodat Google Password Manager
    (en andere managers) de velden herkent.
    """
    st.markdown("""
    <script>
    (function() {
        function fixInputs() {
            // Zoek alle input-elementen in forms
            var inputs = document.querySelectorAll(
                '[data-testid="stForm"] input[type="text"], '
                + '[data-testid="stForm"] input[type="password"]'
            );
            inputs.forEach(function(input) {
                // Zoek het bijbehorende label
                var container = input.closest('[data-testid="stTextInput"]')
                                || input.closest('.stTextInput');
                if (!container) return;
                var label = container.querySelector('label');
                if (!label) return;
                var text = label.textContent.toLowerCase();

                if (text.indexOf('e-mail') !== -1 || text.indexOf('email') !== -1) {
                    input.setAttribute('autocomplete', 'email');
                    input.setAttribute('name', 'email');
                    input.setAttribute('id', 'email-' + Math.random().toString(36).substr(2,4));
                    input.setAttribute('type', 'email');
                    input.setAttribute('inputmode', 'email');
                } else if (text.indexOf('bevestig') !== -1) {
                    input.setAttribute('autocomplete', 'new-password');
                    input.setAttribute('name', 'new-password-confirm');
                } else if (text.indexOf('wachtwoord') !== -1 || text.indexOf('password') !== -1) {
                    // Detect if this is registration or login form
                    var form = input.closest('[data-testid="stForm"]');
                    var formKey = form ? (form.getAttribute('data-testid') || '') : '';
                    var allInputs = form ? form.querySelectorAll('input') : [];
                    // If the form has more than 2 inputs, it's likely registration
                    if (allInputs.length > 2) {
                        input.setAttribute('autocomplete', 'new-password');
                        input.setAttribute('name', 'new-password');
                    } else {
                        input.setAttribute('autocomplete', 'current-password');
                        input.setAttribute('name', 'password');
                    }
                }
            });
        }

        // Run periodically to catch Streamlit's dynamic rendering
        fixInputs();
        var attempts = 0;
        var interval = setInterval(function() {
            fixInputs();
            attempts++;
            if (attempts > 30) clearInterval(interval);
        }, 500);

        // Also use MutationObserver for new elements
        var observer = new MutationObserver(function() { fixInputs(); });
        observer.observe(document.body, { childList: true, subtree: true });
    })();
    </script>
    """, unsafe_allow_html=True)


def render_auth_page():
    """Rendert de authenticatiepagina wanneer niet ingelogd."""

    # Inject password manager fix
    _inject_password_manager_fix()

    # Gecentreerde layout
    _, col, _ = st.columns([1, 2, 1])

    with col:
        # Dark mode toggle bovenaan de auth pagina
        dm_col1, dm_col2 = st.columns([3, 1])
        with dm_col2:
            dark_mode = st.toggle(
                "Donker",
                value=st.session_state.get("dark_mode", False),
                key="auth_dark_toggle",
            )
            if dark_mode != st.session_state.get("dark_mode", False):
                st.session_state["dark_mode"] = dark_mode
                st.rerun()

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
