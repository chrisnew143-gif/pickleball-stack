import streamlit as st

st.set_page_config(page_title="Pickleball Manager", layout="centered")

# -------------------------
# Router
# -------------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

def go(page):
    st.session_state.page = page
    st.rerun()


# =========================
# HOME PAGE
# =========================
if st.session_state.page == "home":

    st.title("🎾 Pickleball Stack System")

    col1, col2 = st.columns(2)

    if col1.button("🏟 Organizer (AutoStack)", use_container_width=True):
        go("autostack")

    if col2.button("🏢 Clubs", use_container_width=True):
        go("registerclub")


# =========================
# AUTOSTACK PAGE
# =========================
elif st.session_state.page == "autostack":
    import AutoStack   # your AutoStack.py module


# =========================
# PLAYER PAGE
# =========================
elif st.session_state.page == "player":
    import PlayerJoin   # your PlayerJoin.py module


# =========================
# REGISTER CLUB PAGE
# =========================
elif st.session_state.page == "registerclub":
    import RegisterClub  # your RegisterClub.py module
