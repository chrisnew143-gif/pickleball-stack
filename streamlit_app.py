import streamlit as st
import random
from collections import deque, defaultdict

# =========================================================
# CONFIG
# =========================================================

CATEGORY_MAP = {
    "BEGINNER",
    "NOVICE",
    "INTERMEDIATE"
}

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


def balanced_queue(players):
    groups = defaultdict(list)

    for p in players:
        groups[p[1]].append(p)

    for g in groups.values():
        random.shuffle(g)

    mixed = []
    while any(groups.values()):
        for cat in groups:
            if groups[cat]:
                mixed.append(groups[cat].pop())

    return deque(mixed)


def start_match(court_id):
    """Fill a court if 4 players available"""
    if len(st.session_state.queue) >= 4:
        four = [st.session_state.queue.popleft() for _ in range(4)]
        st.session_state.courts[court_id] = make_teams(four)
    else:
        st.session_state.courts[court_id] = None


def finish_match(court_id, winner_idx):
    teams = st.session_state.courts[court_id]

    winners = teams[winner_idx]
    losers = teams[1 - winner_idx]

    st.session_state.queue.extend(winners + losers)

    start_match(court_id)


def auto_fill_empty_courts():
    """🔥 AUTO START NEW MATCHES"""
    if not st.session_state.started:
        return

    for c in st.session_state.courts:
        if st.session_state.courts[c] is None and len(st.session_state.queue) >= 4:
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
st.caption("Real-time stacking • first come first play • tap winners to continue")


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

    # ✅ FIX: use form (no session_state modification error)
    with st.form("add_player_form", clear_on_submit=True):
        name = st.text_input("Name")

        cat = st.radio(
            "Skill",
            ["Beginner", "Novice", "Intermediate"]
        )

        submitted = st.form_submit_button("Add to Queue")

        if submitted and name:
            short = cat[0]
            player = (name, CATEGORY_MAP[short])

            if len(st.session_state.queue) < COURT_LIMITS[st.session_state.court_count]:
                st.session_state.queue.append(player)

    st.divider()

    if st.button("🚀 Start Games"):

        st.session_state.started = True
        st.session_state.queue = balanced_queue(list(st.session_state.queue))

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
# 🔥 AUTO START EMPTY COURTS (NEW FEATURE)
# =========================================================

auto_fill_empty_courts()


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

            with c1:
                st.markdown('<div class="big-btn">', unsafe_allow_html=True)
                if st.button("🏆 A Wins", key=f"a{court_id}"):
                    finish_match(court_id, 0)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            with c2:
                st.markdown('<div class="big-btn">', unsafe_allow_html=True)
                if st.button("🏆 B Wins", key=f"b{court_id}"):
                    finish_match(court_id, 1)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        else:
            st.info("Waiting for players...")

        st.markdown('</div>', unsafe_allow_html=True)
