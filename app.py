import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date

# ---------------- DB ----------------
conn = sqlite3.connect("pharmacy.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS medicines(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    quantity INTEGER,
    price REAL,
    expiry_date TEXT,
    location TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS sales(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medicine_name TEXT,
    quantity INTEGER,
    total_price REAL,
    sale_date TEXT
)
""")

conn.commit()

st.set_page_config(page_title="Smart Pharmacy System")
st.title("💊 Smart Pharmacy System (AI + Billing + Reports)")

# ---------------- MENU ----------------
menu = st.sidebar.selectbox(
    "Menu",
    ["Dashboard", "Add Medicine", "View Medicines", "Billing System", "Daily Reports", "Sales History"]
)

# ---------------- DASHBOARD ----------------
if menu == "Dashboard":

    st.header("📊 Dashboard")

    df = pd.read_sql_query("SELECT * FROM medicines", conn)

    st.metric("Total Medicines", len(df))

    if len(df) > 0:
        low_stock = df[df["quantity"] < 10]

        st.subheader("⚠️ Low Stock Alerts")

        if len(low_stock) > 0:
            st.dataframe(low_stock)
        else:
            st.success("Stock is Healthy")

# ---------------- ADD MEDICINE ----------------
elif menu == "Add Medicine":

    st.header("➕ Add Medicine")

    name = st.text_input("Medicine Name")
    quantity = st.number_input("Quantity", min_value=0)
    price = st.number_input("Price", min_value=0.0)
    expiry = st.date_input("Expiry Date")
    location = st.text_input("Location (optional)", "Auto Assigned")

    if st.button("Add Medicine"):

        cursor.execute("""
            INSERT INTO medicines (name, quantity, price, expiry_date, location)
            VALUES (?, ?, ?, ?, ?)
        """, (name, quantity, price, str(expiry), location))

        conn.commit()
        st.success("Medicine Added Successfully")

# ---------------- VIEW ----------------
elif menu == "View Medicines":

    st.header("📦 Inventory")

    df = pd.read_sql_query("SELECT * FROM medicines", conn)
    st.dataframe(df)

# ---------------- BILLING SYSTEM ----------------
elif menu == "Billing System":

    st.header("💰 Billing System")

    df = pd.read_sql_query("SELECT * FROM medicines", conn)

    medicine_list = df["name"].tolist()

    selected_medicine = st.selectbox("Select Medicine", medicine_list)

    qty = st.number_input("Quantity", min_value=1)

    if st.button("Generate Bill"):

        medicine = df[df["name"] == selected_medicine].iloc[0]

        if medicine["quantity"] >= qty:

            total = qty * medicine["price"]

            # reduce stock
            cursor.execute("""
                UPDATE medicines
                SET quantity = quantity - ?
                WHERE name = ?
            """, (qty, selected_medicine))

            # save sale
            cursor.execute("""
                INSERT INTO sales (medicine_name, quantity, total_price, sale_date)
                VALUES (?, ?, ?, ?)
            """, (selected_medicine, qty, total, str(date.today())))

            conn.commit()

            st.success("Bill Generated Successfully 💰")
            st.info(f"Total Amount: ₹{total}")

        else:
            st.error("Not Enough Stock!")

# ---------------- DAILY REPORTS ----------------
elif menu == "Daily Reports":

    st.header("📊 Daily Sales Report")

    today = str(date.today())

    df = pd.read_sql_query("SELECT * FROM sales", conn)

    today_sales = df[df["sale_date"] == today]

    total_revenue = today_sales["total_price"].sum() if len(today_sales) > 0 else 0
    total_items = today_sales["quantity"].sum() if len(today_sales) > 0 else 0

    st.metric("Total Revenue Today (₹)", total_revenue)
    st.metric("Total Items Sold", total_items)

    st.subheader("Today's Sales")

    if len(today_sales) > 0:
        st.dataframe(today_sales)
    else:
        st.warning("No sales today")

# ---------------- SALES HISTORY ----------------
elif menu == "Sales History":

    st.header("🧾 All Sales History")

    df = pd.read_sql_query("SELECT * FROM sales ORDER BY id DESC", conn)

    st.dataframe(df)
