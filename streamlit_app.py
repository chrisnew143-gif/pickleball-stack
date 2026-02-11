import streamlit as st
import random
from collections import deque
import pandas as pd
from itertools import combinations

# ======================================================
# PAGE
# ======================================================
st.set_page_config(
    page_title="Pickleball Auto Stack",
    page_icon="🎾",
    layout="wide",
)

# --- HARD HIDE GITHUB / TOOLBAR ---
st.markdown("""
<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}
[data-testid="stToolbar"] {display:none;}

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
    font-size:14px;
}
</style>
""", unsafe_allow_html=True)

st.title("🎾 Pickleball Auto Stack")
st.caption("First come • first play • fair rotation")


# ======================================================
# HELPERS
# ======================================================
def icon(skill):
    return {
        "BEGINNER": "🟢",
        "NOVICE": "🟡",
        "INTERMEDIATE": "🔴"
    }[skill]


def fmt(p):
    name, skill, _ = p
    return f"{icon(skill)} {name}"


# ======================================================
# SAFETY RULE
# Beginner ❌ Intermediate together
# ======================================================
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
    ss.setdefault("players_master", {})  # name → dupr


init()


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


def finish_match(cid):
    teams = st.session_state.courts[cid]
    scoreA, scoreB = st.session_state.scores[cid]

    players = teams[0] + teams[1]

    st.session_state.history.append({
        "Court": cid,
        "Team A": " & ".join(p[0] for p in teams[0]),
        "Team B": " & ".join(p[0] for p in teams[1]),
        "Score A": scoreA,
        "Score B": scoreB
    })

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
# CSV EXPORTS (NO OPENPYXL)
# ======================================================
def matches_csv():
    if not st.session_state.history:
        return b""

    df = pd.DataFrame(st.session_state.history)
    return df.to_csv(index=False).encode()


def players_csv():
    if not st.session_state.players_master:
        return b""

    df = pd.DataFrame(
        [(k, v) for k, v in st.session_state.players_master.items()],
        columns=["Player Name", "DUPR ID"]
    )

    return df.to_csv(index=False).encode()


# ======================================================
# SIDEBAR
# ======================================================
with st.sidebar:

    st.header("⚙ Setup")

    st.session_state.court_count = st.selectbox(
        "Courts", [2, 3, 4, 5, 6]
    )

    # ADD PLAYER (FRONT)
    with st.form("add", clear_on_submit=True):

        name = st.text_input("Name")
        dupr = st.text_input("DUPR ID (optional)")
        skill = st.radio("Skill", ["Beginner", "Novice", "Intermediate"])

        if st.form_submit_button("Add Player"):
            if name:
                player = (name, skill.upper(), dupr)

                # add to FRONT
                st.session_state.queue.appendleft(player)

                # save master list
                st.session_state.players_master[name] = dupr

    # REMOVE
    if st.session_state.queue:
        names = [p[0] for p in st.session_state.queue]

        pick = st.selectbox("Remove Player", names)

        if st.button("Remove"):
            st.session_state.queue = deque(
                [p for p in st.session_state.queue if p[0] != pick]
            )
            st.rerun()

    st.divider()

    if st.button("🚀 Start Games"):
        st.session_state.started = True
        st.session_state.courts = {i: None for i in range(1, st.session_state.court_count + 1)}
        st.session_state.locked = {i: False for i in range(1, st.session_state.court_count + 1)}
        st.session_state.scores = {i: [0, 0] for i in range(1, st.session_state.court_count + 1)}
        st.rerun()

    if st.button("🔄 Reset"):
        st.session_state.clear()
        st.rerun()

    st.divider()

    st.download_button("📥 Matches CSV", matches_csv(), "matches.csv")
    st.download_button("📥 Players CSV", players_csv(), "players.csv")


# ======================================================
# QUEUE
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


# ======================================================
# COURTS (COMPACT GRID)
# ======================================================
st.divider()
st.subheader("🏟 Live Courts")

cols = st.columns(2)

for i, cid in enumerate(st.session_state.courts):

    with cols[i % 2]:

        st.markdown('<div class="court-card">', unsafe_allow_html=True)
        st.markdown(f"### Court {cid}")

        teams = st.session_state.courts[cid]

        if not teams:
            st.info("Waiting for safe players...")
            st.markdown('</div>', unsafe_allow_html=True)
            continue

        st.write("**Team A**  \n" + " & ".join(fmt(p) for p in teams[0]))
        st.write("**Team B**  \n" + " & ".join(fmt(p) for p in teams[1]))

        a = st.number_input("Score A", 0, key=f"A{cid}")
        b = st.number_input("Score B", 0, key=f"B{cid}")

        if st.button("Submit Score", key=f"S{cid}"):
            st.session_state.scores[cid] = [a, b]
            finish_match(cid)
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
