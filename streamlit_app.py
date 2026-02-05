import streamlit as st
import random

st.set_page_config(page_title="Pickleball Auto Stack", layout="wide")

# =====================================================
# INIT STATE (ONLY RUNS ONCE)
# =====================================================
def init():
    if "page" not in st.session_state:
        st.session_state.page = "home"

    if "players" not in st.session_state:
        st.session_state.players = []

    if "queue" not in st.session_state:
        st.session_state.queue = []

    if "courts" not in st.session_state:
        st.session_state.courts = []

init()


# =====================================================
# HELPERS
# =====================================================

def go_home():
    st.session_state.page = "home"


def start_games():
    """Shuffle ONCE only when starting"""
    q = st.session_state.queue.copy()
    random.shuffle(q)

    courts = []
    while len(q) >= 4:
        courts.append({
            "A": [q.pop(), q.pop()],
            "B": [q.pop(), q.pop()]
        })

    st.session_state.courts = courts
    st.session_state.queue = q


def finish_match(court_index, winner):
    """NO reshuffle — only rotate players"""
    court = st.session_state.courts[court_index]

    winners = court[winner]
    losers = court["A" if winner == "B" else "B"]

    # winners stay
    # losers go back queue
    st.session_state.queue.extend(losers)

    # replace losers from queue if possible
    if len(st.session_state.queue) >= 2:
        court["A" if winner == "B" else "B"] = [
            st.session_state.queue.pop(0),
            st.session_state.queue.pop(0)
        ]

    st.session_state.courts[court_index] = court


# =====================================================
# HOME PAGE
# =====================================================
if st.session_state.page == "home":

    st.title("🎾 Pickleball Stack App")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🏟 Organizer", use_container_width=True):
            st.session_state.page = "organizer"

    with col2:
        if st.button("👤 Player", use_container_width=True):
            st.session_state.page = "player"


# =====================================================
# PLAYER PAGE
# =====================================================
elif st.session_state.page == "player":

    st.button("⬅ Back Home", on_click=go_home)

    st.title("👤 Join Queue")

    name = st.text_input("Your name")

    if st.button("Join"):
        if name and name not in st.session_state.queue:
            st.session_state.queue.append(name)
            st.success("Added to queue!")


# =====================================================
# ORGANIZER PAGE
# =====================================================
elif st.session_state.page == "organizer":

    st.button("⬅ Back Home", on_click=go_home)

    st.title("🏟 Pickleball Auto Stack")

    # --------------------------
    # ADD PLAYER
    # --------------------------
    with st.sidebar:
        st.subheader("Add Player")
        new_player = st.text_input("Name")

        if st.button("Add"):
            if new_player:
                st.session_state.queue.append(new_player)

        st.divider()

        if st.button("Start Games"):
            start_games()

    # --------------------------
    # QUEUE
    # --------------------------
    st.subheader("⏳ Waiting Queue")

    if st.session_state.queue:
        st.write(", ".join(st.session_state.queue))
    else:
        st.success("No players waiting 🎉")

    st.divider()

    # --------------------------
    # COURTS
    # --------------------------
    st.subheader("🏟 Live Courts")

    if not st.session_state.courts:
        st.info("Press Start Games")
    else:
        for i, court in enumerate(st.session_state.courts):

            with st.container(border=True):

                st.markdown(f"### Court {i+1}")

                c1, c2, c3 = st.columns([3,3,2])

                with c1:
                    st.write("**Team A**")
                    st.write(" & ".join(court["A"]))

                with c2:
                    st.write("**Team B**")
                    st.write(" & ".join(court["B"]))

                with c3:
                    if st.button("Winner A", key=f"A{i}"):
                        finish_match(i, "A")

                    if st.button("Winner B", key=f"B{i}"):
                        finish_match(i, "B")
