import streamlit as st

st.title("🏢 Clubs")
st.markdown("## 🚧 Under Construction 🚧")
st.info("Club registration feature coming soon!")

# ✅ Back button
if st.button("⬅ Back to Home"):
    st.session_state.page = "home"
    st.rerun()
