# player_profile.py
import streamlit as st
from supabase_client import get_supabase

# ==========================
# INIT
# ==========================
supabase = get_supabase()

st.set_page_config(page_title="🎾 Player Profiles", layout="centered")
st.title("🎾 Player Profiles - TiraDinks Official")

# =====================================================
# LOAD PLAYERS (used for display + delete dropdown)
# =====================================================
try:
    response = supabase.table("players").select("*").order("created_at").execute()
    players = response.data or []
except Exception as e:
    st.error(f"Error loading players: {e}")
    players = []

# =====================================================
# SIDEBAR - ADD PLAYER
# =====================================================
st.sidebar.header("➕ Add Player")

with st.sidebar.form("add_player_form", clear_on_submit=True):
    name = st.text_input("Player Name")
    dupr = st.text_input("DUPR ID")  # Alphanumeric
    skill = st.radio(
        "Skill",
        ["Beginner", "Novice", "Intermediate"],
        horizontal=False
    )

    submitted = st.form_submit_button("Add Player")

    if submitted:
        if not name.strip() or not dupr.strip():
            st.sidebar.error("Please provide both Name and DUPR ID")
        else:
            try:
                response = supabase.table("players").insert({
                    "name": name.strip(),
                    "dupr": dupr.strip(),
                    "skill": skill
                }).execute()

                if response.data:
                    st.sidebar.success(f"✅ {name} added!")
                    st.rerun()
                else:
                    st.sidebar.error("Insert failed. Player may already exist.")

            except Exception as e:
                st.sidebar.error(f"Error adding player: {e}")

# =====================================================
# SIDEBAR - DELETE PLAYER
# =====================================================
st.sidebar.header("🗑 Delete Player")

if players:
    player_names = [p["name"] for p in players]
    selected_name = st.sidebar.selectbox(
        "Select Player to Delete",
        player_names
    )

    if st.sidebar.button("Delete Selected Player"):
        try:
            selected_player = next(
                (p for p in players if p["name"] == selected_name),
                None
            )

            if selected_player:
                delete_response = (
                    supabase
                    .table("players")
                    .delete()
                    .eq("id", selected_player["id"])
                    .execute()
                )

                if delete_response.data is not None:
                    st.sidebar.success(f"Deleted {selected_name}")
                    st.rerun()
                else:
                    st.sidebar.error("Delete failed.")

        except Exception as e:
            st.sidebar.error(f"Error deleting player: {e}")
else:
    st.sidebar.info("No players to delete.")

# =====================================================
# MAIN PAGE - HD TABLE DISPLAY
# =====================================================
st.subheader("📋 Registered Players")

if not players:
    st.info("No players registered yet.")
else:
    import pandas as pd

    df = pd.DataFrame(players)

    # Ensure numeric fields exist
    df["games"] = df.get("games", 0)
    df["wins"] = df.get("wins", 0)

    # Calculate win rate safely
    df["Win %"] = df.apply(
        lambda row: round((row["wins"] / row["games"]) * 100, 1)
        if row["games"] > 0 else 0,
        axis=1
    )

    # Clean formatting
    df["skill"] = df["skill"].str.upper()

    # Rename columns for display
    df_display = df[[
        "name",
        "dupr",
        "skill",
        "games",
        "wins",
        "Win %"
    ]].rename(columns={
        "name": "Player",
        "dupr": "DUPR ID",
        "skill": "Skill",
        "games": "Games Played",
        "wins": "Wins"
    })

    # Sort by Wins (descending)
    df_display = df_display.sort_values(by="Wins", ascending=False)

    # Show as HD styled dataframe
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True
    )
