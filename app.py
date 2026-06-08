import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# ---------------- DATABASE ----------------
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
conn.commit()

st.set_page_config(page_title="Smart Pharmacy AI System")

st.title("💊 Smart Pharmacy Management System (AI Powered)")

# ---------------- AI FUNCTIONS ----------------

def ai_place(medicine_name):
    name = medicine_name.lower()

    if any(x in name for x in ["paracetamol", "dolo", "crocin"]):
        return "Drawer A1 - Fever"
    elif any(x in name for x in ["metformin", "insulin", "glimepiride"]):
        return "Drawer B1 - Diabetes"
    elif any(x in name for x in ["ibuprofen", "diclofenac", "aspirin"]):
        return "Drawer A2 - Pain Relief"
    elif any(x in name for x in ["amoxicillin", "azithromycin"]):
        return "Drawer C1 - Antibiotics"
    else:
        return "Drawer D1 - General"

# Disease → Medicine AI (basic mapping)
disease_map = {
    "fever": ["Paracetamol", "Dolo 650"],
    "diabetes": ["Metformin", "Insulin"],
    "pain": ["Ibuprofen", "Aspirin"]
}

# ---------------- MENU ----------------
menu = st.sidebar.selectbox(
    "Select Menu",
    ["Dashboard", "Add Medicine", "View Medicines", "Search Medicine", "AI Assistant"]
)

# ---------------- DASHBOARD ----------------
if menu == "Dashboard":

    st.header("📊 Dashboard")

    df = pd.read_sql_query("SELECT * FROM medicines", conn)

    st.metric("Total Medicines", len(df))

    if len(df) > 0:

        # Low stock
        low_stock = df[df["quantity"] < 10]

        st.subheader("⚠️ Low Stock Medicines")
        if len(low_stock) > 0:
            st.dataframe(low_stock)
        else:
            st.success("No Low Stock Medicines")

        # Expiry AI
        st.subheader("⏳ Expiring Soon (30 Days)")
        df["expiry_date"] = pd.to_datetime(df["expiry_date"])

        soon_expiry = df[df["expiry_date"] <= (datetime.today() + timedelta(days=30))]

        if len(soon_expiry) > 0:
            st.dataframe(soon_expiry)
        else:
            st.success("No Expiring Medicines Soon")

        # AI Stock Recommendation
        st.subheader("🤖 AI Stock Prediction")

        avg_stock = df["quantity"].mean() if len(df) > 0 else 0
        prediction = int(avg_stock * 1.3)

        st.info(f"Predicted Demand Next Week: {prediction} Units")

        for _, row in low_stock.iterrows():
            st.warning(f"Restock → {row['name']} (AI Alert)")

# ---------------- ADD MEDICINE ----------------
elif menu == "Add Medicine":

    st.header("➕ Add Medicine")

    name = st.text_input("Medicine Name")
    quantity = st.number_input("Quantity", min_value=0)
    price = st.number_input("Price", min_value=0.0)
    expiry = st.date_input("Expiry Date")

    if st.button("Add Medicine"):

        location = ai_place(name)

        cursor.execute("""
            INSERT INTO medicines
            (name, quantity, price, expiry_date, location)
            VALUES (?, ?, ?, ?, ?)
        """, (name, quantity, price, str(expiry), location))

        conn.commit()

        st.success(f"Medicine Added Successfully → Stored at {location}")

# ---------------- VIEW ----------------
elif menu == "View Medicines":

    st.header("📦 Inventory")

    df = pd.read_sql_query("SELECT * FROM medicines", conn)

    st.dataframe(df)

# ---------------- SEARCH ----------------
elif menu == "Search Medicine":

    st.header("🔍 Search Medicine")

    search = st.text_input("Enter Medicine Name")

    if search:

        query = """
        SELECT * FROM medicines
        WHERE LOWER(name) LIKE LOWER(?)
        """

        df = pd.read_sql_query(query, conn, params=(f"%{search}%",))

        st.dataframe(df)

# ---------------- AI ASSISTANT ----------------
elif menu == "AI Assistant":

    st.header("🤖 Disease → Medicine AI Assistant")

    disease = st.text_input("Enter Disease (fever, diabetes, pain)")

    if disease:

        disease = disease.lower()

        if disease in disease_map:
            st.success("Recommended Medicines:")

            for med in disease_map[disease]:
                st.write("💊", med)
        else:
            st.warning("No data available for this disease")
