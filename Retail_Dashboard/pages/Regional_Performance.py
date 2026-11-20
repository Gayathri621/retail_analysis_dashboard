
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
# FORMATTING HELPERS
# -----------------------------------

def format_indian_number(value, decimals=2):
    value = round(float(value), decimals)

    formatted = f"{value:.{decimals}f}" if decimals > 0 else f"{int(value)}"

    integer_part, decimal_part = formatted.split(".") if decimals > 0 else (formatted, "")

    if len(integer_part) > 3:
        last_three = integer_part[-3:]
        remaining = integer_part[:-3]
        groups = []

        while remaining:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]

        integer_part = ",".join(groups) + "," + last_three

    if decimals > 0:
        return integer_part + "." + decimal_part

    return integer_part


def format_inr(value):
    return f"₹{format_indian_number(value)}"


def format_inr_lakhs(value):
    return f"₹{format_indian_number(value / 100000)} L"


def format_inr_crores(value):
    return f"₹{format_indian_number(value / 10000000)} Cr"


def format_compact_inr(value):
    value = float(value)

    if abs(value) >= 10000000:
        return f"₹{format_indian_number(value / 10000000)} Cr"
    elif abs(value) >= 100000:
        return f"₹{format_indian_number(value / 100000)} L"
    else:
        return f"₹{format_indian_number(value, 0)}"


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
    format_inr_crores(top_sales["Net_Sales"])
)

c2.metric(
    "Highest Profit Region",
    top_profit["Region"],
    format_inr_lakhs(top_profit["Profit"])
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

# -----------------------------------
# NET SALES BY REGION
# -----------------------------------

with col1:
    sales_sorted = regional.sort_values("Net_Sales").copy()

    sales_sorted["Sales_Label"] = sales_sorted["Net_Sales"].apply(
        format_compact_inr
    )
    sales_sorted["Sales_Hover"] = sales_sorted["Net_Sales"].apply(
        format_inr
    )
    sales_sorted["Profit_Hover"] = sales_sorted["Profit"].apply(
        format_inr
    )
    sales_sorted["Discount_Hover"] = sales_sorted["Discount_Amount"].apply(
        format_inr
    )

    fig_sales = px.bar(
        sales_sorted,
        x="Net_Sales",
        y="Region",
        orientation="h",
        text="Sales_Label",
        custom_data=[
            "Orders",
            "Profit_Hover",
            "Profit_Margin",
            "Discount_Hover"
        ],
        title="Net Sales by Region",
        labels={
            "Net_Sales": "Net Sales",
            "Region": ""
        },
        color_discrete_sequence=[SALES_COLOR]
    )

    fig_sales.update_traces(
        width=0.55,
        texttemplate="%{text}",
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Net Sales: %{customdata[0]}<br>"
            "Transactions: %{customdata[1]:,.0f}<br>"
            "Profit: %{customdata[2]}<br>"
            "Profit Margin: %{customdata[3]:.2f}%<br>"
            "Discount Amount: %{customdata[4]}"
            "<extra></extra>"
        )
    )

    fig_sales.update_layout(
        template=chart_template,
        height=380,
        showlegend=False,
        xaxis_title="Net Sales (₹)",
        yaxis_title="",
        margin=dict(l=10, r=80, t=65, b=45)
    )

    fig_sales.update_xaxes(
        tickformat=",.0f"
    )

    st.plotly_chart(fig_sales, use_container_width=True)

# -----------------------------------
# PROFIT BY REGION
# -----------------------------------

with col2:
    profit_sorted = regional.sort_values("Profit").copy()

    profit_sorted["Profit_Label"] = profit_sorted["Profit"].apply(
        format_compact_inr
    )
    profit_sorted["Profit_Hover"] = profit_sorted["Profit"].apply(
        format_inr
    )
    profit_sorted["Sales_Hover"] = profit_sorted["Net_Sales"].apply(
        format_inr
    )
    profit_sorted["Discount_Hover"] = profit_sorted["Discount_Amount"].apply(
        format_inr
    )

    fig_profit = px.bar(
        profit_sorted,
        x="Profit",
        y="Region",
        orientation="h",
        text="Profit_Label",
        custom_data=[
            "Orders",
            "Sales_Hover",
            "Profit_Margin",
            "Discount_Hover"
        ],
        title="Profit by Region",
        labels={
            "Profit": "Profit",
            "Region": ""
        },
        color_discrete_sequence=[PROFIT_COLOR]
    )

    fig_profit.update_traces(
        width=0.55,
        texttemplate="%{text}",
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Profit: %{customdata[0]}<br>"
            "Transactions: %{customdata[1]:,.0f}<br>"
            "Net Sales: %{customdata[2]}<br>"
            "Profit Margin: %{customdata[3]:.2f}%<br>"
            "Discount Amount: %{customdata[4]}"
            "<extra></extra>"
        )
    )

    fig_profit.update_layout(
        template=chart_template,
        height=380,
        showlegend=False,
        xaxis_title="Profit (₹)",
        yaxis_title="",
        margin=dict(l=10, r=80, t=65, b=45)
    )

    fig_profit.update_xaxes(
        tickformat=",.0f"
    )

    st.plotly_chart(fig_profit, use_container_width=True)

st.divider()

# -----------------------------------
# PROFITABILITY COMPARISON
# -----------------------------------

st.subheader("Sales vs Profitability")

margin_sorted = regional.sort_values("Profit_Margin").copy()

margin_sorted["Sales_Hover"] = margin_sorted["Net_Sales"].apply(
    format_inr
)
margin_sorted["Profit_Hover"] = margin_sorted["Profit"].apply(
    format_inr
)
margin_sorted["Discount_Hover"] = margin_sorted["Discount_Amount"].apply(
    format_inr
)

fig_margin = px.bar(
    margin_sorted,
    x="Profit_Margin",
    y="Region",
    orientation="h",
    text="Profit_Margin",
    custom_data=[
        "Orders",
        "Sales_Hover",
        "Profit_Hover",
        "Discount_Hover"
    ],
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
        "Net Sales: %{customdata[1]}<br>"
        "Profit: %{customdata[2]}<br>"
        "Discount Amount: %{customdata[3]}"
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

fig_margin.update_xaxes(
    ticksuffix="%"
)

st.plotly_chart(fig_margin, use_container_width=True)

st.divider()

# -----------------------------------
# REGIONAL SUMMARY TABLE
# -----------------------------------

st.subheader("Regional Performance Summary")

display_regional = regional.copy()

display_regional["Net_Sales"] = display_regional[
    "Net_Sales"
].map(format_inr)

display_regional["Profit"] = display_regional[
    "Profit"
].map(format_inr)

display_regional["Profit_Margin"] = display_regional[
    "Profit_Margin"
].map(lambda x: f"{x:.2f}%")

display_regional["Discount_Amount"] = display_regional[
    "Discount_Amount"
].map(format_inr)

display_regional["Orders"] = display_regional[
    "Orders"
].map(lambda x: format_indian_number(x, 0))

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
- **{top_sales['Region']}** leads in net sales, generating **{format_inr_crores(top_sales['Net_Sales'])}** in the selected period.
- **{top_profit['Region']}** generates the highest absolute profit of **{format_inr_lakhs(top_profit['Profit'])}**.
- **{top_margin['Region']}** records the highest profit margin at **{top_margin['Profit_Margin']:.2f}%**, while **{lowest_margin['Region']}** has the lowest margin at **{lowest_margin['Profit_Margin']:.2f}%**.
- **{lowest_sales['Region']}** has the lowest net sales, making it the smallest regional contributor by revenue.
- Revenue scale and profitability efficiency are not necessarily aligned: a region with higher sales may not generate the strongest margin. Comparing sales, absolute profit, and margin together helps distinguish regional scale from profit efficiency.
""")

st.caption(
    "Profit margin is calculated as total regional profit divided by total regional net sales."
)
