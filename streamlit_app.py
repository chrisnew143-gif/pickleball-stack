import streamlit as st
import random
from collections import deque
from itertools import combinations
import pandas as pd
from pathlib import Path

# =========================================================
# CONFIG
# =========================================================
MAX_PER_COURT = 10   # ⭐ 10 players per court
RESULTS_FILE = Path("pickleball_results.xlsx")  # Excel file to store match results

# =========================================================
# PAGE SETUP
# =========================================================
st.set_page_config(page_title="Pickleball Auto Stack", page_icon="🎾", layout="wide")

st.markdown("""
<style>
.court-card {
    padding: 15px;
    border-radius: 15px;
    background-color: #f3f6fa;
    margin-bottom: 10px;
}
.waiting-box {
    background-color: #fff3cd;
    padding: 12px;
    border-radius: 10px;
    font-size: 18px;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# HELPERS
# =========================================================
def skill_icon(cat):
    return {"BEGINNER": "🟢","NOVICE": "🟡","INTERMEDIATE": "🔴"}[cat]

def format_player(p):
    return f"{skill_icon(p[1])} {p[0]}"

def make_teams(players):
    random.shuffle(players)
    return [players[:2], players[2:]]

def is_safe_combo(players):
    skills = {p[1] for p in players}
    return not ("BEGINNER" in skills and "INTERMEDIATE" in skills)

def pick_four_fifo_safe(queue):
    """Select first safe 4-player combo without removing from queue."""
    if len(queue) < 4:
        return None
    for combo in combinations(queue, 4):
        if is_safe_combo(combo):
            return list(combo)
    return None

# =========================================================
# COURT LOGIC
# =========================================================
def start_match(court_id):
    """Fill a court with 4 players from queue if safe."""
    four = pick_four_fifo_safe(st.session_state.queue)
    if four:
        for p in four:
            st.session_state.queue.remove(p)
        st.session_state.courts[court_id] = make_teams(four)
    else:
        st.session_state.courts[court_id] = None

def submit_score(court_id, scoreA, scoreB):
    """Decide winner based on scores and update queue and Excel log."""
    teams = st.session_state.courts[court_id]
    if not teams:
        return

    # Determine winner
    if scoreA > scoreB:
        winner_team = teams[0]
        loser_team = teams[1]
    else:
        winner_team = teams[1]
        loser_team = teams[0]

    # Losers go back to the queue
    st.session_state.queue.extend(loser_team)

    # Log the match
    match_result = {
        "Court": court_id,
        "Team A": " & ".join([p[0] for p in teams[0]]),
        "Team B": " & ".join([p[0] for p in teams[1]]),
        "Score A": scoreA,
        "Score B": scoreB,
        "Winner": "Team A" if scoreA > scoreB else "Team B"
    }

    # Save to Excel
    if RESULTS_FILE.exists():
        df = pd.read_excel(RESULTS_FILE)
        df = pd.concat([df, pd.DataFrame([match_result])], ignore_index=True)
    else:
        df = pd.DataFrame([match_result])
    df.to_excel(RESULTS_FILE, index=False)

    # Start next match automatically
    start_match(court_id)

def auto_fill_empty_courts():
    """Fill all empty courts automatically."""
    if not st.session_state.started:
        return
    for c in st.session_state.courts:
        if st.session_state.courts[c] is None:
            start_match(c)

# =========================================================
# SESSION STATE
# =========================================================
if "queue" not in st.session_state:
    st.session_state.queue = deque()
if "courts" not in st.session_state:
    st.session_state.courts = {}
if "started" not in st.session_state:
    st.session_state.started = False
if "court_count" not in st.session_state:
    st.session_state.court_count = 2

# =========================================================
# HEADER
# =========================================================
st.title("🎾 Pickleball Auto Stack")
st.caption("First come • first play • fair rotation")

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.header("⚙ Setup")
    st.session_state.court_count = st.selectbox("Number of courts", [2,3,4,5,6,7])
    max_players = st.session_state.court_count * MAX_PER_COURT
    st.write(f"Max players: **{max_players}**")
    st.divider()

    # Add player
    st.subheader("➕ Add Player")
    with st.form("add_player_form", clear_on_submit=True):
        name = st.text_input("Name")
        cat = st.radio("Skill", ["Beginner","Novice","Intermediate"])
        submitted = st.form_submit_button("Add to Queue")
        if submitted and name.strip():
            if len(st.session_state.queue) >= max_players:
                st.warning("⚠️ Queue is FULL for selected courts")
            else:
                st.session_state.queue.append((name.strip(), cat.upper()))

    st.divider()
    if st.button("🚀 Start Games", use_container_width=True):
        st.session_state.started = True
        st.session_state.courts = {i: None for i in range(1, st.session_state.court_count + 1)}
        auto_fill_empty_courts()
    if st.button("🔄 Reset All", use_container_width=True):
        st.session_state.queue = deque()
        st.session_state.courts = {}
        st.session_state.started = False

# =========================================================
# AUTO FILL
# =========================================================
auto_fill_empty_courts()

# =========================================================
# WAITING QUEUE
# =========================================================
st.subheader("⏳ Waiting Queue")
waiting = [format_player(p) for p in st.session_state.queue]
if waiting:
    st.markdown('<div class="waiting-box">' + ", ".join(waiting) + '</div>', unsafe_allow_html=True)
else:
    st.success("No players waiting 🎉")

# =========================================================
# STOP IF NOT STARTED
# =========================================================
if not st.session_state.started:
    st.info("Add players then press **Start Games**")
    st.stop()

# =========================================================
# COURTS DISPLAY
# =========================================================
st.divider()
st.subheader("🏟 Live Courts")
per_row = 3
court_ids = list(st.session_state.courts.keys())

for row in range(0, len(court_ids), per_row):
    cols = st.columns(per_row)
    for idx, court_id in enumerate(court_ids[row:row+per_row]):
        with cols[idx]:
            st.markdown('<div class="court-card">', unsafe_allow_html=True)
            st.markdown(f"### Court {court_id}")

            teams = st.session_state.courts[court_id]
            if teams:
                teamA = " & ".join(format_player(p) for p in teams[0])
                teamB = " & ".join(format_player(p) for p in teams[1])
                st.write(f"**Team A**  \n{teamA}")
                st.write(f"**Team B**  \n{teamB}")

                # Score input
                scoreA = st.number_input(f"Score Team A (Court {court_id})", min_value=0, key=f"scoreA_{court_id}")
                scoreB = st.number_input(f"Score Team B (Court {court_id})", min_value=0, key=f"scoreB_{court_id}")
                if st.button("Submit Score", key=f"submit_{court_id}"):
                    submit_score(court_id, scoreA, scoreB)

            else:
                st.info("Waiting for players...")
            st.markdown('</div>', unsafe_allow_html=True)
