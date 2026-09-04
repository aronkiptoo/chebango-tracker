"""
Chebango Tracker - Fixed Version (handles corrupted stock.json)
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json
from io import BytesIO
import base64
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Chebango Tracker",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- CSS ----------
st.markdown("""
<style>
    .stApp { background-color: #f4f1e8; }
    [data-testid="stSidebar"] { background-color: #1b4332; }
    [data-testid="stSidebar"] * { color: #ecf0f1 !important; }
    [data-testid="stMetricValue"] { color: #1b4332 !important; font-weight: 700 !important; }
    [data-testid="stMetricLabel"] { color: #1b4332 !important; font-weight: 600 !important; }
    h1, h2, h3, p, label, .stMarkdown { color: #1b4332 !important; }
    .stButton > button {
        background-color: #ffffff;
        color: #1b4332 !important;
        border: 2px solid #2d6a4f;
        border-radius: 8px;
        font-weight: 600;
    }
    .stButton > button:hover {
        background-color: #e8f5e9;
        border: 2px solid #1b4332;
        color: #1b4332 !important;
    }
    @media print {
        .stApp > header, .stSidebar, .stButton, .stRadio, 
        .stFileUploader, .stCameraInput, .stSelectbox, 
        .stTextInput, .stNumberInput, .stForm {
            display: none !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# ---------- PATHS ----------
DATA_DIR = "data"
STOCK_FILE = os.path.join(DATA_DIR, "stock.json")
FARMERS_FILE = os.path.join(DATA_DIR, "farmers.csv")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

os.makedirs(DATA_DIR, exist_ok=True)

# ---------- PRODUCTS ----------
PRODUCTS = [
    "Agripest Organic (250ml Bottle)",
    "Agripest Organic (500ml Bottle)",
    "Agripest Organic (1L Bottle)",
    "Flower Dust (1kg Bag)",
    "Flower Dust (5kg Bag)"
]

# ---------- HELPERS ----------
def load_users():
    default_users = {
        "254701593581": {
            "password": "1234",
            "name": "Caroline Cherotich",
            "department": "Accountant",
            "must_change_password": True
        },
        "254724334842": {
            "password": "1234",
            "name": "Too Patrick",
            "department": "Field Manager",
            "must_change_password": True
        },
        "254769468742": {
            "password": "1234",
            "name": "Aron Yegon",
            "department": "ICT",
            "must_change_password": True
        }
    }
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump(default_users, f, indent=2)
        return default_users
    try:
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
        first_user = next(iter(users.values()))
        if "department" not in first_user:
            with open(USERS_FILE, "w") as f:
                json.dump(default_users, f, indent=2)
            return default_users
        return users
    except:
        with open(USERS_FILE, "w") as f:
            json.dump(default_users, f, indent=2)
        return default_users


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def load_stock():
    """Safe loader - recreates stock.json if it is missing or corrupted"""
    default_stock = {p: {"received": 0, "issued": 0, "available": 0} for p in PRODUCTS}

    if not os.path.exists(STOCK_FILE):
        with open(STOCK_FILE, "w") as f:
            json.dump(default_stock, f, indent=2)
        return default_stock

    try:
        with open(STOCK_FILE, "r") as f:
            content = f.read().strip()
            if not content:          # empty file
                raise ValueError("Empty file")
            stock = json.loads(content)

            # Make sure all products exist
            for p in PRODUCTS:
                if p not in stock:
                    stock[p] = {"received": 0, "issued": 0, "available": 0}
            return stock
    except Exception:
        # File is corrupted → recreate it
        with open(STOCK_FILE, "w") as f:
            json.dump(default_stock, f, indent=2)
        return default_stock


def save_stock(stock):
    with open(STOCK_FILE, "w") as f:
        json.dump(stock, f, indent=2)


def load_farmers():
    if not os.path.exists(FARMERS_FILE):
        df = pd.DataFrame(columns=[
            "Receipt_No", "Date", "Time", "Farmer_Name", "Grower_Number", "ID_Number", "Mobile",
            "Product", "Quantity", "Issued_By", "Department", "Issuer_Mobile"
        ])
        df.to_csv(FARMERS_FILE, index=False)
        return df
    return pd.read_csv(FARMERS_FILE)


def save_farmer(record):
    df = load_farmers()
    df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    df.to_csv(FARMERS_FILE, index=False)


def image_to_base64(uploaded_file):
    if uploaded_file is None:
        return None
    try:
        bytes_data = uploaded_file.getvalue()
        b64 = base64.b64encode(bytes_data).decode()
        return f"data:image/jpeg;base64,{b64}"
    except:
        return None


# ---------- SESSION ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "last_receipt" not in st.session_state:
    st.session_state.last_receipt = None


# ---------- LOGIN ----------
def show_login():
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center; margin-bottom:20px;">
            <h1 style="color:#27ae60;">🌱 Chebango Tracker</h1>
            <p>Product Issuance & Stock System</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            st.subheader("Sign in")
            mobile = st.text_input("Mobile number", placeholder="2547XXXXXXXX")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("SIGN IN", use_container_width=True)

            if submitted:
                users = load_users()
                if mobile in users and users[mobile]["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.user = {
                        "mobile": mobile,
                        "name": users[mobile]["name"],
                        "department": users[mobile]["department"],
                        "must_change_password": users[mobile].get("must_change_password", False)
                    }
                    st.success(f"Welcome {users[mobile]['name']}!")
                    st.rerun()
                else:
                    st.error("Invalid mobile number or password.")

        st.info("""
        **Default Password = 1234**  
        • Caroline Cherotich (Accountant) → `254701593581`  
        • Too Patrick (Field Manager) → `254724334842`  
        • Aron Yegon (ICT) → `254769468742`
        """)


def show_change_password():
    st.warning("⚠️ You are using the default password. Please change it now.")
    with st.form("change_pwd"):
        new_pwd = st.text_input("New Password", type="password")
        confirm = st.text_input("Confirm New Password", type="password")
        if st.form_submit_button("Change Password"):
            if new_pwd and new_pwd == confirm:
                users = load_users()
                users[st.session_state.user["mobile"]]["password"] = new_pwd
                users[st.session_state.user["mobile"]]["must_change_password"] = False
                save_users(users)
                st.session_state.user["must_change_password"] = False
                st.success("Password changed successfully!")
                st.rerun()
            else:
                st.error("Passwords do not match.")


def show_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="padding:10px 0; border-bottom:1px solid #34495e; margin-bottom:15px;">
            <h2 style="color:#27ae60; margin:0;">🌱 Chebango</h2>
            <p style="color:#bdc3c7; font-size:13px;">Tracker System</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"**{st.session_state.user['name']}**")
        st.caption(f"{st.session_state.user['department']}")
        st.caption(st.session_state.user['mobile'])
        st.markdown("---")

        menu = st.radio("Menu", [
            "🏠 Home",
            "📦 Receive Stock",
            "📊 View Stock",
            "👨‍🌾 Issue to Farmer",
            "🧾 Receipt",
            "📋 Farmers List",
            "📄 Reports"
        ], label_visibility="collapsed")

        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()
        return menu


# ---------- PAGES ----------
def page_home():
    st.title("Main Menu")
    st.caption(f"Welcome **{st.session_state.user['name']}** ({st.session_state.user['department']})")
    stock = load_stock()
    total = sum(v["available"] for v in stock.values())
    col1, col2, col3 = st.columns(3)
    col1.metric("Products", len(PRODUCTS))
    col2.metric("Total Available", f"{total:,}")
    col3.metric("Department", st.session_state.user["department"])


def page_receive_stock():
    st.title("📦 Receive Stock")
    stock = load_stock()
    with st.form("receive_form"):
        product = st.selectbox("Select Product", PRODUCTS)
        quantity = st.number_input("Quantity Received", min_value=1, value=10)
        if st.form_submit_button("✅ Confirm Receive Stock", use_container_width=True):
            stock[product]["received"] += quantity
            stock[product]["available"] += quantity
            save_stock(stock)
            st.success(f"Received **{quantity}** of **{product}**")
            st.balloons()


def page_view_stock():
    st.title("📊 View Stock")
    stock = load_stock()
    data = [{"Product": p, "Received": v["received"], "Issued": v["issued"], "Available": v["available"]} 
            for p, v in stock.items()]
    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
    total = sum(v["available"] for v in stock.values())
    st.metric("🟢 Total Available Stock", f"{total:,}")


def page_issue_to_farmer():
    st.title("👨‍🌾 Issue Product to Farmer")
    stock = load_stock()
    available_products = [p for p in PRODUCTS if stock[p]["available"] > 0]
    
    if not available_products:
        st.error("No stock available. Please receive stock first.")
        return

    with st.form("issue_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            farmer_name = st.text_input("Name of the Farmer *")
            grower_number = st.text_input("Grower Number *")
            id_number = st.text_input("ID Number *")
        with col2:
            mobile = st.text_input("Mobile Number *")
            product = st.selectbox("Select Product *", available_products)
            quantity = st.number_input("Quantity to Issue *", min_value=1, 
                                      max_value=stock[product]["available"], value=1)

        st.markdown("### ID Capture")
        st.caption("Choose Camera or Upload for both Front and Back")

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**ID Front**")
            front_method = st.radio("Front Method", ["📷 Camera", "📁 Upload"], 
                                    key="front_method", horizontal=True, label_visibility="collapsed")
            if front_method == "📷 Camera":
                id_front = st.camera_input("Take ID Front", key="cam_front")
            else:
                id_front = st.file_uploader("Upload ID Front", type=["jpg","jpeg","png"], key="up_front")

        with col_b:
            st.markdown("**ID Back**")
            back_method = st.radio("Back Method", ["📷 Camera", "📁 Upload"], 
                                   key="back_method", horizontal=True, label_visibility="collapsed")
            if back_method == "📷 Camera":
                id_back = st.camera_input("Take ID Back", key="cam_back")
            else:
                id_back = st.file_uploader("Upload ID Back", type=["jpg","jpeg","png"], key="up_back")

        submitted = st.form_submit_button("✅ Issue Product & Generate Receipt", use_container_width=True)

        if submitted:
            if not farmer_name or not grower_number or not id_number or not mobile:
                st.error("Please fill all required fields.")
            else:
                now = datetime.now()
                receipt_no = f"{now.strftime('%y%m%d%H%M')}"
                date_str = now.strftime("%d %b %Y %H:%M")
                time_str = now.strftime("%H:%M:%S")

                stock[product]["issued"] += quantity
                stock[product]["available"] -= quantity
                save_stock(stock)

                record = {
                    "Receipt_No": receipt_no,
                    "Date": now.strftime("%Y-%m-%d"),
                    "Time": time_str,
                    "Farmer_Name": farmer_name,
                    "Grower_Number": grower_number,
                    "ID_Number": id_number,
                    "Mobile": mobile,
                    "Product": product,
                    "Quantity": quantity,
                    "Issued_By": st.session_state.user["name"],
                    "Department": st.session_state.user["department"],
                    "Issuer_Mobile": st.session_state.user["mobile"]
                }
                save_farmer(record)

                st.session_state.last_receipt = {
                    "receipt_no": receipt_no,
                    "date_str": date_str,
                    "time_str": time_str,
                    "farmer_name": farmer_name,
                    "grower_number": grower_number,
                    "id_number": id_number,
                    "mobile": mobile,
                    "product": product,
                    "quantity": quantity,
                    "issued_by": st.session_state.user["name"],
                    "department": st.session_state.user["department"],
                    "issuer_mobile": st.session_state.user["mobile"],
                    "id_front_b64": image_to_base64(id_front),
                    "id_back_b64": image_to_base64(id_back)
                }

                st.success("✅ Product issued successfully! Go to **Receipt** menu to view and print.")
                st.balloons()


def render_professional_receipt(r):
    front_img = r.get("id_front_b64")
    back_img  = r.get("id_back_b64")

    front_html = f'<img src="{front_img}" style="max-width:260px; max-height:170px; border:1px solid #999;">' if front_img else '<div style="width:260px;height:150px;border:1px dashed #aaa;display:flex;align-items:center;justify-content:center;color:#888;font-size:13px;">No Front ID</div>'
    back_html  = f'<img src="{back_img}"  style="max-width:260px; max-height:170px; border:1px solid #999;">' if back_img else '<div style="width:260px;height:150px;border:1px dashed #aaa;display:flex;align-items:center;justify-content:center;color:#888;font-size:13px;">No Back ID</div>'

    details_rows = f"""
        <tr><td class="label">Farmer Name:</td><td>{r['farmer_name']}</td></tr>
        <tr><td class="label">ID Number:</td><td>{r['id_number']}</td></tr>
        <tr><td class="label">Grower Number:</td><td>{r['grower_number']}</td></tr>
        <tr><td class="label">Product:</td><td>{r['product']}</td></tr>
        <tr><td class="label">Quantity Issued:</td><td><b>{r['quantity']}</b></td></tr>
        <tr><td class="label">Received By:</td><td>{r['issued_by']}</td></tr>
        <tr><td class="label">Phone:</td><td>{r['issuer_mobile']}</td></tr>
    """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, Helvetica, sans-serif; color: #000; margin: 0; padding: 10px; }}
            .id-section {{ text-align: center; margin-bottom: 12px; }}
            .id-section h3 {{ margin: 0 0 10px 0; font-size: 15px; letter-spacing: 1px; }}
            .id-images {{ display: flex; justify-content: center; gap: 25px; }}
            .receipt-box {{ border: 2px solid #1a7a3a; padding: 14px 18px; margin-bottom: 16px; border-radius: 3px; }}
            .header-row {{ display: flex; justify-content: space-between; align-items: flex-start; }}
            .title {{ font-weight: bold; font-size: 13.5px; }}
            .factory {{ font-size: 12.5px; margin-top: 2px; }}
            .right-info {{ text-align: right; font-size: 12.5px; }}
            table {{ width: 100%; margin-top: 12px; font-size: 13px; border-collapse: collapse; }}
            td {{ padding: 3px 0; }}
            .label {{ width: 150px; font-weight: bold; }}
            .signatures {{ display: flex; justify-content: space-between; margin-top: 32px; }}
            .sign-box {{ width: 45%; text-align: center; border-top: 1px solid #333; padding-top: 5px; font-size: 11.5px; }}
            .footer {{ text-align: center; font-size: 11px; color: #555; margin-top: 14px; }}
            .dashed {{ border-top: 1.5px dashed #666; margin: 14px 0; }}
        </style>
    </head>
    <body>
        <div class="id-section">
            <h3>FARMER IDENTIFICATION</h3>
            <div class="id-images">
                <div>{front_html}<div style="font-size:11px; margin-top:3px;">Front</div></div>
                <div>{back_html}<div style="font-size:11px; margin-top:3px;">Back</div></div>
            </div>
        </div>
        <hr style="border:none; border-top:1px solid #333; margin:12px 0;">

        <!-- STORE RECEIPT -->
        <div class="receipt-box">
            <div class="header-row">
                <div>
                    <div class="title">MINISTRY OF AGRICULTURE - PRODUCT DISTRIBUTION PROGRAM</div>
                    <div class="factory">CHEBANGO TEA FACTORY</div>
                </div>
                <div class="right-info">
                    <div style="font-weight:bold;">STORE RECEIPT</div>
                    <div>Receipt No: {r['receipt_no']}</div>
                    <div>Date: {r['date_str']}</div>
                </div>
            </div>
            <table>{details_rows}</table>
            <div class="signatures">
                <div class="sign-box">Recipient Signature</div>
                <div class="sign-box">Authorized Officer</div>
            </div>
        </div>

        <div class="dashed"></div>

        <!-- GATE COPY -->
        <div class="receipt-box">
            <div class="header-row">
                <div>
                    <div class="title">MINISTRY OF AGRICULTURE - PRODUCT DISTRIBUTION PROGRAM</div>
                    <div class="factory">CHEBANGO TEA FACTORY</div>
                </div>
                <div class="right-info">
                    <div style="font-weight:bold;">GATE COPY</div>
                    <div>Receipt No: {r['receipt_no']}</div>
                    <div>Date: {r['date_str']}</div>
                </div>
            </div>
            <table>{details_rows}</table>
            <div class="signatures">
                <div class="sign-box">Recipient Signature</div>
                <div class="sign-box">Authorized Officer</div>
            </div>
        </div>

        <div class="dashed"></div>

        <!-- FARMER COPY -->
        <div class="receipt-box">
            <div class="header-row">
                <div>
                    <div class="title">MINISTRY OF AGRICULTURE - PRODUCT DISTRIBUTION PROGRAM</div>
                    <div class="factory">CHEBANGO TEA FACTORY</div>
                </div>
                <div class="right-info">
                    <div style="font-weight:bold;">FARMER COPY</div>
                    <div>Receipt No: {r['receipt_no']}</div>
                    <div>Date: {r['date_str']}</div>
                </div>
            </div>
            <table>{details_rows}</table>
            <div class="signatures">
                <div class="sign-box">Recipient Signature</div>
                <div class="sign-box">Authorized Officer</div>
            </div>
        </div>

        <p class="footer">This receipt number is traceable and secured. Keep the duplicate copy for your records.</p>
    </body>
    </html>
    """
    components.html(html_content, height=1450, scrolling=True)


def page_receipt():
    st.title("🧾 Receipt")
    st.caption("Store Receipt + Gate Copy + Farmer Copy")

    if not st.session_state.last_receipt:
        st.warning("No receipt has been generated yet. Please go to **Issue to Farmer** first.")
        return

    r = st.session_state.last_receipt
    st.success(f"Receipt No: **{r['receipt_no']}**  |  {r['date_str']}")

    if st.button("🖨️ PRINT RECEIPT", use_container_width=True):
        st.info("Press **Ctrl + P** to print the receipt below.")

    st.markdown("---")
    render_professional_receipt(r)


def page_farmers_list():
    st.title("📋 Farmers List")
    df = load_farmers()
    if df.empty:
        st.warning("No records yet.")
        return
    st.dataframe(df, use_container_width=True, hide_index=True)

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Farmers")
    buffer.seek(0)
    st.download_button(
        "📥 Download Excel",
        data=buffer,
        file_name=f"Chebango_Farmers_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )


def page_reports():
    st.title("📄 Reports")
    stock = load_stock()
    df = load_farmers()
    st.subheader("Stock Summary")
    for p, v in stock.items():
        st.write(f"**{p}** → Available: **{v['available']}** | Issued: {v['issued']}")
    st.subheader("Issuance Summary")
    st.write(f"Total Farmers Served: **{len(df)}**")
    if not df.empty:
        st.write(f"Total Quantity Distributed: **{df['Quantity'].sum()}**")


# ---------- MAIN ----------
def main():
    if not st.session_state.logged_in:
        show_login()
    else:
        if st.session_state.user.get("must_change_password", False):
            show_change_password()
        else:
            menu = show_sidebar()
            if "🏠 Home" in menu:
                page_home()
            elif "📦 Receive Stock" in menu:
                page_receive_stock()
            elif "📊 View Stock" in menu:
                page_view_stock()
            elif "👨‍🌾 Issue to Farmer" in menu:
                page_issue_to_farmer()
            elif "🧾 Receipt" in menu:
                page_receipt()
            elif "📋 Farmers List" in menu:
                page_farmers_list()
            elif "📄 Reports" in menu:
                page_reports()


if __name__ == "__main__":
    main()