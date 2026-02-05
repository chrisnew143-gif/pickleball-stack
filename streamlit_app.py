import streamlit as st
import random

st.set_page_config(page_title="Pickleball Auto Stack", layout="wide")


# =====================================================
# INIT STATE
# =====================================================
def init():
    if "page" not in st.session_state:
        st.session_state.page = "home"

    if "queue" not in st.session_state:
        st.session_state.queue = []   # [{name, skill}]

    if "courts" not in st.session_state:
        st.session_state.courts = []

init()


# =====================================================
# CONFIG
# =====================================================
SKILLS = ["Beginner", "Novice", "Intermediate"]

ICON = {
    "Beginner": "🟢",
    "Novice": "🟡",
    "Intermediate": "🔴"
}

SKILL_VALUE = {
    "Beginner": 1,
    "Novice": 2,
    "Intermediate": 3
}


# =====================================================
# HELPERS
# =====================================================
def show(p):
    return f'{ICON[p["skill"]]} {p["name"]}'


# -----------------------------------------------------
# RULE:
# Beginner + Intermediate NOT allowed
# -----------------------------------------------------
def safe_group(players):
    skills = {p["skill"] for p in players}
    return not ("Beginner" in skills and "Intermediate" in skills)


# -----------------------------------------------------
# MIX BY SKILL (fair order)
# -----------------------------------------------------
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


# -----------------------------------------------------
# ⭐ NEW: BALANCED TEAM BUILDER
# prevents 2 beginners vs 2 novice problem
# -----------------------------------------------------
def build_balanced_teams(group):

    # sort strongest → weakest
    group = sorted(group, key=lambda x: SKILL_VALUE[x["skill"]], reverse=True)

    # snake draft balancing
    teamA = [group[0], group[3]]
    teamB = [group[1], group[2]]

    random.shuffle(teamA)
    random.shuffle(teamB)

    return teamA, teamB


# -----------------------------------------------------
# START GAMES
# -----------------------------------------------------
def start_games():

    players = mix_by_skill(st.session_state.queue.copy())

    courts = []
    remaining = players.copy()

    while len(remaining) >= 4:

        found = False

        for _ in range(10):

            group = remaining[:4]

            if safe_group(group):

                teamA, teamB = build_balanced_teams(group)

                courts.append({"A": teamA, "B": teamB})
                remaining = remaining[4:]
                found = True
                break

            random.shuffle(remaining)

        if not found:
            break

    st.session_state.courts = courts
    st.session_state.queue = remaining


# -----------------------------------------------------
# FINISH MATCH
# winners first, losers next
# no reshuffle bug
# -----------------------------------------------------
def finish_match(idx, winner):

    court = st.session_state.courts[idx]

    winners = court[winner]
    losers = court["A" if winner == "B" else "B"]

    # winners first in queue
    st.session_state.queue.extend(winners + losers)

    # refill safely
    if len(st.session_state.queue) >= 4:

        group = []

        for _ in range(4):
            group.append(st.session_state.queue.pop(0))

        teamA, teamB = build_balanced_teams(group)

        court["A"] = teamA
        court["B"] = teamB

    st.session_state.courts[idx] = court


def go_home():
    st.session_state.page = "home"


# =====================================================
# HOME PAGE
# =====================================================
if st.session_state.page == "home":

    st.title("🎾 Pickleball Stack App")

    c1, c2 = st.columns(2)

    if c1.button("🏟 Organizer", use_container_width=True):
        st.session_state.page = "organizer"

    if c2.button("👤 Player", use_container_width=True):
        st.session_state.page = "player"


# =====================================================
# PLAYER PAGE
# =====================================================
elif st.session_state.page == "player":

    st.button("⬅ Back Home", on_click=go_home)

    st.title("👤 Join Queue")

    name = st.text_input("Name")
    skill = st.selectbox("Skill", SKILLS)

    if st.button("Join") and name:
        st.session_state.queue.append({"name": name, "skill": skill})
        st.success("Added!")


# =====================================================
# ORGANIZER PAGE
# =====================================================
elif st.session_state.page == "organizer":

    st.button("⬅ Back Home", on_click=go_home)

    st.title("🏟 Pickleball Auto Stack")

    # --------------------
    # SIDEBAR
    # --------------------
    with st.sidebar:

        st.subheader("Add Player")

        name = st.text_input("Name")
        skill = st.selectbox("Skill", SKILLS, key="side")

        if st.button("Add") and name:
            st.session_state.queue.append({"name": name, "skill": skill})

        st.divider()

        if st.button("Start Games"):
            start_games()

    # --------------------
    # QUEUE
    # --------------------
    st.subheader("⏳ Waiting Queue")

    if st.session_state.queue:
        st.write(", ".join(show(p) for p in st.session_state.queue))
    else:
        st.success("No players waiting 🎉")

    st.divider()

    # --------------------
    # COURTS
    # --------------------
    st.subheader("🏟 Live Courts")

    if not st.session_state.courts:
        st.info("Press Start Games")

    else:
        for i, court in enumerate(st.session_state.courts):

            with st.container(border=True):

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
