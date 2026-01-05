
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from analytics import DataLoader, KPIEngine, DataQuality

st.set_page_config(page_title="Affiliate Commerce Tracker", layout="wide")

# Custom CSS for "Looker-like" feel
st.markdown("""
<style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        color: #0068c9;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    loader = DataLoader()
    return loader.get_data()

df = load_data()

# Sidebar
st.sidebar.title("Filters")
min_date = df['date'].min()
max_date = df['date'].max()

if pd.isnull(min_date): 
    st.error("No data available.")
    st.stop()

date_range = st.sidebar.date_input("Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)
selected_vertical = st.sidebar.multiselect("Vertical", df['vertical'].unique(), default=df['vertical'].unique())

# Filter Logic
mask = (df['date'] >= pd.to_datetime(date_range[0])) & (df['date'] <= pd.to_datetime(date_range[1]))
mask &= df['vertical'].isin(selected_vertical)
filtered_df = df[mask]

# KPIs
kpis, metrics = KPIEngine.calculate_kpis(filtered_df)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Executive Summary", "Partner Performance", "Campaign Details", "Insights & Report"])

with tab1:
    st.title("Executive Summary")
    
    # Top Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue", f"${metrics['revenue']:,.2f}", f"{kpis['ROI']*100:.1f}% ROI")
    col2.metric("Total Spend (Comm.)", f"${metrics['commission_paid']:,.2f}")
    col3.metric("Total Orders", f"{metrics['orders']}")
    col4.metric("Average Order Value", f"${kpis['AOV']:.2f}")
    
    # Charts
    st.subheader("Revenue & Commission Trend")
    daily_trend = filtered_df.groupby('date')[['revenue', 'commission_paid']].sum().reset_index()
    fig_trend = px.line(daily_trend, x='date', y=['revenue', 'commission_paid'], 
                        labels={'value': 'Amount ($)', 'variable': 'Metric'},
                        color_discrete_map={'revenue': '#0068c9', 'commission_paid': '#ff4b4b'})
    st.plotly_chart(fig_trend, use_container_width=True)
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("Top Partners by Revenue")
        partner_perf = KPIEngine.get_partner_performance(filtered_df)
        top_partners = partner_perf.sort_values('revenue', ascending=False).head(10)
        fig_bar = px.bar(top_partners, x='revenue', y='partner_name', orientation='h', 
                         title="Top 10 Revenue Generators", color='revenue')
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col_b:
        st.subheader("Efficiency (ROI vs Volume)")
        fig_scatter = px.scatter(partner_perf, x='clicks', y='ROI', size='revenue', hover_name='partner_name',
                                 color='vertical', title="Partner Efficiency Matrix")
        st.plotly_chart(fig_scatter, use_container_width=True)

with tab2:
    st.title("Partner Performance Drilldown")
    st.dataframe(partner_perf.style.format({
        'revenue': '${:,.2f}',
        'commission_paid': '${:,.2f}',
        'ROI': '{:.2f}',
        'CTR': '{:.2%}',
        'Conversion_Rate': '{:.2%}',
        'EPC': '${:.2f}',
        'AOV': '${:.2f}'
    }), use_container_width=True)

with tab3:
    st.title("Campaign Analysis")
    camp_perf = KPIEngine.get_campaign_performance(filtered_df)
    
    st.subheader("A/B Test Variant Performance")
    variant_perf = filtered_df.groupby('landing_page_variant').agg({
        'clicks': 'sum', 'orders': 'sum', 'revenue': 'sum'
    }).reset_index()
    variant_perf['CVR'] = variant_perf['orders'] / variant_perf['clicks']
    
    col_v1, col_v2 = st.columns(2)
    col_v1.dataframe(variant_perf)
    
    fig_var = px.bar(variant_perf, x='landing_page_variant', y='CVR', title="Conversion Rate by Variant", color='landing_page_variant')
    col_v2.plotly_chart(fig_var, use_container_width=True)
    
    st.subheader("Full Campaign Data")
    st.dataframe(camp_perf)
    
    st.subheader("Data Quality Anomaly Detection")
    dq = DataQuality()
    issues = dq.run_checks(filtered_df)
    for issue in issues:
        if "CRITICAL" in issue:
            st.error(issue)
        elif "WARNING" in issue:
            st.warning(issue)
        else:
            st.info(issue)

with tab4:
    st.title("Automated Stakeholder Report")
    st.markdown("### 🤖 Agent 4 Recommendations")
    
    # Simple Insight Logic
    low_roi = partner_perf[partner_perf['ROI'] < 1.0]
    high_roi = partner_perf[partner_perf['ROI'] > 4.0]
    
    st.markdown("#### 🚨 Underperforming Partners (ROI < 1.0)")
    if not low_roi.empty:
        st.markdown(f"Found **{len(low_roi)}** partners with negative or low ROI. Consider renegotiating terms or pausing.")
        st.table(low_roi[['partner_name', 'ROI', 'revenue']])
    else:
        st.success("No critical underperformers detected.")
        
    st.markdown("#### 🚀 High Potential Opportunities (ROI > 4.0)")
    if not high_roi.empty:
        st.markdown(f"Found **{len(high_roi)}** partners with exceptional ROI. Recommend increasing budget/exposure.")
        st.table(high_roi[['partner_name', 'ROI', 'revenue']])
    

