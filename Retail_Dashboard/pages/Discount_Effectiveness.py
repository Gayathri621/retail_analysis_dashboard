
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

VOLUME_COLOR = "#2878A5"

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
    df = pd.read_csv(
        BASE_DIR / "data" / "BITS_Retail_Cleaned_Integrated.csv"
    )
    df["Order_Date"] = pd.to_datetime(df["Order_Date"])
    return df

df = load_data()

# -----------------------------------
# HEADER
# -----------------------------------

st.title("Discount Effectiveness")
st.markdown(
    "### Understanding the relationship between discounts, sales and profitability"
)

st.divider()

# -----------------------------------
# FILTERS
# -----------------------------------

years = sorted(df["Order_Date"].dt.year.unique())

selected_years = st.multiselect(
    "Select years",
    years,
    default=years,
    key="discount_years"
)

filtered_df = df[
    df["Order_Date"].dt.year.isin(selected_years)
].copy()

if filtered_df.empty:
    st.warning("Select at least one year to view the analysis.")
    st.stop()

# -----------------------------------
# DISCOUNT BANDS
# -----------------------------------

discount_labels = [
    "0%",
    ">0–5%",
    ">5–10%",
    ">10–15%",
    ">15–20%",
    ">20%"
]

filtered_df["Discount_Band"] = pd.cut(
    filtered_df["Discount_Pct"].round(2) * 100,
    bins=[-0.01, 0, 5, 10, 15, 20, 100],
    labels=discount_labels
)

# -----------------------------------
# AGGREGATION
# -----------------------------------

discount_summary = (
    filtered_df.groupby(
        "Discount_Band",
        observed=False
    )
    .agg(
        Orders=("Order_ID", "nunique"),
        Gross_Sales=("Gross_Sales", "sum"),
        Discount_Amount=("Discount_Amount", "sum"),
        Net_Sales=("Net_Sales", "sum"),
        Profit=("Profit", "sum")
    )
    .reset_index()
)

discount_summary["Profit_Margin"] = (
    discount_summary["Profit"] /
    discount_summary["Net_Sales"].replace(0, float("nan")) * 100
)

# -----------------------------------
# KPI CARDS
# -----------------------------------

def get_band_value(band, column):
    result = discount_summary.loc[
        discount_summary["Discount_Band"] == band,
        column
    ]

    return result.iloc[0] if not result.empty else 0


no_discount_margin = get_band_value("0%", "Profit_Margin")
medium_high_margin = get_band_value(">15–20%", "Profit_Margin")
high_discount_margin = get_band_value(">20%", "Profit_Margin")

c1, c2, c3 = st.columns(3)

c1.metric(
    "No-Discount Margin",
    f"{no_discount_margin:.2f}%" if pd.notna(no_discount_margin) else "N/A"
)

c2.metric(
    "15–20% Discount Margin",
    f"{medium_high_margin:.2f}%" if pd.notna(medium_high_margin) else "N/A"
)

c3.metric(
    "Above 20% Discount Margin",
    f"{high_discount_margin:.2f}%" if pd.notna(high_discount_margin) else "N/A"
)

st.divider()

# -----------------------------------
# MARGIN BY DISCOUNT BAND
# -----------------------------------

st.subheader("How Do Discounts Affect Profitability?")

st.caption(
    "Profit margin represents aggregate transaction profit as a percentage "
    "of net sales within each discount band."
)

# Red for negative margins and green for positive margins
bar_colors = [
    "#16A085" if value >= 0 else "#E74C3C"
    for value in discount_summary["Profit_Margin"].fillna(0)
]

margin_customdata = discount_summary[
    ["Orders", "Net_Sales", "Profit"]
].to_numpy()

# Preformatted monetary hover values
discount_summary["Net_Sales_Hover"] = (
    discount_summary["Net_Sales"].apply(format_inr)
)

discount_summary["Profit_Hover"] = (
    discount_summary["Profit"].apply(format_inr)
)

fig_margin = go.Figure()

fig_margin.add_trace(
    go.Bar(
        x=discount_summary["Discount_Band"].astype(str),
        y=discount_summary["Profit_Margin"],
        width=0.42,
        marker=dict(
            color=bar_colors,
            line=dict(width=0)
        ),
        text=[
            f"{value:.2f}%" if pd.notna(value) else "N/A"
            for value in discount_summary["Profit_Margin"]
        ],
        textposition="outside",
        cliponaxis=False,
        customdata=margin_customdata,
        hovertemplate=(
            "<b>Discount band: %{x}</b><br>"
            "Profit margin: %{y:.2f}%<br>"
            "Transactions: %{customdata[0]:,.0f}<br>"
            "Net sales: %{customdata[1]}<br>"
            "Profit: %{customdata[2]}"
            "<extra></extra>"
        )
    )
)

fig_margin.add_hline(
    y=0,
    line_dash="solid",
    line_color="#E74C3C",
    line_width=2,
    annotation_text="Break-even",
    annotation_position="bottom right"
)

fig_margin.update_layout(
    template=chart_template,
    height=430,
    showlegend=False,
    bargap=0.55,
    xaxis_title="Discount Band",
    yaxis_title="Profit Margin (%)",
    title="Profit Margin Across Discount Bands",
    hoverlabel=dict(namelength=-1),
    margin=dict(t=70, b=60)
)

fig_margin.update_yaxes(
    zeroline=False,
    ticksuffix="%"
)

st.plotly_chart(
    fig_margin,
    use_container_width=True
)

# -----------------------------------
# TRANSACTION VOLUME
# -----------------------------------

st.subheader("Transaction Volume by Discount Band")

fig_volume = px.bar(
    discount_summary,
    x=discount_summary["Discount_Band"].astype(str),
    y="Orders",
    text="Orders",
    custom_data=["Net_Sales", "Profit"],
    title="Number of Transactions Across Discount Bands",
    labels={
        "x": "Discount Band",
        "Orders": "Number of Transactions"
    },
    color_discrete_sequence=[VOLUME_COLOR]
)

fig_volume.update_traces(
    width=0.48,
    textposition="outside",
    cliponaxis=False,
    hovertemplate=(
        "<b>Discount band: %{x}</b><br>"
        "Transactions: %{y:,.0f}<br>"
        "Net sales: ₹%{customdata[0]:,.2f}<br>"
        "Profit: ₹%{customdata[1]:,.2f}"
        "<extra></extra>"
    )
)

fig_volume.update_layout(
    template=chart_template,
    height=380,
    showlegend=False,
    bargap=0.5,
    xaxis_title="Discount Band",
    yaxis_title="Number of Transactions",
    margin=dict(t=70, b=60)
)

st.plotly_chart(
    fig_volume,
    use_container_width=True
)

st.divider()

# -----------------------------------
# CATEGORY-WISE DISCOUNT PERFORMANCE
# -----------------------------------

st.subheader("Discount Effectiveness Across Categories")

category_discount = (
    filtered_df.groupby(
        ["Category", "Discount_Band"],
        observed=False
    )
    .agg(
        Orders=("Order_ID", "nunique"),
        Net_Sales=("Net_Sales", "sum"),
        Profit=("Profit", "sum")
    )
    .reset_index()
)

category_discount["Profit_Margin"] = (
    category_discount["Profit"] /
    category_discount["Net_Sales"].replace(0, float("nan")) * 100
)

# Pivot aggregated values into a heatmap matrix
heatmap_data = category_discount.pivot(
    index="Category",
    columns="Discount_Band",
    values="Profit_Margin"
)

heatmap_data = heatmap_data.reindex(columns=discount_labels)

fig_heatmap = px.imshow(
    heatmap_data,
    text_auto=".1f",
    aspect="auto",
    color_continuous_scale="RdYlGn",
    color_continuous_midpoint=0,
    title="Profit Margin by Category and Discount Band",
    labels={
        "x": "Discount Band",
        "y": "Category",
        "color": "Profit Margin (%)"
    }
)

fig_heatmap.update_traces(
    hovertemplate=(
        "<b>Category: %{y}</b><br>"
        "Discount band: %{x}<br>"
        "Profit margin: %{z:.2f}%"
        "<extra></extra>"
    )
)

fig_heatmap.update_layout(
    template=chart_template,
    height=390,
    margin=dict(t=70, b=60)
)

st.plotly_chart(
    fig_heatmap,
    use_container_width=True
)

# -----------------------------------
# SUBCATEGORY DISCOUNT ANALYSIS
# -----------------------------------

st.subheader("Subcategory Discount Performance")

categories = sorted(filtered_df["Category"].dropna().unique())

selected_category = st.selectbox(
    "Select product category",
    categories,
    key="discount_category"
)

subcategory_discount = (
    filtered_df[
        filtered_df["Category"] == selected_category
    ]
    .groupby(
        ["Subcategory", "Discount_Band"],
        observed=True
    )
    .agg(
        Orders=("Order_ID", "nunique"),
        Net_Sales=("Net_Sales", "sum"),
        Profit=("Profit", "sum")
    )
    .reset_index()
)

subcategory_discount["Profit_Margin"] = (
    subcategory_discount["Profit"] /
    subcategory_discount["Net_Sales"].replace(0, float("nan")) * 100
)

# Remove empty combinations so they do not create misleading line points
subcategory_discount = subcategory_discount.dropna(
    subset=["Profit_Margin"]
)

subcategory_discount["Net_Sales_Hover"] = (
    subcategory_discount["Net_Sales"].apply(format_inr)
)

subcategory_discount["Profit_Hover"] = (
    subcategory_discount["Profit"].apply(format_inr)
)

fig_subcategory = px.line(
    subcategory_discount,
    x="Discount_Band",
    y="Profit_Margin",
    color="Subcategory",
    markers=True,
    custom_data=[
        "Orders",
        "Net_Sales_Hover",
        "Profit_Hover"
    ],
    title=f"Profit Margin Across Discount Bands – {selected_category}",
    labels={
        "Discount_Band": "Discount Band",
        "Profit_Margin": "Profit Margin (%)",
        "Subcategory": "Subcategory"
    }
)

fig_subcategory.update_traces(
    line=dict(width=2),
    marker=dict(size=8),
    hovertemplate=(
        "<b>%{fullData.name}</b><br>"
        "Discount band: %{x}<br>"
        "Profit margin: %{y:.2f}%<br>"
        "Transactions: %{customdata[0]:,.0f}<br>"
        "Net sales: %{customdata[1]}<br>"
        "Profit: %{customdata[2]}"
        "<extra></extra>"
    )
)

fig_subcategory.add_hline(
    y=0,
    line_dash="dash",
    line_color="#E74C3C",
    line_width=2,
    annotation_text="Break-even"
)

fig_subcategory.update_layout(
    template=chart_template,
    height=450,
    xaxis_title="Discount Band",
    yaxis_title="Profit Margin (%)",
    hoverlabel=dict(namelength=-1),
    margin=dict(t=70, b=60)
)

fig_subcategory.update_yaxes(
    ticksuffix="%"
)

st.plotly_chart(
    fig_subcategory,
    use_container_width=True
)

# -----------------------------------
# SUMMARY TABLE
# -----------------------------------

st.subheader("Discount Performance Summary")

display_data = discount_summary.copy()

for col in [
    "Gross_Sales",
    "Discount_Amount",
    "Net_Sales",
    "Profit"
]:
    display_data[col] = display_data[col].map(format_inr)

display_data["Orders"] = display_data["Orders"].map(
    lambda x: format_indian_number(x, 0)
)

display_data["Profit_Margin"] = display_data[
    "Profit_Margin"
].map(
    lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A"
)

display_data = display_data.rename(columns={
    "Discount_Band": "Discount Band",
    "Orders": "Transactions",
    "Gross_Sales": "Gross Sales",
    "Discount_Amount": "Discount Amount",
    "Net_Sales": "Net Sales",
    "Profit": "Profit",
    "Profit_Margin": "Profit Margin"
})

st.dataframe(
    display_data,
    use_container_width=True,
    hide_index=True
)

# -----------------------------------
# BUSINESS INSIGHTS
# -----------------------------------

st.subheader("Key Business Insights")

st.markdown("""
- Profit margins decline progressively as discount levels increase.
- Transactions with discounts above 20% generate negative aggregate profit.
- Higher discounts are associated with substantial margin erosion, particularly in Technology.
- Computers and Phones are especially vulnerable to higher discount levels, while Accessories and Monitors retain stronger profitability.
- Discount decisions should consider product-level margin differences instead of applying a uniform discount policy across categories.
""")

st.warning(
    "These results show an association between discount levels and profitability. "
    "They do not establish that discounts alone caused the decline; product mix, "
    "transaction size and other factors may also influence margins."
)
