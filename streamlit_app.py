import streamlit as st
import random
from collections import deque
import pandas as pd
from itertools import combinations
import json
import os
import time

# ======================================================
# CONFIG & FILE PATHS
# ======================================================
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
QUEUE_FILE = os.path.join(DATA_DIR, "queue.json")
PLAYERS_FILE = os.path.join(DATA_DIR, "players.json")
COURTS_FILE = os.path.join(DATA_DIR, "courts.json")
SCORES_FILE = os.path.join(DATA_DIR, "scores.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")

# ======================================================
# PERSISTENCE FUNCTIONS
# ======================================================
def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

def persist_state():
    ss = st.session_state
    save_json(QUEUE_FILE, list(ss.queue))
    save_json(PLAYERS_FILE, ss.players)
    save_json(COURTS_FILE, {k: v for k,v in ss.courts.items()})
    save_json(SCORES_FILE, ss.scores)
    save_json(HISTORY_FILE, ss.history)

# ======================================================
# AUTO-SAVE EVERY 10 SECONDS
# ======================================================
AUTO_SAVE_INTERVAL = 10  # seconds

if "last_save_time" not in st.session_state:
    st.session_state.last_save_time = time.time()
else:
    if time.time() - st.session_state.last_save_time > AUTO_SAVE_INTERVAL:
        persist_state()
        st.session_state.last_save_time = time.time()
        st.info("💾 Auto-saved data")
