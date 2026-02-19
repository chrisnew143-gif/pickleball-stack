import streamlit as st

st.set_page_config(page_title="Pickleball Manager", layout="centered")

st.title("🏠 Pickleball Manager")
st.write("Welcome to the Auto Stack Application!")

st.divider()

# Button to Open AutoStack page
if st.button("🎾 Open Play Stacking", use_container_width=True):
    st.switch_page("pages/AutoStack.py")
