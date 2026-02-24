import streamlit as st
import random
from collections import deque
import pandas as pd
from itertools import combinations
import json
import os
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
from supabase_client import get_supabase

supabase = get_supabase()


# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(page_title="Pickleball Auto Stack TiraDinks Official", page_icon="🎾", layout="wide")

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

# =========================
# HEADER PHOTO
# =========================
col1, col2, col3 = st.columns([1,2,1])
with col2:
st.image("TDphoto.jpg", width=300)

st.title("🎾 Pickleball Auto Stack TiraDinks Official")
st.caption("WE CAMED WE DINKED!")

# ======================================================
# HELPERS
# ======================================================
def icon(skill):
return {"BEGINNER":"🟢","NOVICE":"🟡","INTERMEDIATE":"🔴"}[skill]

def superscript_number(n):
sup_map = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
return str(n).translate(sup_map)

def fmt(p):
name, skill, dupr = p
games = st.session_state.players.get(name, {}).get("games", 0)
return f"{icon(skill)} {superscript_number(games)} {name}"

def safe_group(players):
skills = {p[1] for p in players}
return not ("BEGINNER" in skills and "INTERMEDIATE" in skills)

def make_teams(players):
random.shuffle(players)
return [players[:2], players[2:]]

# ======================================================
# SESSION INIT
# ======================================================
def init():
ss = st.session_state
ss.setdefault("queue", deque())
ss.setdefault("courts", {})
ss.setdefault("locked", {})
ss.setdefault("scores", {})
ss.setdefault("history", [])
ss.setdefault("started", False)
ss.setdefault("court_count", 2)
ss.setdefault("players", {})
ss.setdefault("match_start_time", {})

init()

# ======================================================
# DELETE PLAYER
# ======================================================
def delete_player(name):
st.session_state.queue = deque([p for p in st.session_state.queue if p[0] != name])
for cid, teams in st.session_state.courts.items():
if not teams:
continue
new_teams = []
for team in teams:
new_teams.append([p for p in team if p[0] != name])
if len(new_teams[0]) < 2 or len(new_teams[1]) < 2:
st.session_state.courts[cid] = None
st.session_state.locked[cid] = False
else:
st.session_state.courts[cid] = new_teams
st.session_state.players.pop(name, None)

# ======================================================
# MATCH ENGINE (FULL FIXED)
# ======================================================
def take_four_safe():
"""
   Find the first safe combination of 4 players 
   while preserving first-come priority as much as possible.
   """
q = list(st.session_state.queue)

if len(q) < 4:
return None

# Try all 4-player combinations in queue order
for combo in combinations(q, 4):
if safe_group(combo):
# Remove selected players from queue
new_queue = q.copy()
for p in combo:
new_queue.remove(p)
st.session_state.queue = deque(new_queue)
return list(combo)

return None

def make_teams(players):
"""Create two teams from 4 players, preserving first-come-first-play order."""
return [players[:2], players[2:]]

def start_match(cid):
"""Start a match on a court if available and not locked."""
if st.session_state.locked.get(cid, False):
return
players = take_four_safe()
if not players:
return
st.session_state.courts[cid] = make_teams(players)
st.session_state.locked[cid] = True
st.session_state.scores[cid] = [0, 0]
st.session_state.match_start_time[cid] = datetime.now()

def finish_match(cid):
"""Finish a match, update stats, return players to queue in FCFS order."""
teams = st.session_state.courts.get(cid)
if not teams:
return

scoreA, scoreB = st.session_state.scores.get(cid, [0, 0])
teamA, teamB = teams

# Determine winners and losers
if scoreA > scoreB:
winner = "Team A"
winners, losers = teamA, teamB
elif scoreB > scoreA:
winner = "Team B"
winners, losers = teamB, teamA
else:
winner = "DRAW"
winners = losers = []

# Update player stats
for p in teamA + teamB:
st.session_state.players[p[0]]["games"] += 1
for p in winners:
st.session_state.players[p[0]]["wins"] += 1
for p in losers:
st.session_state.players[p[0]]["losses"] += 1

# Record match history
end_time = datetime.now()
start_time = st.session_state.match_start_time.get(cid)
if start_time:
duration = round((end_time - start_time).total_seconds() / 60, 2)
start_str = start_time.strftime("%H:%M:%S")
end_str = end_time.strftime("%H:%M:%S")
else:
duration = 0
start_str = ""
end_str = ""

st.session_state.history.append({
"Court": cid,
"Team A": " & ".join(p[0] for p in teamA),
"Team B": " & ".join(p[0] for p in teamB),
"Score A": scoreA,
"Score B": scoreB,
"Winner": winner,
"Start Time": start_str,
"End Time": end_str,
"Duration (Minutes)": duration
})

# Clear court and start time
st.session_state.match_start_time.pop(cid, None)
st.session_state.courts[cid] = None
st.session_state.locked[cid] = False
st.session_state.scores[cid] = [0, 0]

# Return all players to queue in original order (FCFS)
st.session_state.queue.extend(teamA + teamB)

def auto_fill():
"""Automatically fill empty courts if the queue has enough players."""
if not st.session_state.started:
return
for cid in range(1, st.session_state.court_count + 1):
if st.session_state.courts.get(cid) is None:
start_match(cid)

# ===================== WINNER WINNER BUTTON LOGIC =====================
def winner_winner(cid):
"""Keep winners on court and rotate losers to queue."""
teams = st.session_state.courts.get(cid)
if not teams:
st.warning("No players on court to apply Winner Winner")
return

scoreA, scoreB = st.session_state.scores.get(cid, [0, 0])
teamA, teamB = teams

if scoreA > scoreB:
winners, losers = teamA, teamB
elif scoreB > scoreA:
winners, losers = teamB, teamA
else:
st.warning("Match is a draw, cannot use Winner Winner")
return

# Rotate losers back to queue
st.session_state.queue.extend(losers)
# Keep winners on court
st.session_state.courts[cid] = [winners[:2], winners[2:]] if len(winners) > 2 else [winners, []]
st.session_state.scores[cid] = [0, 0]
st.rerun()

# ======================================================
# CSV EXPORTS
# ======================================================
def matches_csv():
if not st.session_state.history:
return b""
return pd.DataFrame(st.session_state.history).to_csv(index=False).encode()

def players_csv():
rows = []
for name, data in st.session_state.players.items():
rows.append({
"Player Name": name,
"DUPR ID": data["dupr"],
"Games Played": data["games"],
"Wins": data["wins"],
"Losses": data["losses"]
})
return pd.DataFrame(rows).to_csv(index=False).encode()

# ======================================================
# PROFILE SAVE / LOAD / DELETE
# ======================================================
SAVE_DIR = "profiles"
os.makedirs(SAVE_DIR, exist_ok=True)

def save_profile(name):
# Convert datetime objects to strings
match_start_time_str = {str(k): v.strftime("%Y-%m-%d %H:%M:%S") 
for k, v in st.session_state.match_start_time.items()}

data = {
"queue": list(st.session_state.queue),
"courts": st.session_state.courts,
"locked": st.session_state.locked,
"scores": st.session_state.scores,
"history": st.session_state.history,
"started": st.session_state.started,
"court_count": st.session_state.court_count,
"players": st.session_state.players,
"match_start_time": match_start_time_str
}
with open(os.path.join(SAVE_DIR, f"{name}.json"), "w") as f:
json.dump(data, f)
st.success(f"Profile '{name}' saved!")

def load_profile(name):
path = os.path.join(SAVE_DIR, f"{name}.json")
if not os.path.exists(path):
st.error("Profile not found!")
return
with open(path, "r") as f:
data = json.load(f)


# Convert keys back to int (VERY IMPORTANT)
st.session_state.courts = {int(k): v for k, v in data["courts"].items()}
st.session_state.locked = {int(k): v for k, v in data["locked"].items()}
st.session_state.scores = {int(k): v for k, v in data["scores"].items()}
st.session_state.queue = deque(data["queue"])
st.session_state.history = data["history"]
st.session_state.started = data["started"]
st.session_state.court_count = data["court_count"]
st.session_state.players = data["players"]

# Restore match_start_time exactly as saved
st.session_state.match_start_time = {}
for k, v in data.get("match_start_time", {}).items():
try:
st.session_state.match_start_time[int(k)] = datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
except Exception:
# fallback if string parsing fails
st.session_state.match_start_time[int(k)] = datetime.now()



def delete_profile(name):
path = os.path.join(SAVE_DIR, f"{name}.json")
if os.path.exists(path):
os.remove(path)
st.success(f"Profile '{name}' deleted!")
st.rerun()
else:
st.error("Profile not found!")

# ======================================================
# SIDEBAR (ORGANIZED WITH DROPDOWNS + DELETE PLAYER)
# ======================================================
with st.sidebar:

st.markdown('<h4 style="margin-bottom:10px;">⚙ Setup</h4>', unsafe_allow_html=True)

# ================== COURTS ==================
with st.expander("🏟 Courts", expanded=True):
st.session_state.court_count = st.selectbox(
"Number of Courts",
[2,3,4,5,6],
index=st.session_state.court_count-2
)

   # ================== ADD PLAYER ==================
with st.expander("➕ Add Player", expanded=False):
   # ================== ADD PLAYER (SIDEBAR) ==================
with st.sidebar.expander("➕ Add Player", expanded=False):

# 1️⃣ Fetch all registered players from Supabase
try:
registered_players = supabase.table("players").select("*").execute().data
except Exception as e:
st.error(f"Error fetching players from database: {e}")
registered_players = []

    player_names = [p["name"] for p in registered_players]
    # Build list of player names safely
    player_names = [p.get("name", "") for p in registered_players if "name" in p]

# 2️⃣ Add Player Form
with st.form("add_player_form", clear_on_submit=True):
selected_name = st.selectbox("Select Registered Player", [""] + player_names)

submitted = st.form_submit_button("Add Player")
if submitted and selected_name:

            # Prevent duplicates
if selected_name in st.session_state.players:
st.warning(f"{selected_name} is already in the queue!")
else:
                # Fetch the player's details from Supabase
                player_data = next((p for p in registered_players if p["name"] == selected_name), None)
                dupr = player_data["dupr"]
                skill = player_data["skill"].upper()

                # Add to queue and session players
                st.session_state.queue.append((selected_name, skill, dupr))
                st.session_state.players.setdefault(
                    selected_name,
                    {"dupr": dupr, "games":0, "wins":0, "losses":0}
                )
                st.success(f"Added player {selected_name} to queue!")
                # Find the player data safely
                player_data = next((p for p in registered_players if p.get("name") == selected_name), None)
                
                if not player_data:
                    st.error("Player data not found in database!")
                else:
                    # Get skill and DUPR safely with defaults
                    dupr = player_data.get("dupr", "N/A")
                    skill = player_data.get("skill", "BEGINNER").upper()

                    # Add to queue and session players
                    st.session_state.queue.append((selected_name, skill, dupr))
                    st.session_state.players.setdefault(
                        selected_name,
                        {"dupr": dupr, "games":0, "wins":0, "losses":0}
                    )
                    st.success(f"Added player {selected_name} to queue!")

# ================== DELETE PLAYER ==================
if st.session_state.players:
with st.expander("❌ Delete Player", expanded=False):
remove = st.selectbox(
"Select Player to Remove",
list(st.session_state.players.keys())
)
if st.button("Delete Player"):
delete_player(remove)
st.rerun()

# ================== START / RESET ==================
with st.expander("🚀 Start / Reset", expanded=True):
col1, col2 = st.columns(2)
with col1:
if st.button("Start Games"):
st.session_state.started = True
st.session_state.courts = {
i:None for i in range(1, st.session_state.court_count+1)
}
st.session_state.locked = {
i:False for i in st.session_state.courts
}
st.session_state.scores = {
i:[0,0] for i in st.session_state.courts
}
st.rerun()
with col2:
if st.button("Reset"):
st.session_state.clear()
st.rerun()

# ================== CSV DOWNLOAD ==================
with st.expander("📥 Export CSV", expanded=False):
st.download_button("Matches CSV", matches_csv(), "matches.csv")
st.download_button("Players CSV", players_csv(), "players.csv")

# ================== PROFILES ==================
with st.expander("💾 Profiles", expanded=False):
profile_name = st.text_input("Profile Name")

col1, col2 = st.columns(2)
with col1:
if st.button("Save") and profile_name:
save_profile(profile_name)
profiles = [f[:-5] for f in os.listdir(SAVE_DIR) if f.endswith(".json")]
selected_profile = st.selectbox("Select Profile", [""] + profiles)
with col2:
if st.button("Load") and selected_profile:
load_profile(selected_profile)
st.rerun()
if st.button("Delete Profile") and selected_profile:
delete_profile(selected_profile)



# ======================================================
# MAIN
# ======================================================
auto_fill()

st.subheader("⏳ Waiting Queue")
if st.session_state.queue:
st.markdown(
f'<div class="waiting-box">{", ".join(fmt(p) for p in st.session_state.queue)}</div>',
unsafe_allow_html=True
)
else:
st.success("No players waiting 🎉")

if not st.session_state.started:
st.stop()
st_autorefresh(interval=1000, key="live_timer")

# ======================================================
# COURTS (LIVE) - COLLAPSIBLE CONTROLS
# ======================================================
st.divider()
st.subheader("🏟 Live Courts")

# 🔁 Auto refresh every 1 second for live timer
st_autorefresh(interval=1000, key="live_timer")

# Custom CSS for font sizes
st.markdown("""
<style>
.court-card {
   padding:10px;
   border-radius:10px;
   background:#f4f6fa;
   margin-bottom:10px;
}

.court-info {
   font-size:14px;  /* small font for names and teams */
}

.control-btn button, .control-btn input[type="number"] {
   font-size:14px !important;  /* smaller than before */
   padding:4px 8px !important;
   margin-top:2px;
   margin-bottom:2px;
   border-radius:6px !important;
}

.swap-section select, .swap-section button {
   font-size:14px !important;
   padding:4px 6px !important;
}

</style>
""", unsafe_allow_html=True)

cols = st.columns(2)

for i, cid in enumerate(st.session_state.courts):
with cols[i % 2]:
st.markdown('<div class="court-card">', unsafe_allow_html=True)
st.markdown(f'<div class="court-info"><b>Court {cid}</b></div>', unsafe_allow_html=True)

# ⏱ Live Timer
start_time = st.session_state.match_start_time.get(cid)
if start_time:
elapsed_seconds = int((datetime.now() - start_time).total_seconds())
minutes = elapsed_seconds // 60
seconds = elapsed_seconds % 60
st.markdown(f'<div class="court-info">⏱ {minutes:02d}:{seconds:02d}</div>', unsafe_allow_html=True)

teams = st.session_state.courts[cid]

# -------------------------
# EMPTY COURT
# -------------------------
if not teams:
st.info("Waiting for safe players...")
st.markdown('</div>', unsafe_allow_html=True)
continue

# -------------------------
# SHOW TEAMS
# -------------------------
st.markdown('<div class="court-info"><b>Team A</b><br>' + "<br>".join(fmt(p) for p in teams[0]) + '</div>', unsafe_allow_html=True)
st.markdown('<div class="court-info"><b>Team B</b><br>' + "<br>".join(fmt(p) for p in teams[1]) + '</div>', unsafe_allow_html=True)

# -------------------------
# COLLAPSIBLE CONTROLS: SCORE & BUTTONS
# -------------------------
with st.expander("🎯 Score & Controls", expanded=False):
st.markdown('<div class="control-btn">', unsafe_allow_html=True)
c1, c2 = st.columns(2)
if c1.button("🔀 Shuffle Teams", key=f"shuffle_{cid}"):
players = teams[0] + teams[1]
random.shuffle(players)
st.session_state.courts[cid] = [players[:2], players[2:]]
st.rerun()

if c2.button("🔁 Rematch", key=f"rematch_{cid}"):
st.session_state.scores[cid] = [0, 0]
st.rerun()

a = st.number_input("Score A", 0, key=f"A_{cid}")
b = st.number_input("Score B", 0, key=f"B_{cid}")

if st.button("✅ Submit Score", key=f"submit_{cid}"):
st.session_state.scores[cid] = [a, b]
finish_match(cid)
st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# COLLAPSIBLE SWAP PLAYER
# -------------------------
with st.expander("🔁 Swap Player", expanded=False):
flat_court = teams[0] + teams[1]
queue_list = list(st.session_state.queue)

if flat_court and queue_list:
swap_from_court = st.selectbox(
"Player OUT (from court)",
[p[0] for p in flat_court],
key=f"swap_out_{cid}"
)

swap_from_queue = st.selectbox(
"Player IN (from waiting)",
[p[0] for p in queue_list],
key=f"swap_in_{cid}"
)

if st.button("🔄 Swap Players", key=f"swap_btn_{cid}"):
court_index = next(i for i, p in enumerate(flat_court) if p[0] == swap_from_court)
queue_index = next(i for i, p in enumerate(queue_list) if p[0] == swap_from_queue)
flat_court[court_index], queue_list[queue_index] = queue_list[queue_index], flat_court[court_index]
st.session_state.courts[cid] = [flat_court[:2], flat_court[2:]]
st.session_state.queue = deque(queue_list)
st.rerun()

st.markdown('</div>', unsafe_allow_html=True)
