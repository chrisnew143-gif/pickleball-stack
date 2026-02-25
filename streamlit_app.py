import streamlit as st

st.set_page_config(page_title="Pickleball Manager", layout="centered")

# =========================
# BACKGROUND IMAGE
# =========================
page_bg_img = """
<style>
[data-testid="stAppViewContainer"] {
background-image: url("TDphoto.jpg");
background-size: cover;
background-position: center;
background-repeat: no-repeat;
background-attachment: fixed;
}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

# =========================
# HEADER PHOTO
# =========================
col1, col2, col3 = st.columns([1,2,1])
with col2:
    st.image("TDphoto.jpg", width=300)

st.title("🏠 TiraDinks Official")
st.write("Welcome to the TiraDinks Club!")
