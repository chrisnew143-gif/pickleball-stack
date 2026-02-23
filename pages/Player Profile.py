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

                # Check for error in APIResponse
                if response.error:
                    st.error(f"Failed to add player: {response.error.message}")
                else:
                    st.success(f"Player '{name}' added successfully!")

            except Exception as e:
                st.error(f"Unexpected error adding player: {e}")

# ==========================
# View Registered Players
# ==========================
st.subheader("📋 Registered Players")

try:
    response = supabase.table("players").select("*").execute()
    players = response.data if response.data else []

    if players:
        # Display players in table format
        st.table(players)

        # ==========================
        # Delete Player Section
        # ==========================
        st.subheader("❌ Delete Player")
        player_names = [p.get("name") for p in players if "name" in p]
        selected_player = st.selectbox("Select player to delete", [""] + player_names)

        if st.button("Delete Player") and selected_player:
            try:
                del_response = supabase.table("players").delete().eq("name", selected_player).execute()
                if del_response.error:
                    st.error(f"Failed to delete player: {del_response.error.message}")
                else:
                    st.success(f"Player '{selected_player}' deleted successfully!")
                    st.experimental_rerun()  # refresh the page to update list
            except Exception as e:
                st.error(f"Unexpected error deleting player: {e}")

    else:
        st.info("No players registered yet.")
except Exception as e:
    st.error(f"Error fetching players: {e}")
