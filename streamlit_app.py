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

def fmt(p):
    return f"{icon(p[1])} {p[0]}"

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

init()

# ======================================================
# PLAYER DELETE
# ======================================================
def delete_player(name):
    st.session_state.queue = deque([p for p in st.session_state.queue if p[0] != name])

    for cid, teams in st.session_state.courts.items():
        if not teams:
            continue
        new = [[p for p in t if p[0] != name] for t in teams]

        if len(new[0]) < 2 or len(new[1]) < 2:
            st.session_state.courts[cid] = None
            st.session_state.locked[cid] = False
        else:
            st.session_state.courts[cid] = new

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
        winners, losers = teamA, teamB
        winner = "Team A"
    elif scoreB > scoreA:
        winners, losers = teamB, teamA
        winner = "Team B"
    else:
        winners = losers = []
        winner = "DRAW"

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
    return pd.DataFrame(st.session_state.history).to_csv(index=False).encode()

def players_csv():
    rows = []
    for name, d in st.session_state.players.items():
        rows.append({
            "Player": name,
            "DUPR": d["dupr"],
            "Games": d["games"],
            "Wins": d["wins"],
            "Losses": d["losses"]
        })
    return pd.DataFrame(rows).to_csv(index=False).encode()

# ======================================================
# PROFILES
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
    with open(f"{SAVE_DIR}/{name}.json", "w") as f:
        json.dump(data, f)

def load_profile(name):
    with open(f"{SAVE_DIR}/{name}.json") as f:
        d = json.load(f)

    st.session_state.queue = deque(d["queue"])
    st.session_state.courts = d["courts"]
    st.session_state.locked = d["locked"]
    st.session_state.scores = d["scores"]
    st.session_state.history = d["history"]
    st.session_state.started = d["started"]
    st.session_state.court_count = d["court_count"]
    st.session_state.players = d["players"]

def delete_profile(name):
    os.remove(f"{SAVE_DIR}/{name}.json")

# ======================================================
# SIDEBAR
# ======================================================
with st.sidebar:
    st.header("⚙ Setup")

    st.session_state.court_count = st.selectbox("Courts", [2,3,4,5,6])

    with st.form("add", clear_on_submit=True):
        name = st.text_input("Name")
        dupr = st.text_input("DUPR ID")
        skill = st.radio("Skill", ["Beginner","Novice","Intermediate"])

        if st.form_submit_button("Add Player") and name:
            st.session_state.queue.appendleft((name, skill.upper(), dupr))
            st.session_state.players.setdefault(name, {"dupr":dupr,"games":0,"wins":0,"losses":0})

    if st.button("🚀 Start Games"):
        st.session_state.started = True
        st.session_state.courts = {i:None for i in range(1, st.session_state.court_count+1)}
        st.session_state.locked = {i:False for i in st.session_state.courts}

    st.download_button("📥 Matches CSV", matches_csv(), "matches.csv")
    st.download_button("📥 Players CSV", players_csv(), "players.csv")

# ======================================================
# MAIN
# ======================================================
auto_fill()

st.subheader("⏳ Waiting Queue")

if st.session_state.queue:
    st.write(", ".join(fmt(p) for p in st.session_state.queue))

if not st.session_state.started:
    st.stop()

# ======================================================
# COURTS (FULL REWRITE)
# ======================================================
st.divider()
st.subheader("🏟 Live Courts")

cols = st.columns(2)

for i, cid in enumerate(st.session_state.courts):

    with cols[i % 2]:

        st.markdown('<div class="court-card">', unsafe_allow_html=True)
        st.markdown(f"### Court {cid}")

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
        st.write("**Team A**  \n" + " & ".join(fmt(p) for p in teams[0]))
        st.write("**Team B**  \n" + " & ".join(fmt(p) for p in teams[1]))

        # -------------------------
        # CONTROL BUTTONS
        # -------------------------
        c1, c2 = st.columns(2)

        # 🔀 Shuffle all 4 players (BEST OPTION)
        if c1.button("🔀 Shuffle Teams", key=f"shuffle_{cid}"):
            players = teams[0] + teams[1]
            random.shuffle(players)
            st.session_state.courts[cid] = [players[:2], players[2:]]
            st.rerun()

        # 🔁 Rematch same teams (reset scores only)
        if c2.button("🔁 Rematch", key=f"rematch_{cid}"):
            st.session_state.scores[cid] = [0, 0]
            st.rerun()

        st.divider()

        # -------------------------
        # SCORES
        # -------------------------
        a = st.number_input("Score A", 0, key=f"A_{cid}")
        b = st.number_input("Score B", 0, key=f"B_{cid}")

        if st.button("✅ Submit Score", key=f"submit_{cid}"):
            st.session_state.scores[cid] = [a, b]
            finish_match(cid)
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
