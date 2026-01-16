import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from rapidfuzz import process, fuzz

# --- JBridges Consulting | Brand Header ---
st.set_page_config(page_title="Heritage Harvest | Audit Portal", page_icon="📊")
st.title("JBridges Consulting | Heritage Harvest 📊")
st.markdown("### Automated Sales & Trade Audit Portal")

# --- 1. SECURE AUTHENTICATION (The Cloud Bridge) ---
@st.cache_resource
def get_gspread_client():
    # Fetch credentials from Streamlit Cloud Secrets (NOT a local file)
    try:
        creds_info = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(
            creds_info,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
        )
        service = build('sheets', 'v4', credentials=credentials)
        return service
    except Exception as e:
        st.error(f"Authentication Error: {e}")
        return None

# --- 2. DATA ACQUISITION ---
def load_data():
    service = get_gspread_client()
    if not service: return pd.DataFrame()
    
    # Replace with your actual Spreadsheet ID from your URL
    SPREADSHEET_ID = '1X58_331T9eC3UAnD7G1_Gv707Pz778_vXz7pW56G6q0' 
    RANGE_NAME = 'Sheet1!A:E' # Adjust to your sheet name/range
    
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME
    ).execute()
    
    values = result.get('values', [])
    if not values:
        return pd.DataFrame()
    
    return pd.DataFrame(values[1:], columns=values[0])

# --- 3. AUDIT LOGIC (Fuzzy Matching) ---
df = load_data()

if not df.empty:
    st.success("✅ Connected to Heritage Harvest Master Data")
    
    with st.sidebar:
        st.header("Search & Audit")
        user_input = st.text_input("Enter SKU Name or ID:")
        threshold = st.slider("Matching Sensitivity", 60, 100, 85)

    if user_input:
        # Match user input against the 'SKU Name' column
        choices = df['SKU Name'].tolist()
        results = process.extract(user_input, choices, scorer=fuzz.WRatio, limit=5)
        
        matches = [res for res in results if res[1] >= threshold]
        
        if matches:
            st.write(f"### Found {len(matches)} Potential Matches:")
            for match_name, score, idx in matches:
                item_data = df[df['SKU Name'] == match_name].iloc[0]
                with st.expander(f"{match_name} (Match Score: {int(score)}%)"):
                    st.write(f"**SKU ID:** {item_data.get('SKU ID', 'N/A')}")
                    st.write(f"**UPC:** {item_data.get('UPC', 'N/A')}")
                    st.write(f"**Standard Price:** ${item_data.get('Price', '0.00')}")
        else:
            st.warning("No matches found. Try lowering the sensitivity.")
else:
    st.info("Awaiting connection to Master Data...")

# --- Footer ---
st.divider()
st.caption("JBridges Consulting | Proprietary Commercial Audit Logic v1.0")