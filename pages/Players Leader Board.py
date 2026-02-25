import streamlit as st
import pandas as pd
from supabase_client import get_supabase

supabase = get_supabase()

# ================== PAGE CONFIG ==================
st.set_page_config(page_title="Pickleball Leaderboard", page_icon="🏆", layout="wide")
st.title("🏆 Pickleball Leaderboard")
st.caption("Rankings based on total wins and win rate")

# ================== GET PLAYER DATA ==================
def get_players_data():
    """Fetch players from Supabase."""
    try:
        response = supabase.table("players").select("*").execute()
        if response.data:
            df = pd.DataFrame(response.data)
            # Calculate win rate
            df["win_rate"] = df.apply(
                lambda row: round((row["wins"] / row["games"]) * 100, 2) if row["games"] > 0 else 0, axis=1
            )
            return df
        else:
            return pd.DataFrame(columns=["name", "skill", "wins", "games", "win_rate"])
    except Exception as e:
        st.error(f"Failed to fetch players: {e}")
        return pd.DataFrame(columns=["name", "skill", "wins", "games", "win_rate"])

df_players = get_players_data()

# ================== LEADERBOARD BY CATEGORY ==================
categories = ["BEGINNER", "NOVICE", "INTERMEDIATE"]

for cat in categories:
    st.subheader(f"{cat.title()}s")
    df_cat = df_players[df_players["skill"].str.upper() == cat].copy()
    
    if not df_cat.empty:
        # Sort by wins descending, then by win_rate descending
        df_cat.sort_values(["wins", "win_rate"], ascending=[False, False], inplace=True)
        # Select only columns to display
        df_display = df_cat[["name", "wins", "win_rate"]]
        df_display.rename(columns={"name": "Player Name", "wins": "Wins", "win_rate": "Win Rate (%)"}, inplace=True)
        st.dataframe(df_display.reset_index(drop=True), use_container_width=True)
    else:
        st.info("No players in this category yet.")
