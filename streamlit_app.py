import streamlit as st
from collections import deque

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(page_title="Pickleball Auto Stack", layout="wide")

st.title("🎾 Pickleball Auto Stack")
st.caption("First come • first play • fair rotation")

# ======================================================
# SMALL SUPERSCRIPT NUMBERS
# ======================================================
SUPERSCRIPT = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def small(n: int):
    return str(n).translate(SUPERSCRIPT)


# ======================================================
# PLAYER FORMAT
# player = [name, games]
# ======================================================
def fmt(player):
    name, games = player
    return f"🔴 {small(games)} {name}"


# ======================================================
# INIT SESSION
# ======================================================
if "queue" not in st.session_state:
    names = [
        "Wyben","Matet B","Pash","Jaime C.","Abe","Star","Ben(nathans+1)",
        "Chian C","Tim C","Edelyn","Roselyn","Ryan","Virgilio DR","Zulficar",
        "Honey Grace","Ally A","Miller C","Jan Ang","Arthur R","Dale Johnson",
        "lahleah Besas J","Noven","Geoffrey","Christian Jay P","Nen","Eduard P",
        "Neil","Franz","Ann (nathans+1)","Job","Sam Jonne B","Reynalyn",
        "Nathan","Blyss","Ting Y","Jad A","Marie Noelle","Han MT","Klark",
        "Joven Clark","Arthur DG","ASH","Enzo S","Bing A","Pao M","Anne C","Coach Chris"
    ]

    st.session_state.queue = deque([[n, 0] for n in names])
    st.session_state.court = []
    st.session_state.playing = False


# ======================================================
# BUTTONS
# ======================================================
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("▶ Start Game"):
        if len(st.session_state.queue) >= 4:
            st.session_state.court = [
                st.session_state.queue.popleft()
                for _ in range(4)
            ]
            st.session_state.playing = True

with col2:
    if st.button("🏁 Submit Score"):
        if st.session_state.court:
            # +1 game each player
            for p in st.session_state.court:
                p[1] += 1

            # return to queue
            st.session_state.queue.extend(st.session_state.court)
            st.session_state.court = []
            st.session_state.playing = False

with col3:
    if st.button("🔄 Reset"):
        st.session_state.queue = deque([[p[0], 0] for p in st.session_state.queue] +
                                       [[p[0], 0] for p in st.session_state.court])
        st.session_state.court = []
        st.session_state.playing = False


st.divider()

# ======================================================
# WAITING QUEUE
# ======================================================
st.subheader("⏳ Waiting Queue")

st.markdown(
    ", ".join(fmt(p) for p in st.session_state.queue)
)


# ======================================================
# COURT
# ======================================================
st.divider()
st.subheader("🏟 Court 1")

if st.session_state.court:

    teamA = st.session_state.court[:2]
    teamB = st.session_state.court[2:]

    st.markdown(f"**Team A:** {fmt(teamA[0])} & {fmt(teamA[1])}")
    st.markdown(f"**Team B:** {fmt(teamB[0])} & {fmt(teamB[1])}")

    st.divider()

    # ==================================================
    # MANUAL SWAP SYSTEM
    # ==================================================
    st.subheader("🔁 Manual Swap Player")

    queue_names = [p[0] for p in st.session_state.queue]
    court_names = [p[0] for p in st.session_state.court]

    c1, c2 = st.columns(2)

    with c1:
        out_player = st.selectbox("Replace OUT", court_names)

    with c2:
        in_player = st.selectbox("Replace WITH", queue_names)

    if st.button("Swap Players"):
        # find indexes
        out_idx = next(i for i, p in enumerate(st.session_state.court) if p[0] == out_player)
        in_idx = next(i for i, p in enumerate(st.session_state.queue) if p[0] == in_player)

        # swap
        st.session_state.court[out_idx], st.session_state.queue[in_idx] = \
            st.session_state.queue[in_idx], st.session_state.court[out_idx]

        st.rerun()

else:
    st.info("Press ▶ Start Game to assign players.")
