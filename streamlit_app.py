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
# HOME
# =========================
if st.session_state.page == "home":

    st.title("🎾 Pickleball Stack System")

    col1, col2, col3, col4 = st.columns(4)

    if col1.button("🏟 Open Play(Stacking)", use_container_width=True):
        go("autostack")

    if col2.button("👤 Tournament Matches", use_container_width=True):
        go("player")

    if col3.button("🏢 DUPR Matches", use_container_width=True):
        go("registerclub")

    if col4.button("🏢 InterClub Matches", use_container_width=True):
        go("registerclub")


# =========================
# Open Play
# =========================
elif st.session_state.page == "autostack":

    if st.button("⬅ Back to Home"):
        go("home")

    import AutoStack   # your module


# =========================
# Tournament Matches
# =========================
elif st.session_state.page == "player":

    if st.button("⬅ Back to Home"):
        go("home")

    st.markdown("## 🚧 Under Construction 🚧")
    st.info("feature coming soon!")



# =========================
# DUPR Matches
# =========================
elif st.session_state.page == "registerclub":

    if st.button("⬅ Back to Home"):
        go("home")

    st.markdown("## 🚧 Under Construction 🚧")
    st.info("feature coming soon!")

# =========================
# InterClub Matches
# =========================
elif st.session_state.page == "registerclub":

    if st.button("⬅ Back to Home"):
        go("home")

    st.markdown("## 🚧 Under Construction 🚧")
    st.info("feature coming soon!")
