import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# 1. PAGE CONFIG (Branding)
st.set_page_config(page_title="Heritage Harvest Sales Portal", page_icon="🥔")

# 2. CONNECT TO CLOUD DATA
def get_data():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("Heritage_Harvest_Pricing").sheet1
    return pd.DataFrame(sheet.get_all_records())

# 3. BUILD THE UI
st.title("🥔 Heritage Harvest Sales Portal")
st.markdown("### Trade Spend & Margin Auditor")

try:
    df = get_data()
    
    # Sidebar for Inputs
    st.sidebar.header("Negotiation Parameters")
    selected_product = st.sidebar.selectbox("Select SKU", df['product_name'].tolist())
    requested_discount = st.sidebar.slider("Requested Discount (%)", 0, 40, 15) / 100

    # Pull data for the selected SKU
    sku_info = df[df['product_name'] == selected_product].iloc[0]
    
    # Audit Logic
    lp = float(sku_info['list_price'])
    cogs = float(sku_info['cogs'])
    net_price = lp * (1 - requested_discount)
    margin = (net_price - cogs) / net_price
    
    # Validation
    is_valid_discount = requested_discount <= float(sku_info['max_allowable_discount'])
    is_valid_margin = margin >= float(sku_info['min_margin_threshold'])

    # Display Results
    col1, col2, col3 = st.columns(3)
    col1.metric("List Price", f"${lp:.2f}")
    col2.metric("Net Price", f"${net_price:.2f}")
    col3.metric("Projected Margin", f"{margin:.1%}")

    if is_valid_discount and is_valid_margin:
        st.success(f"✅ **APPROVED:** This deal meets Heritage Harvest commercial guidelines.")
        if st.button("Send Approval Email to Buyer"):
            # We will link this to your send_summary_email function later
            st.info("Emailing John Bridges...")
    else:
        st.error(f"❌ **DENIED:** This deal falls below margin thresholds.")
        st.warning(f"Required Margin: {float(sku_info['min_margin_threshold']):.1%}")

    # Show the "Master Data" for this SKU for transparency
    with st.expander("View SKU Technical Details"):
        st.write(f"**UPC:** {sku_info['upc']}")
        st.write(f"**SKU ID:** {sku_info['sku_id']}")

except Exception as e:
    st.error(f"Error connecting to Cloud Database: {e}")