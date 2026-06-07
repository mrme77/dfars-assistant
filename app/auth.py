"""Single shared-login gate for the DFARS app.

Authentication is active only when ``DFARS_AUTH_PASSWORD_HASH`` is set (a bcrypt
hash). When unset, the app runs open — convenient for local development. On a
hosted deployment, set the hash (and ideally the username) as a secret to gate
access.

Generate a hash without exposing the plaintext:

    dfars-env/bin/python -m app.auth
"""

from __future__ import annotations

import hmac
import os
import time

import bcrypt
import streamlit as st

_DEFAULT_USERNAME = "dfars"
_MAX_ATTEMPTS = 5
_LOCKOUT_SECONDS = 60


def auth_enabled() -> bool:
    """Return whether a password hash is configured."""
    return bool(os.getenv("DFARS_AUTH_PASSWORD_HASH"))


def require_login() -> None:
    """Gate the app behind a shared username/password.

    Renders a login form and halts the script (``st.stop``) until the user is
    authenticated. No-op when authentication is not configured.
    """
    if not auth_enabled() or st.session_state.get("dfars_authed"):
        return

    _render_login_form()
    st.stop()


def sign_out_button() -> None:
    """Render a sign-out control when authentication is active."""
    if not auth_enabled() or not st.session_state.get("dfars_authed"):
        return
    if st.button("Sign out", key="dfars_signout"):
        st.session_state.pop("dfars_authed", None)
        st.rerun()


def _render_login_form() -> None:
    """Render the login form and process a submission."""
    locked_until = st.session_state.get("dfars_lock_until", 0.0)
    remaining = int(locked_until - time.time())

    st.markdown('<div class="dfars-eyebrow">◆ Authentication required</div>', unsafe_allow_html=True)
    with st.container(border=True):
        with st.form("dfars_login", clear_on_submit=False):
            username = st.text_input("Username", autocomplete="username")
            password = st.text_input("Password", type="password", autocomplete="current-password")
            submitted = st.form_submit_button("Sign in", disabled=remaining > 0)

    if remaining > 0:
        st.warning(f"Too many attempts. Try again in {remaining}s.")
        return

    if submitted:
        if _verify(username, password):
            st.session_state["dfars_authed"] = True
            st.session_state.pop("dfars_attempts", None)
            st.rerun()
        else:
            _register_failure()
            st.error("Invalid credentials.")


def _verify(username: str, password: str) -> bool:
    """Constant-time username check plus bcrypt password verification."""
    expected_user = os.getenv("DFARS_AUTH_USERNAME", _DEFAULT_USERNAME)
    password_hash = os.getenv("DFARS_AUTH_PASSWORD_HASH", "")
    if not password_hash:
        return False

    user_ok = hmac.compare_digest(username.strip(), expected_user)
    try:
        password_ok = bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # Malformed hash in the environment — fail closed.
        return False
    return user_ok and password_ok


def _register_failure() -> None:
    """Track failed attempts and apply a temporary lockout."""
    attempts = st.session_state.get("dfars_attempts", 0) + 1
    st.session_state["dfars_attempts"] = attempts
    if attempts >= _MAX_ATTEMPTS:
        st.session_state["dfars_lock_until"] = time.time() + _LOCKOUT_SECONDS
        st.session_state["dfars_attempts"] = 0


def _generate_hash_cli() -> None:
    """Prompt for a password and print its bcrypt hash (no plaintext echo)."""
    import getpass

    password = getpass.getpass("Password to hash: ")
    if password != getpass.getpass("Confirm password: "):
        raise SystemExit("Passwords do not match.")
    digest = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    print("\nSet these as secrets / env vars:\n")
    print(f"DFARS_AUTH_USERNAME={_DEFAULT_USERNAME}")
    print(f"DFARS_AUTH_PASSWORD_HASH={digest}")


if __name__ == "__main__":
    _generate_hash_cli()
