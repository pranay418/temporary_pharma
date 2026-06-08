import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date

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

# ---------------- AI: STORAGE LOCATION ----------------
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

# ---------------- AI: DISEASE → MEDICINE ----------------
disease_map = {
    "fever": ["Paracetamol", "Dolo 650", "Crocin"],
    "diabetes": ["Metformin", "Insulin"],
    "pain": ["Ibuprofen", "Aspirin"],
    "infection": ["Amoxicillin", "Azithromycin"]
}

# ---------------- MENU ----------------
menu = st.sidebar.selectbox(
    "Menu",
    [
        "Dashboard",
        "Add Medicine",
        "View Medicines",
        "Billing System",
        "Daily Reports",
        "Sales History",
        "Disease AI Assistant"
    ]
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

    st.header("Add Medicine")

    name = st.text_input("Medicine Name")

    quantity = st.number_input(
        "Quantity",
        min_value=0
    )

    price = st.number_input(
        "Price",
        min_value=0.0
    )

    expiry = st.date_input(
        "Expiry Date"
    )

    if st.button("Add Medicine"):

        cursor.execute(
            """
            INSERT INTO medicines
            (name, quantity, price, expiry_date)
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                quantity,
                price,
                str(expiry)
            )
        )

        conn.commit()

        st.success("Medicine Added Successfully")
# ---------------- VIEW MEDICINES (FIXED COLUMN ISSUE) ----------------
elif menu == "View Medicines":

    st.header("Inventory")
    df = df.reset_index(drop=True)

    df = pd.read_sql_query(
        "SELECT * FROM medicines",
        conn
    )

    # Keep header row (Streamlit table)
    st.dataframe(df, use_container_width=True)
    st.markdown("### Manage Medicines")

    for i, row in df.iterrows():

        col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 3])

        with col1:
            st.write(row["id"])

        with col2:
            st.write(row["name"])

        with col3:
            st.write(row["quantity"])

        with col4:
            st.write(row["price"])

        with col5:

            btn1, btn2 = st.columns(2)

            # EDIT BUTTON
            with btn1:
                if st.button("✏️ Edit", key=f"edit_{row['id']}"):

                    st.session_state["edit_id"] = row["id"]
                    st.session_state["edit_name"] = row["name"]
                    st.session_state["edit_qty"] = row["quantity"]
                    st.session_state["edit_price"] = row["price"]
                    st.session_state["edit_expiry"] = row["expiry_date"]

            # DELETE BUTTON
            with btn2:
                if st.button("🗑 Delete", key=f"delete_{row['id']}"):

                    cursor.execute(
                        "DELETE FROM medicines WHERE id=?",
                        (row["id"],)
                    )
                    conn.commit()
                    st.success(f"{row['name']} deleted successfully")
                    st.rerun()
# ---------------- BILLING SYSTEM ----------------
elif menu == "Billing System":

    st.header("💰 Billing System")

    df = pd.read_sql_query("SELECT * FROM medicines", conn)

    if len(df) == 0:
        st.warning("No medicines available")
    else:

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

    st.header("📊 Daily Report")

    today = str(date.today())

    df = pd.read_sql_query("SELECT * FROM sales", conn)

    today_sales = df[df["sale_date"] == today]

    revenue = today_sales["total_price"].sum() if len(today_sales) > 0 else 0
    items = today_sales["quantity"].sum() if len(today_sales) > 0 else 0

    st.metric("Revenue Today (₹)", revenue)
    st.metric("Items Sold", items)

    st.dataframe(today_sales)

# ---------------- SALES HISTORY ----------------
elif menu == "Sales History":

    st.header("🧾 Sales History")

    df = pd.read_sql_query("SELECT * FROM sales ORDER BY id DESC", conn)

    st.dataframe(df)

# ---------------- DISEASE AI ----------------
elif menu == "Disease AI Assistant":

    st.header("🧠 Disease → Medicine AI System")

    disease = st.text_input("Enter Disease (fever, diabetes, pain, infection)")

    if disease:

        disease = disease.lower()

        if disease in disease_map:

            st.success("Recommended Medicines:")

            for med in disease_map[disease]:
                st.write("💊", med)

        else:
            st.warning("No AI data available for this disease yet")
