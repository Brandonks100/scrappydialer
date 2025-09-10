import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

from validators import validate_leads, validate_dids
from queue_builder import build_round_robin_queue
# from workers.fake_worker import run as run_fake_worker


# --- page setup ---
st.set_page_config(page_title="📞 Scrappy Dialer", layout="wide")
st.title("📞 Scrappy Dialer")

# --- session state ---
if "queue" not in st.session_state:
    st.session_state["queue"] = None
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "builder"
if "campaigns" not in st.session_state:
    st.session_state["campaigns"] = []
if "viewing_campaign" not in st.session_state:
    st.session_state["viewing_campaign"] = None
if "view_mode" not in st.session_state:
    st.session_state["view_mode"] = None  # "scheduled_detail" | "launched_detail"
if "dispositions" not in st.session_state:
    st.session_state["dispositions"] = [
        {"name": "Qualified", "tags": ["interested", "warm lead"], "action": "Send to CRM"},
        {"name": "Not Interested", "tags": ["do not call"], "action": "Mark DNC"},
        {"name": "Hang Up", "tags": ["dropped"], "action": "Log Only"},
        {"name": "Callback", "tags": ["retry", "call later"], "action": "Add to Retry Queue"}
    ]
if "classification_prompt" not in st.session_state:
    st.session_state["classification_prompt"] = (
        "Classify call outcomes based on transcript. "
        "Use dispositions: Qualified, Not Interested, Hang Up, Callback."
    )

days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# --- tab ordering ---
builder_tab, manager_tab, dispo_tab = st.tabs(["📋 Campaign Builder", "📊 Campaign Manager", "🎯 Disposition Manager"])
