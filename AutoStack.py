import streamlit as st
import random
from collections import deque
import pandas as pd
from itertools import combinations
import json
import os

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(page_title="Pickleball Auto Stack", page_icon="🎾", layout="wide")

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
    ss.setdefault("active_profile", None)  # ✅ ADDED

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
# MATCH ENGINE
# ======================================================
def take_four_safe():
    q = list(st.session_state.queue)
    if len(q) < 4:
        return None
    for combo in combinations(range(len(q)), 4):
        group = [q[i] for i in combo]
        if safe_group(group):
            for i in sorted(combo, reverse=True):
                del q[i]
            st.session_state.queue = deque(q)
            return group
    return None

def start_match(cid):
    if st.session_state.locked[cid]:
        return
    players = take_four_safe()
    if not players:
        return
    st.session_state.courts[cid] = make_teams(players)
    st.session_state.locked[cid] = True
    st.session_state.scores[cid] = [0, 0]

def finish_match(cid):
    teams = st.session_state.courts[cid]
    scoreA, scoreB = st.session_state.scores[cid]
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

    st.session_state.history.append({
        "Court": cid,
        "Team A": " & ".join(p[0] for p in teamA),
        "Team B": " & ".join(p[0] for p in teamB),
        "Score A": scoreA,
        "Score B": scoreB,
        "Winner": winner
    })

    players = teamA + teamB
    random.shuffle(players)
    st.session_state.queue.extend(players)

    st.session_state.courts[cid] = None
    st.session_state.locked[cid] = False
    st.session_state.scores[cid] = [0, 0]

def auto_fill():
    if not st.session_state.started:
        return
    for cid in st.session_state.courts:
        if st.session_state.courts[cid] is None:
            start_match(cid)

# ======================================================
# PROFILE SAVE / LOAD / DELETE
# ======================================================
SAVE_DIR = "profiles"
os.makedirs(SAVE_DIR, exist_ok=True)

def save_profile(name):
    data = {
        "queue": list(st.session_state.queue),
        "courts": st.session_state.courts,
        "locked": st.session_state.locked,
        "scores": st.session_state.scores,
        "history": st.session_state.history,
        "started": st.session_state.started,
        "court_count": st.session_state.court_count,
        "players": st.session_state.players
    }
    with open(os.path.join(SAVE_DIR, f"{name}.json"), "w") as f:
        json.dump(data, f)
    st.session_state.active_profile = name  # ✅ ADDED
    st.success(f"Profile '{name}' saved!")

def load_profile(name):
    path = os.path.join(SAVE_DIR, f"{name}.json")
    if not os.path.exists(path):
        st.error("Profile not found!")
        return
    with open(path, "r") as f:
        data = json.load(f)
    st.session_state.queue = deque(data["queue"])
    st.session_state.courts = data["courts"]
    st.session_state.locked = data["locked"]
    st.session_state.scores = data["scores"]
    st.session_state.history = data["history"]
    st.session_state.started = data["started"]
    st.session_state.court_count = data["court_count"]
    st.session_state.players = data["players"]
    st.session_state.active_profile = name  # ✅ ADDED
    st.success(f"Profile '{name}' loaded!")

def delete_profile(name):
    path = os.path.join(SAVE_DIR, f"{name}.json")
    if os.path.exists(path):
        os.remove(path)
        st.success(f"Profile '{name}' deleted!")
        st.rerun()
    else:
        st.error("Profile not found!")

# ======================================================
# AUTO SAVE FUNCTION (NEW)
# ======================================================
def auto_save():
    profile = st.session_state.get("active_profile")
    if not profile:
        return
    data = {
        "queue": list(st.session_state.queue),
        "courts": st.session_state.courts,
        "locked": st.session_state.locked,
        "scores": st.session_state.scores,
        "history": st.session_state.history,
        "started": st.session_state.started,
        "court_count": st.session_state.court_count,
        "players": st.session_state.players
    }
    with open(os.path.join(SAVE_DIR, f"{profile}.json"), "w") as f:
        json.dump(data, f)

# ======================================================
# AUTO SAVE TRIGGER (NEW)
# ======================================================
if st.session_state.get("active_profile"):
    auto_save()
