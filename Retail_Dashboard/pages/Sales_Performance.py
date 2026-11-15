
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------
# THEME CONFIGURATION
# -----------------------------------

is_dark = st.get_option("theme.base") == "dark"
chart_template = "plotly_dark" if is_dark else "plotly_white"

year_colors = {
    2024: "#2878A5",
    2025: "#35A68A",
    2026: "#E49B45"
}

# -----------------------------------
# LOAD DATA
# -----------------------------------

@st.cache_data
def load_data():
    df = pd.read_csv("data/BITS_Retail_Cleaned_Integrated.csv")
    df["Order_Date"] = pd.to_datetime(df["Order_Date"])
    return df

df = load_data()

# -----------------------------------
# HEADER
# -----------------------------------

st.title("Sales Performance")
st.markdown(
    "### Revenue growth, monthly trends and profitability | 2024–2026"
)

st.divider()

# -----------------------------------
# YEAR FILTER
# -----------------------------------

years = sorted(df["Order_Date"].dt.year.unique())

selected_years = st.multiselect(
    "Select years",
    years,
    default=years,
    key="sales_years"
)

filtered_df = df[
    df["Order_Date"].dt.year.isin(selected_years)
].copy()

if filtered_df.empty:
    st.warning("Select at least one year to view the analysis.")
    st.stop()

# -----------------------------------
# KPI CALCULATIONS
# -----------------------------------

total_sales = filtered_df["Net_Sales"].sum()
total_profit = filtered_df["Profit"].sum()
total_orders = filtered_df["Order_ID"].nunique()
margin = total_profit / total_sales * 100 if total_sales else 0

c1, c2, c3, c4 = st.columns(4)

c1.metric("Net Sales", f"₹{total_sales/10000000:.2f} Cr")
c2.metric("Total Profit", f"₹{total_profit/100000:.2f} L")
c3.metric("Transactions", f"{total_orders:,}")
c4.metric("Profit Margin", f"{margin:.2f}%")

st.divider()

# -----------------------------------
# ANNUAL PERFORMANCE
# -----------------------------------

st.subheader("Annual Sales and Profit Performance")

annual = (
    filtered_df.assign(
        Year=filtered_df["Order_Date"].dt.year
    )
    .groupby("Year")
    .agg(
        Net_Sales=("Net_Sales", "sum"),
        Profit=("Profit", "sum"),
        Orders=("Order_ID", "nunique")
    )
    .reset_index()
)

annual["Profit_Margin"] = (
    annual["Profit"] / annual["Net_Sales"] * 100
)

annual["Year"] = annual["Year"].astype(str)

col1, col2 = st.columns(2)

# Annual Net Sales
with col1:
    fig_sales = px.bar(
        annual,
        x="Year",
        y="Net_Sales",
        text_auto=".3s",
        custom_data=["Profit", "Orders", "Profit_Margin"],
        title="Annual Net Sales",
        labels={
            "Year": "Year",
            "Net_Sales": "Net Sales (₹)"
        },
        color_discrete_sequence=["#2878A5"]
    )

    fig_sales.update_traces(
        hovertemplate=(
            "<b>Year: %{x}</b><br>"
            "Net Sales: ₹%{y:,.2f}<br>"
            "Profit: ₹%{customdata[0]:,.2f}<br>"
            "Transactions: %{customdata[1]:,.0f}<br>"
            "Profit Margin: %{customdata[2]:.2f}%"
            "<extra></extra>"
        )
    )

    fig_sales.update_layout(
        template=chart_template,
        height=370,
        showlegend=False,
        yaxis_title="Net Sales (₹)",
        xaxis_title="Year",
        margin=dict(t=65, b=50)
    )

    st.plotly_chart(fig_sales, use_container_width=True)

# Annual Profit
with col2:
    fig_profit = px.bar(
        annual,
        x="Year",
        y="Profit",
        text_auto=".3s",
        custom_data=["Net_Sales", "Orders", "Profit_Margin"],
        title="Annual Profit",
        labels={
            "Year": "Year",
            "Profit": "Profit (₹)"
        },
        color_discrete_sequence=["#35A68A"]
    )

    fig_profit.update_traces(
        hovertemplate=(
            "<b>Year: %{x}</b><br>"
            "Profit: ₹%{y:,.2f}<br>"
            "Net Sales: ₹%{customdata[0]:,.2f}<br>"
            "Transactions: %{customdata[1]:,.0f}<br>"
            "Profit Margin: %{customdata[2]:.2f}%"
            "<extra></extra>"
        )
    )

    fig_profit.update_layout(
        template=chart_template,
        height=370,
        showlegend=False,
        yaxis_title="Profit (₹)",
        xaxis_title="Year",
        margin=dict(t=65, b=50)
    )

    st.plotly_chart(fig_profit, use_container_width=True)

st.divider()

# -----------------------------------
# MONTHLY SALES TREND
# -----------------------------------

st.subheader("Monthly Sales Trend")

monthly = (
    filtered_df.assign(
        Year=filtered_df["Order_Date"].dt.year,
        Month=filtered_df["Order_Date"].dt.month,
        Month_Name=filtered_df["Order_Date"].dt.strftime("%b")
    )
    .groupby(["Year", "Month", "Month_Name"])
    .agg(
        Net_Sales=("Net_Sales", "sum"),
        Profit=("Profit", "sum"),
        Orders=("Order_ID", "nunique")
    )
    .reset_index()
    .sort_values(["Year", "Month"])
)

monthly["Profit_Margin"] = (
    monthly["Profit"] / monthly["Net_Sales"] * 100
)

month_order = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]

fig_monthly = px.line(
    monthly,
    x="Month_Name",
    y="Net_Sales",
    color="Year",
    markers=True,
    custom_data=["Profit", "Orders", "Profit_Margin"],
    title="Monthly Net Sales by Year",
    category_orders={
        "Month_Name": month_order
    },
    color_discrete_map=year_colors,
    labels={
        "Month_Name": "Month",
        "Net_Sales": "Net Sales (₹)",
        "Year": "Year"
    }
)

fig_monthly.update_traces(
    line=dict(width=2.5),
    marker=dict(size=8),
    hovertemplate=(
        "<b>%{x} %{fullData.name}</b><br>"
        "Net Sales: ₹%{y:,.2f}<br>"
        "Profit: ₹%{customdata[0]:,.2f}<br>"
        "Transactions: %{customdata[1]:,.0f}<br>"
        "Profit Margin: %{customdata[2]:.2f}%"
        "<extra></extra>"
    )
)

fig_monthly.update_layout(
    template=chart_template,
    height=430,
    xaxis_title="Month",
    yaxis_title="Net Sales (₹)",
    legend_title="Year",
    hovermode="x unified",
    margin=dict(t=65, b=50)
)

st.plotly_chart(fig_monthly, use_container_width=True)

# -----------------------------------
# MONTHLY PROFITABILITY
# -----------------------------------

st.subheader("Monthly Profit Margin")

fig_margin = px.line(
    monthly,
    x="Month_Name",
    y="Profit_Margin",
    color="Year",
    markers=True,
    custom_data=["Net_Sales", "Profit", "Orders"],
    title="Monthly Profit Margin by Year",
    category_orders={
        "Month_Name": month_order
    },
    color_discrete_map=year_colors,
    labels={
        "Month_Name": "Month",
        "Profit_Margin": "Profit Margin (%)",
        "Year": "Year"
    }
)

fig_margin.update_traces(
    line=dict(width=2.5),
    marker=dict(size=8),
    hovertemplate=(
        "<b>%{x} %{fullData.name}</b><br>"
        "Profit Margin: %{y:.2f}%<br>"
        "Net Sales: ₹%{customdata[0]:,.2f}<br>"
        "Profit: ₹%{customdata[1]:,.2f}<br>"
        "Transactions: %{customdata[2]:,.0f}"
        "<extra></extra>"
    )
)

fig_margin.update_layout(
    template=chart_template,
    height=410,
    xaxis_title="Month",
    yaxis_title="Profit Margin (%)",
    legend_title="Year",
    hovermode="x unified",
    margin=dict(t=65, b=50)
)

fig_margin.update_yaxes(ticksuffix="%")

st.plotly_chart(fig_margin, use_container_width=True)

st.divider()

# -----------------------------------
# BUSINESS OBSERVATIONS
# -----------------------------------

st.subheader("Key Observations")

st.markdown("""
- Net sales increased substantially across the three supplied years.
- Profit grew faster than net sales, indicating improving overall margins.
- Monthly performance varies considerably, so annual totals alone do not tell the full story.
""")

st.caption(
    "Note: The analysis includes all supplied transactions for 2024–2026. "
)
