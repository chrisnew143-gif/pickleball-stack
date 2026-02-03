import streamlit as st
import random
from collections import deque

# =========================================================
# CONFIG
# =========================================================

COURT_LIMITS = {2: 16, 3: 26, 4: 36, 5: 46, 6: 56, 7: 66}
SKILLS = ["BEGINNER", "NOVICE", "INTERMEDIATE"]

# =========================================================
# PAGE SETUP
# =========================================================

st.set_page_config(
    page_title="TiraDinks Pickleball Auto Stack",
    page_icon="🎾",
    layout="wide"
)

st.markdown("""
<style>
.big-btn button {
    height: 60px;
    font-size: 18px;
}
.court-card {
    padding: 15px;
    border-radius: 15px;
    background-color: #f3f6fa;
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
    return {
        "BEGINNER": "🟢",
        "NOVICE": "🟡",
        "INTERMEDIATE": "🔴"
    }[cat]

def format_player(p):
    return f"{skill_icon(p[1])} {p[0]}"

def make_teams(players):
    random.shuffle(players)
    return [players[:2], players[2:]]

def is_safe_combo(players):
    skills = {p[1] for p in players}
    if "BEGINNER" in skills and "INTERMEDIATE" in skills:
        return False
    return True

def pick_four_fifo_safe(queue):
    if len(queue) < 4:
        return None
    temp = list(queue)
    for shift in range(len(temp) - 3):
        group = temp[shift:shift+4]
        if is_safe_combo(group):
            for p in group:
                queue.remove(p)
            return group
    return None

def start_match(court_id):
    four = pick_four_fifo_safe(st.session_state.queue)
    if four:
        st.session_state.courts[court_id] = make_teams(four)
        return True
    st.session_state.courts[court_id] = None
    return False

def finish_match(court_id, winner_idx):
    teams = st.session_state.courts[court_id]
    winners = teams[winner_idx]
    losers = teams[1 - winner_idx]
    st.session_state.queue.extend(winners + losers)
    start_match(court_id)
    st.experimental_rerun()  # 2-click approach is now safe

def auto_fill_empty_courts():
    if not st.session_state.started:
        return False
    changed = False
    for c in st.session_state.courts:
        if st.session_state.courts[c] is None:
            if start_match(c):
                changed = True
    return changed

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

if "page" not in st.session_state:
    st.session_state.page = "home"

# =========================================================
# HOMEPAGE
# =========================================================

if st.session_state.page == "home":
    st.title("🎾 TiraDinks Pickleball")
    st.subheader("Select mode")
    c1, c2 = st.columns(2)
    if c1.button("Organizer"):
        st.session_state.page = "organizer"
        st.experimental_rerun()
    if c2.button("Player"):
        st.session_state.page = "player"
        st.experimental_rerun()

# =========================================================
# PLAYER PAGE
# =========================================================

elif st.session_state.page == "player":
    st.title("🎾 Player Page")
    st.warning("UNDER CONSTRUCTION")
    if st.button("Back"):
        st.session_state.page = "home"
        st.experimental_rerun()

# =========================================================
# ORGANIZER PAGE
# =========================================================

elif st.session_state.page == "organizer":

    st.title("🎾 TiraDinks Pickleball Auto Stack")
    st.caption("First come first play • fair skill matching • tap winners to continue")

    # SIDEBAR
    with st.sidebar:

        st.header("⚙ Setup")
        st.session_state.court_count = st.selectbox(
            "Number of courts",
            [2, 3, 4],
            index=0
        )
        st.write(f"Max players: **{COURT_LIMITS[st.session_state.court_count]}**")
        st.divider()

        st.subheader("➕ Add Player")
        with st.form("add_player_form", clear_on_submit=True):
            name = st.text_input("Name")
            cat = st.radio("Skill", ["Beginner", "Novice", "Intermediate"])
            submitted = st.form_submit_button("Add to Queue")
            if submitted and name.strip():
                st.session_state.queue.append((name.strip(), cat.upper()))

        st.divider()
        if st.button("🚀 Start Games"):
            st.session_state.started = True
            st.session_state.courts = {i: None for i in range(1, st.session_state.court_count + 1)}
            st.experimental_rerun()

        if st.button("🔄 Reset All"):
            st.session_state.queue = deque()
            st.session_state.courts = {}
            st.session_state.started = False
            st.experimental_rerun()

    # AUTO FILL COURTS
    auto_fill_empty_courts()

    # WAITING QUEUE
    st.subheader("⏳ Waiting Queue")
    waiting = [format_player(p) for p in st.session_state.queue]
    if waiting:
        st.markdown('<div class="waiting-box">' + ", ".join(waiting) + '</div>', unsafe_allow_html=True)
    else:
        st.success("No players waiting 🎉")

    # STOP IF NOT STARTED
    if not st.session_state.started:
        st.info("Add players then press **Start Games**")
        st.stop()

    # COURTS DISPLAY
    st.divider()
    st.subheader("🏟 Live Courts")
    cols = st.columns(len(st.session_state.courts))

    for idx, court_id in enumerate(st.session_state.courts):
        with cols[idx]:
            st.markdown('<div class="court-card">', unsafe_allow_html=True)
            st.markdown(f"### Court {court_id}")
            teams = st.session_state.courts[court_id]

            if teams:
                teamA = " & ".join(format_player(p) for p in teams[0])
                teamB = " & ".join(format_player(p) for p in teams[1])
                st.write(f"**Team A**  \n{teamA}")
                st.write(f"**Team B**  \n{teamB}")

                c1, c2 = st.columns(2)
                if c1.button("🏆 A Wins", key=f"a{court_id}"):
                    finish_match(court_id, 0)
                if c2.button("🏆 B Wins", key=f"b{court_id}"):
                    finish_match(court_id, 1)
            else:
                st.info("Waiting for players...")

            st.markdown('</div>', unsafe_allow_html=True)
