import streamlit as st

st.set_page_config(page_title="Pickleball Manager", layout="centered")

if "page" not in st.session_state:
    st.session_state.page = "home"

def go(page):
    st.session_state.page = page
    st.rerun()

if st.session_state.page == "home":
    st.title("🎾 Pickleball Stack System")

    col1, col2 = st.columns(2)

    if col1.button("🏟 Organizer (AutoStack)", use_container_width=True):
        go("autostack")

    if col2.button("👤 Player Join", use_container_width=True):
        go("player")

elif st.session_state.page == "autostack":
    import AutoStack   # your module file

elif st.session_state.page == "player":
    import PlayerJoin
