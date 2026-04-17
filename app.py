import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# PAGE CONFIG
st.set_page_config(page_title="Food Wastage Dashboard", layout="wide")

# DB CONNECTION
conn = sqlite3.connect(r"D:\Innovexis\project6\food.db")

# TITLE
st.title(" Food Wastage Management Dashboard")


#  KPI CARDS
total_food = pd.read_sql("SELECT SUM(Quantity) FROM food_listings", conn).iloc[0,0]
total_providers = pd.read_sql("SELECT COUNT(*) FROM providers", conn).iloc[0,0]
total_receivers = pd.read_sql("SELECT COUNT(*) FROM receivers", conn).iloc[0,0]
total_claims = pd.read_sql("SELECT COUNT(*) FROM claims", conn).iloc[0,0]

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Food Quantity", total_food)
col2.metric("Total Providers", total_providers)
col3.metric("Total Receivers", total_receivers)
col4.metric("Total Claims", total_claims)

# SIDEBAR FILTERS
st.sidebar.header(" Filters")

cities = pd.read_sql("SELECT DISTINCT Location FROM food_listings", conn)['Location']
food_types = pd.read_sql("SELECT DISTINCT Food_Type FROM food_listings", conn)['Food_Type']
meal_types = pd.read_sql("SELECT DISTINCT Meal_Type FROM food_listings", conn)['Meal_Type']
provider_ids = pd.read_sql("SELECT DISTINCT Provider_ID FROM food_listings", conn)['Provider_ID']

selected_city = st.sidebar.selectbox("City", ["All"] + list(cities))
selected_food = st.sidebar.selectbox("Food Type", ["All"] + list(food_types))
selected_meal = st.sidebar.selectbox("Meal Type", ["All"] + list(meal_types))
selected_provider = st.sidebar.selectbox("Provider", ["All"] + list(provider_ids))

# FILTERED DATA
query = """
SELECT f.*, p.Name as Provider_Name, p.Contact
FROM food_listings f
JOIN providers p ON f.Provider_ID = p.Provider_ID
WHERE 1=1
"""

if selected_city != "All":
    query += f" AND f.Location = '{selected_city}'"

if selected_food != "All":
    query += f" AND f.Food_Type = '{selected_food}'"

if selected_meal != "All":
    query += f" AND f.Meal_Type = '{selected_meal}'"

if selected_provider != "All":
    query += f" AND p.Name = '{selected_provider}'"

df = pd.read_sql(query, conn)

# DATA TABLE
st.subheader(" Food Listings")
st.dataframe(df, use_container_width=True)

# CHARTS
st.subheader(" Insights")

col1, col2 = st.columns(2)

with col1:
    chart1 = pd.read_sql("SELECT Food_Type, COUNT(*) as count FROM food_listings GROUP BY Food_Type", conn)
    fig1, ax1 = plt.subplots()
    ax1.bar(chart1['Food_Type'], chart1['count'])

    for i, v in enumerate(chart1['count']):
      ax1.text(i, v, str(v), ha='center', va='bottom')

    ax1.set_title("Food Type Distribution")
    st.pyplot(fig1)

with col2:
    chart2 = pd.read_sql("SELECT Meal_Type, COUNT(*) as count FROM food_listings GROUP BY Meal_Type", conn)
    fig2, ax2 = plt.subplots()
    ax2.bar(chart2['Meal_Type'], chart2['count'])

    for i, v in enumerate(chart2['count']):
      ax2.text(i, v, str(v), ha='center', va='bottom')

    ax2.set_title("Meal Type Distribution")
    st.pyplot(fig2)

    

# SQL INSIGHTS
st.subheader(" SQL Insights")

option = st.selectbox("Select Query", [
    "1. Providers per city",
    "2. Receivers per city",
    "3. Provider type contributes most",
    "4. Provider contact by city",
    "5. Top receiver",
    "6. Total food available",
    "7. City with most listings",
    "8. Most common food type",
    "9. Claims per food item",
    "10. Top provider (successful claims)",
    "11. Claim status %",
    "12. Avg food per receiver",
    "13. Most claimed meal type",
    "14. Total food per provider",
    "15. Expiring soon food"
])

if option == "1. Providers per city":
    q = "SELECT City, COUNT(*) as total_providers FROM providers GROUP BY City"

elif option == "2. Receivers per city":
    q = "SELECT City, COUNT(*) as total_receivers FROM receivers GROUP BY City"

elif option == "3. Provider type contributes most":
    q = "SELECT Provider_Type, SUM(Quantity) as total_food FROM food_listings GROUP BY Provider_Type ORDER BY total_food DESC"

elif option == "4. Provider contact by city":
    city = st.selectbox("Select City", pd.read_sql("SELECT DISTINCT City FROM providers", conn)['City'])
    q = f"SELECT Name, Contact, City FROM providers WHERE City = '{city}'"

elif option == "5. Top receiver":
    q = """SELECT r.Name, COUNT(c.Claim_ID) AS total_claims
           FROM claims c
           JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
           GROUP BY r.Name
           ORDER BY total_claims DESC"""

elif option == "6. Total food available":
    q = "SELECT SUM(Quantity) as total_food FROM food_listings"

elif option == "7. City with most listings":
    q = "SELECT Location, COUNT(*) as total_listings FROM food_listings GROUP BY Location ORDER BY total_listings DESC"

elif option == "8. Most common food type":
    q = "SELECT Food_Type, COUNT(*) as count FROM food_listings GROUP BY Food_Type ORDER BY count DESC"

elif option == "9. Claims per food item":
    q = "SELECT Food_ID, COUNT(*) as total_claims FROM claims GROUP BY Food_ID"

elif option == "10. Top provider (successful claims)":
    q = """SELECT p.Name, COUNT(*) as successful_claims
           FROM claims c
           JOIN food_listings f ON c.Food_ID = f.Food_ID
           JOIN providers p ON f.Provider_ID = p.Provider_ID
           WHERE c.Status = 'Completed'
           GROUP BY p.Name
           ORDER BY successful_claims DESC"""

elif option == "11. Claim status %":
    q = """SELECT Status,
           COUNT(*) * 100.0 / (SELECT COUNT(*) FROM claims) as percentage
           FROM claims
           GROUP BY Status"""

elif option == "12. Avg food per receiver":
    q = """SELECT r.Name, AVG(f.Quantity) as avg_quantity
           FROM claims c
           JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
           JOIN food_listings f ON c.Food_ID = f.Food_ID
           GROUP BY r.Name"""

elif option == "13. Most claimed meal type":
    q = """SELECT f.Meal_Type, COUNT(*) as total_claims
           FROM claims c
           JOIN food_listings f ON c.Food_ID = f.Food_ID
           GROUP BY f.Meal_Type
           ORDER BY total_claims DESC"""

elif option == "14. Total food per provider":
    q = """SELECT p.Name, SUM(f.Quantity) as total_donated
           FROM food_listings f
           JOIN providers p ON f.Provider_ID = p.Provider_ID
           GROUP BY p.Name
           ORDER BY total_donated DESC"""

elif option == "15. Expiring soon food":
    q = "SELECT Food_Name, Expiry_Date FROM food_listings WHERE Expiry_Date <= DATE('now', '+1 day')"
# run query
df_query = pd.read_sql(q, conn)
st.dataframe(df_query)

# CRUD SECTION
st.subheader(" Manage Food Listings")

tab1, tab2, tab3 = st.tabs([" Add", " Update", " Delete"])

# ADD
with tab1:
    food_name = st.text_input("Food Name")
    quantity = st.number_input("Quantity", min_value=1)
    provider_id = st.number_input("Provider ID", min_value=1)
    location = st.text_input("Location")
    food_type = st.selectbox("Food Type", ["Vegetarian", "Non-Vegetarian", "Vegan"])
    meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snacks"])

    if st.button("Add Food"):
        conn.execute(f"""
        INSERT INTO food_listings (Food_Name, Quantity, Provider_ID, Location, Food_Type, Meal_Type)
        VALUES ('{food_name}', {quantity}, {provider_id}, '{location}', '{food_type}', '{meal_type}')
        """)
        conn.commit()
        st.success("Added successfully ")

# UPDATE
with tab2:
    food_ids = pd.read_sql("SELECT Food_ID FROM food_listings", conn)['Food_ID']
    update_id = st.selectbox("Select Food ID", food_ids)

    data = pd.read_sql(f"SELECT * FROM food_listings WHERE Food_ID={update_id}", conn)

    if not data.empty:
        row = data.iloc[0]

        new_name = st.text_input("Food Name", row['Food_Name'])
        new_qty = st.number_input("Quantity", value=int(row['Quantity']))
        new_loc = st.text_input("Location", row['Location'])

        if st.button("Update Food"):
            conn.execute(f"""
            UPDATE food_listings
            SET Food_Name='{new_name}', Quantity={new_qty}, Location='{new_loc}'
            WHERE Food_ID={update_id}
            """)
            conn.commit()
            st.success("Updated ")

# DELETE
with tab3:
    food_ids = pd.read_sql("SELECT Food_ID FROM food_listings", conn)['Food_ID']
    delete_id = st.selectbox("Select Food ID to delete", food_ids)

    if st.button("Delete Food"):
        conn.execute(f"DELETE FROM food_listings WHERE Food_ID={delete_id}")
        conn.commit()
        st.warning("Deleted ")


#  MANAGE CLAIMS
st.subheader(" Manage Claims")

tab1, tab2, tab3 = st.tabs([" Add Claim", " Update Claim", " Delete Claim"])

#  ADD CLAIM
with tab1:
    food_ids = pd.read_sql("SELECT Food_ID FROM food_listings", conn)['Food_ID']
    receiver_ids = pd.read_sql("SELECT Receiver_ID FROM receivers", conn)['Receiver_ID']

    food_id = st.selectbox("Select Food ID", food_ids, key="add_food")
    receiver_id = st.selectbox("Select Receiver ID", receiver_ids, key="add_receiver")
    status = st.selectbox("Status", ["Pending", "Completed", "Cancelled"])

    if st.button("Add Claim"):
        conn.execute(f"""
        INSERT INTO claims (Food_ID, Receiver_ID, Status, Timestamp)
        VALUES ({food_id}, {receiver_id}, '{status}', datetime('now'))
        """)
        conn.commit()
        st.success("Claim Added ")

#  UPDATE CLAIM
with tab2:
    claim_ids = pd.read_sql("SELECT Claim_ID FROM claims", conn)['Claim_ID']
    claim_id = st.selectbox("Select Claim ID", claim_ids, key="update_claim")

    claim_data = pd.read_sql(f"SELECT * FROM claims WHERE Claim_ID={claim_id}", conn)

    if not claim_data.empty:
        row = claim_data.iloc[0]

        new_status = st.selectbox(
            "Update Status",
            ["Pending", "Completed", "Cancelled"],
            index=["Pending", "Completed", "Cancelled"].index(row['Status'])
        )

        if st.button("Update Claim"):
            conn.execute(f"""
            UPDATE claims
            SET Status = '{new_status}'
            WHERE Claim_ID = {claim_id}
            """)
            conn.commit()
            st.success("Claim Updated ")

#  DELETE CLAIM
with tab3:
    claim_ids = pd.read_sql("SELECT Claim_ID FROM claims", conn)['Claim_ID']
    delete_claim = st.selectbox("Select Claim ID to delete", claim_ids, key="delete_claim")

    if st.button("Delete Claim"):
        conn.execute(f"DELETE FROM claims WHERE Claim_ID = {delete_claim}")
        conn.commit()
        st.warning("Claim Deleted ")

