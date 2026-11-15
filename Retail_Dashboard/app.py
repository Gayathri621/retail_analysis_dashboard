
import streamlit as st
import pandas as pd

# -----------------------------------
# PAGE CONFIGURATION
# -----------------------------------

st.set_page_config(
    page_title="Retail Insights Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------
# DATA LOADING
# -----------------------------------

@st.cache_data
def load_data():
    df = pd.read_csv("data/BITS_Retail_Cleaned_Integrated.csv")
    df["Order_Date"] = pd.to_datetime(df["Order_Date"])
    return df


# -----------------------------------
# HOME PAGE
# -----------------------------------

def home_page():

    df = load_data()

    total_sales = df["Net_Sales"].sum()
    total_profit = df["Profit"].sum()
    total_orders = df["Order_ID"].nunique()
    profit_margin = total_profit / total_sales * 100

    st.title("📊 Retail Insights Dashboard")
    st.subheader("Management Performance Overview | 2024–2026")

    st.markdown(
        "Explore business performance across sales, regions, "
        "product categories and discount strategies."
    )

    st.divider()

    # KPI CARDS

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Net Sales",
        f"₹{total_sales / 10000000:.2f} Cr"
    )

    col2.metric(
        "Total Profit",
        f"₹{total_profit / 100000:.2f} L"
    )

    col3.metric(
        "Transactions",
        f"{total_orders:,}"
    )

    col4.metric(
        "Profit Margin",
        f"{profit_margin:.2f}%"
    )

    st.divider()

    st.subheader("Explore Business Performance")

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("### 📈 Sales Performance")
            st.write(
                "Understand annual growth, monthly trends "
                "and changes in profitability."
            )

        with st.container(border=True):
            st.markdown("### 🌍 Regional Performance")
            st.write(
                "Compare sales, profit and margins across "
                "the five business regions."
            )

        with st.container(border=True):
            st.markdown("### 📦 Product Performance")
            st.write(
                "Identify the categories and subcategories "
                "driving revenue and profit."
            )

    with col2:
        with st.container(border=True):
            st.markdown("### 🏷️ Discount Effectiveness")
            st.write(
                "Evaluate how discount levels are associated "
                "with sales and profitability."
            )

        with st.container(border=True):
            st.markdown("### 💡 Management Recommendations")
            st.write(
                "Explore the key findings and two recommended "
                "actions for management."
            )

    st.divider()

    st.caption(
        "Data source: Integrated retail transactions and master data. "
        "All supplied records for 2024–2026 are included."
    )


# -----------------------------------
# CONTROLLED NAVIGATION
# -----------------------------------

pg = st.navigation([
    st.Page(home_page, title="Overview", icon="🏠", default=True),
    st.Page("pages/Sales_Performance.py",
            title="Sales Performance", icon="📈"),
    st.Page("pages/Regional_Performance.py",
            title="Regional Performance", icon="🌍"),
    st.Page("pages/Product_Performance.py",
            title="Product Performance", icon="📦"),
    st.Page("pages/Discount_Effectiveness.py",
            title="Discount Effectiveness", icon="🏷️"),
    st.Page("pages/Recommendations.py",
            title="Recommendations", icon="💡")
])

# -----------------------------------
# SIDEBAR BRANDING
# -----------------------------------

st.sidebar.title("📊 Retail Insights")
st.sidebar.caption("Business Performance Dashboard")
st.sidebar.divider()

try:
    df_sidebar = load_data()

    st.sidebar.metric(
        "Total Transactions",
        f"{df_sidebar['Order_ID'].nunique():,}"
    )

    st.sidebar.metric(
        "Total Net Sales",
        f"₹{df_sidebar['Net_Sales'].sum()/10000000:.2f} Cr"
    )

    st.sidebar.divider()

    st.sidebar.caption("Retail analytics | 2024–2026")

except Exception as e:
    st.sidebar.error(f"Dataset loading error: {e}")

# -----------------------------------
# RUN SELECTED PAGE
# -----------------------------------

pg.run()
