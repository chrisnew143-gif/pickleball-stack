import streamlit as st
import pandas as pd
import random
from collections import defaultdict
from io import BytesIO
import math

# ============================
# PAGE CONFIG
# ============================
st.set_page_config(page_title="DUPR Fair Match Generator", layout="wide")
st.title("🏆 DUPR Fair Match Generator")
st.write("Upload Excel file with columns: Name, DUPR_ID, Rating")

# ============================
# FILE UPLOADER
# ============================
uploaded_file = st.file_uploader("Upload Players Excel File", type=["xlsx", "csv"])

# ============================
# CONFIG INPUTS
# ============================
NUM_MATCHES = st.number_input("Number of Matches", min_value=1, max_value=50, value=5)
NUM_COURTS = st.number_input("Number of Courts", min_value=1, max_value=10, value=4)

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

        # Sort players by rating (HIGH to LOW)
        df = df.sort_values(by="Rating", ascending=False).reset_index(drop=True)

        total_players = len(df)
        players_per_court = math.ceil(total_players / NUM_COURTS)

        matches_output = []
        court_assignments_output = []

        # ============================
        # SPLIT PLAYERS EVENLY BY SKILL
        # ============================
        courts_players = []

        for i in range(NUM_COURTS):
            start = i * players_per_court
            end = start + players_per_court
            court_group = df.iloc[start:end].to_dict("records")
            courts_players.append(court_group)

        # ============================
        # SAVE COURT ASSIGNMENTS
        # ============================
        for court_number, court_players in enumerate(courts_players, start=1):
            for p in court_players:
                court_assignments_output.append({
                    "Court": court_number,
                    "Player Name": p["Name"],
                    "DUPR_ID": p["DUPR_ID"],
                    "Rating": p["Rating"]
                })

        # ============================
        # GENERATE MATCHES
        # ============================
        for court_number, court_players in enumerate(courts_players, start=1):

            if len(court_players) < 4:
                continue

            partner_history = defaultdict(set)

            for match_number in range(1, NUM_MATCHES + 1):

                random.shuffle(court_players)

                group = court_players[:4]

                # Balanced pairing (strongest + weakest)
                group_sorted = sorted(group, key=lambda x: x["Rating"])
                team_a = [group_sorted[0], group_sorted[-1]]
                team_b = [group_sorted[1], group_sorted[2]]

                # Avoid repeat partners
                def repeated(team):
                    return team[1]["Name"] in partner_history[team[0]["Name"]]

                if repeated(team_a) or repeated(team_b):
                    random.shuffle(group_sorted)
                    team_a = group_sorted[:2]
                    team_b = group_sorted[2:4]

                # Update partner history
                partner_history[team_a[0]["Name"]].add(team_a[1]["Name"])
                partner_history[team_a[1]["Name"]].add(team_a[0]["Name"])
                partner_history[team_b[0]["Name"]].add(team_b[1]["Name"])
                partner_history[team_b[1]["Name"]].add(team_b[0]["Name"])

                matches_output.append({
                    "Court": court_number,
                    "Match": match_number,
                    "Team A Player 1": team_a[0]["Name"],
                    "Team A Player 2": team_a[1]["Name"],
                    "Team A Avg Rating": round((team_a[0]["Rating"] + team_a[1]["Rating"]) / 2, 3),
                    "Team B Player 1": team_b[0]["Name"],
                    "Team B Player 2": team_b[1]["Name"],
                    "Team B Avg Rating": round((team_b[0]["Rating"] + team_b[1]["Rating"]) / 2, 3),
                })

        # ============================
        # DISPLAY RESULTS
        # ============================
        if matches_output:

            matches_df = pd.DataFrame(matches_output)
            st.success("✅ Matches Generated Successfully!")
            st.dataframe(matches_df, use_container_width=True)

            # Download Matches Excel
            output_matches = BytesIO()
            matches_df.to_excel(output_matches, index=False, engine="openpyxl")
            output_matches.seek(0)

            st.download_button(
                label="📥 Download Match Schedule",
                data=output_matches,
                file_name="DUPR_Match_Schedule.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

            # Download Court Assignment Excel
            court_df = pd.DataFrame(court_assignments_output)
            output_courts = BytesIO()
            court_df.to_excel(output_courts, index=False, engine="openpyxl")
            output_courts.seek(0)

            st.download_button(
                label="📥 Download Court Assignments",
                data=output_courts,
                file_name="DUPR_Court_Assignments.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        else:
            st.warning("Not enough players to generate matches.")
