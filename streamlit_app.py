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

st.title("🎾 Pickleball Auto Stack")
st.caption("First come • first play • fair rotation")

# ======================================================
# STYLE
# ======================================================
st.markdown("""
<style>
footer {visibility:hidden;}

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
.small{
    font-size:11px;
    opacity:0.7;
}
</style>
""", unsafe_allow_html=True)

# ======================================================
# HELPERS
# ======================================================
def icon(skill):
    return {"BEGINNER":"🟢","NOVICE":"🟡","INTERMEDIATE":"🔴"}[skill]


def fmt(p):
    name, skill, dupr = p
    games = st.session_state.players.get(name, {}).get("games", 0)
    return f"{icon(skill)} <span class='small'>{games}</span> {name}"


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
    ss.setdefault("players", {})
    ss.setdefault("started", False)
    ss.setdefault("court_count", 2)

init()

# ======================================================
# DELETE PLAYER
# ======================================================
def delete_player(name):

    # remove from queue
    st.session_state.queue = deque(
        [p for p in st.session_state.queue if p[0] != name]
    )

    # remove from courts
    for cid, teams in st.session_state.courts.items():
        if not teams:
            continue

        flat = teams[0] + teams[1]
        flat = [p for p in flat if p[0] != name]

        if len(flat) < 4:
            st.session_state.courts[cid] = None
            st.session_state.locked[cid] = False
        else:
            st.session_state.courts[cid] = [flat[:2], flat[2:]]

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
    if not teams:
        return

    a, b = st.session_state.scores[cid]
    teamA, teamB = teams

    for p in teamA + teamB:
        st.session_state.players[p[0]]["games"] += 1

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
# PROFILE SAVE/LOAD
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
        "players": st.session_state.players,
        "started": st.session_state.started,
        "court_count": st.session_state.court_count
    }

    with open(f"{SAVE_DIR}/{name}.json", "w") as f:
        json.dump(data, f)

    st.success("Saved!")


def load_profile(name):
    with open(f"{SAVE_DIR}/{name}.json") as f:
        data = json.load(f)

    for k, v in data.items():
        if k == "queue":
            st.session_state.queue = deque(v)
        else:
            st.session_state[k] = v

    st.success("Loaded!")
    st.rerun()


def delete_profile(name):
    os.remove(f"{SAVE_DIR}/{name}.json")
    st.success("Deleted!")
    st.rerun()


# ======================================================
# SIDEBAR
# ======================================================
with st.sidebar:

    st.header("⚙ Setup")

    st.session_state.court_count = st.selectbox(
        "Courts", [1,2,3,4,5,6], index=st.session_state.court_count-1
    )

    # Add Player
    with st.form("add", clear_on_submit=True):
        name = st.text_input("Name")
        dupr = st.text_input("DUPR")
        skill = st.radio("Skill", ["Beginner","Novice","Intermediate"])

        if st.form_submit_button("Add") and name:
            st.session_state.queue.appendleft((name, skill.upper(), dupr))
            st.session_state.players.setdefault(
                name, {"dupr":dupr, "games":0}
            )

    # Delete player
    if st.session_state.players:
        st.divider()
        rm = st.selectbox("Remove Player", list(st.session_state.players.keys()))
        if st.button("Delete Player"):
            delete_player(rm)
            st.rerun()

    # START + RESET (FIXED HERE 🔥)
    st.divider()

    col1, col2 = st.columns(2)

    if col1.button("🚀 Start"):
        st.session_state.started = True
        st.session_state.courts = {i:None for i in range(1, st.session_state.court_count+1)}
        st.session_state.locked = {i:False for i in st.session_state.courts}
        st.session_state.scores = {i:[0,0] for i in st.session_state.courts}
        st.rerun()

    if col2.button("🔄 Reset"):
        st.session_state.clear()
        st.rerun()

    # Profiles
    st.divider()
    st.header("💾 Profiles")

    pname = st.text_input("Profile Name")

    if st.button("Save Profile") and pname:
        save_profile(pname)

    profiles = [f[:-5] for f in os.listdir(SAVE_DIR)]

    sel = st.selectbox("Load/Delete", [""] + profiles)

    if st.button("Load Profile") and sel:
        load_profile(sel)

    if st.button("Delete Profile") and sel:
        delete_profile(sel)


# ======================================================
# MAIN
# ======================================================
auto_fill()

st.subheader("⏳ Waiting Queue")

if st.session_state.queue:
    st.markdown(
        f"<div class='waiting-box'>{', '.join(fmt(p) for p in st.session_state.queue)}</div>",
        unsafe_allow_html=True
    )

if not st.session_state.started:
    st.stop()


# ======================================================
# COURTS
# ======================================================
st.divider()
st.subheader("🏟 Courts")

for cid in st.session_state.courts:

    st.markdown('<div class="court-card">', unsafe_allow_html=True)
    st.markdown(f"### Court {cid}")

    teams = st.session_state.courts[cid]

    if not teams:
        st.info("Waiting players...")
        st.markdown('</div>', unsafe_allow_html=True)
        continue

    st.markdown("**Team A**  \n" + " & ".join(fmt(p) for p in teams[0]), unsafe_allow_html=True)
    st.markdown("**Team B**  \n" + " & ".join(fmt(p) for p in teams[1]), unsafe_allow_html=True)

    a = st.number_input("Score A", 0, key=f"a{cid}")
    b = st.number_input("Score B", 0, key=f"b{cid}")

    if st.button("Finish", key=f"f{cid}"):
        st.session_state.scores[cid] = [a, b]
        finish_match(cid)
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
