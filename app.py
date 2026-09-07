"""
Chebango Tracker - Supabase-backed Version (persistent storage)
Mobile-responsive UI with logo branding + Multi-product issuance
FIXES: stock math, EAT timezone, receipt labels, single-page PDF download
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import base64
import random
import string
from io import BytesIO
import streamlit.components.v1 as components
from PIL import Image
from supabase import create_client, Client

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False

# East Africa Time (Kenya)
EAT = ZoneInfo("Africa/Nairobi")

def now_eat():
    return datetime.now(EAT)

# ---------- SUPABASE CLIENT ----------
@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase_client()

# ---------- LOGO ----------
LOGO_PATH = "chebango_logo.png"

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

# ---------- CSS ----------
st.markdown("""
<style>
    .stApp { background-color: #f4f1e8; }
    [data-testid="stSidebar"] { background-color: #1b4332; }
    [data-testid="stSidebar"] * { color: #ecf0f1 !important; }
    [data-testid="stMetricValue"] { color: #1b4332 !important; font-weight: 700 !important; }
    [data-testid="stMetricLabel"] { color: #1b4332 !important; font-weight: 600 !important; }
    h1, h2, h3, p, label, .stMarkdown { color: #1b4332 !important; }

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

# ---------- PRODUCTS ----------
PRODUCTS = [
    "Agripest Organic (250ml Bottle)",
    "Agripest Organic (500ml Bottle)",
    "Agripest Organic (1L Bottle)",
    "Flower Dust (1kg Bag)",
    "Flower Dust (5kg Bag)"
]

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
    try:
        res = supabase.table("products").select("*").execute()
        rows = res.data or []
        return [r["name"] for r in rows if r.get("name")]
    except Exception:
        return []


def save_new_product(name):
    supabase.table("products").insert({"name": name}).execute()


def delete_product_everywhere(name):
    try:
        supabase.table("products").delete().eq("name", name).execute()
    except Exception:
        pass
    try:
        supabase.table("stock").delete().eq("product", name).execute()
    except Exception:
        pass


def get_all_products():
    all_products = list(PRODUCTS)
    for p in load_extra_products():
        if p not in all_products:
            all_products.append(p)
    return all_products


def _sync_available(values):
    """Always force available = received - issued (never trust a stale available)."""
    received = int(values.get("received", 0) or 0)
    issued = int(values.get("issued", 0) or 0)
    return {
        "received": received,
        "issued": issued,
        "available": max(0, received - issued)
    }


def load_stock():
    res = supabase.table("stock").select("*").execute()
    rows = res.data or []
    stock = {}
    for r in rows:
        stock[r["product"]] = _sync_available({
            "received": r["received"],
            "issued": r["issued"],
            "available": r["available"]
        })
    for p in get_all_products():
        if p not in stock:
            stock[p] = {"received": 0, "issued": 0, "available": 0}
    return stock


def save_stock_row(product, values):
    synced = _sync_available(values)
    supabase.table("stock").upsert({
        "product": product,
        "received": synced["received"],
        "issued": synced["issued"],
        "available": synced["available"]
    }).execute()
    return synced


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


def delete_receipt_permanently(receipt_no, restore_stock=True):
    """
    Permanently delete all farmer rows for a receipt number.
    If restore_stock is True, reverse the stock impact (issued down, available up).
    Returns (deleted_count, restored_summary_list).
    """
    receipt_no = str(receipt_no).strip()
    if not receipt_no:
        return 0, []

    # Fetch rows for this receipt before deleting
    res = supabase.table("farmers").select("*").eq("receipt_no", receipt_no).execute()
    rows = res.data or []
    if not rows:
        return 0, []

    restored = []
    if restore_stock:
        stock = load_stock()
        for row in rows:
            product = row.get("product")
            qty = int(row.get("quantity") or 0)
            if not product or qty <= 0:
                continue
            if product not in stock:
                stock[product] = {"received": 0, "issued": 0, "available": 0}
            stock[product]["issued"] = max(0, int(stock[product]["issued"]) - qty)
            # available will be recalculated as received - issued in save_stock_row
            save_stock_row(product, stock[product])
            restored.append(f"{qty} × {product}")

    # Permanent delete
    supabase.table("farmers").delete().eq("receipt_no", receipt_no).execute()
    return len(rows), restored


def image_to_base64(uploaded_file):
    if uploaded_file is None:
        return None
    try:
        bytes_data = uploaded_file.getvalue()
        b64 = base64.b64encode(bytes_data).decode()
        return f"data:image/jpeg;base64,{b64}"
    except Exception:
        return None


def b64_to_bytes(data_uri):
    """Convert data:image/...;base64,... to raw bytes for PDF embedding."""
    if not data_uri:
        return None
    try:
        if "," in data_uri:
            data_uri = data_uri.split(",", 1)[1]
        return base64.b64decode(data_uri)
    except Exception:
        return None


# ---------- REMOTE ID CAPTURE ----------
def generate_capture_code():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def load_id_capture(code):
    if not code:
        return None
    try:
        res = supabase.table("id_captures").select("*").eq("code", code).execute()
        rows = res.data or []
        return rows[0] if rows else None
    except Exception:
        return None


def save_id_capture(code, front_b64=None, back_b64=None):
    existing = load_id_capture(code) or {}
    payload = {
        "code": code,
        "front_b64": front_b64 if front_b64 is not None else existing.get("front_b64"),
        "back_b64": back_b64 if back_b64 is not None else existing.get("back_b64"),
    }
    supabase.table("id_captures").upsert(payload).execute()


def delete_id_capture(code):
    if not code:
        return
    try:
        supabase.table("id_captures").delete().eq("code", code).execute()
    except Exception:
        pass


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
if "capture_code" not in st.session_state:
    st.session_state.capture_code = None


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
            "📷 Remote ID Capture",
            "🧾 Receipt",
            "📋 Farmers List",
            "📄 Reports"
        ]
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
    st.caption("View only. New products and received quantities are added by the admin under **⚙️ Manage Products**.")
    stock = load_stock()
    data = [{"Product": p, "Received": v["received"], "Issued": v["issued"], "Available": v["available"]}
            for p, v in stock.items()]
    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)


def page_view_stock():
    st.title("📊 View Stock")
    stock = load_stock()
    data = [{"Product": p, "Received": v["received"], "Issued": v["issued"], "Available": v["available"]}
            for p, v in stock.items()]
    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
    total = sum(v["available"] for v in stock.values())
    st.metric("🟢 Total Available Stock", f"{total:,}")


def page_manage_products():
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

    stock = load_stock()
    existing = get_all_products()

    st.write("**Current Products & Stock** (Available is always Received − Issued):")
    data = [{"Product": p, "Received": stock[p]["received"], "Issued": stock[p]["issued"], "Available": stock[p]["available"]}
            for p in existing]
    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

    # One-click heal of any stale DB rows
    if st.button("🔄 Recalculate All Available (Received − Issued)", use_container_width=True):
        for p in existing:
            save_stock_row(p, stock[p])
        st.success("All available quantities recalculated and saved.")
        st.rerun()

    st.markdown("---")
    st.subheader("➕ Add a New Product")
    st.caption("Register a brand-new product name. It starts at 0 stock — use the section below to receive quantity.")
    with st.form("add_product_form"):
        new_product = st.text_input("New Product Name", placeholder="e.g. Agripest Organic (2L Bottle)")
        new_qty = st.number_input("Opening Quantity (optional)", min_value=0, value=0)
        if st.form_submit_button("➕ Add Product", use_container_width=True):
            new_product = new_product.strip()
            if not new_product:
                st.error("Please enter a product name.")
            elif new_product in existing:
                st.warning("This product already exists.")
            else:
                save_new_product(new_product)
                save_stock_row(new_product, {
                    "received": new_qty,
                    "issued": 0,
                    "available": new_qty
                })
                st.success(f"Product **{new_product}** added with opening quantity **{new_qty}**!")
                st.balloons()
                st.rerun()

    st.markdown("---")
    st.subheader("📥 Receive Stock (Existing Product)")
    st.caption("Add received quantity to a product that already exists.")
    with st.form("receive_stock_form"):
        product = st.selectbox("Select Product", existing)
        quantity = st.number_input("Quantity Received", min_value=1, value=10, key="admin_receive_qty")
        if st.form_submit_button("✅ Confirm Receive Stock", use_container_width=True):
            stock[product]["received"] += quantity
            save_stock_row(product, stock[product])
            st.success(f"Received **{quantity}** of **{product}**")
            st.balloons()
            st.rerun()

    st.markdown("---")
    st.subheader("🛠️ Fix / Correct Stock Numbers")
    st.caption("Edit Received or Issued. Available is always recalculated as Received − Issued when you save.")

    fix_df = pd.DataFrame([
        {"Product": p, "Received": stock[p]["received"], "Issued": stock[p]["issued"], "Available": stock[p]["available"]}
        for p in existing
    ])
    edited_df = st.data_editor(
        fix_df,
        use_container_width=True,
        hide_index=True,
        disabled=["Product", "Available"],
        key="stock_fix_editor"
    )

    if st.button("💾 Save Corrected Numbers", use_container_width=True):
        for _, row in edited_df.iterrows():
            save_stock_row(row["Product"], {
                "received": int(row["Received"]),
                "issued": int(row["Issued"]),
                "available": 0  # will be recalculated
            })
        st.success("Stock numbers updated (Available = Received − Issued).")
        st.rerun()

    st.markdown("---")
    st.subheader("🗑️ Delete a Product")
    deletable = load_extra_products()
    if not deletable:
        st.caption("No admin-added products to delete. (Built-in products can't be removed; zero them out above.)")
    else:
        with st.form("delete_product_form"):
            product_to_delete = st.selectbox("Select Product to Delete", deletable)
            confirm = st.checkbox("I confirm I want to permanently delete this product and its stock record.")
            if st.form_submit_button("🗑️ Delete Product", use_container_width=True):
                if not confirm:
                    st.error("Please confirm before deleting.")
                else:
                    delete_product_everywhere(product_to_delete)
                    st.success(f"Deleted **{product_to_delete}**.")
                    st.rerun()

    st.markdown("---")
    st.subheader("🧾 Delete Duplicate / Accidental Receipts")
    st.caption(
        "Permanently delete a receipt and all its line items. "
        "Stock is restored automatically (Issued goes down, Available goes up)."
    )

    farmers_df = load_farmers()
    if farmers_df.empty:
        st.info("No receipts to delete.")
    else:
        # One row per receipt for selection
        receipt_summary = (
            farmers_df.groupby("Receipt_No", as_index=False)
            .agg({
                "Date": "first",
                "Time": "first",
                "Farmer_Name": "first",
                "ID_Number": "first",
                "Grower_Number": "first",
                "Quantity": "sum",
                "Product": lambda x: " + ".join(str(p) for p in x),
                "Issued_By": "first",
            })
            .sort_values(["Date", "Time"], ascending=False)
        )
        receipt_summary = receipt_summary.rename(columns={
            "Quantity": "Total_Qty",
            "Product": "Products",
        })

        st.dataframe(receipt_summary, use_container_width=True, hide_index=True)

        receipt_options = [
            f"{row['Receipt_No']}  |  {row['Date']} {row['Time']}  |  {row['Farmer_Name']}  |  ID {row['ID_Number']}  |  Qty {row['Total_Qty']}"
            for _, row in receipt_summary.iterrows()
        ]
        receipt_map = {
            f"{row['Receipt_No']}  |  {row['Date']} {row['Time']}  |  {row['Farmer_Name']}  |  ID {row['ID_Number']}  |  Qty {row['Total_Qty']}": row["Receipt_No"]
            for _, row in receipt_summary.iterrows()
        }

        with st.form("delete_receipt_form"):
            selected = st.selectbox("Select receipt to delete", receipt_options)
            restore = st.checkbox("Restore stock quantities for this receipt", value=True)
            confirm_del = st.checkbox("I confirm this receipt will be permanently deleted and cannot be recovered.")
            if st.form_submit_button("🗑️ Delete Selected Receipt Permanently", use_container_width=True):
                if not confirm_del:
                    st.error("Please tick the confirmation box before deleting.")
                else:
                    receipt_no = receipt_map[selected]
                    count, restored = delete_receipt_permanently(receipt_no, restore_stock=restore)
                    if count == 0:
                        st.warning("No rows found for that receipt (maybe already deleted).")
                    else:
                        msg = f"Permanently deleted receipt **{receipt_no}** ({count} line item(s))."
                        if restored:
                            msg += " Stock restored: " + "; ".join(restored)
                        st.success(msg)
                        st.rerun()

    st.markdown("---")
    if st.button("🔒 Lock Admin Panel", use_container_width=True):
        st.session_state.admin_unlocked = False
        st.rerun()


def page_remote_capture():
    st.title("📷 Remote ID Capture")
    st.caption("Use this on your phone: enter the code shown on the laptop's **Issue to Farmer** page, then capture the farmer's ID.")

    code = st.text_input("Capture Code", placeholder="e.g. 7F3K9Q").strip().upper()
    if not code:
        st.info("Enter the code from the laptop to begin.")
        return

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**ID Front**")
        front = st.camera_input("Capture ID Front", key="remote_cam_front")
        if front and st.button("⬆️ Upload Front", use_container_width=True, key="upload_front_btn"):
            save_id_capture(code, front_b64=image_to_base64(front))
            st.success("Front uploaded! Go back to the laptop and press '🔄 Refresh from Phone'.")
            st.balloons()

    with col2:
        st.markdown("**ID Back**")
        back = st.camera_input("Capture ID Back", key="remote_cam_back")
        if back and st.button("⬆️ Upload Back", use_container_width=True, key="upload_back_btn"):
            save_id_capture(code, back_b64=image_to_base64(back))
            st.success("Back uploaded! Go back to the laptop and press '🔄 Refresh from Phone'.")
            st.balloons()

    st.markdown("---")
    pending = load_id_capture(code)
    if pending:
        st.write("**Current upload status for this code:**")
        st.write(f"Front: {'✅ Uploaded' if pending.get('front_b64') else '⏳ Not yet'}")
        st.write(f"Back: {'✅ Uploaded' if pending.get('back_b64') else '⏳ Not yet'}")


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

    with st.expander("➕ Add Product", expanded=True):
        col_p, col_q = st.columns([3, 1])
        with col_p:
            product = st.selectbox("Select Product", available_products, key="add_product")
        with col_q:
            max_qty = stock[product]["available"]
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

    capture_mode = st.radio(
        "How is the ID being captured?",
        ["💻 This Device (camera/upload)", "📱 Phone (remote capture)"],
        horizontal=True,
        key="capture_mode"
    )

    id_front = None
    id_back = None
    remote_front_b64 = None
    remote_back_b64 = None

    if capture_mode == "💻 This Device (camera/upload)":
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

    else:
        st.caption("Generate a code here, capture the ID on your phone under **📷 Remote ID Capture**, then refresh here to pull it in.")

        col_gen, col_ref = st.columns(2)
        with col_gen:
            if st.button("🔁 Generate New Code", use_container_width=True):
                st.session_state.capture_code = generate_capture_code()
                st.rerun()
        with col_ref:
            if st.button("🔄 Refresh from Phone", use_container_width=True):
                st.rerun()

        if not st.session_state.capture_code:
            st.session_state.capture_code = generate_capture_code()

        st.markdown(f"### Code: `{st.session_state.capture_code}`")
        st.info("On the phone: open this app → log in → **📷 Remote ID Capture** → enter this code → capture Front & Back.")

        pending = load_id_capture(st.session_state.capture_code)
        remote_front_b64 = pending.get("front_b64") if pending else None
        remote_back_b64 = pending.get("back_b64") if pending else None

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("**ID Front**")
            if remote_front_b64:
                st.image(remote_front_b64, use_container_width=True)
                st.success("Received from phone ✅")
            else:
                st.warning("Not yet captured on phone")
        with col_p2:
            st.markdown("**ID Back**")
            if remote_back_b64:
                st.image(remote_back_b64, use_container_width=True)
                st.success("Received from phone ✅")
            else:
                st.warning("Not yet captured on phone")

    st.markdown("---")

    if st.button("✅ Issue All Products & Generate Receipt", type="primary", use_container_width=True):
        if not farmer_name or not grower_number or not id_number or not mobile:
            st.error("Please fill all farmer details.")
        elif not st.session_state.issue_items:
            st.error("Please add at least one product.")
        else:
            now = now_eat()
            receipt_no = f"{now.strftime('%y%m%d%H%M')}"
            date_str = now.strftime("%d %b %Y %H:%M")
            time_str = now.strftime("%H:%M:%S")

            issued_products = []
            total_qty = 0

            for item in st.session_state.issue_items:
                product = item["product"]
                quantity = item["quantity"]

                stock[product]["issued"] += quantity
                save_stock_row(product, stock[product])

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
                "id_front_b64": remote_front_b64 if capture_mode != "💻 This Device (camera/upload)" else image_to_base64(id_front),
                "id_back_b64": remote_back_b64 if capture_mode != "💻 This Device (camera/upload)" else image_to_base64(id_back)
            }

            st.session_state.issue_items = []
            if capture_mode != "💻 This Device (camera/upload)" and st.session_state.capture_code:
                delete_id_capture(st.session_state.capture_code)
                st.session_state.capture_code = None

            st.success("✅ All products issued successfully! Go to **Receipt** menu to download the PDF.")
            st.balloons()
            st.rerun()


# ---------- PDF RECEIPT (single A4 page) ----------
def build_receipt_pdf(r) -> bytes:
    """Build a compact single-page PDF with ID photos + Store / Gate / Farmer copies."""
    if not FPDF_AVAILABLE:
        raise RuntimeError("fpdf2 is not installed")

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    pdf.set_margins(8, 6, 8)

    page_w = 210 - 16  # usable width

    # --- ID section ---
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 5, "FARMER IDENTIFICATION", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    front_bytes = b64_to_bytes(r.get("id_front_b64"))
    back_bytes = b64_to_bytes(r.get("id_back_b64"))

    img_w = 55
    img_h = 35
    y_img = pdf.get_y()
    x1 = 20
    x2 = 110

    if front_bytes:
        try:
            pdf.image(BytesIO(front_bytes), x=x1, y=y_img, w=img_w, h=img_h)
        except Exception:
            pdf.set_xy(x1, y_img)
            pdf.set_font("Helvetica", "", 8)
            pdf.cell(img_w, img_h, "[No Front ID]", border=1, align="C")
    else:
        pdf.set_xy(x1, y_img)
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(img_w, img_h, "[No Front ID]", border=1, align="C")

    if back_bytes:
        try:
            pdf.image(BytesIO(back_bytes), x=x2, y=y_img, w=img_w, h=img_h)
        except Exception:
            pdf.set_xy(x2, y_img)
            pdf.set_font("Helvetica", "", 8)
            pdf.cell(img_w, img_h, "[No Back ID]", border=1, align="C")
    else:
        pdf.set_xy(x2, y_img)
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(img_w, img_h, "[No Back ID]", border=1, align="C")

    pdf.set_y(y_img + img_h + 1)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_x(x1)
    pdf.cell(img_w, 3, "Front", align="C")
    pdf.set_x(x2)
    pdf.cell(img_w, 3, "Back", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    def draw_copy(label):
        """Draw one compact receipt block."""
        start_y = pdf.get_y()
        pdf.set_draw_color(26, 122, 58)
        pdf.set_line_width(0.4)

        # Outer box height estimate ~42mm
        box_h = 42
        pdf.rect(8, start_y, page_w, box_h)

        pdf.set_xy(10, start_y + 2)
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.cell(120, 3.5, "MINISTRY OF AGRICULTURE - PRODUCT DISTRIBUTION PROGRAM")
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(0, 3.5, label, align="R", new_x="LMARGIN", new_y="NEXT")

        pdf.set_x(10)
        pdf.set_font("Helvetica", "", 7)
        pdf.cell(120, 3, "CHEBANGO TEA FACTORY")
        pdf.cell(0, 3, f"Receipt No: {r['receipt_no']}", align="R", new_x="LMARGIN", new_y="NEXT")

        pdf.set_x(10)
        pdf.cell(0, 3, f"Date: {r['date_str']}", align="R", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

        # Details — Received By = farmer, Phone = farmer mobile
        rows = [
            ("Farmer Name:", r["farmer_name"]),
            ("ID Number:", r["id_number"]),
            ("Grower Number:", r["grower_number"]),
            ("Product(s):", r["product"]),
            ("Total Quantity:", str(r["quantity"])),
            ("Received By:", r["farmer_name"]),
            ("Phone:", r["mobile"]),
        ]
        pdf.set_font("Helvetica", "", 7.5)
        for label_t, val in rows:
            pdf.set_x(12)
            pdf.set_font("Helvetica", "B", 7.5)
            pdf.cell(32, 3.2, label_t)
            pdf.set_font("Helvetica", "", 7.5)
            # Truncate long product lines
            text = str(val)
            if len(text) > 70:
                text = text[:67] + "..."
            pdf.cell(0, 3.2, text, new_x="LMARGIN", new_y="NEXT")

        # Signature lines
        sig_y = start_y + box_h - 8
        pdf.set_draw_color(50, 50, 50)
        pdf.set_line_width(0.2)
        pdf.line(18, sig_y, 80, sig_y)
        pdf.line(120, sig_y, 185, sig_y)
        pdf.set_xy(18, sig_y + 1)
        pdf.set_font("Helvetica", "", 6.5)
        pdf.cell(62, 3, "Recipient Signature", align="C")
        pdf.set_xy(120, sig_y + 1)
        pdf.cell(65, 3, "Authorized Officer", align="C")

        pdf.set_y(start_y + box_h + 2)

    draw_copy("STORE RECEIPT")
    # dashed separator
    pdf.set_draw_color(100, 100, 100)
    y = pdf.get_y()
    for x in range(10, 200, 4):
        pdf.line(x, y, x + 2, y)
    pdf.ln(3)

    draw_copy("GATE COPY")
    y = pdf.get_y()
    for x in range(10, 200, 4):
        pdf.line(x, y, x + 2, y)
    pdf.ln(3)

    draw_copy("FARMER COPY")

    pdf.set_y(pdf.get_y() + 1)
    pdf.set_font("Helvetica", "I", 6.5)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 3, "This receipt number is traceable and secured. Keep the duplicate copy for your records.", align="C")

    buf = BytesIO()
    pdf.output(buf)
    return buf.getvalue()


def render_professional_receipt_preview(r):
    """Compact on-screen preview (not for printing — use PDF)."""
    front_img = r.get("id_front_b64")
    back_img = r.get("id_back_b64")

    front_html = (
        f'<img src="{front_img}" style="max-width:360px; max-height:220px; border:1px solid #999;">'
        if front_img else
        '<div style="width:360px;height:220px;border:1px dashed #aaa;display:flex;align-items:center;justify-content:center;color:#888;font-size:12px;">No Front ID</div>'
    )
    back_html = (
        f'<img src="{back_img}" style="max-width:360px; max-height:220px; border:1px solid #999;">'
        if back_img else
        '<div style="width:360px;height:220px;border:1px dashed #aaa;display:flex;align-items:center;justify-content:center;color:#888;font-size:12px;">No Back ID</div>'
    )

    details = f"""
        <tr><td class="label">Farmer Name:</td><td>{r['farmer_name']}</td></tr>
        <tr><td class="label">ID Number:</td><td>{r['id_number']}</td></tr>
        <tr><td class="label">Grower Number:</td><td>{r['grower_number']}</td></tr>
        <tr><td class="label">Product(s):</td><td>{r['product']}</td></tr>
        <tr><td class="label">Total Quantity:</td><td><b>{r['quantity']}</b></td></tr>
        <tr><td class="label">Received By:</td><td>{r['farmer_name']}</td></tr>
        <tr><td class="label">Phone:</td><td>{r['mobile']}</td></tr>
    """

    def block(copy_label):
        return f"""
        <div class="receipt-box">
            <div class="header-row">
                <div>
                    <div class="title">MINISTRY OF AGRICULTURE - PRODUCT DISTRIBUTION PROGRAM</div>
                    <div class="factory">CHEBANGO TEA FACTORY</div>
                </div>
                <div class="right-info">
                    <div style="font-weight:bold;">{copy_label}</div>
                    <div>Receipt No: {r['receipt_no']}</div>
                    <div>Date: {r['date_str']}</div>
                </div>
            </div>
            <table>{details}</table>
            <div class="signatures">
                <div class="sign-box">Recipient Signature</div>
                <div class="sign-box">Authorized Officer</div>
            </div>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html><head>
    <style>
        body {{ font-family: Arial, sans-serif; color: #000; margin: 0; padding: 6px; font-size: 12px; }}
        .id-section {{ text-align: center; margin-bottom: 6px; }}
        .id-section h3 {{ margin: 0 0 6px 0; font-size: 13px; }}
        .id-images {{ display: flex; justify-content: center; gap: 16px; flex-wrap: wrap; }}
        .receipt-box {{ border: 1.5px solid #1a7a3a; padding: 8px 10px; margin-bottom: 8px; border-radius: 2px; }}
        .header-row {{ display: flex; justify-content: space-between; gap: 6px; }}
        .title {{ font-weight: bold; font-size: 11px; }}
        .factory {{ font-size: 10px; }}
        .right-info {{ text-align: right; font-size: 11px; }}
        table {{ width: 100%; margin-top: 6px; font-size: 11.5px; border-collapse: collapse; }}
        td {{ padding: 1px 0; }}
        .label {{ width: 110px; font-weight: bold; }}
        .signatures {{ display: flex; justify-content: space-between; margin-top: 16px; }}
        .sign-box {{ width: 42%; text-align: center; border-top: 1px solid #333; padding-top: 3px; font-size: 10px; }}
        .footer {{ text-align: center; font-size: 10px; color: #555; margin-top: 6px; }}
        .dashed {{ border-top: 1px dashed #666; margin: 6px 0; }}
    </style>
    </head><body>
        <div class="id-section">
            <h3>FARMER IDENTIFICATION</h3>
            <div class="id-images">
                <div>{front_html}<div style="font-size:10px;">Front</div></div>
                <div>{back_html}<div style="font-size:10px;">Back</div></div>
            </div>
        </div>
        <hr style="border:none;border-top:1px solid #333;margin:6px 0;">
        {block("STORE RECEIPT")}
        <div class="dashed"></div>
        {block("GATE COPY")}
        <div class="dashed"></div>
        {block("FARMER COPY")}
        <p class="footer">This receipt number is traceable and secured.</p>
    </body></html>
    """
    components.html(html, height=980, scrolling=True)


def page_receipt():
    st.title("🧾 Receipt")

    if not st.session_state.last_receipt:
        st.warning("No receipt has been generated yet. Please go to **Issue to Farmer** first.")
        return

    r = st.session_state.last_receipt

    # PDF download — primary action
    if FPDF_AVAILABLE:
        try:
            pdf_bytes = build_receipt_pdf(r)
            st.download_button(
                label="📥 Download Receipt PDF",
                data=pdf_bytes,
                file_name=f"Chebango_Receipt_{r['receipt_no']}.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )
            st.caption("Download the PDF, open it, then print. This avoids browser headers/footers and system links.")
        except Exception as e:
            st.error(f"Could not generate PDF: {e}")
            st.info("You can still use the preview below and print with Ctrl+P (turn off headers/footers in the print dialog).")
    else:
        st.warning("PDF library not available. Use the preview below and print with Ctrl+P.")

    st.markdown("---")
    st.caption(f"Receipt No: **{r['receipt_no']}**  ·  {r['date_str']} (East Africa Time)")
    render_professional_receipt_preview(r)


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
        file_name=f"Chebango_Farmers_{now_eat().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )


def page_reports():
    st.title("📄 Reports")
    stock = load_stock()
    df = load_farmers()

    st.subheader("Stock Summary")
    st.caption("Available is always calculated as Received − Issued.")
    for p, v in stock.items():
        st.write(f"**{p}** → Received: **{v['received']}** | Issued: **{v['issued']}** | Available: **{v['available']}**")

    st.subheader("Issuance Summary")
    # Unique farmers by receipt (multi-product issues share one receipt)
    if not df.empty:
        unique_receipts = df["Receipt_No"].nunique() if "Receipt_No" in df.columns else len(df)
        st.write(f"Total Issuance Transactions: **{unique_receipts}**")
        st.write(f"Total Line Items: **{len(df)}**")
        st.write(f"Total Quantity Distributed: **{df['Quantity'].sum()}**")
    else:
        st.write("Total Farmers Served: **0**")


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
            elif "📷 Remote ID Capture" in menu:
                page_remote_capture()
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
