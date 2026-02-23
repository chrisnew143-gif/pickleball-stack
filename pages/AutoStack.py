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

# -------------------------
# Supabase client
# -------------------------
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

    # Also delete from Supabase
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

    # Update player stats
    for p in teamA + teamB:
        st.session_state.players[p[0]]["games"] += 1
    for p in winners:
        st.session_state.players[p[0]]["wins"] += 1
    for p in losers:
        st.session_state.players[p[0]]["losses"] += 1

    # Sync updated stats to Supabase
    for p_name, data in st.session_state.players.items():
        supabase.table("players").update({
            "games": data["games"],
            "wins": data["wins"],
            "losses": data["losses"]
        }).eq("name", p_name).execute()

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

# ======================================================
# SIDEBAR - ADD PLAYER
# ======================================================
with st.sidebar:
    with st.expander("➕ Add Player", expanded=False):
        with st.form("add", clear_on_submit=True):
            name = st.text_input("Name")
            dupr = st.text_input("DUPR ID")
            skill = st.radio("Skill", ["Beginner","Novice","Intermediate"], horizontal=True)
            submitted = st.form_submit_button("Add Player")
            if submitted and name:
                st.session_state.queue.append((name, skill.upper(), dupr))
                st.session_state.players.setdefault(
                    name,
                    {"dupr": dupr, "games":0, "wins":0, "losses":0}
                )
                # ------------------------
                # SAVE TO SUPABASE
                # ------------------------
                supabase.table("players").insert({
                    "name": name,
                    "dupr": dupr,
                    "games": 0,
                    "wins": 0,
                    "losses": 0
                }).execute()

# ======================================================
# (rest of your script remains EXACTLY the same)
# ======================================================
