import streamlit as st
import random

st.set_page_config(page_title="Pickleball AutoStack", layout="wide")

# ================= INIT STATE =================
def init():
    if "queue" not in st.session_state:
        st.session_state.queue = []
    if "courts" not in st.session_state:
        st.session_state.courts = []
    if "court_updated" not in st.session_state:
        st.session_state.court_updated = {}  # track single-click winners

init()

# ================= CONFIG =================
SKILLS = ["Beginner", "Novice", "Intermediate"]
ICON = {"Beginner":"🟢", "Novice":"🟡", "Intermediate":"🔴"}
LEVEL = {"Beginner":1, "Novice":2, "Intermediate":3}

# ================= HELPERS =================
def show(p):
    return f'{ICON[p["skill"]]} {p["name"]}'

def safe_group(players):
    skills = {p["skill"] for p in players}
    return not ("Beginner" in skills and "Intermediate" in skills)

def build_balanced(group):
    ordered = sorted(group, key=lambda x: LEVEL[x["skill"]], reverse=True)
    teamA = [ordered[0], ordered[3]]
    teamB = [ordered[1], ordered[2]]
    random.shuffle(teamA)
    random.shuffle(teamB)
    return teamA.copy(), teamB.copy()

def mix_by_skill(players):
    buckets = {s: [] for s in SKILLS}
    for p in players:
        buckets[p["skill"]].append(p)
    for b in buckets.values():
        random.shuffle(b)
    mixed = []
    while any(buckets.values()):
        for s in SKILLS:
            if buckets[s]:
                mixed.append(buckets[s].pop())
    return mixed

# ================= ASSIGN PLAYERS =================
def assign_players():
    """Assign players to courts automatically, max 7 courts"""
    remaining = st.session_state.queue.copy()
    st.session_state.queue = []

    # fill empty slots in existing courts
    for court in st.session_state.courts:
        if len(court["A"]) + len(court["B"]) < 4 and len(remaining) >= 4:
            group = remaining[:4]
            if not safe_group(group):
                random.shuffle(remaining)
                continue
            teamA, teamB = build_balanced(group)
            court["A"] = teamA
            court["B"] = teamB
            remaining = remaining[4:]

    # create new courts if needed (max 7)
    while len(remaining) >= 4 and len(st.session_state.courts) < 7:
        group = remaining[:4]
        if not safe_group(group):
            random.shuffle(remaining)
            continue
        teamA, teamB = build_balanced(group)
        st.session_state.courts.append({"A": teamA, "B": teamB})
        remaining = remaining[4:]

    # leftover players stay in queue
    st.session_state.queue.extend(remaining)

# ================= FINISH MATCH =================
def finish_match(idx, winner):
    # prevent double click
    if st.session_state.court_updated.get(idx):
        return
    st.session_state.court_updated[idx] = True

    court = st.session_state.courts[idx]
    winners = court[winner].copy()
    losers = court["A" if winner == "B" else "B"].copy()

    # add back to queue
    st.session_state.queue.extend(winners + losers)

    # rebuild only this court if enough players
    if len(st.session_state.queue) >= 4:
        group = [st.session_state.queue.pop(0) for _ in range(4)]
        teamA, teamB = build_balanced(group)
        st.session_state.courts[idx] = {"A": teamA, "B": teamB}
    else:
        st.session_state.courts[idx] = {"A": [], "B": []}

# ================= STREAMLIT UI =================
st.title("🏟 Pickleball Auto Stack")

with st.sidebar:
    st.subheader("Add Player")
    name = st.text_input("Name")
    skill = st.selectbox("Skill", SKILLS, key="s")
    if st.button("Add") and name:
        st.session_state.queue.append({"name": name, "skill": skill})
        assign_players()
        st.session_state.court_updated = {}

# Waiting Queue
st.subheader("⏳ Waiting Queue")
if st.session_state.queue:
    st.write(", ".join(show(p) for p in st.session_state.queue))
else:
    st.success("No players waiting 🎉")

st.divider()

# Live Courts
st.subheader("🏟 Live Courts")
if not st.session_state.courts:
    st.info("No courts yet")

for i, court in enumerate(st.session_state.courts):
    with st.container():
        st.markdown(f"### Court {i+1}")
        c1, c2, c3 = st.columns([3, 3, 2])

        with c1:
            st.write("**Team A**")
            for p in court["A"]:
                st.write(show(p))
        with c2:
            st.write("**Team B**")
            for p in court["B"]:
                st.write(show(p))
        with c3:
            if st.button("Winner A", key=f"A{i}"):
                finish_match(i, "A")
            if st.button("Winner B", key=f"B{i}"):
                finish_match(i, "B")
