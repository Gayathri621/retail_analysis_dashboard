
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

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
    """Indian-style compact currency for chart labels."""
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

c1.metric("Net Sales", format_inr_crores(total_sales))
c2.metric("Total Profit", format_inr_lakhs(total_profit))
c3.metric("Transactions", format_indian_number(total_orders, 0))
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

annual = annual.sort_values("Year")

# YoY growth
annual["Sales_Growth"] = annual["Net_Sales"].pct_change() * 100
annual["Profit_Growth"] = annual["Profit"].pct_change() * 100

annual["Year"] = annual["Year"].astype(str)

# Explicit chart labels to prevent Plotly M/k abbreviations
annual["Sales_Label"] = annual["Net_Sales"].apply(format_compact_inr)
annual["Profit_Label"] = annual["Profit"].apply(format_compact_inr)

# Explicit Indian-format hover values
annual["Sales_Hover"] = annual["Net_Sales"].apply(format_inr)
annual["Profit_Hover"] = annual["Profit"].apply(format_inr)

annual["Sales_Growth_Hover"] = annual["Sales_Growth"].apply(
    lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A"
)

annual["Profit_Growth_Hover"] = annual["Profit_Growth"].apply(
    lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A"
)

col1, col2 = st.columns(2)

# -----------------------------------
# ANNUAL NET SALES
# -----------------------------------

with col1:
    fig_sales = px.bar(
        annual,
        x="Year",
        y="Net_Sales",
        text="Sales_Label",
        custom_data=[
            "Profit_Hover",
            "Orders",
            "Profit_Margin",
            "Sales_Growth_Hover"
        ],
        title="Annual Net Sales",
        labels={
            "Year": "Year",
            "Net_Sales": "Net Sales"
        },
        color_discrete_sequence=["#2878A5"]
    )

    fig_sales.update_traces(
        texttemplate="%{text}",
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>Year: %{x}</b><br>"
            "Net Sales: %{y:,.2f}<br>"
            "Profit: %{customdata[0]}<br>"
            "Transactions: %{customdata[1]:,.0f}<br>"
            "Profit Margin: %{customdata[2]:.2f}%<br>"
            "YoY Sales Growth: %{customdata[3]}"
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

    fig_sales.update_yaxes(
        tickformat=",.0f"
    )

    st.plotly_chart(fig_sales, use_container_width=True)

# -----------------------------------
# ANNUAL PROFIT
# -----------------------------------

with col2:
    fig_profit = px.bar(
        annual,
        x="Year",
        y="Profit",
        text="Profit_Label",
        custom_data=[
            "Sales_Hover",
            "Orders",
            "Profit_Margin",
            "Profit_Growth_Hover"
        ],
        title="Annual Profit",
        labels={
            "Year": "Year",
            "Profit": "Profit"
        },
        color_discrete_sequence=["#35A68A"]
    )

    fig_profit.update_traces(
        texttemplate="%{text}",
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>Year: %{x}</b><br>"
            "Profit: %{y:,.2f}<br>"
            "Net Sales: %{customdata[0]}<br>"
            "Transactions: %{customdata[1]:,.0f}<br>"
            "Profit Margin: %{customdata[2]:.2f}%<br>"
            "YoY Profit Growth: %{customdata[3]}"
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

    fig_profit.update_yaxes(
        tickformat=",.0f"
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

# Indian-format hover data
monthly["Sales_Hover"] = monthly["Net_Sales"].apply(format_inr)
monthly["Profit_Hover"] = monthly["Profit"].apply(format_inr)

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
    custom_data=[
        "Profit_Hover",
        "Orders",
        "Profit_Margin",
        "Sales_Hover"
    ],
    title="Monthly Net Sales by Year",
    category_orders={
        "Month_Name": month_order
    },
    color_discrete_map=year_colors,
    labels={
        "Month_Name": "Month",
        "Net_Sales": "Net Sales",
        "Year": "Year"
    }
)

fig_monthly.update_traces(
    line=dict(width=2.5),
    marker=dict(size=8),
    hovertemplate=(
        "<b>%{x} %{fullData.name}</b><br>"
        "Net Sales: %{customdata[3]}<br>"
        "Profit: %{customdata[0]}<br>"
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

fig_monthly.update_yaxes(
    tickformat=",.0f"
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
    custom_data=[
        "Sales_Hover",
        "Profit_Hover",
        "Orders"
    ],
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
        "Net Sales: %{customdata[0]}<br>"
        "Profit: %{customdata[1]}<br>"
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

annual_numeric = (
    filtered_df.assign(
        Year=filtered_df["Order_Date"].dt.year
    )
    .groupby("Year")
    .agg(
        Net_Sales=("Net_Sales", "sum"),
        Profit=("Profit", "sum")
    )
    .sort_index()
)

observations = []

if len(annual_numeric) >= 2:
    first_year = annual_numeric.index[0]
    last_year = annual_numeric.index[-1]

    sales_growth = (
        (annual_numeric.loc[last_year, "Net_Sales"] -
         annual_numeric.loc[first_year, "Net_Sales"])
        / annual_numeric.loc[first_year, "Net_Sales"] * 100
    )

    profit_growth = (
        (annual_numeric.loc[last_year, "Profit"] -
         annual_numeric.loc[first_year, "Profit"])
        / annual_numeric.loc[first_year, "Profit"] * 100
    )

    observations.append(
        f"Net sales changed by **{sales_growth:.1f}%** between "
        f"{first_year} and {last_year}."
    )

    observations.append(
        f"Profit changed by **{profit_growth:.1f}%** over the same period."
    )

# Highest sales month
if not monthly.empty:
    peak_month = monthly.loc[monthly["Net_Sales"].idxmax()]

    observations.append(
        f"The highest monthly sales occurred in **{peak_month['Month_Name']} "
        f"{int(peak_month['Year'])}**, reaching "
        f"**{format_inr_lakhs(peak_month['Net_Sales'])}**."
    )

# Margin trend
if len(annual_numeric) >= 2:
    annual_margin = (
        annual_numeric["Profit"] / annual_numeric["Net_Sales"] * 100
    )

    first_margin = annual_margin.iloc[0]
    last_margin = annual_margin.iloc[-1]
    margin_change = last_margin - first_margin

    if margin_change > 0:
        observations.append(
            f"Profit margin improved by **{margin_change:.2f} percentage points** "
            f"between {annual_numeric.index[0]} and {annual_numeric.index[-1]}."
        )

    elif margin_change < 0:
        observations.append(
            f"Profit margin declined by **{abs(margin_change):.2f} percentage points** "
            f"between {annual_numeric.index[0]} and {annual_numeric.index[-1]}."
        )

    else:
        observations.append(
            "Profit margin remained unchanged between the first and last selected years."
        )

if observations:
    for observation in observations:
        st.markdown(f"- {observation}")
else:
    st.info(
        "Select multiple years to compare annual growth, or explore the monthly trends."
    )

st.caption(
    "Note: The analysis includes all supplied transactions for 2024–2026."
)
