import streamlit as st
import random
from collections import deque

# -----------------------
# CONFIG
# -----------------------
COURT_LIMITS = {2: 16, 3: 26, 4: 36, 5: 46, 6: 56, 7: 66}
SKILLS = ["BEGINNER", "NOVICE", "INTERMEDIATE"]


# -----------------------
# PAGE SETUP
# -----------------------
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


# -----------------------
# HELPERS
# -----------------------
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


# -----------------------
# SKILL RULE
# Beginner + Intermediate NOT allowed
# everything else allowed
# -----------------------
def is_safe_combo(players):
    skills = {p[1] for p in players}

    if "BEGINNER" in skills and "INTERMEDIATE" in skills:
        return False

    return True


# -----------------------
# FIFO MATCHING
# -----------------------
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


# -----------------------
# COURT LOGIC
# -----------------------
def start_match(court_id):
    four = pick_four_fifo_safe(st.session_state.queue)

    if four:
        st.session_state.courts[court_id] = make_teams(four)
    else:
        st.session_state.courts[court_id] = None


def finish_match(court_id, winner_idx):
    teams = st.session_state.courts[court_id]

    if not teams:
        return

    winners = teams[winner_idx]
    losers = teams[1 - winner_idx]

    st.session_state.queue.extend(winners + losers)
    start_match(court_id)


def auto_fill_empty_courts():
    if not st.session_state.started:
        return

    for c in st.session_state.courts:
        if st.session_state.courts[c] is None:
            start_match(c)


# -----------------------
# SESSION STATE
# -----------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

if "queue" not in st.session_state:
    st.session_state.queue = deque()

if "courts" not in st.session_state:
    st.session_state.courts = {}

if "started" not in st.session_state:
    st.session_state.started = False

if "court_count" not in st.session_state:
    st.session_state.court_count = 2


# =====================================================
# HOME PAGE
# =====================================================
if st.session_state.page == "home":

    st.title("🎾 TiraDinks Pickleball")
    st.subheader("Choose your role")

    col1, col2 = st.columns(2)

    if col1.button("Organizer", use_container_width=True):
        st.session_state.page = "organizer"

    if col2.button("Player", use_container_width=True):
        st.session_state.page = "player"

    st.stop()


# =====================================================
# PLAYER PAGE
# =====================================================
if st.session_state.page == "player":

    st.title("🎾 Player")
    st.warning("UNDER CONSTRUCTION")

    if st.button("🏠 Back to Home"):
        st.session_state.page = "home"

    st.stop()


# =====================================================
# ORGANIZER PAGE
# =====================================================
st.title("🎾 Pickleball Auto Stack (Organizer)")
st.caption("First come • first play • fair rotation")


# -----------------------
# SIDEBAR
# -----------------------
with st.sidebar:

    st.header("⚙ Setup")

    # ✅ FIX: dynamic courts 2–7
    st.session_state.court_count = st.selectbox(
        "Number of courts",
        list(COURT_LIMITS.keys())
    )

    st.write(f"Max players: **{COURT_LIMITS[st.session_state.court_count]}**")

    st.divider()

    with st.form("add_player_form", clear_on_submit=True):
        name = st.text_input("Name")
        cat = st.radio("Skill", ["Beginner", "Novice", "Intermediate"])
        submitted = st.form_submit_button("Add Player")

        if submitted and name.strip():
            st.session_state.queue.append((name.strip(), cat.upper()))

    st.divider()

    if st.button("🚀 Start Games"):
        st.session_state.started = True
        st.session_state.courts = {
            i: None for i in range(1, st.session_state.court_count + 1)
        }

    if st.button("🔄 Reset"):
        st.session_state.queue = deque()
        st.session_state.courts = {}
        st.session_state.started = False

    if st.button("🏠 Back Home"):
        st.session_state.page = "home"


# -----------------------
# AUTO FILL
# -----------------------
auto_fill_empty_courts()


# -----------------------
# WAITING
# -----------------------
st.subheader("⏳ Waiting Queue")

waiting = [format_player(p) for p in st.session_state.queue]

if waiting:
    st.markdown(
        '<div class="waiting-box">' + ", ".join(waiting) + '</div>',
        unsafe_allow_html=True
    )
else:
    st.success("No players waiting 🎉")


if not st.session_state.started:
    st.info("Add players then press Start Games")
    st.stop()


# -----------------------
# COURTS
# -----------------------
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

                c1, c2 = st.columns(2)

                if c1.button("🏆 A Wins", key=f"a{court_id}"):
                    finish_match(court_id, 0)

                if c2.button("🏆 B Wins", key=f"b{court_id}"):
                    finish_match(court_id, 1)

            else:
                st.info("Waiting for players...")

            st.markdown('</div>', unsafe_allow_html=True)
