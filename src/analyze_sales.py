"""
src/analyze_sales.py

Exploratory Data Analysis (EDA) for the E-Commerce Sales Analytics project.

This script:
- Loads the cleaned dataset from data/ecommerce_sales_cleaned.csv (falls back to data/ecommerce_sales.csv if not present).
- Prints dataset shape, column list, date range, and descriptive statistics for numeric columns.
- Computes business KPIs: total revenue, total orders, unique customers, total units sold, average order value, average discount.
- Aggregates sales by product, category, region, payment method, and month.
- Identifies top 10 products by revenue and top 5 regions by revenue.
- Produces charts (Matplotlib/Seaborn) and saves them to outputs/charts/.
- Saves summary metrics and grouped CSVs to outputs/.
- Prints a concise business summary (which category, product, and region generated the most revenue).

Run from project root:
    python src/analyze_sales.py

Requirements:
- pandas, numpy, matplotlib, seaborn must be installed in your environment.
  Install with: python -m pip install pandas numpy matplotlib seaborn

Notes for beginners:
- The script uses the 'Sales' column as the canonical revenue value and groups/orders by Order_ID to avoid double-counting.
- If there are missing or invalid values, the script reports counts and excludes them from aggregations where appropriate (for example, rows with missing Sales are excluded from revenue sums).

"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

sns.set_theme(style='whitegrid')

# Helper
def section(title):
    print('\n' + '='*len(title))
    print(title)
    print('='*len(title) + '\n')

# Paths
CLEANED_PATH = os.path.join('data', 'ecommerce_sales_cleaned.csv')
FALLBACK_PATH = os.path.join('data', 'ecommerce_sales.csv')

# Find file
if os.path.exists(CLEANED_PATH):
    data_path = CLEANED_PATH
elif os.path.exists(FALLBACK_PATH):
    print(f"Warning: cleaned file not found at {CLEANED_PATH}, falling back to raw file {FALLBACK_PATH}.")
    data_path = FALLBACK_PATH
else:
    print('ERROR: No dataset found. Expected data/ecommerce_sales_cleaned.csv or data/ecommerce_sales.csv')
    sys.exit(1)

section('Loading cleaned dataset')
print('Using data file:', data_path)
try:
    df = pd.read_csv(data_path)
except Exception as e:
    print('Failed to read dataset:', e)
    sys.exit(1)

# Basic info
section('Dataset overview')
print('Shape (rows, columns):', df.shape)
print('\nColumns:')
print(list(df.columns))

# Ensure Order_Date is datetime
if 'Order_Date' in df.columns:
    df['Order_Date'] = pd.to_datetime(df['Order_Date'], errors='coerce')
    valid_dates = df['Order_Date'].notna().sum()
    date_min = df['Order_Date'].min()
    date_max = df['Order_Date'].max()
    print(f"Valid Order_Date rows: {valid_dates} / {df.shape[0]}")
    print('Order date range:', date_min, 'to', date_max)
else:
    print('WARNING: Order_Date column not found; month-level analysis will be skipped')

section('Descriptive statistics (numeric columns)')
print(df.describe(include=[np.number]).transpose())

# Report missing values
section('Missing / invalid data summary')
print('Missing values per column:')
print(df.isna().sum())

# Use Sales as revenue; coerce numeric types for safety
for col in ['Quantity', 'Unit_Price', 'Discount', 'Sales']:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# Exclude rows with missing Sales for revenue calculations
valid_revenue_mask = df['Sales'].notna() if 'Sales' in df.columns else pd.Series([False]*len(df))

# KPI calculations
section('Key performance indicators (KPIs)')
# Total revenue: sum of Sales (use Sales column as canonical revenue)
if 'Sales' in df.columns:
    total_revenue = df.loc[valid_revenue_mask, 'Sales'].sum()
else:
    print('ERROR: Sales column missing; cannot compute revenue')
    total_revenue = np.nan

# Total orders: count unique Order_ID values (avoids double-counting lines belonging to same order)
if 'Order_ID' in df.columns:
    total_orders = df['Order_ID'].nunique()
else:
    total_orders = df.shape[0]
    print('Warning: Order_ID not found — using row count as orders (may double-count)')

# Unique customers
unique_customers = df['Customer_ID'].nunique() if 'Customer_ID' in df.columns else np.nan

# Total units sold
total_units_sold = df['Quantity'].sum() if 'Quantity' in df.columns else np.nan

# Average order value: revenue per order using Sales grouped by Order_ID
if 'Sales' in df.columns and 'Order_ID' in df.columns:
    revenue_per_order = df.groupby('Order_ID')['Sales'].sum()
    average_order_value = revenue_per_order.mean()
else:
    average_order_value = np.nan

# Average discount (mean across orders or rows?) — compute weighted by order count: average discount per order (mean of order-level average discount)
if 'Discount' in df.columns and 'Order_ID' in df.columns:
    order_discount = df.groupby('Order_ID')['Discount'].mean()
    average_discount = order_discount.mean()
elif 'Discount' in df.columns:
    average_discount = df['Discount'].mean()
else:
    average_discount = np.nan

print(f"Total revenue: {total_revenue:,.2f}")
print(f"Total orders (unique Order_ID): {total_orders}")
print(f"Unique customers: {unique_customers}")
print(f"Total units sold (sum Quantity): {total_units_sold}")
print(f"Average order value (AOV): {average_order_value:,.2f}")
print(f"Average discount (per order): {average_discount:.4f}")

# Grouped analyses
section('Aggregations by product, category, region, payment method, month')

# Helper to ensure grouping uses Sales column and excludes missing Sales
def safe_groupby_sum(df, group_cols, value_col='Sales'):
    if value_col not in df.columns:
        return pd.DataFrame()
    g = df[df[value_col].notna()].groupby(group_cols)[value_col].sum().reset_index().sort_values(by=value_col, ascending=False)
    return g

# Sales by product
if 'Product' in df.columns:
    revenue_by_product = safe_groupby_sum(df, ['Product'])
    # total units per product
    units_by_product = df.groupby('Product')['Quantity'].sum().reset_index().rename(columns={'Quantity': 'Total_Units'}) if 'Quantity' in df.columns else None
else:
    revenue_by_product = pd.DataFrame()
    units_by_product = pd.DataFrame()

# Sales by category
if 'Category' in df.columns:
    revenue_by_category = safe_groupby_sum(df, ['Category'])
else:
    revenue_by_category = pd.DataFrame()

# Sales by region
if 'Region' in df.columns:
    revenue_by_region = safe_groupby_sum(df, ['Region'])
else:
    revenue_by_region = pd.DataFrame()

# Sales by payment method
if 'Payment_Method' in df.columns:
    revenue_by_payment = safe_groupby_sum(df, ['Payment_Method'])
else:
    revenue_by_payment = pd.DataFrame()

# Monthly revenue trend
if 'Order_Date' in df.columns:
    df['YearMonth'] = df['Order_Date'].dt.to_period('M').dt.to_timestamp()
    revenue_by_month = safe_groupby_sum(df, ['YearMonth'])
else:
    revenue_by_month = pd.DataFrame()

# Top products and regions
section('Top products and top regions')
if not revenue_by_product.empty:
    top10_products = revenue_by_product.head(10)
    print('Top 10 products by revenue:')
    print(top10_products.to_string(index=False))
else:
    top10_products = pd.DataFrame()
    print('No product revenue data available')

if not revenue_by_region.empty:
    top5_regions = revenue_by_region.head(5)
    print('\nTop 5 regions by revenue:')
    print(top5_regions.to_string(index=False))
else:
    top5_regions = pd.DataFrame()
    print('No region revenue data available')

# Create outputs directories
os.makedirs(os.path.join('outputs', 'charts'), exist_ok=True)
os.makedirs('outputs', exist_ok=True)

section('Charts (saving to outputs/charts/)')

# 1) Monthly revenue trend
if not revenue_by_month.empty:
    plt.figure(figsize=(10,5))
    sns.lineplot(data=revenue_by_month, x='YearMonth', y='Sales', marker='o')
    plt.title('Monthly Revenue Trend')
    plt.xlabel('Month')
    plt.ylabel('Revenue (Sales)')
    plt.tight_layout()
    path = os.path.join('outputs', 'charts', 'monthly_revenue_trend.png')
    plt.savefig(path)
    plt.close()
    print('Saved chart:', path)
else:
    print('Skipping monthly revenue chart: no date-based revenue available')

# 2) Revenue by category (bar chart)
if not revenue_by_category.empty:
    plt.figure(figsize=(8,5))
    sns.barplot(data=revenue_by_category, x='Sales', y='Category', palette='viridis')
    plt.title('Revenue by Category')
    plt.xlabel('Revenue')
    plt.ylabel('Category')
    plt.tight_layout()
    path = os.path.join('outputs', 'charts', 'revenue_by_category.png')
    plt.savefig(path)
    plt.close()
    print('Saved chart:', path)
else:
    print('Skipping revenue by category chart: no category data')

# 3) Top 10 products by revenue (bar chart)
if not top10_products.empty:
    plt.figure(figsize=(10,6))
    sns.barplot(data=top10_products, x='Sales', y='Product', palette='magma')
    plt.title('Top 10 Products by Revenue')
    plt.xlabel('Revenue')
    plt.ylabel('Product')
    plt.tight_layout()
    path = os.path.join('outputs', 'charts', 'top10_products.png')
    plt.savefig(path)
    plt.close()
    print('Saved chart:', path)
else:
    print('Skipping top products chart: no product revenue data')

# 4) Revenue by region (bar chart)
if not revenue_by_region.empty:
    plt.figure(figsize=(8,5))
    sns.barplot(data=revenue_by_region, x='Sales', y='Region', palette='cubehelix')
    plt.title('Revenue by Region')
    plt.xlabel('Revenue')
    plt.ylabel('Region')
    plt.tight_layout()
    path = os.path.join('outputs', 'charts', 'revenue_by_region.png')
    plt.savefig(path)
    plt.close()
    print('Saved chart:', path)
else:
    print('Skipping revenue by region chart: no region data')

# 5) Payment method distribution (pie chart)
if not revenue_by_payment.empty:
    plt.figure(figsize=(6,6))
    plt.pie(revenue_by_payment['Sales'], labels=revenue_by_payment['Payment_Method'], autopct='%1.1f%%', startangle=140)
    plt.title('Revenue share by Payment Method')
    plt.tight_layout()
    path = os.path.join('outputs', 'charts', 'payment_method_distribution.png')
    plt.savefig(path)
    plt.close()
    print('Saved chart:', path)
else:
    print('Skipping payment method distribution chart: no payment method data')

section('Saving aggregated CSVs to outputs/')
# Save KPIs and grouped CSVs
summary_metrics = {
    'total_revenue': [total_revenue],
    'total_orders': [total_orders],
    'unique_customers': [unique_customers],
    'total_units_sold': [total_units_sold],
    'average_order_value': [average_order_value],
    'average_discount': [average_discount]
}
summary_df = pd.DataFrame(summary_metrics)
summary_path = os.path.join('outputs', 'summary_metrics.csv')
summary_df.to_csv(summary_path, index=False)
print('Saved summary metrics to', summary_path)

# Save grouped results
if not revenue_by_product.empty:
    revenue_by_product.to_csv(os.path.join('outputs', 'revenue_by_product.csv'), index=False)
    print('Saved revenue_by_product.csv')
if units_by_product is not None and not units_by_product.empty:
    units_by_product.to_csv(os.path.join('outputs', 'units_by_product.csv'), index=False)
    print('Saved units_by_product.csv')
if not revenue_by_category.empty:
    revenue_by_category.to_csv(os.path.join('outputs', 'revenue_by_category.csv'), index=False)
    print('Saved revenue_by_category.csv')
if not revenue_by_region.empty:
    revenue_by_region.to_csv(os.path.join('outputs', 'revenue_by_region.csv'), index=False)
    print('Saved revenue_by_region.csv')
if not revenue_by_payment.empty:
    revenue_by_payment.to_csv(os.path.join('outputs', 'revenue_by_payment_method.csv'), index=False)
    print('Saved revenue_by_payment_method.csv')
if not revenue_by_month.empty:
    revenue_by_month.to_csv(os.path.join('outputs', 'revenue_by_month.csv'), index=False)
    print('Saved revenue_by_month.csv')
if not top10_products.empty:
    top10_products.to_csv(os.path.join('outputs', 'top10_products.csv'), index=False)
    print('Saved top10_products.csv')
if not top5_regions.empty:
    top5_regions.to_csv(os.path.join('outputs', 'top5_regions.csv'), index=False)
    print('Saved top5_regions.csv')

section('Business summary (concise)')
# Determine highest revenue category/product/region (handle ties)
most_revenue_category = None
most_revenue_product = None
most_revenue_region = None

if not revenue_by_category.empty:
    max_cat_rev = revenue_by_category['Sales'].max()
    top_cats = revenue_by_category[revenue_by_category['Sales'] == max_cat_rev]['Category'].tolist()
    most_revenue_category = top_cats

if not revenue_by_product.empty:
    max_prod_rev = revenue_by_product['Sales'].max()
    top_prods = revenue_by_product[revenue_by_product['Sales'] == max_prod_rev]['Product'].tolist()
    most_revenue_product = top_prods

if not revenue_by_region.empty:
    max_reg_rev = revenue_by_region['Sales'].max()
    top_regs = revenue_by_region[revenue_by_region['Sales'] == max_reg_rev]['Region'].tolist()
    most_revenue_region = top_regs

print('Summary of top performers:')
if most_revenue_category:
    print(f" - Top category by revenue: {', '.join(most_revenue_category)} (Revenue = {max_cat_rev:,.2f})")
else:
    print(' - No category revenue data available')

if most_revenue_product:
    print(f" - Top product by revenue: {', '.join(most_revenue_product)} (Revenue = {max_prod_rev:,.2f})")
else:
    print(' - No product revenue data available')

if most_revenue_region:
    print(f" - Top region by revenue: {', '.join(most_revenue_region)} (Revenue = {max_reg_rev:,.2f})")
else:
    print(' - No region revenue data available')

print('\nEDA complete. Charts and CSVs are in the outputs/ directory. Review the saved charts and CSVs to continue to visualization or dashboard steps.')

# End of script
