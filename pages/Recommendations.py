
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
# DISCOUNT ANALYSIS
# -----------------------------------

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


def calculate_margin(data):
    sales = data["Net_Sales"].sum()
    profit = data["Profit"].sum()

    return profit / sales * 100 if sales else 0


no_discount_margin = calculate_margin(no_discount)
mid_discount_margin = calculate_margin(mid_discount)
high_discount_margin = calculate_margin(high_discount)

high_discount_profit = high_discount["Profit"].sum()
high_discount_orders = high_discount["Order_ID"].nunique()


# -----------------------------------
# OVERALL BUSINESS METRICS
# -----------------------------------

total_sales = filtered_df["Net_Sales"].sum()
total_profit = filtered_df["Profit"].sum()

total_margin = (
    total_profit / total_sales * 100
    if total_sales else 0
)

st.subheader("The Business Performance Snapshot")

c1, c2, c3 = st.columns(3)

c1.metric(
    "Net Sales",
    f"₹{total_sales/10000000:.2f} Cr"
)

c2.metric(
    "Total Profit",
    f"₹{total_profit/100000:.2f} L"
)

c3.metric(
    "Overall Profit Margin",
    f"{total_margin:.2f}%"
)

st.divider()


# -----------------------------------
# RECOMMENDATION 1
# -----------------------------------

st.subheader("01 | Introduce Margin-Based Discount Controls")

st.markdown("""
**Business issue:** Increasing discount levels are associated with
a substantial decline in profit margins.
""")

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


# -----------------------------------
# DISCOUNT COMPARISON CHART
# -----------------------------------

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
    title="Profitability Declines at Higher Discount Levels",
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
    width=0.48,
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
    margin=dict(
        t=70,
        b=55,
        l=45,
        r=35
    )
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

st.markdown("""
- Establish minimum transaction-level profit-margin thresholds.
- Introduce approval requirements for discounts exceeding defined limits.
- Flag transactions expected to generate negative contribution profit.
- Evaluate product cost and shipping expense before approving discounts.
""")

st.success(
    f"Evidence: Transactions with discounts above 20% "
    f"generated ₹{high_discount_profit:,.0f} in aggregate profit "
    f"across {high_discount_orders:,} transactions in the selected period."
)

st.divider()


# -----------------------------------
# RECOMMENDATION 2
# -----------------------------------

st.subheader("02 | Adopt Subcategory-Specific Pricing Strategies")

st.markdown("""
**Business issue:** Product categories and subcategories contribute
differently to revenue and profitability. Uniform discount policies
may therefore fail to protect margins.
""")

technology = filtered_df[
    filtered_df["Category"] == "Technology"
]

technology_sales = technology["Net_Sales"].sum()

technology_share = (
    technology_sales / total_sales * 100
    if total_sales else 0
)

technology_high_discount = technology[
    technology["Discount_Pct"] > 0.15
]

technology_subcategory = (
    technology_high_discount
    .groupby("Subcategory")
    .agg(
        Orders=("Order_ID", "nunique"),
        Net_Sales=("Net_Sales", "sum"),
        Profit=("Profit", "sum")
    )
    .reset_index()
)

technology_subcategory["Profit_Margin"] = (
    technology_subcategory["Profit"] /
    technology_subcategory["Net_Sales"] * 100
)

c1, c2 = st.columns(2)

c1.metric(
    "Technology Sales Contribution",
    f"{technology_share:.1f}%"
)

c2.metric(
    "Technology Net Sales",
    f"₹{technology_sales/10000000:.2f} Cr"
)

st.markdown(
    "**Technology subcategory profitability at discounts above 15%**"
)


# -----------------------------------
# TECHNOLOGY SUBCATEGORY CHART
# -----------------------------------

fig_technology = px.bar(
    technology_subcategory.sort_values("Profit_Margin"),
    x="Profit_Margin",
    y="Subcategory",
    orientation="h",
    text=technology_subcategory.sort_values(
        "Profit_Margin"
    )["Profit_Margin"].map(lambda x: f"{x:.2f}%"),
    color="Profit_Margin",
    color_continuous_scale="RdYlGn",
    title="High-Discount Profit Margin by Technology Subcategory"
)

fig_technology.add_vline(
    x=0,
    line_dash="dash",
    line_color="red"
)

fig_technology.update_layout(
    template="plotly_white",
    height=400,
    coloraxis_showscale=False,
    xaxis_title="Profit Margin (%)"
)

st.plotly_chart(
    fig_technology,
    use_container_width=True
)


st.markdown("**Recommended actions**")

st.markdown("""
- Apply tighter discount controls to Computers and Phones.
- Use targeted promotions for products with greater margin headroom.
- Review subcategory-level margins before launching campaigns.
- Measure promotion success using incremental profit rather than sales growth alone.
""")

st.success(
    "Expected benefit: Protect margins in the largest revenue category "
    "while allowing targeted promotions where profitability can be sustained."
)

st.divider()


# -----------------------------------
# MANAGEMENT TAKEAWAY
# -----------------------------------

st.subheader("Overall Management Takeaway")

st.markdown("""
The analysis indicates that revenue growth should be balanced with
profitability. Management should prioritize disciplined discounting
and differentiated pricing strategies rather than relying on
uniform promotions across all products.

These actions can help protect transaction-level contribution
profit while supporting sustainable sales growth.
""")

st.caption(
    "Note: Observed discount-profitability relationships are associations, "
    "not proof of causation. Results reflect the supplied dataset and "
    "do not represent projected savings."
)
