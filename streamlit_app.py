import streamlit as st
import random
from collections import deque

# =====================================================
# PAGE CONFIG (MUST BE FIRST)
# =====================================================
st.set_page_config(
    page_title="TiraDinks Pickleball Auto Stack",
    page_icon="🎾",
    layout="wide"
)

# =====================================================
# 🔒 HIDE STREAMLIT CLOUD UI (GitHub / Settings / Manage App)
# =====================================================
st.markdown("""
<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}
[data-testid="stToolbar"]{display:none !important;}
[data-testid="stDecoration"]{display:none !important;}
[data-testid="stStatusWidget"]{display:none !important;}
[data-testid="stSettingsButton"]{display:none !important;}

.court-card{
    padding:15px;
    border-radius:14px;
    background:#f3f6fa;
}
.waiting-box{
    background:#fff3cd;
    padding:12px;
    border-radius:10px;
    font-size:18px;
}
</style>
""", unsafe_allow_html=True)


# =====================================================
# CONFIG
# =====================================================
COURT_LIMITS = {2:16, 3:26, 4:36, 5:46, 6:56, 7:66}
SKILLS = ["BEGINNER","NOVICE","INTERMEDIATE"]


# =====================================================
# HELPERS
# =====================================================
def skill_icon(cat):
    return {
        "BEGINNER":"🟢",
        "NOVICE":"🟡",
        "INTERMEDIATE":"🔴"
    }[cat]


def fmt(p):
    return f"{skill_icon(p[1])} {p[0]}"


def make_teams(players):
    random.shuffle(players)
    return [players[:2], players[2:]]


# -----------------------------------------------------
# Skill rule
# Beginner + Intermediate NOT allowed
# everything else allowed
# -----------------------------------------------------
def is_safe_combo(players):
    skills = {p[1] for p in players}
    if "BEGINNER" in skills and "INTERMEDIATE" in skills:
        return False
    return True


# -----------------------------------------------------
# FIXED FIFO MATCHING
# prevents "first player stuck" bug
# -----------------------------------------------------
def pick_four(queue):
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


def start_match(court_id):
    group = pick_four(st.session_state.queue)
    if group:
        st.session_state.courts[court_id] = make_teams(group)


def finish_match(court_id, winner_idx):
    teams = st.session_state.courts[court_id]
    if not teams:
        return

    winners = teams[winner_idx]
    losers = teams[1-winner_idx]

    # winners first = fair rotation
    st.session_state.queue.extend(winners + losers)
    start_match(court_id)


def auto_fill():
    if not st.session_state.started:
        return

    for c in st.session_state.courts:
        if st.session_state.courts[c] is None:
            start_match(c)


# =====================================================
# SESSION STATE
# =====================================================
defaults = {
    "page":"home",
    "queue":deque(),
    "courts":{},
    "started":False,
    "court_count":2
}

for k,v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# =====================================================
# HOME PAGE
# =====================================================
if st.session_state.page == "home":

    st.title("🎾 TiraDinks Pickleball")
    st.subheader("Choose your role")

    c1, c2 = st.columns(2)

    if c1.button("Organizer", use_container_width=True):
        st.session_state.page = "organizer"

    if c2.button("Player", use_container_width=True):
        st.session_state.page = "player"

    st.stop()


# =====================================================
# PLAYER PAGE
# =====================================================
if st.session_state.page == "player":

    st.title("🎾 Player")
    st.info("Coming soon 👷")

    if st.button("🏠 Back Home"):
        st.session_state.page = "home"

    st.stop()


# =====================================================
# ORGANIZER PAGE
# =====================================================
st.title("🎾 Pickleball Auto Stack (Organizer)")
st.caption("First come • first play • fair skill matching")


# =====================================================
# SIDEBAR
# =====================================================
with st.sidebar:

    st.header("⚙ Setup")

    st.session_state.court_count = st.selectbox(
        "Number of courts",
        list(COURT_LIMITS.keys())
    )

    st.write(f"Max players: **{COURT_LIMITS[st.session_state.court_count]}**")

    st.divider()

    # add player
    with st.form("add", clear_on_submit=True):
        name = st.text_input("Name")
        skill = st.radio("Skill", ["Beginner","Novice","Intermediate"])
        if st.form_submit_button("Add Player") and name.strip():
            st.session_state.queue.append((name.strip(), skill.upper()))

    st.divider()

    if st.button("🚀 Start Games"):
        st.session_state.started = True
        st.session_state.courts = {
            i:None for i in range(1, st.session_state.court_count+1)
        }

    if st.button("🔄 Reset"):
        st.session_state.queue = deque()
        st.session_state.courts = {}
        st.session_state.started = False

    if st.button("🏠 Back Home"):
        st.session_state.page = "home"


# =====================================================
# MAIN LOGIC
# =====================================================
auto_fill()


# =====================================================
# WAITING QUEUE
# =====================================================
st.subheader("⏳ Waiting Queue")

waiting = [fmt(p) for p in st.session_state.queue]

if waiting:
    st.markdown(
        '<div class="waiting-box">'+", ".join(waiting)+'</div>',
        unsafe_allow_html=True
    )
else:
    st.success("No players waiting 🎉")


if not st.session_state.started:
    st.info("Add players then press Start Games")
    st.stop()


# =====================================================
# COURTS GRID
# =====================================================
st.divider()
st.subheader("🏟 Live Courts")

per_row = 3
ids = list(st.session_state.courts.keys())

for r in range(0, len(ids), per_row):

    cols = st.columns(per_row)

    for idx, court_id in enumerate(ids[r:r+per_row]):

        with cols[idx]:

            st.markdown('<div class="court-card">', unsafe_allow_html=True)
            st.markdown(f"### Court {court_id}")

            teams = st.session_state.courts[court_id]

            if teams:
                st.write("**Team A**  \n" + " & ".join(fmt(p) for p in teams[0]))
                st.write("**Team B**  \n" + " & ".join(fmt(p) for p in teams[1]))

                c1, c2 = st.columns(2)

                if c1.button("🏆 A Wins", key=f"a{court_id}"):
                    finish_match(court_id, 0)

                if c2.button("🏆 B Wins", key=f"b{court_id}"):
                    finish_match(court_id, 1)
            else:
                st.info("Waiting for players...")

            st.markdown('</div>', unsafe_allow_html=True)
