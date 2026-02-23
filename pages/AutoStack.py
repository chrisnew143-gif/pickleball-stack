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
# LOAD PLAYERS FROM SUPABASE
# ======================================================
def load_players_from_db():
    response = supabase.table("players").select("*").execute()
    if response.data:
        for p in response.data:
            name = p["name"]
            st.session_state.players.setdefault(
                name,
                {
                    "dupr": p.get("dupr", ""),
                    "games": p.get("games", 0),
                    "wins": p.get("wins", 0),
                    "losses": p.get("losses", 0)
                }
            )

if not st.session_state.players:
    load_players_from_db()

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
    
    # DELETE FROM SUPABASE
    supabase.table("players").delete().eq("name", name).execute()

# ======================================================
# MATCH ENGINE (FULL FIXED)
# ======================================================
def take_four_safe():
    q = list(st.session_state.queue)
    if len(q) < 4:
        return None
    for combo in combinations(q, 4):
        if safe_group(combo):
            new_queue = q.copy()
            for p in combo:
                new_queue.remove(p)
            st.session_state.queue = deque(new_queue)
            return list(combo)
    return None

def start_match(cid):
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
    teams = st.session_state.courts.get(cid)
    if not teams:
        return

    scoreA, scoreB = st.session_state.scores.get(cid, [0, 0])
    teamA, teamB = teams

    if scoreA > scoreB:
        winner = "Team A"
        winners, losers = teamA, teamB
    elif scoreB > scoreA:
        winner = "Team B"
        winners, losers = teamB, teamA
    else:
        winner = "DRAW"
        winners = losers = []

    for p in teamA + teamB:
        st.session_state.players[p[0]]["games"] += 1
    for p in winners:
        st.session_state.players[p[0]]["wins"] += 1
    for p in losers:
        st.session_state.players[p[0]]["losses"] += 1

    # UPDATE SUPABASE
    for p_name, data in st.session_state.players.items():
        supabase.table("players").update({
            "games": data["games"],
            "wins": data["wins"],
            "losses": data["losses"]
        }).eq("name", p_name).execute()

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

    st.session_state.match_start_time.pop(cid, None)
    st.session_state.courts[cid] = None
    st.session_state.locked[cid] = False
    st.session_state.scores[cid] = [0, 0]
    st.session_state.queue.extend(teamA + teamB)

def auto_fill():
    if not st.session_state.started:
        return
    for cid in range(1, st.session_state.court_count + 1):
        if st.session_state.courts.get(cid) is None:
            start_match(cid)

def winner_winner(cid):
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

    st.session_state.queue.extend(losers)
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

    st.session_state.courts = {int(k): v for k, v in data["courts"].items()}
    st.session_state.locked = {int(k): v for k, v in data["locked"].items()}
    st.session_state.scores = {int(k): v for k, v in data["scores"].items()}
    st.session_state.queue = deque(data["queue"])
    st.session_state.history = data["history"]
    st.session_state.started = data["started"]
    st.session_state.court_count = data["court_count"]
    st.session_state.players = data["players"]

    st.session_state.match_start_time = {}
    for k, v in data.get("match_start_time", {}).items():
        try:
            st.session_state.match_start_time[int(k)] = datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
        except Exception:
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
# SIDEBAR, MAIN UI, COURTS, SWAP etc...
# ======================================================
# ... rest of your UI remains unchanged ...
# Everything from here on is the same as your original script
