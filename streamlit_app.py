import streamlit as st

st.set_page_config(page_title="Pickleball Manager", layout="centered")
st.title("🎾 Pickleball Stack System")

col1, col2 = st.columns(2)

if col1.button("Organizer (AutoStack)"):
    st.switch_page("1_AutoStack")  # matches filename without .py

if col2.button("Player Join"):
    st.switch_page("2_PlayerJoin")  # matches filename without .py
