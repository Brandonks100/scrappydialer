import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

from services.validators import validate_leads, validate_dids
from services.queue_builder import build_round_robin_queue
from workers.fake_worker import run as run_fake_worker

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

# =========================
#      CAMPAIGN BUILDER
# =========================
with builder_tab:
    st.subheader("🛠 Campaign Builder")

    # inputs
    campaign_name = st.text_input("Campaign Name", placeholder="Austin-PW", key="builder_name")
    leads_file = st.file_uploader("Upload Leads CSV", type=["csv"], key="builder_leads")
    num_dids = st.number_input("How many DIDs?", min_value=1, max_value=100, value=3, key="builder_didcount")
    dids_text = st.text_area("Paste DIDs (one per line)", placeholder="15551234567\n15552345678\n15553456789", key="builder_dids")

    st.markdown("### Campaign Rules")
    max_concurrent = st.number_input("Max Concurrent Calls", 1, 100, 5, key="builder_maxconcurrent")
    pacing = st.number_input("Pacing (seconds between calls)", 1, 60, 5, key="builder_pacing")
    max_attempts = st.number_input("Max Attempts per Lead", 1, 10, 3, key="builder_maxattempts")
    retry1 = st.number_input("Time Between Retry 1 (minutes)", 1, 120, 15, key="builder_retry1")
    retry2 = st.number_input("Time Between Retry 2 (minutes)", 1, 240, 60, key="builder_retry2")
    allowed_days = st.multiselect("Allowed Days", options=days_of_week, default=days_of_week, key="builder_days")

    st.markdown("### Quiet Hours")
    quiet_start = st.time_input("Quiet Hours Start", value=None, key="builder_quietstart")
    quiet_end = st.time_input("Quiet Hours End", value=None, key="builder_quietend")
    timezones = pytz.all_timezones
    default_tz_idx = timezones.index("US/Central") if "US/Central" in timezones else 0
    quiet_tz = st.selectbox("Quiet Hours Time Zone", options=timezones, index=default_tz_idx, key="builder_quiettz")

    # campaign preview
    st.subheader("📋 Campaign Preview")

    leads_df, dids_df = None, None
    if leads_file is not None:
        leads_df = pd.read_csv(leads_file)
        if validate_leads(leads_df):
            st.error("❌ Leads file invalid")
            leads_df = None

    if dids_text.strip():
        dids_list = [line.strip() for line in dids_text.splitlines() if line.strip()]
        dids_df = pd.DataFrame({"did": dids_list})
        if validate_dids(dids_df):
            st.error("❌ DIDs invalid")
            dids_df = None

    if leads_df is not None and dids_df is not None:
        queue_df = build_round_robin_queue(leads_df, dids_df, max_attempts=max_attempts)

        config = {
            "name": campaign_name,
            "lead_count": len(leads_df),
            "max_concurrent": max_concurrent,
            "pacing": pacing,
            "max_attempts": max_attempts,
            "retry1": retry1,
            "retry2": retry2,
            "allowed_days": allowed_days,
            "quiet_hours": {"start": str(quiet_start), "end": str(quiet_end), "timezone": quiet_tz},
            "dids": dids_df["did"].tolist(),
            "queue": queue_df,
            "status": "Draft",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        st.success(f"✅ Campaign ready: {campaign_name} ({len(leads_df)} leads, {len(dids_df)} DIDs)")
        st.dataframe(queue_df.head(10), use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 Launch Campaign Now", key="builder_launchnow"):
                config["status"] = "Launched"
                st.session_state["campaigns"].append(config)
                st.session_state["active_tab"] = "manager"
                st.rerun()
        with col2:
            scheduled_date = st.date_input("Schedule Launch Date", key="builder_sched_date")
            scheduled_time = st.time_input("Schedule Launch Time", key="builder_sched_time")
            scheduled_tz = st.selectbox("Schedule Time Zone", options=timezones, index=default_tz_idx, key="builder_sched_tz")
            if st.button("📅 Schedule Launch", key="builder_schedule"):
                config["status"] = "Scheduled"
                config["scheduled_for"] = {
                    "date": str(scheduled_date),
                    "time": str(scheduled_time),
                    "timezone": scheduled_tz,
                }
                st.session_state["campaigns"].append(config)
                st.session_state["active_tab"] = "manager"
                st.rerun()

# =========================
#      CAMPAIGN MANAGER
# =========================
with manager_tab:
    # (unchanged manager code goes here...)
    # keep your existing detail and tables logic
    pass

# =========================
#   DISPOSITION MANAGER
# =========================
with dispo_tab:
    st.subheader("🎯 Disposition Manager (Global Settings)")
    st.write("Configure how AI classifies call outcomes. All campaigns use these dispositions.")

    # Classification Prompt
    st.session_state["classification_prompt"] = st.text_area(
        "Classification Prompt for AI",
        value=st.session_state["classification_prompt"]
    )

    # Disposition Table
    st.markdown("### Configured Dispositions")
    for i, dispo in enumerate(st.session_state["dispositions"]):
        cols = st.columns([2, 3, 2, 1])
        with cols[0]:
            st.text_input("Disposition", value=dispo["name"], key=f"name_{i}")
        with cols[1]:
            tags_str = ", ".join(dispo["tags"])
            new_tags = st.text_input("Tags (comma-separated)", value=tags_str, key=f"tags_{i}")
            st.session_state["dispositions"][i]["tags"] = [t.strip() for t in new_tags.split(",") if t.strip()]
        with cols[2]:
            st.selectbox(
                "Action",
                ["Send to CRM", "Mark DNC", "Log Only", "Add to Retry Queue", "Custom"],
                index=["Send to CRM", "Mark DNC", "Log Only", "Add to Retry Queue", "Custom"].index(dispo["action"]),
                key=f"action_{i}"
            )
        with cols[3]:
            if st.button("🗑️", key=f"delete_{i}"):
                st.session_state["dispositions"].pop(i)
                st.experimental_rerun()

    # Add new disposition button
    if st.button("+ Add Disposition"):
        st.session_state["dispositions"].append({"name": "New Disposition", "tags": [], "action": "Log Only"})

    st.success("✅ These dispositions apply globally to all campaigns.")
