import streamlit as st
import random
from collections import deque, defaultdict

# =========================================================
# CONFIG
# =========================================================

SKILLS = ["BEGINNER", "NOVICE", "INTERMEDIATE"]

COURT_LIMITS = {2: 16, 3: 26, 4: 36}


# =========================================================
# PAGE
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
    name, cat = p
    return f"{skill_icon(cat)} {name}"


def make_teams(players):
    random.shuffle(players)
    return [players[:2], players[2:]]


# =========================================================
# ⭐ SMART MATCHMAKING LOGIC (NEW)
# =========================================================

def extract_players(queue, category, count):
    """Pull players of specific category"""
    selected = []
    remaining = deque()

    while queue:
        p = queue.popleft()
        if p[1] == category and len(selected) < count:
            selected.append(p)
        else:
            remaining.append(p)

    queue.extend(remaining)
    return selected


def find_best_four(queue):
    """
    Priority:
    1) 4 same skill
    2) Beginner + Novice
    3) Novice + Intermediate
    4) else None
    """

    temp = deque(queue)

    groups = defaultdict(list)
    for p in temp:
        groups[p[1]].append(p)

    # ---------- SAME SKILL ----------
    for cat in SKILLS:
        if len(groups[cat]) >= 4:
            return extract_players(queue, cat, 4)

    # ---------- BEGINNER + NOVICE ----------
    if len(groups["BEGINNER"]) + len(groups["NOVICE"]) >= 4:
        result = []
        result += extract_players(queue, "BEGINNER", min(4, len(groups["BEGINNER"])))
        if len(result) < 4:
            result += extract_players(queue, "NOVICE", 4 - len(result))
        if len(result) == 4:
            return result

    # ---------- NOVICE + INTERMEDIATE ----------
    if len(groups["NOVICE"]) + len(groups["INTERMEDIATE"]) >= 4:
        result = []
        result += extract_players(queue, "NOVICE", min(4, len(groups["NOVICE"])))
        if len(result) < 4:
            result += extract_players(queue, "INTERMEDIATE", 4 - len(result))
        if len(result) == 4:
            return result

    return None


# =========================================================
# MATCH CONTROL
# =========================================================

def start_match(court_id):
    players = find_best_four(st.session_state.queue)

    if players:
        st.session_state.courts[court_id] = make_teams(players)
    else:
        st.session_state.courts[court_id] = None


def finish_match(court_id, winner_idx):
    teams = st.session_state.courts[court_id]

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

st.title("🎾 TiraDinks Pickleball Auto Stack")
st.caption("Real-time stacking • fair skill matching • tap winners to continue")


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("⚙ Setup")

    st.session_state.court_count = st.selectbox(
        "Number of courts",
        [2, 3, 4]
    )

    st.write(f"Max players: **{COURT_LIMITS[st.session_state.court_count]}**")

    st.divider()

    with st.form("add_player_form", clear_on_submit=True):

        name = st.text_input("Name")

        cat = st.radio(
            "Skill",
            ["Beginner", "Novice", "Intermediate"]
        )

        if st.form_submit_button("Add to Queue") and name.strip():
            player = (name.strip(), cat.upper())
            st.session_state.queue.append(player)

    st.divider()

    if st.button("🚀 Start Games"):
        st.session_state.started = True
        st.session_state.courts = {
            i: None for i in range(1, st.session_state.court_count + 1)
        }
        for c in st.session_state.courts:
            start_match(c)
        st.rerun()

    if st.button("🔄 Reset All"):
        st.session_state.queue = deque()
        st.session_state.courts = {}
        st.session_state.started = False
        st.rerun()


# =========================================================
# WAITING LIST
# =========================================================

st.subheader("⏳ Waiting Queue")

waiting = [format_player(p) for p in st.session_state.queue]

if waiting:
    st.markdown(
        '<div class="waiting-box">' + ", ".join(waiting) + '</div>',
        unsafe_allow_html=True
    )
else:
    st.success("No players waiting 🎉")


# =========================================================
# AUTO FILL
# =========================================================

auto_fill_empty_courts()

if not st.session_state.started:
    st.info("Add players then press **Start Games**")
    st.stop()


# =========================================================
# COURTS
# =========================================================

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
                st.rerun()

            if c2.button("🏆 B Wins", key=f"b{court_id}"):
                finish_match(court_id, 1)
                st.rerun()

        else:
            st.info("Waiting for players...")

        st.markdown('</div>', unsafe_allow_html=True)
