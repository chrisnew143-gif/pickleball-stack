import streamlit as st
import base64

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

# ✅ BACKGROUND IMAGE FUNCTION ADDED
def set_background(image_file):
    with open(image_file, "rb") as img:
        encoded = base64.b64encode(img.read()).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: contain;   /* ✅ Show full image */
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-color: #000000;  /* Optional: fills empty space */
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_background("TDphoto.jpg")
