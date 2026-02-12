import streamlit as st
import random
from collections import deque
import pandas as pd
from itertools import combinations
import json
import os
import time

# ======================================================
# CONFIG & FILE PATHS
# ======================================================
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
QUEUE_FILE = os.path.join(DATA_DIR, "queue.json")
PLAYERS_FILE = os.path.join(DATA_DIR, "players.json")
COURTS_FILE = os.path.join(DATA_DIR, "courts.json")
SCORES_FILE = os.path.join(DATA_DIR, "scores.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")

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

def fmt(p):
    return f"{icon(p[1])} {p[0]}"

def safe_group(players):
    skills = {p[1] for p in players}
    return not ("BEGINNER" in skills and "INTERMEDIATE" in skills)

def make_teams(players):
    random.shuffle(players)
    return [players[:2], players[2:]]

# ======================================================
# PERSISTENCE FUNCTIONS
# ======================================================
def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return default

def persist_state():
    ss = st.session_state
    save_json(QUEUE_FILE, list(ss.queue))
    save_json(PLAYERS_FILE, ss.players)
    save_json(COURTS_FILE, {k: v for k,v in ss.courts.items()})
    save_json(SCORES_FILE, ss.scores)
    save_json(HISTORY_FILE, ss.history)

def load_saved_state():
    ss = st.session_state
    ss.queue = deque(load_json(QUEUE_FILE, []))
    ss.players = load_json(PLAYERS_FILE, {})
    ss.courts = load_json(COURTS_FILE, {})
    ss.scores = load_json(SCORES_FILE, {})
    ss.history = load_json(HISTORY_FILE, [])
    ss.started = bool(ss.courts)
    ss.locked = {int(k):True for k,v in ss.courts.items() if v}

# ======================================================
# SESSION INIT
# ======================================================
def init():
    ss = st.session_state
    ss.setdefault("queue", deque())
    ss.setdefault("players", {})
    ss.setdefault("courts", {})
    ss.setdefault("scores", {})
    ss.setdefault("history", [])
    ss.setdefault("started", False)
    ss.setdefault("court_count", 2)
    ss.setdefault("locked", {})
    ss.setdefault("last_save_time", time.time())
    
    # Load previous state if exists
    load_saved_state()
    
init()

# ======================================================
# PLAYER MANAGEMENT
# ======================================================
def delete_player(name):
    ss = st.session_state

    # remove from queue
    ss.queue = deque([p for p in ss.queue if p[0] != name])

    # remove from courts
    for cid, teams in ss.courts.items():
        if not teams:
            continue
        new_teams = []
        for team in teams:
            new_teams.append([p for p in team if p[0] != name])
        if len(new_teams[0]) < 2 or len(new_teams[1]) < 2:
            ss.courts[cid] = None
            ss.locked[cid] = False
        else:
            ss.courts[cid] = new_teams

    # remove stats
    ss.players.pop(name, None)
    persist_state()

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
            persist_state()
            return group
    return None

def start_match(cid):
    ss = st.session_state
    if ss.locked.get(cid):
        return
    players = take_four_safe()
    if not players:
        return
    ss.courts[cid] = make_teams(players)
    ss.locked[cid] = True
    ss.scores[cid] = [0, 0]
    persist_state()

def finish_match(cid):
    ss = st.session_state
    teams = ss.courts[cid]
    if not teams:
        return
    scoreA, scoreB = ss.scores[cid]
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

    # update stats
    for p in teamA + teamB:
        ss.players[p[0]]["games"] += 1
    for p in winners:
        ss.players[p[0]]["wins"] += 1
    for p in losers:
        ss.players[p[0]]["losses"] += 1

    # save history
    ss.history.append({
        "Court": cid,
        "Team A": " & ".join(p[0] for p in teamA),
        "Team B": " & ".join(p[0] for p in teamB),
        "Score A": scoreA,
        "Score B": scoreB,
        "Winner": winner
    })

    # rotate back to queue
    players = teamA + teamB
    random.shuffle(players)
    ss.queue.extend(players)

    ss.courts[cid] = None
    ss.locked[cid] = False
    ss.scores[cid] = [0,0]
    persist_state()

def auto_fill():
    if not st.session_state.started:
        return
    for cid in st.session_state.courts:
        if st.session_state.courts[cid] is None:
            start_match(cid)

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
# SIDEBAR
# ======================================================
with st.sidebar:
    st.header("⚙ Setup")

    st.session_state.court_count = st.selectbox("Courts", [2,3,4,5,6], index=st.session_state.court_count-2)

    # Add player
    with st.form("add", clear_on_submit=True):
        name = st.text_input("Name")
        dupr = st.text_input("DUPR ID")
        skill = st.radio("Skill", ["Beginner","Novice","Intermediate"])

        if st.form_submit_button("Add Player") and name:
            st.session_state.queue.appendleft((name, skill.upper(), dupr))
            st.session_state.players.setdefault(
                name, {"dupr": dupr, "games":0, "wins":0, "losses":0}
            )
            persist_state()

    # Delete player
    if st.session_state.players:
        st.divider()
        remove = st.selectbox("❌ Remove Player", list(st.session_state.players.keys()))
        if st.button("Delete"):
            delete_player(remove)
            st.rerun()

    # Start games
    if st.button("🚀 Start Games"):
        st.session_state.started = True
        st.session_state.courts = {i:None for i in range(1, st.session_state.court_count+1)}
        st.session_state.locked = {i:False for i in st.session_state.courts}
        st.session_state.scores = {i:[0,0] for i in st.session_state.courts}
        persist_state()
        st.rerun()

    # Reset
    if st.button("🔄 Reset"):
        st.session_state.clear()
        for f in [QUEUE_FILE, PLAYERS_FILE, COURTS_FILE, SCORES_FILE, HISTORY_FILE]:
            if os.path.exists(f):
                os.remove(f)
        st.rerun()

    st.divider()

    # Manual save
    if st.button("💾 Save Now"):
        persist_state()
        st.success("Data saved!")

    # Load saved data
    if st.button("📂 Load Saved Data"):
        load_saved_state()
        st.success("Saved data loaded!")
        st.experimental_rerun()

    st.divider()
    st.download_button("📥 Matches CSV", matches_csv(), "matches.csv")
    st.download_button("📥 Players CSV", players_csv(), "players.csv")

# ======================================================
# AUTO SAVE EVERY 10 SECONDS
# ======================================================
if time.time() - st.session_state.last_save_time > 10:
    persist_state()
    st.session_state.last_save_time = time.time()

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

# ======================================================
# COURTS
# ======================================================
st.divider()
st.subheader("🏟 Live Courts")
cols = st.columns(2)

for i, cid in enumerate(st.session_state.courts):
    with cols[i % 2]:
        st.markdown('<div class="court-card">', unsafe_allow_html=True)
        st.markdown(f"### Court {cid}")

        teams = st.session_state.courts[cid]

        if not teams:
            st.info("Waiting for safe players...")
            st.markdown('</div>', unsafe_allow_html=True)
            continue

        st.write("**Team A**  \n" + " & ".join(fmt(p) for p in teams[0]))
        st.write("**Team B**  \n" + " & ".join(fmt(p) for p in teams[1]))

        a = st.number_input("Score A", 0, key=f"A{cid}")
        b = st.number_input("Score B", 0, key=f"B{cid}")

        if st.button("Submit Score", key=f"S{cid}"):
            st.session_state.scores[cid] = [a, b]
            finish_match(cid)
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
