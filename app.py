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
if "campaigns" not in st.session_state:
    st.session_state["campaigns"] = []

# =========================
#      CAMPAIGN BUILDER
# =========================
st.subheader("🛠 Campaign Builder (Simulation)")

# Simulate campaign creation
if st.button("➕ Simulate Campaign Creation"):
    campaign_id = len(st.session_state["campaigns"]) + 1
    fake_campaign = {
        "id": campaign_id,
        "name": f"Test Campaign {campaign_id}",
        "status": "Scheduled",
        "leads": 10,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    st.session_state["campaigns"].append(fake_campaign)
    st.success(f"Campaign {campaign_id} created and scheduled ✅")

# Simulate campaign launch
if st.button("🚀 Simulate Campaign Launch"):
    if st.session_state["campaigns"]:
        st.session_state["campaigns"][-1]["status"] = "Running"
        st.info(f"Campaign {st.session_state['campaigns'][-1]['id']} is now running…")
    else:
        st.warning("No campaigns available to launch.")

# Simulate calls
if st.button("📞 Simulate Calls"):
    if st.session_state["campaigns"]:
        current = st.session_state["campaigns"][-1]
        if current["status"] == "Running":
            results = []
            for i in range(current["leads"]):
                result = ["Answered ✅", "No Answer ❌", "Busy 🔁"][i % 3]
                results.append(f"Lead {i+1}: {result}")
            st.write("\n".join(results))
            current["status"] = "Completed"
            st.success(f"Campaign {current['id']} completed! ✅")
        else:
            st.warning("Please launch a campaign before simulating calls.")
    else:
        st.warning("No campaigns to simulate.")

# =========================
#   CAMPAIGN DASHBOARD
# =========================
st.subheader("📊 Campaign Dashboard")
if st.session_state["campaigns"]:
    st.table(pd.DataFrame(st.session_state["campaigns"]))
else:
    st.write("No campaigns created yet.")
