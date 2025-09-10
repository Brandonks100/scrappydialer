import pandas as pd

def build_round_robin_queue(leads_df: pd.DataFrame, dids_df: pd.DataFrame, max_attempts: int = 3) -> pd.DataFrame:
    """
    Build a dialing queue by pairing leads with DIDs in round-robin style.

    Args:
        leads_df (pd.DataFrame): DataFrame of leads, must include `phone`.
        dids_df (pd.DataFrame): DataFrame of DIDs, must include `did`.
        max_attempts (int): Maximum number of attempts allowed per lead.

    Returns:
        pd.DataFrame: Queue DataFrame with lead → DID assignment and metadata.
    """
    # extract values
    leads = leads_df["phone"].tolist()
    dids = dids_df["did"].tolist()

    # round-robin assignment
    queue_data = []
    for i, lead_phone in enumerate(leads):
        assigned_did = dids[i % len(dids)]
        queue_data.append({
            "lead_phone": lead_phone,
            "did": assigned_did,
            "attempt": 0,
            "max_attempts": max_attempts,
            "status": "queued",
            "disposition": None,
            "last_attempt_time": None,
            "notes": None,
            "recording_link": None
        })

    return pd.DataFrame(queue_data)