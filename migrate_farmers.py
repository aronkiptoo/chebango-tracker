"""
One-time migration script: pushes your exported Farmers Excel file into Supabase.

HOW TO USE:
1. Run `pip install supabase pandas openpyxl` on your own computer (not on Streamlit Cloud).
2. Fill in SUPABASE_URL and SUPABASE_KEY below (same values you put in Streamlit secrets).
3. Put the Excel file you downloaded from "Farmers List -> Download Excel" in the same
   folder as this script, and set EXCEL_FILE to its filename below.
4. Run:  python migrate_farmers.py
5. Delete this file afterwards (or at least blank out the keys) since it contains secrets.
"""

import pandas as pd
from supabase import create_client

# ---- FILL THESE IN ----
SUPABASE_URL = "https://YOUR-PROJECT.supabase.co"
SUPABASE_KEY = "YOUR-SERVICE-ROLE-KEY"
EXCEL_FILE = "Chebango_Farmers_20260101.xlsx"  # change to your actual exported filename

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

df = pd.read_excel(EXCEL_FILE)

# Map the Excel's Title_Case columns to the database's lowercase columns
column_map = {
    "Receipt_No": "receipt_no",
    "Date": "date",
    "Time": "time",
    "Farmer_Name": "farmer_name",
    "Grower_Number": "grower_number",
    "ID_Number": "id_number",
    "Mobile": "mobile",
    "Product": "product",
    "Quantity": "quantity",
    "Issued_By": "issued_by",
    "Department": "department",
    "Issuer_Mobile": "issuer_mobile",
}

records = []
for _, row in df.iterrows():
    record = {}
    for excel_col, db_col in column_map.items():
        if excel_col in df.columns:
            value = row[excel_col]
            # Convert NaN / pandas nulls to None so Supabase accepts them
            record[db_col] = None if pd.isna(value) else value
    records.append(record)

if not records:
    print("No records found in the Excel file. Nothing to migrate.")
else:
    # Insert in batches of 200 to stay well under request size limits
    batch_size = 200
    total = len(records)
    for i in range(0, total, batch_size):
        batch = records[i:i + batch_size]
        supabase.table("farmers").insert(batch).execute()
        print(f"Inserted {min(i + batch_size, total)}/{total} records...")

    print(f"Done. Migrated {total} farmer records into Supabase.")