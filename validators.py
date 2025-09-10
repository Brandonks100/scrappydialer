import pandas as pd

# expected columns
REQUIRED_LEAD_COLS = ["first_name","last_name","phone","address","city","state","zip"]
REQUIRED_DID_COLS  = ["did"]

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Make column names flexible:
    - lowercases everything
    - strips spaces
    - replaces spaces with underscores
    """
    df = df.copy()
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    return df

def validate_leads(df: pd.DataFrame) -> list[str]:
    df = normalize_columns(df)
    errors = []
    for col in REQUIRED_LEAD_COLS:
        if col not in df.columns:
            errors.append(f"Missing lead column: {col}")
    if "phone" in df and not df["phone"].astype(str).str.fullmatch(r"\d{11}").all():
        errors.append("All lead phone numbers must be 11 digits (e.g., 15551234567).")
    return errors

def validate_dids(df: pd.DataFrame) -> list[str]:
    df = normalize_columns(df)
    errors = []
    for col in REQUIRED_DID_COLS:
        if col not in df.columns:
            errors.append(f"Missing DID column: {col}")
    if "did" in df and not df["did"].astype(str).str.fullmatch(r"\d{11}").all():
        errors.append("All DIDs must be 11 digits (e.g., 15557654321).")
    return errors