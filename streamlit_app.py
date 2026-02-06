import streamlit as st

st.set_page_config(page_title="Pickleball Manager", layout="centered")

st.title("🎾 Pickleball Stack System")

col1, col2 = st.columns(2)

if col1.button("🏟 Organizer (AutoStack)", use_container_width=True):
    st.switch_page("1_AutoStack.py")

if col2.button("👤 Player Join", use_container_width=True):
    st.switch_page("pages/2_PlayerJoin.py")
