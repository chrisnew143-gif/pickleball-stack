import streamlit as st
import random
from collections import deque
import pandas as pd

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Pickleball Auto Stack",
    page_icon="🎾",
    layout="wide"
)

# =========================================================
# CSS  (hide ONLY github icon)
# =========================================================
st.markdown("""
<style>

/* hide only github icon */
a[href*="github.com/streamlit"]{
    display:none !important;
}

.court-card{
    padding:18px;
    border-radius:14px;
    background:#f4f6fa;
    margin-bottom:14px;
}

.waiting-box{
    background:#fff3cd;
    padding:12px;
    border-radius:10px;
    font-size:17px;
}

</style>
""", unsafe_allow_html=True)

st.title("🎾 Pickleball Auto Stack")
st.caption("First come • first play • fair rotation")

# =========================================================
# CONSTANTS
# =========================================================
MAX_PER_COURT = 10


# =========================================================
# HELPERS
# =========================================================
def icon(skill):
    return {
        "BEGINNER": "🟢",
        "NOVICE": "🟡",
        "INTERMEDIATE": "🔴"
    }[skill]


def fmt(player):
    return f"{icon(player[1])} {player[0]}"


def make_teams(players):
    random.shuffle(players)
    return [players[:2], players[2:]]


# =========================================================
# SESSION INIT
# =========================================================
def init():
    ss = st.session_state

    ss.setdefault("queue", deque())
    ss.setdefault("courts", {})
    ss.setdefault("locked", {})
    ss.setdefault("scores", {})
    ss.setdefault("history", [])
    ss.setdefault("started", False)
    ss.setdefault("court_count", 2)


init()


# =========================================================
# MATCH ENGINE (VERY STABLE)
# =========================================================
def take_four():
    """FIFO take first 4 players"""
    if len(st.session_state.queue) < 4:
        return None

    return [st.session_state.queue.popleft() for _ in range(4)]


def start_match(cid):
    """Start ONLY this court (no global reshuffle)"""

    if st.session_state.locked[cid]:
        return

    players = take_four()
    if not players:
        return

    st.session_state.courts[cid] = make_teams(players)
    st.session_state.locked[cid] = True
    st.session_state.scores[cid] = [0, 0]


def finish_match(cid):
    """Finish ONLY this court"""

    teams = st.session_state.courts[cid]
    scoreA, scoreB = st.session_state.scores[cid]

    players = teams[0] + teams[1]

    # save history
    st.session_state.history.append({
        "Court": cid,
        "Team A": " & ".join(p[0] for p in teams[0]),
        "Team B": " & ".join(p[0] for p in teams[1]),
        "Score A": scoreA,
        "Score B": scoreB
    })

    # mix players back
    random.shuffle(players)
    for p in players:
        st.session_state.queue.append(p)

    # unlock + reset
    st.session_state.courts[cid] = None
    st.session_state.locked[cid] = False
    st.session_state.scores[cid] = [0, 0]


def auto_fill():
    """Fill only empty courts"""
    if not st.session_state.started:
        return

    for cid in st.session_state.courts:
        if st.session_state.courts[cid] is None:
            start_match(cid)


# =========================================================
# CSV DOWNLOAD (no openpyxl needed)
# =========================================================
def create_csv():
    if not st.session_state.history:
        return b""

    df = pd.DataFrame(st.session_state.history)
    return df.to_csv(index=False).encode("utf-8")


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.header("⚙ Setup")

    st.session_state.court_count = st.selectbox(
        "Courts",
        [2, 3, 4, 5, 6]
    )

    st.write(f"Max players: **{MAX_PER_COURT * st.session_state.court_count}**")

    st.divider()

    # ADD PLAYER
    with st.form("add_player", clear_on_submit=True):
        name = st.text_input("Name")
        skill = st.radio("Skill", ["Beginner", "Novice", "Intermediate"])
        ok = st.form_submit_button("Add Player")

        if ok and name:
            st.session_state.queue.append((name, skill.upper()))

    st.divider()

    # START
    if st.button("🚀 Start Games", use_container_width=True):
        st.session_state.started = True
        st.session_state.courts = {i: None for i in range(1, st.session_state.court_count + 1)}
        st.session_state.locked = {i: False for i in range(1, st.session_state.court_count + 1)}
        st.session_state.scores = {i: [0, 0] for i in range(1, st.session_state.court_count + 1)}
        st.rerun()

    # RESET
    if st.button("🔄 Reset All", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    st.divider()

    # DOWNLOAD RESULTS
    st.download_button(
        "📥 Download Results (CSV)",
        data=create_csv(),
        file_name="pickleball_results.csv",
        mime="text/csv",
        use_container_width=True
    )


# =========================================================
# WAITING QUEUE
# =========================================================
st.subheader("⏳ Waiting Queue")

if st.session_state.queue:
    st.markdown(
        f'<div class="waiting-box">{", ".join(fmt(p) for p in st.session_state.queue)}</div>',
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
# LIVE COURTS
# =========================================================
auto_fill()

st.divider()
st.subheader("🏟 Live Courts")

ids = list(st.session_state.courts.keys())
per_row = 3

for r in range(0, len(ids), per_row):
    cols = st.columns(per_row)

    for i, cid in enumerate(ids[r:r+per_row]):

        with cols[i]:

            st.markdown('<div class="court-card">', unsafe_allow_html=True)
            st.markdown(f"### Court {cid}")

            teams = st.session_state.courts[cid]

            if not teams:
                st.info("Waiting for players...")
                st.markdown('</div>', unsafe_allow_html=True)
                continue

            st.write("**Team A**  \n" + " & ".join(fmt(p) for p in teams[0]))
            st.write("**Team B**  \n" + " & ".join(fmt(p) for p in teams[1]))

            scoreA = st.number_input("Score A", 0, key=f"A{cid}")
            scoreB = st.number_input("Score B", 0, key=f"B{cid}")

            if st.button("Submit Score", key=f"S{cid}"):

                st.session_state.scores[cid] = [scoreA, scoreB]

                finish_match(cid)

                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)
