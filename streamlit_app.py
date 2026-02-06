import streamlit as st

st.set_page_config(page_title="Pickleball Manager", layout="centered")
st.title("🎾 Pickleball Stack System")
st.write("Welcome! Choose from the sidebar to manage players or AutoStack courts.")

st.write("""
- **AutoStack Organizer** → Assign players to courts automatically  
- **Player Join** → Players can join the queue
""")

st.info("Use the sidebar on the left to navigate to pages.")
