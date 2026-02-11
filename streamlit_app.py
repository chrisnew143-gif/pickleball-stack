import streamlit as st
import random
from collections import deque

# =========================================================
# PAGE
# =========================================================
st.set_page_config(page_title="Pickleball Auto Stack", layout="wide")
st.title("🎾 Pickleball Auto Stack")
st.caption("First come • first play • fair rotation")

# =========================================================
# SESSION STATE
# =========================================================
if "queue" not in st.session_state:
    st.session_state.queue = deque()

if "courts" not in st.session_state:
    st.session_state.courts = [
        {"teams": None, "locked": False},
        {"teams": None, "locked": False},
    ]


# =========================================================
# PLAYER HELPERS
# =========================================================
def category(name):
    if name.lower().startswith("b"):
        return "B"
    if name.lower().startswith("n"):
        return "N"
    if name.lower().startswith("i"):
        return "I"
    return "B"


def valid_pair(p1, p2):
    c1, c2 = category(p1), category(p2)

    # Beginner ❌ Intermediate
    if (c1 == "B" and c2 == "I") or (c1 == "I" and c2 == "B"):
        return False

    return True


def valid_match(teamA, teamB):
    for p1 in teamA:
        for p2 in teamB:
            if not valid_pair(p1, p2):
                return False
    return True


def find_match():
    players = list(st.session_state.queue)

    if len(players) < 4:
        return None

    for _ in range(100):
        sample = random.sample(players, 4)
        tA = sample[:2]
        tB = sample[2:]

        if valid_pair(*tA) and valid_pair(*tB) and valid_match(tA, tB):
            return tA, tB

    return None


def fill_courts():
    for court in st.session_state.courts:
        if court["locked"]:
            continue

        match = find_match()
        if not match:
            return

        tA, tB = match

        for p in tA + tB:
            st.session_state.queue.remove(p)

        court["teams"] = (tA, tB)
        court["locked"] = True


# =========================================================
# ADD PLAYER (front of queue)
# =========================================================
st.subheader("➕ Add Player")

c1, c2 = st.columns([3, 1])

with c1:
    name = st.text_input("Player name (b/n/i prefix)")

with c2:
    if st.button("Add", use_container_width=True):
        if name:
            st.session_state.queue.appendleft(name)


# =========================================================
# WAITING QUEUE
# =========================================================
st.subheader("⏳ Waiting Queue")
st.write(", ".join(st.session_state.queue) if st.session_state.queue else "Empty")


# =========================================================
# AUTO FILL COURTS
# =========================================================
fill_courts()


# =========================================================
# COURTS UI (SIDE BY SIDE + COMPACT)
# =========================================================
st.subheader("🏟 Live Courts")

col_left, col_right = st.columns(2)


def show_court(idx, column):
    court = st.session_state.courts[idx]

    with column:
        st.markdown(f"### Court {idx+1}")

        if not court["teams"]:
            st.info("Waiting for players")
            return

        tA, tB = court["teams"]

        st.write(f"**A:** {tA[0]} & {tA[1]}")
        st.write(f"**B:** {tB[0]} & {tB[1]}")

        s1, s2, s3 = st.columns([1, 1, 1])

        scoreA = s1.number_input(
            "A",
            key=f"a{idx}",
            min_value=0,
            max_value=21,
            step=1,
        )

        scoreB = s2.number_input(
            "B",
            key=f"b{idx}",
            min_value=0,
            max_value=21,
            step=1,
        )

        if s3.button("Submit", key=f"submit{idx}"):

            winner = tA if scoreA > scoreB else tB
            loser = tB if scoreA > scoreB else tA

            # Winner front, loser back
            for p in winner:
                st.session_state.queue.appendleft(p)

            for p in loser:
                st.session_state.queue.append(p)

            court["teams"] = None
            court["locked"] = False

            st.session_state[f"a{idx}"] = 0
            st.session_state[f"b{idx}"] = 0

            st.rerun()


show_court(0, col_left)
show_court(1, col_right)
