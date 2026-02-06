import streamlit as st
import random
from collections import deque

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="TiraDinks Pickleball Auto Stack",
    page_icon="🎾",
    layout="wide"
)

# =========================================================
# CONFIG
# =========================================================

COURT_LIMITS = {
    2: 16,
    3: 26,
    4: 36,
    5: 46,
    6: 56,
    7: 66,
}

HOME_FILE = "streamlit_app.py"   # 👈 your real home page


# =========================================================
# STYLES
# =========================================================

st.markdown("""
<style>
.court-card {
    padding: 16px;
    border-radius: 16px;
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
# SESSION STATE INIT
# =========================================================

defaults = {
    "queue": deque(),
    "courts": {},
    "started": False,
    "court_count": 2,
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# =========================================================
# HELPERS
# =========================================================

def skill_icon(cat):
    return {
        "BEGINNER": "🟢",
        "NOVICE": "🟡",
        "INTERMEDIATE": "🔴",
    }[cat]


def format_player(p):
    return f"{skill_icon(p[1])} {p[0]}"


def make_teams(players):
    random.shuffle(players)
    return [players[:2], players[2:]]


# =========================================================
# MATCHING LOGIC
# =========================================================

def is_safe_combo(players):
    skills = {p[1] for p in players}
    return not ("BEGINNER" in skills and "INTERMEDIATE" in skills)


def pick_four_fifo_safe(queue):
    if len(queue) < 4:
        return None

    temp = list(queue)

    for i in range(len(temp) - 3):
        group = temp[i:i+4]

        if is_safe_combo(group):
            for p in group:
                queue.remove(p)
            return group

    return None


# =========================================================
# COURT LOGIC
# =========================================================

def start_match(court_id):
    four = pick_four_fifo_safe(st.session_state.queue)

    if not four:
        st.session_state.courts[court_id] = None
        return False

    st.session_state.courts[court_id] = make_teams(four)
    return True


def finish_match(court_id, winner_idx):
    teams = st.session_state.courts[court_id]

    winners = teams[winner_idx]
    losers = teams[1 - winner_idx]

    st.session_state.queue.extend(winners + losers)
    start_match(court_id)


def auto_fill():
    if not st.session_state.started:
        return

    changed = False

    for c in st.session_state.courts:
        if st.session_state.courts[c] is None:
            if start_match(c):
                changed = True

    if changed:
        st.rerun()


# =========================================================
# HEADER
# =========================================================

st.title("🎾 TiraDinks Pickleball Auto Stack")
st.caption("First come • first play • fair rotation")


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    # ⭐ HOME BUTTON
    if st.button("🏠 Back to Home", use_container_width=True):
        st.switch_page(HOME_FILE)

    st.divider()

    st.header("⚙ Setup")

    st.session_state.court_count = st.selectbox(
        "Number of courts",
        list(COURT_LIMITS.keys())
    )

    st.write(f"Max players: **{COURT_LIMITS[st.session_state.court_count]}**")

    st.divider()

    # ADD PLAYER
    st.subheader("➕ Add Player")

    with st.form("add_player", clear_on_submit=True):
        name = st.text_input("Name")
        cat = st.radio("Skill", ["Beginner", "Novice", "Intermediate"])

        if st.form_submit_button("Add to Queue") and name.strip():
            st.session_state.queue.append((name.strip(), cat.upper()))

    st.divider()

    # CONTROLS
    if st.button("🚀 Start Games", use_container_width=True):
        st.session_state.started = True
        st.session_state.courts = {
            i: None for i in range(1, st.session_state.court_count + 1)
        }
        st.rerun()

    if st.button("🔄 Reset All", use_container_width=True):
        st.session_state.queue = deque()
        st.session_state.courts = {}
        st.session_state.started = False
        st.rerun()


# =========================================================
# AUTO FILL EMPTY COURTS
# =========================================================

auto_fill()


# =========================================================
# WAITING QUEUE
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
# COURTS UI
# =========================================================

st.divider()
st.subheader("🏟 Live Courts")

per_row = 3
ids = list(st.session_state.courts.keys())

for row in range(0, len(ids), per_row):
    cols = st.columns(per_row)

    for idx, cid in enumerate(ids[row:row+per_row]):

        with cols[idx]:

            st.markdown('<div class="court-card">', unsafe_allow_html=True)
            st.markdown(f"### Court {cid}")

            teams = st.session_state.courts[cid]

            if teams:
                teamA = " & ".join(format_player(p) for p in teams[0])
                teamB = " & ".join(format_player(p) for p in teams[1])

                st.write(f"**Team A**  \n{teamA}")
                st.write(f"**Team B**  \n{teamB}")

                c1, c2 = st.columns(2)

                if c1.button("🏆 A Wins", key=f"a{cid}"):
                    finish_match(cid, 0)
                    st.rerun()

                if c2.button("🏆 B Wins", key=f"b{cid}"):
                    finish_match(cid, 1)
                    st.rerun()

            else:
                st.info("Waiting for players...")

            st.markdown("</div>", unsafe_allow_html=True)
