# app.py
"""
Streamlit dashboard for E‑Commerce Sales Analytics (portfolio project).

- Loads cleaned dataset from data/ecommerce_sales_cleaned.csv (falls back to data/ecommerce_sales.csv).
- Shows KPI cards, interactive filters, charts, and a data table with CSV download.
- Uses Pandas for data handling and Plotly Express for charts.

Notes for beginners are included as comments next to important blocks.

Run locally from the project root (after installing dependencies):
    python -m streamlit run app.py

Do not modify the source CSV from the dashboard.
"""

from pathlib import Path
import io
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# ---------- Helper functions ----------
@st.cache_data
def load_data():
    """Load the cleaned dataset using a robust relative path.
    Returns a DataFrame (may be empty if file not found).
    """
    base = Path(__file__).parent
    # Prefer cleaned file but fall back to raw CSV if cleaned missing
    candidates = [base / 'data' / 'ecommerce_sales_cleaned.csv', base / 'data' / 'ecommerce_sales.csv']
    for p in candidates:
        if p.exists():
            try:
                df = pd.read_csv(p)
            except Exception as e:
                st.error(f"Failed to read CSV at {p}: {e}")
                return pd.DataFrame()
            # Ensure expected columns exist and coerce types
            for col in ['Order_Date']:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            for col in ['Quantity', 'Unit_Price', 'Discount', 'Sales']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            return df
    # If neither file exists, return empty DataFrame
    return pd.DataFrame()


def format_currency(x):
    try:
        return f"₹{x:,.2f}"
    except Exception:
        return x


# ---------- App layout & logic ----------
st.set_page_config(page_title='E-Commerce Sales Analytics', layout='wide')
st.title('E-Commerce Sales Analytics — Interactive Dashboard')
st.markdown('This dashboard uses a synthetic sample dataset for learning and portfolio purposes. Do not present it as real company data.')

# Load data
with st.spinner('Loading data...'):
    df = load_data()

if df.empty:
    st.error('No data found. Expected data/ecommerce_sales_cleaned.csv (or data/ecommerce_sales.csv). Run the data generation and cleaning scripts first.')
    st.stop()

# Sidebar filters
st.sidebar.header('Filters')
min_date = df['Order_Date'].min() if 'Order_Date' in df.columns else None
max_date = df['Order_Date'].max() if 'Order_Date' in df.columns else None

if min_date is not None and max_date is not None:
    date_range = st.sidebar.date_input('Order date range', value=(min_date.date(), max_date.date()), min_value=min_date.date(), max_value=max_date.date())
else:
    date_range = None

# Category, Region, Payment Method filters (multi-select). Use unique values from data.
category_options = df['Category'].dropna().unique().tolist() if 'Category' in df.columns else []
region_options = df['Region'].dropna().unique().tolist() if 'Region' in df.columns else []
payment_options = df['Payment_Method'].dropna().unique().tolist() if 'Payment_Method' in df.columns else []

selected_categories = st.sidebar.multiselect('Category', options=sorted(category_options), default=sorted(category_options))
selected_regions = st.sidebar.multiselect('Region', options=sorted(region_options), default=sorted(region_options))
selected_payments = st.sidebar.multiselect('Payment Method', options=sorted(payment_options), default=sorted(payment_options))

# Apply filters
filtered = df.copy()
if date_range and len(date_range) == 2:
    start_dt = pd.to_datetime(date_range[0])
    end_dt = pd.to_datetime(date_range[1])
    filtered = filtered[(filtered['Order_Date'] >= start_dt) & (filtered['Order_Date'] <= end_dt)]

if 'Category' in filtered.columns and selected_categories:
    filtered = filtered[filtered['Category'].isin(selected_categories)]
if 'Region' in filtered.columns and selected_regions:
    filtered = filtered[filtered['Region'].isin(selected_regions)]
if 'Payment_Method' in filtered.columns and selected_payments:
    filtered = filtered[filtered['Payment_Method'].isin(selected_payments)]

# Handle case where filters exclude all rows
if filtered.shape[0] == 0:
    st.warning('No records match the selected filters. Try widening the date range or selecting more categories/regions/payment methods.')
    st.stop()

# KPI calculations (use consistent aggregation logic)
total_revenue = filtered['Sales'].sum() if 'Sales' in filtered.columns else np.nan
total_orders = filtered['Order_ID'].nunique() if 'Order_ID' in filtered.columns else filtered.shape[0]
unique_customers = filtered['Customer_ID'].nunique() if 'Customer_ID' in filtered.columns else np.nan
units_sold = int(filtered['Quantity'].sum()) if 'Quantity' in filtered.columns else np.nan

# Average order value: sum of Sales per Order_ID, then mean
if 'Sales' in filtered.columns and 'Order_ID' in filtered.columns:
    order_totals = filtered.groupby('Order_ID')['Sales'].sum()
    aov = order_totals.mean()
else:
    aov = np.nan

# Display KPI cards in 5 columns
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

kpi1.metric('Total revenue', format_currency(total_revenue), delta=None)
kpi2.metric('Total orders', f"{total_orders:,}")
kpi3.metric('Unique customers', f"{unique_customers:,}")
kpi4.metric('Units sold', f"{units_sold:,}")
kpi5.metric('Average order value', format_currency(aov))

st.markdown('---')

# Charts area
st.subheader('Sales charts')

# Monthly revenue trend
col1, col2 = st.columns([2, 1])
with col1:
    st.markdown('**Monthly revenue trend**')
    if 'Order_Date' in filtered.columns:
        monthly = filtered.copy()
        monthly['YearMonth'] = monthly['Order_Date'].dt.to_period('M').dt.to_timestamp()
        monthly_rev = monthly.groupby('YearMonth', as_index=False)['Sales'].sum()
        fig_month = px.line(monthly_rev, x='YearMonth', y='Sales', markers=True, title='Monthly Revenue')
        fig_month.update_layout(yaxis_tickformat=',.2f')
        st.plotly_chart(fig_month, use_container_width=True)
    else:
        st.info('Order_Date column missing — cannot show monthly trend')

# Revenue by category
with col2:
    st.markdown('**Revenue by category**')
    if 'Category' in filtered.columns:
        cat_rev = filtered.groupby('Category', as_index=False)['Sales'].sum().sort_values('Sales', ascending=False)
        fig_cat = px.bar(cat_rev, x='Sales', y='Category', orientation='h', title='Revenue by Category', height=400)
        fig_cat.update_layout(yaxis={'categoryorder':'total descending'}, xaxis_tickformat=',.2f')
        st.plotly_chart(fig_cat, use_container_width=True)
    else:
        st.info('Category column missing — cannot show category breakdown')

st.markdown('---')

# Top 10 products and regional revenue
col3, col4 = st.columns(2)
with col3:
    st.markdown('**Top 10 products by revenue**')
    if 'Product' in filtered.columns:
        prod_rev = filtered.groupby('Product', as_index=False)['Sales'].sum().sort_values('Sales', ascending=False).head(10)
        fig_prod = px.bar(prod_rev, x='Sales', y='Product', orientation='h', title='Top 10 Products', height=500)
        fig_prod.update_layout(yaxis={'categoryorder':'total descending'}, xaxis_tickformat=',.2f')
        st.plotly_chart(fig_prod, use_container_width=True)
    else:
        st.info('Product column missing — cannot show top products')

with col4:
    st.markdown('**Revenue by region**')
    if 'Region' in filtered.columns:
        reg_rev = filtered.groupby('Region', as_index=False)['Sales'].sum().sort_values('Sales', ascending=False)
        fig_reg = px.bar(reg_rev, x='Sales', y='Region', orientation='h', title='Revenue by Region', height=500)
        fig_reg.update_layout(yaxis={'categoryorder':'total descending'}, xaxis_tickformat=',.2f')
        st.plotly_chart(fig_reg, use_container_width=True)
    else:
        st.info('Region column missing — cannot show regional revenue')

st.markdown('---')

# Payment method distribution
st.subheader('Payment method distribution')
if 'Payment_Method' in filtered.columns:
    pay_rev = filtered.groupby('Payment_Method', as_index=False)['Sales'].sum()
    fig_pay = px.pie(pay_rev, values='Sales', names='Payment_Method', title='Revenue share by Payment Method')
    st.plotly_chart(fig_pay, use_container_width=True)
else:
    st.info('Payment_Method column missing — cannot show payment breakdown')

st.markdown('---')

# Detailed table and download
st.subheader('Filtered sales table')
# Show a sample of columns that are useful
table_cols = [c for c in ['Order_ID','Order_Date','Customer_ID','Product','Category','Quantity','Unit_Price','Discount','Payment_Method','Region','Sales'] if c in filtered.columns]

st.dataframe(filtered[table_cols].sort_values(by='Order_Date', ascending=False).reset_index(drop=True))

# Download button
csv = filtered[table_cols].to_csv(index=False).encode('utf-8')
st.download_button('Download filtered data as CSV', data=csv, file_name='filtered_ecommerce_sales.csv', mime='text/csv')

st.markdown('---')

# Footer / Notes
st.markdown('''
**Notes:**
- The dashboard reads data from the project `data/` folder and does not modify source files.
- Discount is stored as a decimal (e.g. 0.10 = 10%).
- Sales is computed as Quantity * Unit_Price * (1 - Discount) in the cleaned dataset generator.
''')
