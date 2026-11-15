
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
# -----------------------------------
# THEME CONFIGURATION
# -----------------------------------

is_dark = st.get_option("theme.base") == "dark"
chart_template = "plotly_dark" if is_dark else "plotly_white"

SALES_COLOR = "#2878A5"
PROFIT_COLOR = "#35A68A"
MARGIN_COLOR = "#8B75B5"

# -----------------------------------
# LOAD DATA
# -----------------------------------

@st.cache_data
def load_data():
    df = pd.read_csv(BASE_DIR / "data" / "BITS_Retail_Cleaned_Integrated.csv")
    df["Order_Date"] = pd.to_datetime(df["Order_Date"])
    return df

df = load_data()

# -----------------------------------
# HEADER
# -----------------------------------

st.title("Regional Performance")
st.markdown(
    "### Comparing sales, profit and profitability across regions"
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
    key="regional_years"
)

filtered_df = df[
    df["Order_Date"].dt.year.isin(selected_years)
].copy()

if filtered_df.empty:
    st.warning("Select at least one year to view the regional analysis.")
    st.stop()

# -----------------------------------
# REGIONAL AGGREGATION
# -----------------------------------

regional = (
    filtered_df.groupby("Region")
    .agg(
        Orders=("Order_ID", "nunique"),
        Net_Sales=("Net_Sales", "sum"),
        Profit=("Profit", "sum"),
        Discount_Amount=("Discount_Amount", "sum")
    )
    .reset_index()
)

regional["Profit_Margin"] = (
    regional["Profit"] / regional["Net_Sales"] * 100
)

regional = regional.sort_values(
    "Net_Sales",
    ascending=False
)

# Identify leading and lowest-performing regions
top_sales = regional.loc[regional["Net_Sales"].idxmax()]
top_profit = regional.loc[regional["Profit"].idxmax()]
top_margin = regional.loc[regional["Profit_Margin"].idxmax()]
lowest_margin = regional.loc[regional["Profit_Margin"].idxmin()]
lowest_sales = regional.loc[regional["Net_Sales"].idxmin()]

# -----------------------------------
# KPI CARDS
# -----------------------------------

c1, c2, c3 = st.columns(3)

c1.metric(
    "Highest Sales Region",
    top_sales["Region"],
    f"₹{top_sales['Net_Sales']/10000000:.2f} Cr"
)

c2.metric(
    "Highest Profit Region",
    top_profit["Region"],
    f"₹{top_profit['Profit']/100000:.2f} L"
)

c3.metric(
    "Highest Margin Region",
    top_margin["Region"],
    f"{top_margin['Profit_Margin']:.2f}%"
)

st.divider()

# -----------------------------------
# SALES AND PROFIT COMPARISON
# -----------------------------------

st.subheader("Regional Sales and Profit")

col1, col2 = st.columns(2)

# Net Sales by Region
with col1:
    sales_sorted = regional.sort_values("Net_Sales")

    fig_sales = px.bar(
        sales_sorted,
        x="Net_Sales",
        y="Region",
        orientation="h",
        text="Net_Sales",
        custom_data=["Orders", "Profit", "Profit_Margin", "Discount_Amount"],
        title="Net Sales by Region",
        labels={
            "Net_Sales": "Net Sales (₹)",
            "Region": ""
        },
        color_discrete_sequence=[SALES_COLOR]
    )

    fig_sales.update_traces(
        width=0.55,
        texttemplate="%{x:.3s}",
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Net Sales: ₹%{x:,.2f}<br>"
            "Transactions: %{customdata[0]:,.0f}<br>"
            "Profit: ₹%{customdata[1]:,.2f}<br>"
            "Profit Margin: %{customdata[2]:.2f}%<br>"
            "Discount Amount: ₹%{customdata[3]:,.2f}"
            "<extra></extra>"
        )
    )

    fig_sales.update_layout(
        template=chart_template,
        height=380,
        showlegend=False,
        xaxis_title="Net Sales (₹)",
        yaxis_title="",
        margin=dict(l=10, r=55, t=65, b=45)
    )

    st.plotly_chart(fig_sales, use_container_width=True)

# Profit by Region
with col2:
    profit_sorted = regional.sort_values("Profit")

    fig_profit = px.bar(
        profit_sorted,
        x="Profit",
        y="Region",
        orientation="h",
        text="Profit",
        custom_data=["Orders", "Net_Sales", "Profit_Margin", "Discount_Amount"],
        title="Profit by Region",
        labels={
            "Profit": "Profit (₹)",
            "Region": ""
        },
        color_discrete_sequence=[PROFIT_COLOR]
    )

    fig_profit.update_traces(
        width=0.55,
        texttemplate="%{x:.3s}",
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Profit: ₹%{x:,.2f}<br>"
            "Transactions: %{customdata[0]:,.0f}<br>"
            "Net Sales: ₹%{customdata[1]:,.2f}<br>"
            "Profit Margin: %{customdata[2]:.2f}%<br>"
            "Discount Amount: ₹%{customdata[3]:,.2f}"
            "<extra></extra>"
        )
    )

    fig_profit.update_layout(
        template=chart_template,
        height=380,
        showlegend=False,
        xaxis_title="Profit (₹)",
        yaxis_title="",
        margin=dict(l=10, r=55, t=65, b=45)
    )

    st.plotly_chart(fig_profit, use_container_width=True)

st.divider()

# -----------------------------------
# PROFITABILITY COMPARISON
# -----------------------------------

st.subheader("Sales vs Profitability")

margin_sorted = regional.sort_values("Profit_Margin")

fig_margin = px.bar(
    margin_sorted,
    x="Profit_Margin",
    y="Region",
    orientation="h",
    text="Profit_Margin",
    custom_data=["Orders", "Net_Sales", "Profit", "Discount_Amount"],
    title="Profit Margin by Region",
    labels={
        "Profit_Margin": "Profit Margin (%)",
        "Region": ""
    },
    color_discrete_sequence=[MARGIN_COLOR]
)

fig_margin.update_traces(
    width=0.55,
    texttemplate="%{x:.2f}%",
    textposition="outside",
    cliponaxis=False,
    hovertemplate=(
        "<b>%{y}</b><br>"
        "Profit Margin: %{x:.2f}%<br>"
        "Transactions: %{customdata[0]:,.0f}<br>"
        "Net Sales: ₹%{customdata[1]:,.2f}<br>"
        "Profit: ₹%{customdata[2]:,.2f}<br>"
        "Discount Amount: ₹%{customdata[3]:,.2f}"
        "<extra></extra>"
    )
)

fig_margin.update_layout(
    template=chart_template,
    height=380,
    showlegend=False,
    xaxis_title="Profit Margin (%)",
    yaxis_title="",
    margin=dict(l=10, r=65, t=65, b=45)
)

fig_margin.update_xaxes(ticksuffix="%")

st.plotly_chart(fig_margin, use_container_width=True)

st.divider()

# -----------------------------------
# REGIONAL SUMMARY TABLE
# -----------------------------------

st.subheader("Regional Performance Summary")

display_regional = regional.copy()

display_regional["Net_Sales"] = display_regional[
    "Net_Sales"
].map(lambda x: f"₹{x:,.2f}")

display_regional["Profit"] = display_regional[
    "Profit"
].map(lambda x: f"₹{x:,.2f}")

display_regional["Profit_Margin"] = display_regional[
    "Profit_Margin"
].map(lambda x: f"{x:.2f}%")

display_regional["Discount_Amount"] = display_regional[
    "Discount_Amount"
].map(lambda x: f"₹{x:,.2f}")

display_regional = display_regional.rename(columns={
    "Region": "Region",
    "Orders": "Transactions",
    "Net_Sales": "Net Sales",
    "Profit": "Profit",
    "Discount_Amount": "Discount Amount",
    "Profit_Margin": "Profit Margin"
})

st.dataframe(
    display_regional,
    use_container_width=True,
    hide_index=True
)

# -----------------------------------
# BUSINESS INSIGHTS
# -----------------------------------

st.subheader("Key Business Insights")

st.markdown(f"""
- **{top_sales['Region']}** leads in net sales, generating ₹{top_sales['Net_Sales']/10000000:.2f} Cr in the selected period.
- **{top_profit['Region']}** generates the highest absolute profit of ₹{top_profit['Profit']/100000:.2f} L.
- **{top_margin['Region']}** records the highest profit margin at {top_margin['Profit_Margin']:.2f}%, while **{lowest_margin['Region']}** has the lowest margin at {lowest_margin['Profit_Margin']:.2f}%.
- **{lowest_sales['Region']}** has the lowest net sales, making it the smallest regional contributor by revenue.
- Higher sales do not necessarily translate into higher profitability. Regional margin comparisons help distinguish revenue scale from profit efficiency.
""")

st.caption(
    "Profit margin is calculated as total regional profit divided by total regional net sales."
)
