import streamlit as st
import random
from collections import deque
import pandas as pd
from itertools import combinations
import json
import os
import base64  # ✅ ADDED

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(page_title="Pickleball Auto Stack", page_icon="🎾", layout="wide")

# ✅ FIXED BACKGROUND (does NOT block UI)
def set_background(image_file):
    with open(image_file, "rb") as img:
        encoded = base64.b64encode(img.read()).decode()

    st.markdown(
        f"""
        <style>

        /* Background layer */
        .stApp {{
            background: url("data:image/jpg;base64,{encoded}") no-repeat center center fixed;
            background-size: cover;
        }}

        /* Dark overlay WITHOUT blocking clicks */
        .stApp::before {{
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.45);
            pointer-events: none;   /* ✅ THIS FIXES YOUR SETTINGS BUTTON */
            z-index: 0;
        }}

        </style>
        """,
        unsafe_allow_html=True
    )

set_background("TDphoto.jpg")

st.markdown("""
<style>
footer {visibility:hidden;}
a[href*="github.com/streamlit"]{display:none!important;}

.court-card{
    padding:14px;
    border-radius:12px;
    background:#f4f6fa;
    margin-bottom:12px;
}
.waiting-box{
    background:#fff3cd;
    padding:10px;
    border-radius:10px;
}
</style>
""", unsafe_allow_html=True)

st.title("🎾 Pickleball Auto Stack")
st.caption("First come • first play • fair rotation")

# ======================================================
# (EVERYTHING BELOW REMAINS EXACTLY THE SAME)
# ======================================================
