import streamlit as st
import random
from collections import deque
from itertools import combinations
import pandas as pd
import json
import os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from supabase_client import get_supabase

# ==========================
# SUPABASE CLIENT
# ==========================
supabase = get_supabase()

# ==========================
# PAGE CONFIG
# ==========================
st.set_page_config(
    page_title="🎾 Pickleball Auto Stack TiraDinks Official",
    page_icon="🎾",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
footer {visibility:hidden;}
a[href*="github.com/streamlit"]{display:none!important;}
.court-card{padding:14px;border-radius:12px;background:#f4f6fa;margin-bottom:12px;}
.waiting-box{background:#fff3cd;padding:10px;border-radius:10px;}
.court-info{font-size:14px;}
.control-btn button, .control-btn input[type="number"]{font-size:14px !important;padding:4px 8px !important;margin:2px;border-radius:6px !important;}
.swap-section select, .swap-section button{font-size:14px !important;padding:4px 6px !important;}
</style>
""", unsafe_allow_html=True)

# HEADER PHOTO
col1, col2, col3 = st.columns([1,2,1])
with col2:
    st.image("TDphoto.jpg", width=300)

st.title("🎾 Pickleball Auto Stack TiraDinks Official")
st.caption("WE CAMED WE DINKED!")

# ==========================
# HELPERS
# ==========================
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

def take_four_safe():
    q = list(st.session_state.queue)
    if len(q) < 4:
        return None
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
    return [players[:2], players[2:]]

# ==========================
# SESSION INIT
# ==========================
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

# ==========================
# PLAYER MANAGEMENT
# ==========================
def delete_player(name):
    # Remove from queue
    st.session_state.queue = deque([p for p in st.session_state.queue if p[0] != name])
    # Remove from courts
    for cid, teams in st.session_state.courts.items():
        if not teams: continue
        new_teams = []
        for team in teams:
            new_teams.append([p for p in team if p[0] != name])
        # If team less than 2, clear court
        if len(new_teams[0]) < 2 or len(new_teams[1]) < 2:
            st.session_state.courts[cid] = None
            st.session_state.locked[cid] = False
        else:
            st.session_state.courts[cid] = new_teams
    st.session_state.players.pop(name, None)

# ==========================
# MATCH ENGINE
# ==========================
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
    if not teams: return
    scoreA, scoreB = st.session_state.scores.get(cid, [0,0])
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

    # Update stats in session
    for p in teamA + teamB:
        st.session_state.players[p[0]]["games"] += 1
    for p in winners:
        st.session_state.players[p[0]]["wins"] += 1
    for p in losers:
        st.session_state.players[p[0]]["losses"] += 1

    # Update Supabase (only games & wins)
    try:
        for p in teamA + teamB:
            name = p[0]
            stats = st.session_state.players[name]
            supabase.table("players").update({
                "games": stats["games"],
                "wins": stats["wins"]
            }).eq("name", name).execute()
    except Exception as e:
        st.error(f"Supabase update failed: {e}")

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

    # Reset court
    st.session_state.match_start_time.pop(cid, None)
    st.session_state.courts[cid] = None
    st.session_state.locked[cid] = False
    st.session_state.scores[cid] = [0, 0]

    # Return players to queue (FCFS)
    st.session_state.queue.extend(teamA + teamB)

def auto_fill():
    if not st.session_state.started: return
    for cid in range(1, st.session_state.court_count+1):
        if st.session_state.courts.get(cid) is None:
            start_match(cid)

def winner_winner(cid):
    """Keep winners on court, rotate losers to queue, and update Supabase stats."""
    teams = st.session_state.courts.get(cid)
    if not teams:
        st.warning("No players on court")
        return

    scoreA, scoreB = st.session_state.scores.get(cid, [0, 0])
    teamA, teamB = teams

    if scoreA > scoreB:
        winners, losers = teamA, teamB
    elif scoreB > scoreA:
        winners, losers = teamB, teamA
    else:
        st.warning("Draw, cannot use Winner Winner")
        return

    # Update local session stats
    for p in teamA + teamB:
        st.session_state.players[p[0]]["games"] += 1
    for p in winners:
        st.session_state.players[p[0]]["wins"] += 1
    for p in losers:
        st.session_state.players[p[0]]["losses"] += 1

    # Update Supabase
    try:
        for p in teamA + teamB:
            name = p[0]
            stats = st.session_state.players[name]
            supabase.table("players").update({
                "games": stats["games"],
                "wins": stats["wins"]
            }).eq("name", name).execute()
    except Exception as e:
        st.error(f"Supabase update failed: {e}")

    # Rotate losers back to queue
    st.session_state.queue.extend(losers)

    # Keep winners on court
    st.session_state.courts[cid] = [winners[:2], winners[2:]] if len(winners) > 2 else [winners, []]
    st.session_state.scores[cid] = [0, 0]

    st.success(f"Winners stayed on court: {', '.join(p[0] for p in winners)}")

# ==========================
# CSV EXPORT
# ==========================
def matches_csv():
    if not st.session_state.history: return b""
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

# ==========================
# SIDEBAR: Players, Courts, Profiles
# ==========================
with st.sidebar:
    st.markdown('<h4>⚙ Setup</h4>', unsafe_allow_html=True)

    with st.expander("🏟 Courts", expanded=True):
        st.session_state.court_count = st.selectbox("Number of Courts", [2,3,4,5,6], index=st.session_state.court_count-2)

    with st.expander("➕ Add Player", expanded=False):
        with st.form("add", clear_on_submit=True):
            name = st.text_input("Name")
            dupr = st.text_input("DUPR ID")
            skill = st.radio("Skill", ["Beginner","Novice","Intermediate"], horizontal=True)
            if st.form_submit_button("Add Player") and name:
                st.session_state.queue.append((name, skill.upper(), dupr))
                st.session_state.players.setdefault(name, {"dupr": dupr,"games":0,"wins":0,"losses":0})

    if st.session_state.players:
        with st.expander("❌ Delete Player", expanded=False):
            remove = st.selectbox("Select Player to Remove", list(st.session_state.players.keys()))
            if st.button("Delete Player"):
                delete_player(remove)
                st.rerun()

    with st.expander("🚀 Start / Reset", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start Games"):
                st.session_state.started = True
                st.session_state.courts = {i:None for i in range(1, st.session_state.court_count+1)}
                st.session_state.locked = {i:False for i in st.session_state.courts}
                st.session_state.scores = {i:[0,0] for i in st.session_state.courts}
                st.rerun()
        with col2:
            if st.button("Reset"):
                st.session_state.clear()
                st.rerun()

    with st.expander("📥 Export CSV", expanded=False):
        st.download_button("Matches CSV", matches_csv(), "matches.csv")
        st.download_button("Players CSV", players_csv(), "players.csv")

# ==========================
# MAIN UI
# ==========================
auto_fill()

st.subheader("⏳ Waiting Queue")
if st.session_state.queue:
    st.markdown(f'<div class="waiting-box">{", ".join(fmt(p) for p in st.session_state.queue)}</div>', unsafe_allow_html=True)
else:
    st.success("No players waiting 🎉")

if not st.session_state.started:
    st.stop()
    st_autorefresh(interval=1000, key="live_timer")

# Live courts
st.divider()
st.subheader("🏟 Live Courts")
st_autorefresh(interval=1000, key="live_timer")

cols = st.columns(2)
for i, cid in enumerate(st.session_state.courts):
    with cols[i % 2]:
        st.markdown('<div class="court-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="court-info"><b>Court {cid}</b></div>', unsafe_allow_html=True)

        start_time = st.session_state.match_start_time.get(cid)
        if start_time:
            elapsed = int((datetime.now() - start_time).total_seconds())
            minutes, seconds = divmod(elapsed, 60)
            st.markdown(f'<div class="court-info">⏱ {minutes:02d}:{seconds:02d}</div>', unsafe_allow_html=True)

        teams = st.session_state.courts[cid]
        if not teams:
            st.info("Waiting for safe players...")
            st.markdown('</div>', unsafe_allow_html=True)
            continue

        st.markdown('<div class="court-info"><b>Team A</b><br>' + "<br>".join(fmt(p) for p in teams[0]) + '</div>', unsafe_allow_html=True)
        st.markdown('<div class="court-info"><b>Team B</b><br>' + "<br>".join(fmt(p) for p in teams[1]) + '</div>', unsafe_allow_html=True)

        # Controls
        with st.expander("🎯 Score & Controls", expanded=False):
            st.markdown('<div class="control-btn">', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            if c1.button("🔀 Shuffle Teams", key=f"shuffle_{cid}"):
                players = teams[0] + teams[1]
                random.shuffle(players)
                st.session_state.courts[cid] = [players[:2], players[2:]]
                st.rerun()
            if c2.button("🔁 Rematch", key=f"rematch_{cid}"):
                st.session_state.scores[cid] = [0,0]
                st.rerun()

            a = st.number_input("Score A", 0, key=f"A_{cid}")
            b = st.number_input("Score B", 0, key=f"B_{cid}")
            if st.button("✅ Submit Score", key=f"submit_{cid}"):
                st.session_state.scores[cid] = [a,b]
                finish_match(cid)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # Swap players
        with st.expander("🔁 Swap Player", expanded=False):
            flat_court = teams[0] + teams[1]
            queue_list = list(st.session_state.queue)
            if flat_court and queue_list:
                swap_out = st.selectbox("Player OUT", [p[0] for p in flat_court], key=f"swap_out_{cid}")
                swap_in = st.selectbox("Player IN", [p[0] for p in queue_list], key=f"swap_in_{cid}")
                if st.button("🔄 Swap Players", key=f"swap_btn_{cid}"):
                    court_index = next(i for i, p in enumerate(flat_court) if p[0]==swap_out)
                    queue_index = next(i for i, p in enumerate(queue_list) if p[0]==swap_in)
                    flat_court[court_index], queue_list[queue_index] = queue_list[queue_index], flat_court[court_index]
                    st.session_state.courts[cid] = [flat_court[:2], flat_court[2:]]
                    st.session_state.queue = deque(queue_list)
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
