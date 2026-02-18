import streamlit as st
import random
from collections import deque
import pandas as pd
from itertools import combinations
import json
import os
from streamlit_autorefresh import st_autorefresh
from datetime import datetime


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
    
    st.session_state.match_start_time[cid] = datetime.now()



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

    # Clear start time
    st.session_state.match_start_time.pop(cid, None)

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

    st.session_state.queue = deque(data["queue"])
    st.session_state.courts = data["courts"]
    st.session_state.locked = data["locked"]
    st.session_state.scores = data["scores"]
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
            st.session_state.players.setdefault(name, {"dupr": dupr, "games":0, "wins":0, "losses":0})

    # Delete player
    if st.session_state.players:
        st.divider()
        remove = st.selectbox("❌ Remove Player", list(st.session_state.players.keys()))
        if st.button("Delete"):
            delete_player(remove)
            st.rerun()

    # Start / Reset
    col1, col2 = st.columns(2)
    if col1.button("🚀 Start Games"):
        st.session_state.started = True
        st.session_state.courts = {i:None for i in range(1, st.session_state.court_count+1)}
        st.session_state.locked = {i:False for i in st.session_state.courts}
        st.session_state.scores = {i:[0,0] for i in st.session_state.courts}
        st.rerun()
    if col2.button("🔄 Reset"):
        st.session_state.clear()
        st.rerun()

    st.divider()

    # Download CSV
    st.download_button("📥 Matches CSV", matches_csv(), "matches.csv")
    st.download_button("📥 Players CSV", players_csv(), "players.csv")

    st.divider()
    # Profile Save/Load/Delete
    st.header("💾 Profiles")
    profile_name = st.text_input("Profile Name")
    col1, col2 = st.columns(2)
    if col1.button("Save Profile") and profile_name:
        save_profile(profile_name)
    profiles = [f[:-5] for f in os.listdir(SAVE_DIR) if f.endswith(".json")]
    selected_profile = st.selectbox("Select Profile", [""] + profiles)
    if col2.button("Load Profile") and selected_profile:
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
# COURTS (LIVE)
# ======================================================
st.divider()
st.subheader("🏟 Live Courts")

# 🔁 Auto refresh every 1 second for live timer
st_autorefresh(interval=1000, key="live_timer")

# ================= UI STYLE =================
st.markdown("""
<style>
.court-card{
    padding:20px;
    border-radius:16px;
    background:#f8f9fc;
    margin-bottom:20px;
    box-shadow:0 6px 16px rgba(0,0,0,0.05);
}
.court-title{
    font-size:20px;
    font-weight:600;
    margin-bottom:6px;
}
.timer-text{
    font-size:15px;
    color:#444;
    margin-bottom:12px;
}
.team-title{
    font-size:14px;
    font-weight:600;
    margin-bottom:4px;
}
.team-text{
    font-size:14px;
    line-height:1.4;
}
.score-box{
    font-size:20px;
    font-weight:600;
    text-align:center;
    padding-top:20px;
}
</style>
""", unsafe_allow_html=True)

cols = st.columns(2)

for i, cid in enumerate(st.session_state.courts):

    with cols[i % 2]:

        st.markdown('<div class="court-card">', unsafe_allow_html=True)

        # -------------------------
        # TITLE
        # -------------------------
        st.markdown(f'<div class="court-title">Court {cid}</div>', unsafe_allow_html=True)

        teams = st.session_state.courts[cid]

        # -------------------------
        # TIMER
        # -------------------------
        start_time = st.session_state.match_start_time.get(cid)
        if start_time:
            elapsed = int((datetime.now() - start_time).total_seconds())
            minutes = elapsed // 60
            seconds = elapsed % 60
            st.markdown(
                f'<div class="timer-text">⏱ {minutes:02d}:{seconds:02d}</div>',
                unsafe_allow_html=True
            )

        # -------------------------
        # EMPTY COURT
        # -------------------------
        if not teams:
            st.info("Waiting for safe players...")
            st.markdown('</div>', unsafe_allow_html=True)
            continue

        # -------------------------
        # TEAMS + SCORE (SIDE BY SIDE)
        # -------------------------
        colA, colMid, colB = st.columns([3,1.5,3])

        with colA:
            st.markdown('<div class="team-title">Team A</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="team-text">{"<br>".join(fmt(p) for p in teams[0])}</div>',
                unsafe_allow_html=True
            )

        with colMid:
            scoreA = st.session_state.scores[cid][0]
            scoreB = st.session_state.scores[cid][1]
            st.markdown(
                f'<div class="score-box">{scoreA} - {scoreB}</div>',
                unsafe_allow_html=True
            )

        with colB:
            st.markdown('<div class="team-title">Team B</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="team-text">{"<br>".join(fmt(p) for p in teams[1])}</div>',
                unsafe_allow_html=True
            )

        st.divider()

        # -------------------------
        # SCORE INPUT + SUBMIT (COMPACT ROW)
        # -------------------------
        c1, c2, c3 = st.columns([2,2,3])

        with c1:
            a = st.number_input("A", 0, key=f"A_{cid}")

        with c2:
            b = st.number_input("B", 0, key=f"B_{cid}")

        with c3:
            if st.button("✅ Submit", key=f"submit_{cid}", use_container_width=True):
                st.session_state.scores[cid] = [a, b]
                finish_match(cid)
                st.rerun()

        # -------------------------
        # CONTROL BUTTONS
        # -------------------------
        c1, c2 = st.columns(2)

        if c1.button("🔀 Shuffle", key=f"shuffle_{cid}", use_container_width=True):
            players = teams[0] + teams[1]
            random.shuffle(players)
            st.session_state.courts[cid] = [players[:2], players[2:]]
            st.rerun()

        if c2.button("🔁 Rematch", key=f"rematch_{cid}", use_container_width=True):
            st.session_state.scores[cid] = [0, 0]
            st.rerun()

        # -------------------------
        # SWAP (COLLAPSIBLE TO SAVE SPACE)
        # -------------------------
        with st.expander("🔁 Swap Player"):

            flat_court = teams[0] + teams[1]
            queue_list = list(st.session_state.queue)

            if flat_court and queue_list:

                swap_from_court = st.selectbox(
                    "Player OUT",
                    [p[0] for p in flat_court],
                    key=f"swap_out_{cid}"
                )

                swap_from_queue = st.selectbox(
                    "Player IN",
                    [p[0] for p in queue_list],
                    key=f"swap_in_{cid}"
                )

                if st.button("🔄 Confirm Swap", key=f"swap_btn_{cid}", use_container_width=True):

                    court_index = next(i for i, p in enumerate(flat_court) if p[0] == swap_from_court)
                    queue_index = next(i for i, p in enumerate(queue_list) if p[0] == swap_from_queue)

                    flat_court[court_index], queue_list[queue_index] = \
                        queue_list[queue_index], flat_court[court_index]

                    st.session_state.courts[cid] = [flat_court[:2], flat_court[2:]]
                    st.session_state.queue = deque(queue_list)

                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
