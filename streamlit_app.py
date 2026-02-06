import streamlit as st
import random

# ================== CONFIG ==================
SKILLS = ["Beginner", "Novice", "Intermediate"]

ICON = {
    "Beginner": "🟢",
    "Novice": "🟡",
    "Intermediate": "🔴"
}

LEVEL = {
    "Beginner": 1,
    "Novice": 2,
    "Intermediate": 3
}

MAX_COURTS = 7  # max courts allowed

# ================== SESSION STATE ==================
if "page" not in st.session_state:
    st.session_state.page = "home"

if "queue" not in st.session_state:
    st.session_state.queue = []

if "courts" not in st.session_state:
    st.session_state.courts = []  # list of dicts: {"A": [], "B": []}

# ================== HELPERS ==================
def show(p):
    return f'{ICON[p["skill"]]} {p["name"]}'

def safe_group(players):
    skills = {p["skill"] for p in players}
    return not ("Beginner" in skills and "Intermediate" in skills)

def build_balanced(group):
    """Return two balanced teams (copies, shuffled)"""
    ordered = sorted(group, key=lambda x: LEVEL[x["skill"]], reverse=True)
    teamA = [ordered[0], ordered[3]]
    teamB = [ordered[1], ordered[2]]
    random.shuffle(teamA)
    random.shuffle(teamB)
    return teamA.copy(), teamB.copy()

def mix_by_skill(players):
    """Shuffle players by skill fairly"""
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

# ================== COURT LOGIC ==================
def assign_players_to_courts():
    """Assign players from queue to courts automatically"""
    remaining = st.session_state.queue.copy()
    st.session_state.queue = []

    # Refill empty courts first
    for court in st.session_state.courts:
        empty_slots = 4 - (len(court["A"]) + len(court["B"]))
        if empty_slots >= 4 and len(remaining) >= 4:
            group = remaining[:4]
            if not safe_group(group):
                random.shuffle(remaining)
                continue
            teamA, teamB = build_balanced(group)
            court["A"] = teamA
            court["B"] = teamB
            remaining = remaining[4:]

    # Add new courts if needed
    while len(st.session_state.courts) < MAX_COURTS and len(remaining) >= 4:
        group = remaining[:4]
        if not safe_group(group):
            random.shuffle(remaining)
            continue
        teamA, teamB = build_balanced(group)
        st.session_state.courts.append({"A": teamA, "B": teamB})
        remaining = remaining[4:]

    # leftover players go back to queue
    st.session_state.queue.extend(remaining)

def finish_match(idx, winner):
    """Finish match only for clicked court, single click"""
    court = st.session_state.courts[idx]
    winners = court[winner].copy()
    losers = court["A" if winner == "B" else "B"].copy()

    # Add back to queue
    st.session_state.queue.extend(winners + losers)

    # Rebuild this court if enough players
    if len(st.session_state.queue) >= 4:
        group = [st.session_state.queue.pop(0) for _ in range(4)]
        teamA, teamB = build_balanced(group)
        st.session_state.courts[idx] = {"A": teamA, "B": teamB}
    else:
        st.session_state.courts[idx] = {"A": [], "B": []}

# ================== NAVIGATION ==================
def go_home():
    st.session_state.page = "home"

def go_autostack():
    st.session_state.page = "autostack"

def go_player():
    st.session_state.page = "player"

# ================== PAGES ==================
if st.session_state.page == "home":
    st.title("🎾 Pickleball Stack System")
    col1, col2 = st.columns(2)
    if col1.button("🏟 Organizer (AutoStack)"):
        go_autostack()
    if col2.button("👤 Player Join"):
        go_player()

elif st.session_state.page == "player":
    st.button("⬅ Back Home", on_click=go_home)
    st.title("👤 Join Queue")

    name = st.text_input("Name")
    skill = st.selectbox("Skill", SKILLS)

    if st.button("Join") and name:
        st.session_state.queue.append({"name": name, "skill": skill})
        assign_players_to_courts()  # assign immediately

    st.divider()
    st.subheader("⏳ Waiting Queue")
    if st.session_state.queue:
        st.write(", ".join(show(p) for p in st.session_state.queue))
    else:
        st.success("No players waiting 🎉")

elif st.session_state.page == "autostack":
    st.button("⬅ Back Home", on_click=go_home)
    st.title("🏟 Pickleball Auto Stack")

    # ---------------- queue
    st.subheader("⏳ Waiting Queue")
    if st.session_state.queue:
        st.write(", ".join(show(p) for p in st.session_state.queue))
    else:
        st.success("No players waiting 🎉")

    st.divider()

    # ---------------- courts
    st.subheader(f"🏟 Live Courts ({len(st.session_state.courts)} courts)")
    if not st.session_state.courts:
        st.info("No courts yet. Add players from Player Join page.")

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
