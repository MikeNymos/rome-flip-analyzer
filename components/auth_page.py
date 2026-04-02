"""
Authenticatiepagina met login, registratie en wachtwoord-reset formulieren.
Inclusief password-manager compatibility fix en dark-mode toggle.
"""
from __future__ import annotations

import streamlit as st
from services.auth import login, register, forgot_password


def _inject_password_manager_fix():
    """
    Injecteert JavaScript + onzichtbare HTML die password managers helpen
    de e-mail en wachtwoord velden correct te herkennen.

    Strategie:
    1. Maak een onzichtbare <form> met correcte <input> velden die password
       managers herkennen (autocomplete, name, type attributen)
    2. Sync waarden vanuit de onzichtbare inputs naar Streamlit's echte inputs
    3. Pas ook attributen aan op Streamlit's eigen inputs als extra vangnet
    """
    st.markdown("""
    <!-- Onzichtbaar login-formulier voor password manager herkenning -->
    <form id="pm-login-form" autocomplete="on"
          style="position:absolute;left:-9999px;top:-9999px;opacity:0;pointer-events:none;"
          aria-hidden="true">
        <input type="email" name="email" id="pm-email"
               autocomplete="email username" tabindex="-1">
        <input type="password" name="password" id="pm-password"
               autocomplete="current-password" tabindex="-1">
    </form>

    <script>
    (function() {
        var FIXED_MARKER = '__pm_fixed__';

        function getStInputs() {
            // Vind Streamlit inputs - probeer meerdere selectors
            var inputs = document.querySelectorAll('input');
            var result = { email: null, password: null };
            inputs.forEach(function(inp) {
                // Skip onze onzichtbare inputs
                if (inp.id === 'pm-email' || inp.id === 'pm-password') return;
                // Skip al-gemarkeerde
                var container = inp.closest('[data-testid="stTextInput"]')
                                || inp.closest('.stTextInput')
                                || inp.parentElement;
                if (!container) return;

                // Zoek label
                var label = container.querySelector('label');
                var labelText = label ? label.textContent.toLowerCase() : '';

                // Herken op basis van type + label
                if (inp.type === 'password' && !result.password) {
                    result.password = inp;
                } else if (inp.type !== 'password' &&
                           (labelText.indexOf('e-mail') !== -1 ||
                            labelText.indexOf('email') !== -1) &&
                           !result.email) {
                    result.email = inp;
                }
            });
            return result;
        }

        function fixAttributes() {
            var st = getStInputs();

            if (st.email && !st.email[FIXED_MARKER]) {
                // Forceer type="email" via DOM property (niet alleen attribute)
                try { st.email.type = 'email'; } catch(e) {}
                st.email.setAttribute('type', 'email');
                st.email.setAttribute('autocomplete', 'email');
                st.email.setAttribute('name', 'email');
                st.email.setAttribute('id', 'login-email');
                st.email.setAttribute('inputmode', 'email');
                st.email[FIXED_MARKER] = true;

                // Sync met onzichtbare PM input
                st.email.addEventListener('input', function() {
                    var pmEmail = document.getElementById('pm-email');
                    if (pmEmail) pmEmail.value = this.value;
                });
                st.email.addEventListener('change', function() {
                    var pmEmail = document.getElementById('pm-email');
                    if (pmEmail) pmEmail.value = this.value;
                });
            }

            if (st.password && !st.password[FIXED_MARKER]) {
                st.password.setAttribute('autocomplete', 'current-password');
                st.password.setAttribute('name', 'password');
                st.password.setAttribute('id', 'login-password');
                st.password[FIXED_MARKER] = true;

                st.password.addEventListener('input', function() {
                    var pmPw = document.getElementById('pm-password');
                    if (pmPw) pmPw.value = this.value;
                });
            }

            // Probeer ook Streamlit's form element de juiste attributen te geven
            var forms = document.querySelectorAll('[data-testid="stForm"]');
            forms.forEach(function(form) {
                if (!form.getAttribute('autocomplete')) {
                    form.setAttribute('autocomplete', 'on');
                    form.setAttribute('method', 'post');
                }
            });
        }

        // React-proof: gebruik Object.defineProperty om type="email" te forceren
        function forceEmailType() {
            var st = getStInputs();
            if (st.email && st.email.type !== 'email') {
                try {
                    // Forceer via nativeInputValueSetter (omzeil React)
                    var nativeType = Object.getOwnPropertyDescriptor(
                        HTMLInputElement.prototype, 'type'
                    );
                    if (nativeType && nativeType.set) {
                        nativeType.set.call(st.email, 'email');
                    }
                } catch(e) {
                    st.email.setAttribute('type', 'email');
                }
            }
        }

        // Start onmiddellijk en blijf proberen
        fixAttributes();
        forceEmailType();

        // Regelmatige checks (React kan attributen resetten)
        var attempts = 0;
        var interval = setInterval(function() {
            fixAttributes();
            forceEmailType();
            attempts++;
            if (attempts > 60) clearInterval(interval);
        }, 300);

        // MutationObserver als vangnet
        var observer = new MutationObserver(function(mutations) {
            // Reset markers als inputs vervangen zijn
            mutations.forEach(function(m) {
                if (m.addedNodes.length > 0) {
                    fixAttributes();
                    forceEmailType();
                }
            });
        });
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
            "<h1 style='text-align: center; color: #1A1A2E; font-family: Inter, sans-serif; "
            "font-weight: 700; letter-spacing: -0.02em;'>🏛️ Rome Flip Analyzer</h1>"
            "<p style='text-align: center; color: #E8956A; font-size: 1.1em; "
            "font-family: Inter, sans-serif; margin-bottom: 2em;'>Vastgoed Investeringsanalyse</p>",
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
