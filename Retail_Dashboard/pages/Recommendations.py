
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------------------------
# THEME
# -----------------------------------

is_dark = st.get_option("theme.base") == "dark"
chart_template = "plotly_dark" if is_dark else "plotly_white"


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
        return format_inr_crores(value)
    elif abs(value) >= 100000:
        return format_inr_lakhs(value)
    else:
        return format_inr(value)


def calculate_margin(data):
    sales = data["Net_Sales"].sum()
    profit = data["Profit"].sum()

    return profit / sales * 100 if sales else 0


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

st.title("Management Recommendations")

st.markdown(
    "### Translating business analysis into actionable decisions"
)

st.markdown(
    """
    Recommendations are drawn from sales trends, regional performance,
    product profitability, and discount analysis to support sustainable
    business growth.
    """
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
    key="recommendation_years"
)

if not selected_years:
    st.warning("Please select at least one year to view the recommendations.")
    st.stop()

filtered_df = df[
    df["Order_Date"].dt.year.isin(selected_years)
].copy()


# -----------------------------------
# BUSINESS PERFORMANCE SNAPSHOT
# -----------------------------------

total_sales = filtered_df["Net_Sales"].sum()
total_profit = filtered_df["Profit"].sum()
total_margin = calculate_margin(filtered_df)

st.subheader("Business Performance Snapshot")

c1, c2, c3 = st.columns(3)

c1.metric(
    "Net Sales",
    format_inr_crores(total_sales)
)

c2.metric(
    "Total Profit",
    format_inr_lakhs(total_profit)
)

c3.metric(
    "Overall Profit Margin",
    f"{total_margin:.2f}%"
)

st.divider()


# ==========================================================
# RECOMMENDATION 1 - SALES GROWTH
# ==========================================================

st.subheader("01 | Sustain Sales Growth Through Demand Planning")

st.markdown(
    """
    **Business opportunity:** Sustained sales growth creates an opportunity
    to improve planning and align operational resources with demand.
    """
)

# Yearly sales
yearly_sales = (
    filtered_df
    .groupby(filtered_df["Order_Date"].dt.year)
    ["Net_Sales"]
    .sum()
    .reset_index()
)

yearly_sales.columns = ["Year", "Net_Sales"]

yearly_sales["Sales_Label"] = yearly_sales["Net_Sales"].apply(
    format_compact_inr
)

fig_sales = px.bar(
    yearly_sales,
    x="Year",
    y="Net_Sales",
    text="Sales_Label",
    title="Annual Net Sales Trend",
)

fig_sales.update_traces(
    textposition="outside",
    cliponaxis=False,
    hovertemplate=(
        "<b>Year: %{x}</b><br>"
        "Net Sales: %{y:,.2f}"
        "<extra></extra>"
    )
)

fig_sales.update_layout(
    template=chart_template,
    height=380,
    showlegend=False,
    yaxis_title="Net Sales (₹)",
    xaxis_title="Year",
    margin=dict(t=70, b=50, l=50, r=30),
)

st.plotly_chart(
    fig_sales,
    use_container_width=True
)

# Sales growth calculation
yearly_sales_sorted = yearly_sales.sort_values("Year").copy()

if len(yearly_sales_sorted) >= 2:
    previous_sales = yearly_sales_sorted.iloc[-2]["Net_Sales"]
    current_sales = yearly_sales_sorted.iloc[-1]["Net_Sales"]

    sales_growth = (
        (current_sales - previous_sales) / previous_sales * 100
        if previous_sales else 0
    )

    st.metric(
        "Sales Growth Between Latest Selected Years",
        f"{sales_growth:.2f}%"
    )

st.markdown("**Recommended actions**")

st.markdown(
    """
    - Use historical sales trends to anticipate demand across the year.
    - Align marketing campaigns and operational capacity with high-demand periods.
    - Monitor growth patterns to support sales targets and planning.
    - Review whether growth is sustainable rather than relying on short-term spikes.
    """
)

st.info(
    "Management focus: Convert historical sales growth into more predictable "
    "demand planning and resource allocation."
)

st.divider()


# ==========================================================
# RECOMMENDATION 2 - REGIONAL PERFORMANCE
# ==========================================================

st.subheader("02 | Strengthen Regional Performance")

st.markdown(
    """
    **Business opportunity:** Regional differences in sales and profitability
    can help management identify where to replicate successful practices
    and where targeted improvements may be needed.
    """
)

regional_summary = (
    filtered_df
    .groupby("Region")
    .agg(
        Net_Sales=("Net_Sales", "sum"),
        Profit=("Profit", "sum"),
        Orders=("Order_ID", "nunique")
    )
    .reset_index()
)

regional_summary["Profit_Margin"] = (
    regional_summary["Profit"] /
    regional_summary["Net_Sales"].replace(0, float("nan")) * 100
)

regional_summary = regional_summary.sort_values(
    "Net_Sales",
    ascending=False
)

regional_summary["Sales_Label"] = regional_summary["Net_Sales"].apply(
    format_compact_inr
)

fig_region_sales = px.bar(
    regional_summary,
    x="Region",
    y="Net_Sales",
    text="Sales_Label",
    title="Regional Sales Contribution",
)

fig_region_sales.update_traces(
    textposition="outside",
    cliponaxis=False,
    hovertemplate=(
        "<b>%{x}</b><br>"
        "Net Sales: %{y:,.2f}"
        "<extra></extra>"
    )
)

fig_region_sales.update_layout(
    template=chart_template,
    height=380,
    showlegend=False,
    xaxis_title="Region",
    yaxis_title="Net Sales (₹)",
    margin=dict(t=70, b=50, l=50, r=30),
)

st.plotly_chart(
    fig_region_sales,
    use_container_width=True
)

fig_region_margin = px.bar(
    regional_summary.sort_values("Profit_Margin"),
    x="Profit_Margin",
    y="Region",
    orientation="h",
    text="Profit_Margin",
    title="Regional Profitability",
)

fig_region_margin.update_traces(
    texttemplate="%{x:.2f}%",
    textposition="outside",
    cliponaxis=False,
    hovertemplate=(
        "<b>%{y}</b><br>"
        "Profit Margin: %{x:.2f}%"
        "<extra></extra>"
    )
)

fig_region_margin.update_layout(
    template=chart_template,
    height=380,
    showlegend=False,
    xaxis_title="Profit Margin (%)",
    yaxis_title="Region",
    margin=dict(t=70, b=50, l=10, r=60),
)

fig_region_margin.update_xaxes(ticksuffix="%")

st.plotly_chart(
    fig_region_margin,
    use_container_width=True
)

highest_sales_region = regional_summary.iloc[0]

highest_margin_region = regional_summary.loc[
    regional_summary["Profit_Margin"].idxmax()
]

st.markdown("**Recommended actions**")

st.markdown(
    f"""
    - Protect the performance of **{highest_sales_region['Region']}**,
      the leading region by sales in the selected period.
    - Use high-performing regions as benchmarks for sales and operational practices.
    - Investigate regions with lower margins to identify product mix,
      pricing, or cost-related improvement opportunities.
    - Allocate regional resources based on both revenue contribution
      and profitability.
    """
)

st.info(
    f"Regional evidence: {highest_sales_region['Region']} leads in sales, "
    f"while {highest_margin_region['Region']} has the highest profit margin. "
    "Revenue leadership and margin leadership should be evaluated separately."
)

st.divider()


# ==========================================================
# RECOMMENDATION 3 - PRODUCT PORTFOLIO
# ==========================================================

st.subheader("03 | Optimize the Product Portfolio for Profitability")

st.markdown(
    """
    **Business opportunity:** Product categories contribute differently
    to revenue and profit. Management should prioritize profitable growth
    rather than revenue alone.
    """
)

category_summary = (
    filtered_df
    .groupby("Category")
    .agg(
        Net_Sales=("Net_Sales", "sum"),
        Profit=("Profit", "sum"),
        Orders=("Order_ID", "nunique")
    )
    .reset_index()
)

category_summary["Profit_Margin"] = (
    category_summary["Profit"] /
    category_summary["Net_Sales"].replace(0, float("nan")) * 100
)

category_summary["Sales_Label"] = category_summary["Net_Sales"].apply(
    format_compact_inr
)

fig_category_sales = px.bar(
    category_summary.sort_values("Net_Sales", ascending=False),
    x="Category",
    y="Net_Sales",
    text="Sales_Label",
    title="Sales Contribution by Product Category",
)

fig_category_sales.update_traces(
    textposition="outside",
    cliponaxis=False,
    hovertemplate=(
        "<b>%{x}</b><br>"
        "Net Sales: %{y:,.2f}"
        "<extra></extra>"
    )
)

fig_category_sales.update_layout(
    template=chart_template,
    height=380,
    showlegend=False,
    xaxis_title="Category",
    yaxis_title="Net Sales (₹)",
    margin=dict(t=70, b=50, l=50, r=30),
)

st.plotly_chart(
    fig_category_sales,
    use_container_width=True
)

fig_category_margin = px.bar(
    category_summary.sort_values("Profit_Margin"),
    x="Profit_Margin",
    y="Category",
    orientation="h",
    text="Profit_Margin",
    title="Profit Margin by Product Category",
)

fig_category_margin.update_traces(
    texttemplate="%{x:.2f}%",
    textposition="outside",
    cliponaxis=False,
    hovertemplate=(
        "<b>%{y}</b><br>"
        "Profit Margin: %{x:.2f}%"
        "<extra></extra>"
    )
)

fig_category_margin.update_layout(
    template=chart_template,
    height=380,
    showlegend=False,
    xaxis_title="Profit Margin (%)",
    yaxis_title="Category",
    margin=dict(t=70, b=50, l=10, r=60),
)

fig_category_margin.update_xaxes(ticksuffix="%")

st.plotly_chart(
    fig_category_margin,
    use_container_width=True
)

highest_category_sales = category_summary.loc[
    category_summary["Net_Sales"].idxmax()
]

highest_category_margin = category_summary.loc[
    category_summary["Profit_Margin"].idxmax()
]

st.markdown("**Recommended actions**")

st.markdown(
    f"""
    - Prioritize products and categories with strong profit contribution.
    - Review high-revenue categories whose margins are comparatively weaker.
    - Reassess consistently low-performing products and subcategories.
    - Use both sales contribution and profit margin when making assortment decisions.
    """
)

st.info(
    f"Product evidence: {highest_category_sales['Category']} leads category sales, "
    f"while {highest_category_margin['Category']} has the highest category profit margin. "
    "The strongest revenue contributors are not necessarily the most profitable."
)

st.divider()


# ==========================================================
# RECOMMENDATION 4 - DISCOUNT MANAGEMENT
# ==========================================================

st.subheader("04 | Implement Margin-Based Discount Controls")

st.markdown(
    """
    **Business issue:** Increasing discount levels are associated with
    declining profit margins. Promotions should be evaluated based on
    their contribution to profitability rather than sales volume alone.
    """
)

no_discount = filtered_df[
    filtered_df["Discount_Pct"].round(2) == 0
]

mid_discount = filtered_df[
    (filtered_df["Discount_Pct"] > 0.15) &
    (filtered_df["Discount_Pct"] <= 0.20)
]

high_discount = filtered_df[
    filtered_df["Discount_Pct"] > 0.20
]

no_discount_margin = calculate_margin(no_discount)
mid_discount_margin = calculate_margin(mid_discount)
high_discount_margin = calculate_margin(high_discount)

high_discount_profit = high_discount["Profit"].sum()
high_discount_orders = high_discount["Order_ID"].nunique()

c1, c2, c3 = st.columns(3)

c1.metric(
    "No Discount Margin",
    f"{no_discount_margin:.2f}%"
)

c2.metric(
    "15–20% Discount Margin",
    f"{mid_discount_margin:.2f}%"
)

c3.metric(
    "Above 20% Discount Margin",
    f"{high_discount_margin:.2f}%",
    delta=f"{high_discount_margin-no_discount_margin:.2f} pp",
    delta_color="inverse"
)

discount_comparison = pd.DataFrame({
    "Discount Group": [
        "No discount",
        "15–20%",
        "Above 20%"
    ],
    "Profit Margin": [
        no_discount_margin,
        mid_discount_margin,
        high_discount_margin
    ]
})

fig_discount = px.bar(
    discount_comparison,
    x="Discount Group",
    y="Profit Margin",
    text="Profit Margin",
    title="Profitability Across Discount Levels",
    color="Discount Group",
    color_discrete_map={
        "No discount": "#35A68A",
        "15–20%": "#E49B45",
        "Above 20%": "#D9534F"
    }
)

fig_discount.update_traces(
    texttemplate="%{y:.2f}%",
    textposition="outside",
    cliponaxis=False,
    hovertemplate=(
        "<b>%{x}</b><br>"
        "Profit Margin: %{y:.2f}%"
        "<extra></extra>"
    )
)

min_margin = min(
    0,
    discount_comparison["Profit Margin"].min()
)

max_margin = max(
    0,
    discount_comparison["Profit Margin"].max()
)

padding = max(
    (max_margin - min_margin) * 0.15,
    2
)

fig_discount.update_layout(
    template=chart_template,
    height=380,
    showlegend=False,
    yaxis_title="Profit Margin (%)",
    xaxis_title="Discount Group",
    yaxis=dict(
        range=[
            min_margin - padding,
            max_margin + padding
        ],
        zeroline=False
    ),
    margin=dict(t=70, b=55, l=45, r=35)
)

fig_discount.add_hline(
    y=0,
    line_dash="dash",
    line_color="#D9534F",
    line_width=2,
    annotation_text="Break-even",
    annotation_position="top left"
)

st.plotly_chart(
    fig_discount,
    use_container_width=True
)

st.markdown("**Recommended actions**")

st.markdown(
    """
    - Establish minimum transaction-level profit thresholds.
    - Introduce approval requirements for discounts exceeding defined limits.
    - Flag transactions expected to generate negative profit.
    - Evaluate product cost and shipping expense before approving discounts.
    - Measure promotional success using incremental profit rather than revenue alone.
    """
)

st.success(
    f"Evidence: Transactions with discounts above 20% generated "
    f"{format_inr(high_discount_profit)} in aggregate profit across "
    f"{format_indian_number(high_discount_orders, 0)} transactions "
    "in the selected period."
)

st.divider()


# ==========================================================
# RECOMMENDATION 5 - CROSS-ANALYSIS / RESOURCE ALLOCATION
# ==========================================================

st.subheader("05 | Prioritize Regional Product Opportunities")

st.markdown(
    """
    **Business opportunity:** Combining regional and product performance
    can help management identify where sales are concentrated and
    allocate commercial resources more effectively.
    """
)

region_category_sales = (
    filtered_df
    .groupby(["Region", "Category"])["Net_Sales"]
    .sum()
    .reset_index()
)

region_category_pivot = region_category_sales.pivot(
    index="Region",
    columns="Category",
    values="Net_Sales"
).fillna(0)

# Indian currency formatting for cell labels and hover
formatted_values = region_category_pivot.map(
    format_inr_lakhs
)

fig_region_category = px.imshow(
    region_category_pivot,
    text_auto=False,
    aspect="auto",
    color_continuous_scale="Blues",
    title="Sales Distribution Across Regions and Product Categories"
)

fig_region_category.update_traces(
    text=formatted_values.values,
    customdata=formatted_values.values,
    texttemplate="%{text}",
    hovertemplate=(
        "<b>Region: %{y}</b><br>"
        "Category: %{x}<br>"
        "Net Sales: %{customdata}"
        "<extra></extra>"
    )
)

# Color scale remains based on the original sales values
max_sales = region_category_pivot.values.max()

tick_step = 2000000
tick_max = ((max_sales // tick_step) + 1) * tick_step

tick_values = list(range(0, int(tick_max) + tick_step, tick_step))

tick_labels = [
    f"₹{format_indian_number(value / 100000, 0)} L"
    for value in tick_values
]

fig_region_category.update_layout(
    template=chart_template,
    height=420,
    xaxis_title="Product Category",
    yaxis_title="Region",
    coloraxis_colorbar=dict(
        title="Net Sales",
        tickvals=tick_values,
        ticktext=tick_labels
    ),
    margin=dict(t=70, b=50, l=50, r=40)
)

st.plotly_chart(
    fig_region_category,
    use_container_width=True
)

st.markdown("**Recommended actions**")

st.markdown(
    """
    - Prioritize regional markets with strong product-category sales.
    - Maintain focus on high-performing Technology markets.
    - Investigate opportunities to strengthen Furniture and Office Supplies
      sales through targeted assortment and cross-selling initiatives.
    - Use regional product demand patterns to inform future resource planning.
    """
)

st.warning(
    "The dataset supports analysis of sales demand patterns, but does not "
    "directly measure inventory levels or stockouts. Inventory recommendations "
    "should therefore be validated using operational inventory data."
)

st.divider()


# ==========================================================
# OVERALL MANAGEMENT TAKEAWAY
# ==========================================================

st.subheader("Overall Management Takeaway")

st.markdown(
    """
    Sustainable retail performance requires balancing revenue growth,
    regional opportunities, product profitability, and pricing discipline.

    Management should use sales trends to support demand planning,
    regional performance to guide resource allocation, product analysis
    to prioritize profitable categories, and discount analysis to protect margins.

    These decisions should be reviewed together rather than treated
    as independent activities.
    """
)

st.caption(
    "Note: Findings reflect the selected period and the supplied dataset. "
    "Observed relationships are descriptive and do not establish causation. "
    "Recommendations are strategic opportunities, not projected financial savings."
)
