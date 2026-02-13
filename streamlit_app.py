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
# HELPERS
# ======================================================
def icon(skill):
    return {"BEGINNER":"🟢","NOVICE":"🟡","INTERMEDIATE":"🔴"}[skill]

def superscript_number(n):
    return str(n).translate(str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹"))

# UPDATED → supports preferred court
def fmt(p):
    name, skill, dupr, pref = p
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

init()

# ======================================================
# DELETE PLAYER
# ======================================================
def delete_player(name):
    st.session_state.queue = deque([p for p in st.session_state.queue if p[0] != name])
    st.session_state.players.pop(name, None)

# ======================================================
# NEW — PRIORITY MATCH ENGINE
# ======================================================
def take_four_for_court(cid):

    q = list(st.session_state.queue)

    # players who prefer this court OR any
    preferred = [p for p in q if p[3] in (None, cid)]

    if len(preferred) < 4:
        return None

    for combo in combinations(range(len(preferred)), 4):
        group = [preferred[i] for i in combo]
        if safe_group(group):
            for g in group:
                q.remove(g)
            st.session_state.queue = deque(q)
            return group

    return None


def start_match(cid):
    if st.session_state.locked[cid]:
        return

    players = take_four_for_court(cid)
    if not players:
        return

    st.session_state.courts[cid] = make_teams(players)
    st.session_state.locked[cid] = True
    st.session_state.scores[cid] = [0, 0]


# ======================================================
# FINISH MATCH
# ======================================================
def finish_match(cid):
    teams = st.session_state.courts[cid]
    if not teams:
        return

    scoreA, scoreB = st.session_state.scores[cid]
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
# SIDEBAR
# ======================================================
with st.sidebar:

    st.header("⚙ Setup")

    st.session_state.court_count = st.selectbox(
        "Courts",
        [2,3,4,5,6],
        index=st.session_state.court_count-2
    )

    # ==================================================
    # ⭐ UPDATED ADD PLAYER FORM
    # ==================================================
    with st.form("add", clear_on_submit=True):

        name = st.text_input("Name")
        dupr = st.text_input("DUPR ID")
        skill = st.radio("Skill", ["Beginner","Novice","Intermediate"])

        pref = st.selectbox(
            "Preferred Court",
            ["Any"] + list(range(1, st.session_state.court_count+1))
        )

        if st.form_submit_button("Add Player") and name:

            pref_val = None if pref == "Any" else int(pref)

            st.session_state.queue.appendleft(
                (name, skill.upper(), dupr, pref_val)
            )

            st.session_state.players.setdefault(
                name,
                {"dupr": dupr, "games":0}
            )

    if st.button("🚀 Start Games"):
        st.session_state.started = True
        st.session_state.courts = {i:None for i in range(1, st.session_state.court_count+1)}
        st.session_state.locked = {i:False for i in st.session_state.courts}
        st.session_state.scores = {i:[0,0] for i in st.session_state.courts}
        st.rerun()

# ======================================================
# MAIN
# ======================================================
auto_fill()

st.subheader("⏳ Waiting Queue")

if st.session_state.queue:
    st.write(", ".join(fmt(p) for p in st.session_state.queue))
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

        st.markdown(f"### Court {cid}")

        teams = st.session_state.courts[cid]

        if not teams:
            st.info("Waiting for players...")
            continue

        st.write("**Team A**  " + " & ".join(fmt(p) for p in teams[0]))
        st.write("**Team B**  " + " & ".join(fmt(p) for p in teams[1]))

        a = st.number_input("Score A", 0, key=f"A_{cid}")
        b = st.number_input("Score B", 0, key=f"B_{cid}")

        if st.button("✅ Submit Score", key=f"submit_{cid}"):
            st.session_state.scores[cid] = [a, b]
            finish_match(cid)
            st.rerun()
