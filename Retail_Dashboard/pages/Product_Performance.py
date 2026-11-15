
import streamlit as st
import pandas as pd
import plotly.express as px

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
    f"₹{top_subcategory['Net_Sales']/100000:.2f} L"
)

c3.metric(
    "Highest Subcategory Margin",
    top_margin_subcategory["Subcategory"],
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

# Category Treemap
with col1:
    fig_treemap = px.treemap(
        category,
        path=["Category"],
        values="Net_Sales",
        color="Profit_Margin",
        color_continuous_scale="Teal",
        custom_data=["Profit", "Profit_Margin", "Sales_Share", "Orders"],
        title="Category Sales Contribution"
    )

    fig_treemap.update_traces(
        texttemplate="%{label}<br>%{percentRoot:.1%}",
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Net Sales: ₹%{value:,.2f}<br>"
            "Sales Share: %{customdata[2]:.1f}%<br>"
            "Profit: ₹%{customdata[0]:,.2f}<br>"
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

# Category Profit Margin
with col2:
    category_margin_sorted = category.sort_values("Profit_Margin")

    fig_category_margin = px.bar(
        category_margin_sorted,
        x="Profit_Margin",
        y="Category",
        orientation="h",
        text="Profit_Margin",
        custom_data=["Net_Sales", "Profit", "Sales_Share", "Orders"],
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
            "Net Sales: ₹%{customdata[0]:,.2f}<br>"
            "Profit: ₹%{customdata[1]:,.2f}<br>"
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

    fig_category_margin.update_xaxes(ticksuffix="%")

    st.plotly_chart(fig_category_margin, use_container_width=True)

st.divider()

# -----------------------------------
# SUBCATEGORY SALES
# -----------------------------------

st.subheader("Subcategory Performance")

subcategory_sales_sorted = subcategory.sort_values("Net_Sales")

fig_subcategory_sales = px.bar(
    subcategory_sales_sorted,
    x="Net_Sales",
    y="Display_Label",
    color="Category",
    orientation="h",
    text="Net_Sales",
    custom_data=["Orders", "Profit", "Profit_Margin", "Quantity", "Sales_Share"],
    title="Net Sales by Subcategory",
    labels={
        "Net_Sales": "Net Sales (₹)",
        "Display_Label": "",
        "Category": "Category"
    },
    color_discrete_map=category_colors
)

fig_subcategory_sales.update_traces(
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
    margin=dict(t=65, b=45, l=10, r=65)
)

st.plotly_chart(fig_subcategory_sales, use_container_width=True)

# -----------------------------------
# SUBCATEGORY PROFIT MARGIN
# -----------------------------------

st.subheader("Subcategory Profitability")

subcategory_margin_sorted = subcategory.sort_values("Profit_Margin")

fig_subcategory_margin = px.bar(
    subcategory_margin_sorted,
    x="Profit_Margin",
    y="Display_Label",
    color="Category",
    orientation="h",
    text="Profit_Margin",
    custom_data=["Orders", "Net_Sales", "Profit", "Quantity"],
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
        "Net Sales: ₹%{customdata[1]:,.2f}<br>"
        "Profit: ₹%{customdata[2]:,.2f}<br>"
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
    margin=dict(t=65, b=45, l=10, r=65)
)

fig_subcategory_margin.update_xaxes(ticksuffix="%")

st.plotly_chart(fig_subcategory_margin, use_container_width=True)

st.divider()

# -----------------------------------
# DETAILED SUMMARY TABLE
# -----------------------------------

st.subheader("Detailed Product Performance")

display_data = subcategory.copy()

display_data["Net_Sales"] = display_data[
    "Net_Sales"
].map(lambda x: f"₹{x:,.2f}")

display_data["Profit"] = display_data[
    "Profit"
].map(lambda x: f"₹{x:,.2f}")

display_data["Profit_Margin"] = display_data[
    "Profit_Margin"
].map(lambda x: f"{x:.2f}%")

display_data["Sales_Share"] = display_data[
    "Sales_Share"
].map(lambda x: f"{x:.2f}%")

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

technology = category[
    category["Category"] == "Technology"
]

technology_share = (
    technology["Sales_Share"].iloc[0]
    if not technology.empty else 0
)

lowest_margin_category = category.loc[
    category["Profit_Margin"].idxmin()
]

st.markdown(f"""
- **{top_category['Category']}** is the leading revenue category, contributing {top_category['Sales_Share']:.1f}% of net sales.
- **{top_subcategory['Category']} – {top_subcategory['Subcategory']}** is the largest subcategory by net sales, generating ₹{top_subcategory['Net_Sales']/100000:.2f} L.
- **{top_margin_subcategory['Category']} – {top_margin_subcategory['Subcategory']}** records the highest subcategory profit margin at {top_margin_subcategory['Profit_Margin']:.2f}%, showing that the largest revenue contributor is not necessarily the most profitable.
- **{lowest_margin_category['Category']}** has the lowest category-level margin at {lowest_margin_category['Profit_Margin']:.2f}%, making it worth examining its product mix and discount strategy.
- Product-level decisions should consider both sales contribution and profit margin rather than relying on revenue alone.
""")
