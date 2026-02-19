import pandas as pd
import random
from collections import defaultdict

# ==========================================================
# CONFIGURATION
# ==========================================================
INPUT_FILE = "players.xlsx"
OUTPUT_FILE = "generated_matches.xlsx"

BRACKETS = [
    (2.5, 3.0),
    (3.0, 3.5),
    (3.5, 4.0)
]

ROUNDS = 3   # how many match rounds per bracket

# ==========================================================
# LOAD PLAYERS
# ==========================================================
df = pd.read_excel(INPUT_FILE)

required_columns = ["Name", "DUPR_ID", "Rating"]
for col in required_columns:
    if col not in df.columns:
        raise ValueError(f"Missing required column: {col}")

# ==========================================================
# HELPER: BALANCED TEAM CREATION
# Highest + Lowest pairing
# ==========================================================
def create_balanced_teams(players, partner_history):

    # Sort players by rating
    players_sorted = sorted(players, key=lambda x: x["Rating"])

    # Pair highest + lowest
    team1 = [players_sorted[0], players_sorted[-1]]
    team2 = [players_sorted[1], players_sorted[-2]]

    # Check if partners already played together
    def partners_repeated(team):
        p1 = team[0]["Name"]
        p2 = team[1]["Name"]
        return p2 in partner_history[p1]

    # If repeated, reshuffle
    if partners_repeated(team1) or partners_repeated(team2):
        random.shuffle(players_sorted)
        team1 = players_sorted[:2]
        team2 = players_sorted[2:]

    return team1, team2


# ==========================================================
# GROUP PLAYERS BY RATING BRACKET
# ==========================================================
bracket_groups = {}

for low, high in BRACKETS:
    bracket_name = f"{low}-{high}"
    group = df[(df["Rating"] >= low) & (df["Rating"] < high)]
    bracket_groups[bracket_name] = group.to_dict("records")

# ==========================================================
# GENERATE MATCHES
# ==========================================================
matches_output = []

for bracket, players in bracket_groups.items():

    if len(players) < 4:
        continue

    print(f"\nGenerating matches for bracket {bracket}")

    partner_history = defaultdict(set)

    for round_number in range(1, ROUNDS + 1):

        random.shuffle(players)

        court_number = 1

        for i in range(0, len(players), 4):

            group = players[i:i+4]

            if len(group) < 4:
                continue

            team_a, team_b = create_balanced_teams(group, partner_history)

            # Update partner history
            partner_history[team_a[0]["Name"]].add(team_a[1]["Name"])
            partner_history[team_a[1]["Name"]].add(team_a[0]["Name"])
            partner_history[team_b[0]["Name"]].add(team_b[1]["Name"])
            partner_history[team_b[1]["Name"]].add(team_b[0]["Name"])

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

            court_number += 1

# ==========================================================
# EXPORT TO EXCEL
# ==========================================================
matches_df = pd.DataFrame(matches_output)
matches_df.to_excel(OUTPUT_FILE, index=False)

print("\n✅ DUPR-Style Matches Generated Successfully!")
