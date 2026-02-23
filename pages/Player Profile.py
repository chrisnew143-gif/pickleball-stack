# player_profile.py
import streamlit as st
from supabase_client import get_supabase

# Initialize Supabase client
supabase = get_supabase()

st.set_page_config(page_title="🎾 Player Profiles", layout="centered")
st.title("🎾 Player Profiles - TiraDinks Official")

# ==========================
# Add Player Form
# ==========================
st.subheader("➕ Add New Player")

with st.form("add_player_form", clear_on_submit=True):
    name = st.text_input("Player Name")
    dupr = st.text_input("DUPR ID")
    skill = st.radio("Skill", ["Beginner", "Novice", "Intermediate"], horizontal=True)
    
    submitted = st.form_submit_button("Add Player")
    if submitted:
        if not name or not dupr:
            st.error("Please provide both Name and DUPR ID")
        else:
            try:
                # Insert into Supabase table 'players'
                response = supabase.table("players").insert({
                    "name": name,
                    "dupr": dupr,
                    "skill": skill
                }).execute()
                
                if response.status_code == 201 or response.data:
                    st.success(f"Player '{name}' added successfully!")
                else:
                    st.error(f"Failed to add player: {response.data}")
            except Exception as e:
                st.error(f"Error adding player: {e}")

# ==========================
# View Registered Players
# ==========================
st.subheader("📋 Registered Players")

try:
    response = supabase.table("players").select("*").execute()
    players = response.data if response.data else []
    if players:
        st.table(players)
    else:
        st.info("No players registered yet.")
except Exception as e:
    st.error(f"Error fetching players: {e}")
