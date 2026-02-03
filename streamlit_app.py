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


# ---------------------------------------------------------
# FAIR MATCHING LOGIC
# ---------------------------------------------------------

def allowed_mix(group_skills):
    """Return True if skill combination is allowed"""
    unique = set(group_skills)

    # same category always ok
    if len(unique) == 1:
        return True

    # allowed mixes
    if unique == {"BEGINNER", "NOVICE"}:
        return True
    if unique == {"NOVICE", "INTERMEDIATE"}:
        return True

    # beginner + intermediate NOT allowed
    return False


def pick_four_fair(queue):
    """Pick 4 players fairly and remove from queue"""

    players = list(queue)

    if len(players) < 4:
        return None

    # 1️⃣ Try same-skill first
    by_skill = defaultdict(list)
    for p in players:
        by_skill[p[1]].append(p)

    for skill in SKILLS:
        if len(by_skill[skill]) >= 4:
            chosen = by_skill[skill][:4]
            for p in chosen:
                queue.remove(p)
            return chosen

    # 2️⃣ Try allowed mixes
    for i in range(len(players)):
        for j in range(i+1, len(players)):
            for k in range(j+1, len(players)):
                for l in range(k+1, len(players)):
                    group = [players[i], players[j], players[k], players[l]]
                    skills = [p[1] for p in group]

                    if allowed_mix(skills):
                        for p in group:
                            queue.remove(p)
                        return group

    return None


# ---------------------------------------------------------
# COURT CONTROL
# ---------------------------------------------------------

def start_match(court_id):
    four = pick_four_fair(st.session_state.queue)

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


def auto_fill_empty_courts():
    """Auto start matches BEFORE rendering queue"""
    if not st.session_state.started:
        return False

    changed = False

    for c in st.session_state.courts:
        if st.session_state.courts[c] is None:
            started = start_match(c)
            if started:
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

    st.subheader("➕ Add Player")

    with st.form("add_player_form", clear_on_submit=True):

        name = st.text_input("Name")

        cat = st.radio(
            "Skill",
            ["Beginner", "Novice", "Intermediate"]
        )

        submitted = st.form_submit_button("Add to Queue")

        if submitted and name.strip():

            player = (name.strip(), cat.upper())

            if len(st.session_state.queue) < COURT_LIMITS[st.session_state.court_count]:
                st.session_state.queue.append(player)

    st.divider()

    if st.button("🚀 Start Games"):

        st.session_state.started = True

        st.session_state.courts = {
            i: None for i in range(1, st.session_state.court_count + 1)
        }

        st.rerun()

    if st.button("🔄 Reset All"):
        st.session_state.queue = deque()
        st.session_state.courts = {}
        st.session_state.started = False
        st.rerun()


# =========================================================
# 🔥 AUTO FILL FIRST (CRITICAL FIX)
# =========================================================

changed = auto_fill_empty_courts()
if changed:
    st.rerun()


# =========================================================
# WAITING LIST (now always correct)
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
# STOP IF NOT STARTED
# =========================================================

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
