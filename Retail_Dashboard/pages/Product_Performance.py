
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

category_colors = {
    "Technology": "#2878A5",
    "Furniture": "#35A68A",
    "Office Supplies": "#E49B45"
}

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

st.title("Product Performance")
st.markdown(
    "### Understanding category contribution and subcategory profitability"
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
    key="product_years"
)

filtered_df = df[
    df["Order_Date"].dt.year.isin(selected_years)
].copy()

if filtered_df.empty:
    st.warning("Select at least one year to view the product analysis.")
    st.stop()

# -----------------------------------
# CATEGORY AGGREGATION
# -----------------------------------

category = (
    filtered_df.groupby("Category")
    .agg(
        Orders=("Order_ID", "nunique"),
        Net_Sales=("Net_Sales", "sum"),
        Profit=("Profit", "sum"),
        Quantity=("Quantity", "sum")
    )
    .reset_index()
)

category["Profit_Margin"] = (
    category["Profit"] / category["Net_Sales"] * 100
)

total_category_sales = category["Net_Sales"].sum()

category["Sales_Share"] = (
    category["Net_Sales"] / total_category_sales * 100
)

# -----------------------------------
# SUBCATEGORY AGGREGATION
# -----------------------------------

subcategory = (
    filtered_df.groupby(["Category", "Subcategory"])
    .agg(
        Orders=("Order_ID", "nunique"),
        Net_Sales=("Net_Sales", "sum"),
        Profit=("Profit", "sum"),
        Quantity=("Quantity", "sum")
    )
    .reset_index()
)

subcategory["Profit_Margin"] = (
    subcategory["Profit"] / subcategory["Net_Sales"] * 100
)

subcategory["Sales_Share"] = (
    subcategory["Net_Sales"] / subcategory["Net_Sales"].sum() * 100
)

# Unique display label avoids confusion for repeated subcategory names
subcategory["Display_Label"] = (
    subcategory["Category"] + " – " + subcategory["Subcategory"]
)

# -----------------------------------
# KPI CALCULATIONS
# -----------------------------------

top_category = category.loc[
    category["Net_Sales"].idxmax()
]

top_subcategory = subcategory.loc[
    subcategory["Net_Sales"].idxmax()
]

top_margin_subcategory = subcategory.loc[
    subcategory["Profit_Margin"].idxmax()
]

c1, c2, c3 = st.columns(3)

c1.metric(
    "Leading Sales Category",
    top_category["Category"],
    f"{top_category['Sales_Share']:.1f}% of sales"
)

c2.metric(
    "Top Subcategory by Sales",
    top_subcategory["Subcategory"],
    format_inr_lakhs(top_subcategory["Net_Sales"])
)

c3.metric(
    "Highest Subcategory Margin",
    f"{top_margin_subcategory['Category']} – {top_margin_subcategory['Subcategory']}",
    f"{top_margin_subcategory['Profit_Margin']:.2f}%"
)

st.caption(
    f"Highest-margin subcategory belongs to {top_margin_subcategory['Category']}."
)

st.divider()

# -----------------------------------
# CATEGORY SALES CONTRIBUTION
# -----------------------------------

st.subheader("Category Contribution to Net Sales")

col1, col2 = st.columns([1, 1])

# -----------------------------------
# CATEGORY TREEMAP
# -----------------------------------

with col1:

    category_display = category.copy()

    category_display["Profit_Hover"] = category_display["Profit"].apply(
        format_inr
    )

    category_display["Sales_Hover"] = category_display["Net_Sales"].apply(
        format_inr
    )

    fig_treemap = px.treemap(
        category_display,
        path=["Category"],
        values="Net_Sales",
        color="Profit_Margin",
        color_continuous_scale="Teal",
        custom_data=[
            "Profit_Hover",
            "Profit_Margin",
            "Sales_Share",
            "Orders",
            "Sales_Hover"
        ],
        title="Category Sales Contribution"
    )

    fig_treemap.update_traces(
        texttemplate="%{label}<br>%{percentRoot:.1%}",
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Net Sales: %{customdata[4]}<br>"
            "Sales Share: %{customdata[2]:.1f}%<br>"
            "Profit: %{customdata[0]}<br>"
            "Profit Margin: %{customdata[1]:.2f}%<br>"
            "Transactions: %{customdata[3]:,.0f}"
            "<extra></extra>"
        )
    )

    fig_treemap.update_layout(
        template=chart_template,
        height=420,
        margin=dict(t=65, b=15, l=10, r=10)
    )

    st.plotly_chart(fig_treemap, use_container_width=True)

# -----------------------------------
# CATEGORY PROFIT MARGIN
# -----------------------------------

with col2:

    category_margin_sorted = category.sort_values("Profit_Margin").copy()

    category_margin_sorted["Sales_Hover"] = (
        category_margin_sorted["Net_Sales"].apply(format_inr)
    )

    category_margin_sorted["Profit_Hover"] = (
        category_margin_sorted["Profit"].apply(format_inr)
    )

    fig_category_margin = px.bar(
        category_margin_sorted,
        x="Profit_Margin",
        y="Category",
        orientation="h",
        text="Profit_Margin",
        custom_data=[
            "Sales_Hover",
            "Profit_Hover",
            "Sales_Share",
            "Orders"
        ],
        title="Profit Margin by Category",
        labels={
            "Profit_Margin": "Profit Margin (%)",
            "Category": ""
        },
        color_discrete_sequence=[MARGIN_COLOR]
    )

    fig_category_margin.update_traces(
        width=0.55,
        texttemplate="%{x:.2f}%",
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Profit Margin: %{x:.2f}%<br>"
            "Net Sales: %{customdata[0]}<br>"
            "Profit: %{customdata[1]}<br>"
            "Sales Share: %{customdata[2]:.1f}%<br>"
            "Transactions: %{customdata[3]:,.0f}"
            "<extra></extra>"
        )
    )

    fig_category_margin.update_layout(
        template=chart_template,
        height=420,
        showlegend=False,
        xaxis_title="Profit Margin (%)",
        yaxis_title="",
        margin=dict(t=65, b=45, l=10, r=65)
    )

    fig_category_margin.update_xaxes(
        ticksuffix="%"
    )

    st.plotly_chart(fig_category_margin, use_container_width=True)

st.divider()

# -----------------------------------
# SUBCATEGORY SALES
# -----------------------------------

st.subheader("Subcategory Performance")

subcategory_sales_sorted = subcategory.sort_values("Net_Sales").copy()

subcategory_sales_sorted["Sales_Label"] = (
    subcategory_sales_sorted["Net_Sales"].apply(format_compact_inr)
)

subcategory_sales_sorted["Sales_Hover"] = (
    subcategory_sales_sorted["Net_Sales"].apply(format_inr)
)

subcategory_sales_sorted["Profit_Hover"] = (
    subcategory_sales_sorted["Profit"].apply(format_inr)
)

fig_subcategory_sales = px.bar(
    subcategory_sales_sorted,
    x="Net_Sales",
    y="Display_Label",
    color="Category",
    orientation="h",
    text="Sales_Label",
    custom_data=[
        "Orders",
        "Profit_Hover",
        "Profit_Margin",
        "Quantity",
        "Sales_Share",
        "Sales_Hover"
    ],
    title="Net Sales by Subcategory",
    labels={
        "Net_Sales": "Net Sales",
        "Display_Label": "",
        "Category": "Category"
    },
    color_discrete_map=category_colors
)

fig_subcategory_sales.update_traces(
    width=0.55,
    texttemplate="%{text}",
    textposition="outside",
    cliponaxis=False,
    hovertemplate=(
        "<b>%{y}</b><br>"
        "Net Sales: %{customdata[5]}<br>"
        "Transactions: %{customdata[0]:,.0f}<br>"
        "Profit: %{customdata[1]}<br>"
        "Profit Margin: %{customdata[2]:.2f}%<br>"
        "Quantity Sold: %{customdata[3]:,.0f}<br>"
        "Sales Share: %{customdata[4]:.1f}%"
        "<extra></extra>"
    )
)

fig_subcategory_sales.update_layout(
    template=chart_template,
    height=550,
    xaxis_title="Net Sales (₹)",
    yaxis_title="",
    legend_title="Category",
    margin=dict(t=65, b=45, l=10, r=85)
)

fig_subcategory_sales.update_xaxes(
    tickformat=",.0f"
)

st.plotly_chart(fig_subcategory_sales, use_container_width=True)

# -----------------------------------
# SUBCATEGORY PROFIT MARGIN
# -----------------------------------

st.subheader("Subcategory Profitability")

subcategory_margin_sorted = subcategory.sort_values("Profit_Margin").copy()

subcategory_margin_sorted["Sales_Hover"] = (
    subcategory_margin_sorted["Net_Sales"].apply(format_inr)
)

subcategory_margin_sorted["Profit_Hover"] = (
    subcategory_margin_sorted["Profit"].apply(format_inr)
)

fig_subcategory_margin = px.bar(
    subcategory_margin_sorted,
    x="Profit_Margin",
    y="Display_Label",
    color="Category",
    orientation="h",
    text="Profit_Margin",
    custom_data=[
        "Orders",
        "Sales_Hover",
        "Profit_Hover",
        "Quantity"
    ],
    title="Profit Margin by Subcategory",
    labels={
        "Profit_Margin": "Profit Margin (%)",
        "Display_Label": "",
        "Category": "Category"
    },
    color_discrete_map=category_colors
)

fig_subcategory_margin.update_traces(
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
        "Quantity Sold: %{customdata[3]:,.0f}"
        "<extra></extra>"
    )
)

fig_subcategory_margin.update_layout(
    template=chart_template,
    height=550,
    xaxis_title="Profit Margin (%)",
    yaxis_title="",
    legend_title="Category",
    margin=dict(t=65, b=45, l=10, r=85)
)

fig_subcategory_margin.update_xaxes(
    ticksuffix="%"
)

st.plotly_chart(fig_subcategory_margin, use_container_width=True)

st.divider()

# -----------------------------------
# DETAILED SUMMARY TABLE
# -----------------------------------

st.subheader("Detailed Product Performance")

display_data = subcategory.copy()

display_data["Net_Sales"] = display_data[
    "Net_Sales"
].map(format_inr)

display_data["Profit"] = display_data[
    "Profit"
].map(format_inr)

display_data["Profit_Margin"] = display_data[
    "Profit_Margin"
].map(lambda x: f"{x:.2f}%")

display_data["Sales_Share"] = display_data[
    "Sales_Share"
].map(lambda x: f"{x:.2f}%")

display_data["Orders"] = display_data[
    "Orders"
].map(lambda x: format_indian_number(x, 0))

display_data["Quantity"] = display_data[
    "Quantity"
].map(lambda x: format_indian_number(x, 0))

display_data = display_data.rename(columns={
    "Orders": "Transactions",
    "Net_Sales": "Net Sales",
    "Profit": "Profit",
    "Profit_Margin": "Profit Margin",
    "Sales_Share": "Sales Share",
    "Quantity": "Quantity Sold"
})

st.dataframe(
    display_data[
        [
            "Category",
            "Subcategory",
            "Transactions",
            "Net Sales",
            "Profit",
            "Profit Margin",
            "Quantity Sold",
            "Sales Share"
        ]
    ],
    use_container_width=True,
    hide_index=True
)

# -----------------------------------
# BUSINESS INSIGHTS
# -----------------------------------

st.subheader("Key Business Insights")

lowest_margin_category = category.loc[
    category["Profit_Margin"].idxmin()
]

st.markdown(f"""
- **{top_category['Category']}** is the leading revenue category, contributing **{top_category['Sales_Share']:.1f}%** of net sales.
- **{top_subcategory['Category']} – {top_subcategory['Subcategory']}** is the largest subcategory by net sales, generating **{format_inr_lakhs(top_subcategory['Net_Sales'])}**.
- **{top_margin_subcategory['Category']} – {top_margin_subcategory['Subcategory']}** records the highest subcategory profit margin at **{top_margin_subcategory['Profit_Margin']:.2f}%**, demonstrating that the largest revenue contributor is not necessarily the most margin-efficient.
- **{lowest_margin_category['Category']}** has the lowest category-level margin at **{lowest_margin_category['Profit_Margin']:.2f}%**, making it worth examining its product mix and discount strategy.
- Product-level decisions should consider both sales contribution and profit margin rather than relying on revenue alone.
""")
 