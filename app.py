"""
Chebango Tracker - Supabase-backed Version (persistent storage)
Mobile-responsive UI with logo branding + Multi-product issuance
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from io import BytesIO
import streamlit.components.v1 as components
from PIL import Image
from supabase import create_client, Client

# ---------- SUPABASE CLIENT ----------
@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase_client()

# ---------- LOGO ----------
LOGO_PATH = "chebango_logo.png"  # keep this file in the same folder as app.py

def get_logo_image():
    if os.path.exists(LOGO_PATH):
        try:
            return Image.open(LOGO_PATH)
        except Exception:
            return None
    return None

logo_img = get_logo_image()

st.set_page_config(
    page_title="Chebango Tracker",
    page_icon=logo_img if logo_img else "🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- CSS (mobile-responsive + centered) ----------
st.markdown("""
<style>
    .stApp { background-color: #f4f1e8; }
    [data-testid="stSidebar"] { background-color: #1b4332; }
    [data-testid="stSidebar"] * { color: #ecf0f1 !important; }
    [data-testid="stMetricValue"] { color: #1b4332 !important; font-weight: 700 !important; }
    [data-testid="stMetricLabel"] { color: #1b4332 !important; font-weight: 600 !important; }
    h1, h2, h3, p, label, .stMarkdown { color: #1b4332 !important; }
    
    /* Center main content */
    .block-container {
        max-width: 1100px !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        margin: 0 auto !important;
    }

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
    .sidebar-logo-wrap { display: flex; justify-content: center; padding: 6px 0 14px 0; }
    .sidebar-logo-wrap img { max-width: 150px; width: 100%; height: auto; border-radius: 6px; background: #fff; padding: 6px; }
    .login-logo-wrap { display: flex; justify-content: center; margin-bottom: 10px; }
    .login-logo-wrap img { max-width: 240px; width: 70%; height: auto; }

    @media (max-width: 768px) {
        .block-container { 
            padding-left: 0.8rem !important; 
            padding-right: 0.8rem !important; 
            padding-top: 1rem !important; 
            max-width: 100% !important;
        }
        h1 { font-size: 1.45rem !important; }
        h2 { font-size: 1.2rem !important; }
        h3 { font-size: 1.05rem !important; }
        p, label, .stMarkdown, .stCaption { font-size: 0.92rem !important; }
        [data-testid="stMetricValue"] { font-size: 1.35rem !important; }
        [data-testid="stMetricLabel"] { font-size: 0.85rem !important; }
        .stButton > button { font-size: 0.95rem !important; padding: 0.6rem 0.5rem !important; width: 100% !important; }
        .stTextInput input, .stNumberInput input, .stSelectbox, .stTextArea textarea { font-size: 0.95rem !important; }
        [data-testid="stDataFrame"] { overflow-x: auto !important; }
        .login-logo-wrap img { max-width: 190px; width: 60%; }
        .sidebar-logo-wrap img { max-width: 110px; }
    }

    @media print {
        .stApp > header, .stSidebar, .stButton, .stRadio,
        .stFileUploader, .stCameraInput, .stSelectbox,
        .stTextInput, .stNumberInput, .stForm { display: none !important; }
    }
</style>
""", unsafe_allow_html=True)

# ---------- PRODUCTS (built-in defaults) ----------
PRODUCTS = [
    "Agripest Organic (250ml Bottle)",
    "Agripest Organic (500ml Bottle)",
    "Agripest Organic (1L Bottle)",
    "Flower Dust (1kg Bag)",
    "Flower Dust (5kg Bag)"
]

# ---------- ADMIN CONFIG ----------
# Only these mobile numbers can add new products. Add/remove numbers as needed.
# Currently set to Aron Yegon (ICT). Too Patrick and Caroline are NOT in this
# set, so they will only ever see "View Stock" and never the "Manage Products"
# admin page.
ADMIN_MOBILES = {"254769468742"}  # Aron Yegon (ICT)

def is_admin():
    user = st.session_state.get("user")
    return bool(user) and user.get("mobile") in ADMIN_MOBILES


# ---------- LOGO HELPERS ----------
def logo_base64():
    if os.path.exists(LOGO_PATH):
        try:
            with open(LOGO_PATH, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except Exception:
            return None
    return None

LOGO_B64 = logo_base64()

def render_login_logo():
    if LOGO_B64:
        st.markdown(f'<div class="login-logo-wrap"><img src="data:image/png;base64,{LOGO_B64}"></div>', unsafe_allow_html=True)
    else:
        st.markdown("### 🌱 Chebango Tracker")

def render_sidebar_logo():
    if LOGO_B64:
        st.markdown(f'<div class="sidebar-logo-wrap"><img src="data:image/png;base64,{LOGO_B64}"></div>', unsafe_allow_html=True)

# ---------- SUPABASE DATA HELPERS ----------
def load_users():
    res = supabase.table("users").select("*").execute()
    rows = res.data or []
    return {r["mobile"]: r for r in rows}


def update_user_password(mobile, new_password):
    supabase.table("users").update({
        "password": new_password,
        "must_change_password": False
    }).eq("mobile", mobile).execute()


def load_extra_products():
    """
    Products added by the admin through the 'Manage Products' page, stored in
    a Supabase table called 'products' (columns: id, name).
    Returns an empty list if the table doesn't exist yet or on any error.
    """
    try:
        res = supabase.table("products").select("*").execute()
        rows = res.data or []
        return [r["name"] for r in rows if r.get("name")]
    except Exception:
        return []


def save_new_product(name):
    supabase.table("products").insert({"name": name}).execute()


def get_all_products():
    """Built-in PRODUCTS list + any admin-added products, de-duplicated, in order."""
    all_products = list(PRODUCTS)
    for p in load_extra_products():
        if p not in all_products:
            all_products.append(p)
    return all_products


def load_stock():
    res = supabase.table("stock").select("*").execute()
    rows = res.data or []
    stock = {r["product"]: {"received": r["received"], "issued": r["issued"], "available": r["available"]} for r in rows}
    for p in get_all_products():
        if p not in stock:
            stock[p] = {"received": 0, "issued": 0, "available": 0}
    return stock


def save_stock_row(product, values):
    supabase.table("stock").upsert({
        "product": product,
        "received": values["received"],
        "issued": values["issued"],
        "available": values["available"]
    }).execute()


def load_farmers():
    res = supabase.table("farmers").select("*").order("id", desc=False).execute()
    rows = res.data or []
    if not rows:
        return pd.DataFrame(columns=[
            "Receipt_No", "Date", "Time", "Farmer_Name", "Grower_Number", "ID_Number", "Mobile",
            "Product", "Quantity", "Issued_By", "Department", "Issuer_Mobile"
        ])
    df = pd.DataFrame(rows)
    rename_map = {
        "receipt_no": "Receipt_No", "date": "Date", "time": "Time", "farmer_name": "Farmer_Name",
        "grower_number": "Grower_Number", "id_number": "ID_Number", "mobile": "Mobile",
        "product": "Product", "quantity": "Quantity", "issued_by": "Issued_By",
        "department": "Department", "issuer_mobile": "Issuer_Mobile"
    }
    df = df.rename(columns=rename_map)
    keep_cols = list(rename_map.values())
    return df[[c for c in keep_cols if c in df.columns]]


def save_farmer(record):
    supabase.table("farmers").insert({
        "receipt_no": record["Receipt_No"],
        "date": record["Date"],
        "time": record["Time"],
        "farmer_name": record["Farmer_Name"],
        "grower_number": record["Grower_Number"],
        "id_number": record["ID_Number"],
        "mobile": record["Mobile"],
        "product": record["Product"],
        "quantity": record["Quantity"],
        "issued_by": record["Issued_By"],
        "department": record["Department"],
        "issuer_mobile": record["Issuer_Mobile"]
    }).execute()


def image_to_base64(uploaded_file):
    if uploaded_file is None:
        return None
    try:
        bytes_data = uploaded_file.getvalue()
        b64 = base64.b64encode(bytes_data).decode()
        return f"data:image/jpeg;base64,{b64}"
    except Exception:
        return None


# ---------- SESSION ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "last_receipt" not in st.session_state:
    st.session_state.last_receipt = None
if "issue_items" not in st.session_state:
    st.session_state.issue_items = []
if "admin_unlocked" not in st.session_state:
    st.session_state.admin_unlocked = False


# ---------- LOGIN ----------
def show_login():
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        render_login_logo()
        st.markdown("""
        <div style="text-align:center; margin-bottom:20px;">
            <h1 style="color:#27ae60;">Chebango Tracker</h1>
            <p>Product Issuance &amp; Stock System</p>
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
        **Default Password = 1234** (unless already changed)
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
                update_user_password(st.session_state.user["mobile"], new_pwd)
                st.session_state.user["must_change_password"] = False
                st.success("Password changed successfully!")
                st.rerun()
            else:
                st.error("Passwords do not match.")


def show_sidebar():
    with st.sidebar:
        render_sidebar_logo()
        st.markdown("""
        <div style="padding:10px 0; border-bottom:1px solid #34495e; margin-bottom:15px; text-align:center;">
            <h2 style="color:#27ae60; margin:0;">Chebango</h2>
            <p style="color:#bdc3c7; font-size:13px;">Tracker System</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"**{st.session_state.user['name']}**")
        st.caption(f"{st.session_state.user['department']}")
        st.caption(st.session_state.user['mobile'])
        st.markdown("---")

        menu_items = [
            "🏠 Home",
            "📦 Receive Stock",
            "📊 View Stock",
            "👨‍🌾 Issue to Farmer",
            "🧾 Receipt",
            "📋 Farmers List",
            "📄 Reports"
        ]
        # Only admins ever see this option — everyone else (e.g. Too Patrick,
        # Caroline) only ever gets "📊 View Stock" to look at available stock.
        if is_admin():
            menu_items.append("⚙️ Manage Products")

        menu = st.radio("Menu", menu_items, label_visibility="collapsed")

        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.issue_items = []
            st.session_state.admin_unlocked = False
            st.rerun()
        return menu


# ---------- PAGES ----------
def page_home():
    st.title("Main Menu")
    st.caption(f"Welcome **{st.session_state.user['name']}** ({st.session_state.user['department']})")
    stock = load_stock()
    total = sum(v["available"] for v in stock.values())
    col1, col2, col3 = st.columns(3)
    col1.metric("Products", len(get_all_products()))
    col2.metric("Total Available", f"{total:,}")
    col3.metric("Department", st.session_state.user["department"])


def page_receive_stock():
    st.title("📦 Receive Stock")
    stock = load_stock()
    with st.form("receive_form"):
        product = st.selectbox("Select Product", get_all_products())
        quantity = st.number_input("Quantity Received", min_value=1, value=10)
        if st.form_submit_button("✅ Confirm Receive Stock", use_container_width=True):
            stock[product]["received"] += quantity
            stock[product]["available"] += quantity
            save_stock_row(product, stock[product])
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


def page_manage_products():
    """Admin-only, password-protected page for adding new products."""
    st.title("⚙️ Manage Products")
    st.caption("Admin only — add new products so they appear across the system.")

    if not is_admin():
        st.error("You do not have permission to access this page.")
        return

    if not st.session_state.admin_unlocked:
        st.info("Enter the admin password to unlock this page.")
        with st.form("admin_pwd_form"):
            pwd = st.text_input("Admin Password", type="password")
            if st.form_submit_button("🔓 Unlock", use_container_width=True):
                admin_password = st.secrets.get("ADMIN_PASSWORD", "changeme123")
                if pwd == admin_password:
                    st.session_state.admin_unlocked = True
                    st.rerun()
                else:
                    st.error("Incorrect admin password.")
        return

    st.success("🔓 Admin access granted.")
    st.markdown("---")

    existing = get_all_products()
    st.write("**Current Products:**")
    for p in existing:
        st.write(f"• {p}")

    st.markdown("---")
    with st.form("add_product_form"):
        new_product = st.text_input("New Product Name", placeholder="e.g. Agripest Organic (2L Bottle)")
        if st.form_submit_button("➕ Add Product", use_container_width=True):
            new_product = new_product.strip()
            if not new_product:
                st.error("Please enter a product name.")
            elif new_product in existing:
                st.warning("This product already exists.")
            else:
                save_new_product(new_product)
                save_stock_row(new_product, {"received": 0, "issued": 0, "available": 0})
                st.success(f"Product **{new_product}** added successfully!")
                st.balloons()
                st.rerun()

    st.markdown("---")
    if st.button("🔒 Lock Admin Panel", use_container_width=True):
        st.session_state.admin_unlocked = False
        st.rerun()


def page_issue_to_farmer():
    st.title("👨‍🌾 Issue Product to Farmer")
    stock = load_stock()
    available_products = [p for p in get_all_products() if stock[p]["available"] > 0]

    if not available_products:
        st.error("No stock available. Please receive stock first.")
        return

    st.markdown("### Farmer Details")
    col1, col2 = st.columns(2)
    with col1:
        farmer_name = st.text_input("Name of the Farmer *", key="farmer_name")
        grower_number = st.text_input("Grower Number *", key="grower_number")
        id_number = st.text_input("ID Number *", key="id_number")
    with col2:
        mobile = st.text_input("Mobile Number *", key="mobile")

    st.markdown("---")
    st.markdown("### Products to Issue")

    # Show currently added products
    if st.session_state.issue_items:
        st.write("**Selected Products:**")
        for i, item in enumerate(st.session_state.issue_items):
            col_a, col_b, col_c = st.columns([5, 2, 1])
            with col_a:
                st.write(f"• **{item['product']}**")
            with col_b:
                st.write(f"Qty: **{item['quantity']}**")
            with col_c:
                if st.button("🗑️", key=f"remove_{i}"):
                    st.session_state.issue_items.pop(i)
                    st.rerun()

    # Add new product section
    with st.expander("➕ Add Product", expanded=True):
        col_p, col_q = st.columns([3, 1])
        with col_p:
            product = st.selectbox("Select Product", available_products, key="add_product")
        with col_q:
            max_qty = stock[product]["available"]
            # Reduce max_qty by already selected quantity of same product
            already_selected = sum(item["quantity"] for item in st.session_state.issue_items if item["product"] == product)
            max_qty = max(1, max_qty - already_selected)
            quantity = st.number_input("Quantity", min_value=1, max_value=max_qty, value=1, key="add_qty")

        if st.button("➕ Add to List", use_container_width=True):
            existing = next((item for item in st.session_state.issue_items if item["product"] == product), None)
            if existing:
                st.warning(f"**{product}** is already in the list. Remove it first if you want to change the quantity.")
            else:
                st.session_state.issue_items.append({
                    "product": product,
                    "quantity": quantity
                })
                st.success(f"Added **{quantity}** × {product}")
                st.rerun()

    st.markdown("---")
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
            id_front = st.file_uploader("Upload ID Front", type=["jpg", "jpeg", "png"], key="up_front")

    with col_b:
        st.markdown("**ID Back**")
        back_method = st.radio("Back Method", ["📷 Camera", "📁 Upload"],
                               key="back_method", horizontal=True, label_visibility="collapsed")
        if back_method == "📷 Camera":
            id_back = st.camera_input("Take ID Back", key="cam_back")
        else:
            id_back = st.file_uploader("Upload ID Back", type=["jpg", "jpeg", "png"], key="up_back")

    st.markdown("---")

    # Final submit button
    if st.button("✅ Issue All Products & Generate Receipt", type="primary", use_container_width=True):
        if not farmer_name or not grower_number or not id_number or not mobile:
            st.error("Please fill all farmer details.")
        elif not st.session_state.issue_items:
            st.error("Please add at least one product.")
        else:
            now = datetime.now()
            receipt_no = f"{now.strftime('%y%m%d%H%M')}"
            date_str = now.strftime("%d %b %Y %H:%M")
            time_str = now.strftime("%H:%M:%S")

            issued_products = []
            total_qty = 0

            for item in st.session_state.issue_items:
                product = item["product"]
                quantity = item["quantity"]

                # Update stock
                stock[product]["issued"] += quantity
                stock[product]["available"] -= quantity
                save_stock_row(product, stock[product])

                # Save farmer record
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

                issued_products.append(f"{quantity} × {product}")
                total_qty += quantity

            # Create receipt data
            st.session_state.last_receipt = {
                "receipt_no": receipt_no,
                "date_str": date_str,
                "time_str": time_str,
                "farmer_name": farmer_name,
                "grower_number": grower_number,
                "id_number": id_number,
                "mobile": mobile,
                "product": " + ".join(issued_products),
                "quantity": total_qty,
                "issued_by": st.session_state.user["name"],
                "department": st.session_state.user["department"],
                "issuer_mobile": st.session_state.user["mobile"],
                "id_front_b64": image_to_base64(id_front),
                "id_back_b64": image_to_base64(id_back)
            }

            # Clear the list
            st.session_state.issue_items = []

            st.success("✅ All products issued successfully! Go to **Receipt** menu to view and print.")
            st.balloons()
            st.rerun()


def render_professional_receipt(r):
    front_img = r.get("id_front_b64")
    back_img = r.get("id_back_b64")

    front_html = f'<img src="{front_img}" style="max-width:100%; width:260px; max-height:170px; border:1px solid #999;">' if front_img else '<div style="width:100%;max-width:260px;height:150px;border:1px dashed #aaa;display:flex;align-items:center;justify-content:center;color:#888;font-size:13px;">No Front ID</div>'
    back_html = f'<img src="{back_img}" style="max-width:100%; width:260px; max-height:170px; border:1px solid #999;">' if back_img else '<div style="width:100%;max-width:260px;height:150px;border:1px dashed #aaa;display:flex;align-items:center;justify-content:center;color:#888;font-size:13px;">No Back ID</div>'

    logo_tag = f'<img src="data:image/png;base64,{LOGO_B64}" style="height:40px;">' if LOGO_B64 else ""

    details_rows = f"""
        <tr><td class="label">Farmer Name:</td><td>{r['farmer_name']}</td></tr>
        <tr><td class="label">ID Number:</td><td>{r['id_number']}</td></tr>
        <tr><td class="label">Grower Number:</td><td>{r['grower_number']}</td></tr>
        <tr><td class="label">Product(s):</td><td>{r['product']}</td></tr>
        <tr><td class="label">Total Quantity:</td><td><b>{r['quantity']}</b></td></tr>
        <tr><td class="label">Issued By:</td><td>{r['issued_by']}</td></tr>
        <tr><td class="label">Phone:</td><td>{r['issuer_mobile']}</td></tr>
    """

    def receipt_block(copy_label):
        return f"""
        <div class="receipt-box">
            <div class="header-row">
                <div class="header-left">
                    {logo_tag}
                    <div>
                        <div class="title">MINISTRY OF AGRICULTURE - PRODUCT DISTRIBUTION PROGRAM</div>
                        <div class="factory">CHEBANGO TEA FACTORY</div>
                    </div>
                </div>
                <div class="right-info">
                    <div style="font-weight:bold;">{copy_label}</div>
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
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: Arial, Helvetica, sans-serif; color: #000; margin: 0; padding: 10px; }}
            .id-section {{ text-align: center; margin-bottom: 12px; }}
            .id-section h3 {{ margin: 0 0 10px 0; font-size: 15px; letter-spacing: 1px; }}
            .id-images {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; }}
            .receipt-box {{ border: 2px solid #1a7a3a; padding: 14px 16px; margin-bottom: 16px; border-radius: 3px; }}
            .header-row {{ display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-start; gap: 6px; }}
            .header-left {{ display: flex; align-items: center; gap: 8px; }}
            .title {{ font-weight: bold; font-size: 12.5px; }}
            .factory {{ font-size: 12px; margin-top: 2px; }}
            .right-info {{ text-align: right; font-size: 12.5px; }}
            table {{ width: 100%; margin-top: 12px; font-size: 13px; border-collapse: collapse; }}
            td {{ padding: 3px 0; word-break: break-word; }}
            .label {{ width: 130px; font-weight: bold; }}
            .signatures {{ display: flex; flex-wrap: wrap; justify-content: space-between; margin-top: 28px; gap: 10px; }}
            .sign-box {{ flex: 1 1 45%; min-width: 130px; text-align: center; border-top: 1px solid #333; padding-top: 5px; font-size: 11px; }}
            .footer {{ text-align: center; font-size: 11px; color: #555; margin-top: 14px; }}
            .dashed {{ border-top: 1.5px dashed #666; margin: 14px 0; }}
            @media (max-width: 480px) {{
                .label {{ width: 105px; font-size: 12px; }}
                table {{ font-size: 12px; }}
                .title {{ font-size: 11px; }}
                .factory {{ font-size: 10.5px; }}
                .right-info {{ font-size: 11px; }}
            }}
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
        {receipt_block("STORE RECEIPT")}
        <div class="dashed"></div>
        {receipt_block("GATE COPY")}
        <div class="dashed"></div>
        {receipt_block("FARMER COPY")}
        <p class="footer">This receipt number is traceable and secured. Keep the duplicate copy for your records.</p>
    </body>
    </html>
    """
    components.html(html_content, height=1550, scrolling=True)


def page_receipt():
    st.title("🧾 Receipt")
    st.caption("Store Receipt + Gate Copy + Farmer Copy")

    if not st.session_state.last_receipt:
        st.warning("No receipt has been generated yet. Please go to **Issue to Farmer** first.")
        return

    r = st.session_state.last_receipt
    st.success(f"Receipt No: **{r['receipt_no']}**  |  {r['date_str']}")

    if st.button("🖨️ PRINT RECEIPT", use_container_width=True):
        st.info("Press **Ctrl + P** (or use your phone's share/print option) to print the receipt below.")

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
            elif "⚙️ Manage Products" in menu:
                page_manage_products()


if __name__ == "__main__":
    main()
