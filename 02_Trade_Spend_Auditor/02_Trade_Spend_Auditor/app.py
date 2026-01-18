import streamlit as st
import pandas as pd
import smtplib
from email.message import EmailMessage
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- PAGE CONFIG ---
st.set_page_config(page_title="Heritage Harvest | Audit Portal", page_icon="📊", layout="wide")
st.title("Heritage Harvest 📊")
st.markdown("### Automated Sales & Trade Audit Portal")

# --- 1. HARDENED AUTH (FIXES SSL WRONG_VERSION_NUMBER) ---
@st.cache_resource
def get_gspread_client():
    try:
        creds_info = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(
            creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
        )
        # Using discoveryServiceUrl forces a modern HTTPS endpoint to bypass local SSL decryption errors
        return build('sheets', 'v4', credentials=credentials, 
                     discoveryServiceUrl="https://sheets.googleapis.com/$discovery/rest?version=v4")
    except Exception as e:
        st.error(f"Authentication Error: {e}")
        return None

# --- 2. EMAIL ENGINE (EXPLICIT SKU ID LABELS) ---
def send_buyer_approval_email(approved_df, recipient_name, recipient_email):
    sender_email = "jbconsultingdemo@gmail.com"
    app_password = "hryfpqvirwvxjkhc" 
    
    msg = EmailMessage()
    msg['Subject'] = "✔️ Approval: Heritage Harvest Items Cleared for Planning"
    msg['From'] = f"Jenica Bridges <{sender_email}>"
    msg['To'] = f"{recipient_name} <{recipient_email}>"

    # BUILD ITEM LIST WITH PROFESSIONAL "SKU ID" LABEL
    item_rows = [
        f"- SKU ID: {row['sku_id']} | UPC: {row['upc']} | {row['product_name']}"
        for _, row in approved_df.iterrows()
    ]
    
    body = f"Hi {recipient_name},\n\nThe following Heritage Harvest items are approved for planning:\n\n{chr(10).join(item_rows)}\n\nBest Regards,\nJenica"
    msg.set_content(body)
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.starttls()
            smtp.login(sender_email, app_password)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.sidebar.error(f"Email failure: {e}")
        return False

# --- 3. LIVE DATA LOAD & MARGIN FIX ---
def load_data():
    service = get_gspread_client()
    if not service: return pd.DataFrame()
    SPREADSHEET_ID = '1aX-RfPcICG1H6llj9TeKJ9E3UeXnkOW02HARDnqUlvY'
    try:
        # Pulling fresh data from Google Sheets
        result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range='A:I').execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        
        df = pd.DataFrame(values[1:], columns=values[0])
        df = df[df['product_name'].notna()]
        
        # Numeric conversion for Audit Math
        for col in ['list_price', 'cogs', 'min_margin_threshold']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # MARGIN MATH + UNIFORM FORMAT (e.g. 59.2%)
        df['Calculated_Margin'] = (df['list_price'] - df['cogs']) / df['list_price']
        # Converting to string ensures Streamlit doesn't mess up formatting to 0.6%
        df['Margin_Display'] = df['Calculated_Margin'].apply(lambda x: f"{x*100:.1f}%" if pd.notnull(x) else "0.0%")
        
        df['Audit_Status'] = df.apply(lambda r: "APPROVED" if r['Calculated_Margin'] >= r['min_margin_threshold'] else "REJECTED", axis=1)
        return df
    except Exception as e:
        # Catching the SSL error here
        st.error(f"Data Load Error: {e}")
        return pd.DataFrame()

# --- 4. INTERFACE ---
df = load_data()

if not df.empty:
    if st.sidebar.button("🔄 Sync with Google Sheets"):
        st.rerun()
    
    st.sidebar.header("Audit Controls")
    product_list = sorted(df['product_name'].unique())
    selected = st.sidebar.multiselect("Select Products:", options=["SELECT ALL"] + product_list, default=["SELECT ALL"])
    display_df = df if "SELECT ALL" in selected else df[df['product_name'].isin(selected)]

    recipient_name = st.sidebar.text_input("Buyer Name", value="Buyer Name")
    recipient_email = st.sidebar.text_input("Buyer Email", value="buyer@heritageharvest.com")
    
    if st.sidebar.button("📧 Send Approval Email"):
        approved_only = display_df[display_df['Audit_Status'] == "APPROVED"]
        if not approved_only.empty:
            if send_buyer_approval_email(approved_only, recipient_name, recipient_email):
                st.sidebar.success(f"Sent to {recipient_name}!")

    # Restored Download Button
    excel_data = display_df[['sku_id', 'upc', 'product_name', 'Audit_Status']].to_csv(index=False).encode('utf-8-sig')
    st.sidebar.download_button(label="📥 Download Excel Audit", data=excel_data, file_name=f"Audit.csv")

    # Main Dashboard Table
    st.success("✅ Audit Logic Active")
    st.dataframe(
        display_df[['Audit_Status', 'sku_id', 'upc', 'product_name', 'list_price', 'Margin_Display']], 
        use_container_width=True, hide_index=True,
        column_config={
            "sku_id": "SKU ID",
            "upc": "UPC",
            "list_price": st.column_config.NumberColumn("Price", format="$%.2f"),
            "Margin_Display": "Calculated Margin"
        }
    )