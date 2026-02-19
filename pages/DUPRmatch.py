import streamlit as st
import pandas as pd
import random
from collections import defaultdict
from io import BytesIO

# ============================
# PAGE CONFIG
# ============================
st.set_page_config(page_title="DUPR Match Generator", layout="wide")
st.title("🏆 DUPR Match Generator")
st.write("Upload your Excel file with columns: Name, DUPR_ID, Rating")

# ============================
# FILE UPLOADER
# ============================
uploaded_file = st.file_uploader("Upload Players Excel File", type=["xlsx", "csv"])

# ============================
# CONFIG INPUTS
# ============================
BRACKETS = [
    (2.0, 2.5),
    (2.5, 3.0),
    (3.0, 3.5),
    (3.5, 4.0)
]

ROUNDS = st.number_input("Number of Rounds", min_value=1, max_value=10, value=2)
NUM_COURTS = st.number_input("Number of Courts", min_value=1, max_value=10, value=2)

# ============================
# GENERATE MATCHES
# ============================
if uploaded_file is not None:
    # Read file
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file, engine="openpyxl")

    # Validate required columns
    required_columns = ["Name", "DUPR_ID", "Rating"]
    for col in required_columns:
        if col not in df.columns:
            st.error(f"Missing required column: {col}")
            st.stop()

    if st.button("🚀 Generate Matches", use_container_width=True):
        matches_output = []

        # Group players by bracket
        bracket_groups = {}
        for low, high in BRACKETS:
            bracket_name = f"{low}-{high}"
            group = df[(df["Rating"] >= low) & (df["Rating"] < high)]
            bracket_groups[bracket_name] = group.to_dict("records")

        # Generate matches for each bracket
        for bracket, players in bracket_groups.items():

            if len(players) < 4:
                continue  # Skip brackets with less than 4 players

            partner_history = defaultdict(set)

            # ============================
            # Assign players to fixed courts evenly
            # ============================
        courts_players = [[] for _ in range(NUM_COURTS)]

        for idx, player in enumerate(players):
            court_idx = idx % NUM_COURTS  # Distribute players round-robin
            courts_players[court_idx].append(player)

            # Remove courts with less than 4 players (optional)
                courts_players = [court for court in courts_players if len(court) >= 4]


            

            # ============================
            # Generate rounds
            # ============================
            for round_number in range(1, ROUNDS + 1):
                for court_number, court_players in enumerate(courts_players, start=1):
                    random.shuffle(court_players)

                    # Create balanced teams
                    court_players_sorted = sorted(court_players, key=lambda x: x["Rating"])
                    team_a = [court_players_sorted[0], court_players_sorted[-1]]
                    team_b = [court_players_sorted[1], court_players_sorted[2]]

                    # Avoid repeat partners
                    def repeated(team):
                        return team[1]["Name"] in partner_history[team[0]["Name"]]

                    if repeated(team_a) or repeated(team_b):
                        random.shuffle(court_players_sorted)
                        team_a = court_players_sorted[:2]
                        team_b = court_players_sorted[2:4]

                    # Update partner history
                    partner_history[team_a[0]["Name"]].add(team_a[1]["Name"])
                    partner_history[team_a[1]["Name"]].add(team_a[0]["Name"])
                    partner_history[team_b[0]["Name"]].add(team_b[1]["Name"])
                    partner_history[team_b[1]["Name"]].add(team_b[0]["Name"])

                    # Append match to output
                    matches_output.append({
                        "Bracket": bracket,
                        "Round": round_number,
                        "Court": court_number,
                        "Team A Player 1": team_a[0]["Name"],
                        "Team A Player 2": team_a[1]["Name"],
                        "Team A Avg Rating": round((team_a[0]["Rating"] + team_a[1]["Rating"]) / 2, 2),
                        "Team B Player 1": team_b[0]["Name"],
                        "Team B Player 2": team_b[1]["Name"],
                        "Team B Avg Rating": round((team_b[0]["Rating"] + team_b[1]["Rating"]) / 2, 2),
                    })

        if matches_output:
            matches_df = pd.DataFrame(matches_output)
            st.success("✅ Matches Generated Successfully!")
            st.dataframe(matches_df, use_container_width=True)

            # ============================
            # DOWNLOAD EXCEL
            # ============================
            output = BytesIO()
            matches_df.to_excel(output, index=False, engine="openpyxl")
            output.seek(0)
            st.download_button(
                label="📥 Download Matches Excel",
                data=output,
                file_name="DUPR_Matches.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            st.warning("Not enough players to generate matches in the selected brackets.")
