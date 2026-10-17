"""
src/clean_data.py

Data quality checks and cleaning for the synthetic e-commerce dataset.

What this script does:
- Loads the raw CSV (prefers data/ecommerce_sales.csv; falls back to ecommerce_sales.csv in repo root if needed).
- Prints dataset shape, column names, dtypes, missing values, duplicate rows, and duplicate Order_ID issues.
- Validates Order_Date, Quantity, Unit_Price, Discount, and Sales consistency (Sales = Quantity * Unit_Price * (1 - Discount)).
- Converts Order_Date to datetime and numeric columns to appropriate types.
- Removes exact duplicate rows (justified) and, if there are duplicated Order_IDs, keeps the first occurrence and drops the rest (with explanation).
- Saves the cleaned dataset to data/ecommerce_sales_cleaned.csv (never overwrites the original raw file).

Run from project root:
    python src/clean_data.py

Expected output:
- A readable printed report showing the initial checks, any problems found, actions taken, and final validation showing the cleaned dataset saved to data/ecommerce_sales_cleaned.csv.

Common errors and fixes:
- FileNotFoundError: if neither data/ecommerce_sales.csv nor ecommerce_sales.csv exists. Fix: run the data generator (python generate_dataset.py) or put the CSV in data/.
- If pandas is not installed: install it in your venv: python -m pip install pandas

"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

# Helper to print section headers for readability
def section(title):
    print('\n' + '='*len(title))
    print(title)
    print('='*len(title) + '\n')

# Paths we will check. Prefer data/ecommerce_sales.csv
RAW_PATHS = [
    os.path.join('data', 'ecommerce_sales.csv'),
    'ecommerce_sales.csv'
]

def find_raw_file():
    for p in RAW_PATHS:
        if os.path.exists(p):
            return p
    return None

raw_file = find_raw_file()
if raw_file is None:
    print('ERROR: Could not find the raw dataset. Looked for:')
    for p in RAW_PATHS:
        print(' -', p)
    print('\nFix: run the dataset generator or place the CSV at data/ecommerce_sales.csv')
    sys.exit(1)

section('Loading raw dataset')
print('Raw file found at:', raw_file)

# Read CSV with pandas. We avoid parsing dates here so we can validate them explicitly.
try:
    df_raw = pd.read_csv(raw_file)
except Exception as e:
    print('Failed to read CSV:', e)
    sys.exit(1)

# Show initial quick info
section('Initial dataset info')
print('Number of rows, columns:', df_raw.shape)
print('\nColumn names:')
print(list(df_raw.columns))

print('\nData types as read by pandas:')
print(df_raw.dtypes)

# Missing values per column
print('\nMissing values per column:')
print(df_raw.isna().sum())

# Duplicate full rows
dup_full_count = df_raw.duplicated().sum()
print('\nExact duplicate rows (all columns match):', dup_full_count)

# Duplicate Order_IDs
if 'Order_ID' in df_raw.columns:
    dup_order_id_count = df_raw['Order_ID'].duplicated().sum()
    print('Duplicate Order_ID count:', dup_order_id_count)
else:
    print('WARNING: Order_ID column not found in raw data')
    dup_order_id_count = 0

# Show sample rows to inspect (first 5)
print('\nFirst 5 rows:')
print(df_raw.head().to_string(index=False))

section('Field-by-field validation')

problems = []

# 1) Validate Order_Date parseability
if 'Order_Date' in df_raw.columns:
    # Attempt to parse; keep failures for reporting
    parsed_dates = pd.to_datetime(df_raw['Order_Date'], errors='coerce', format='%Y-%m-%d')
    invalid_dates = parsed_dates.isna().sum()
    print('Order_Date parseable rows (YYYY-MM-DD expected). Invalid/missing dates:', invalid_dates)
    if invalid_dates > 0:
        problems.append(f'Order_Date has {invalid_dates} invalid or missing values')
else:
    problems.append('Order_Date column missing')

# 2) Quantity should be positive integer
if 'Quantity' in df_raw.columns:
    # Coerce to numeric and check
    q_numeric = pd.to_numeric(df_raw['Quantity'], errors='coerce')
    non_numeric_q = q_numeric.isna().sum()
    non_positive_q = (q_numeric <= 0).sum()
    print(f"Quantity non-numeric: {non_numeric_q}, Quantity non-positive: {non_positive_q}")
    if non_numeric_q > 0:
        problems.append(f'Quantity has {non_numeric_q} non-numeric values')
    if non_positive_q > 0:
        problems.append(f'Quantity has {non_positive_q} non-positive values')
else:
    problems.append('Quantity column missing')

# 3) Unit_Price should be non-negative
if 'Unit_Price' in df_raw.columns:
    up_numeric = pd.to_numeric(df_raw['Unit_Price'], errors='coerce')
    non_numeric_up = up_numeric.isna().sum()
    negative_up = (up_numeric < 0).sum()
    print(f"Unit_Price non-numeric: {non_numeric_up}, negative Unit_Price: {negative_up}")
    if non_numeric_up > 0:
        problems.append(f'Unit_Price has {non_numeric_up} non-numeric values')
    if negative_up > 0:
        problems.append(f'Unit_Price has {negative_up} negative values')
else:
    problems.append('Unit_Price column missing')

# 4) Discount should be within expected documented range (0.0 to 0.2 in our generator)
DISCOUNT_MIN = 0.0
DISCOUNT_MAX = 0.2
if 'Discount' in df_raw.columns:
    disc_numeric = pd.to_numeric(df_raw['Discount'], errors='coerce')
    non_numeric_disc = disc_numeric.isna().sum()
    out_of_range_disc = ((disc_numeric < DISCOUNT_MIN) | (disc_numeric > DISCOUNT_MAX)).sum()
    print(f"Discount non-numeric: {non_numeric_disc}, out-of-range Discount (<{DISCOUNT_MIN} or >{DISCOUNT_MAX}): {out_of_range_disc}")
    if non_numeric_disc > 0:
        problems.append(f'Discount has {non_numeric_disc} non-numeric values')
    if out_of_range_disc > 0:
        problems.append(f'Discount has {out_of_range_disc} values outside [{DISCOUNT_MIN}, {DISCOUNT_MAX}]')
else:
    problems.append('Discount column missing')

# 5) Sales consistency check: Sales ≈ Quantity * Unit_Price * (1 - Discount)
if all(col in df_raw.columns for col in ['Quantity', 'Unit_Price', 'Discount', 'Sales']):
    # Coerce numeric
    q = pd.to_numeric(df_raw['Quantity'], errors='coerce')
    up = pd.to_numeric(df_raw['Unit_Price'], errors='coerce')
    disc = pd.to_numeric(df_raw['Discount'], errors='coerce')
    sales = pd.to_numeric(df_raw['Sales'], errors='coerce')

    # Compute expected sales
    expected_sales = q * up * (1 - disc)
    # Allow small rounding tolerance (e.g., 0.01)
    tolerance = 0.02  # INR cents tolerance; increase if prices are large or rounding differences exist
    sales_mismatch = (~np.isclose(sales.fillna(-999999), expected_sales.fillna(-999999), atol=tolerance)).sum()
    nan_sales = sales.isna().sum()
    print(f"Sales missing: {nan_sales}. Sales mismatching expected calculation (tolerance {tolerance}): {sales_mismatch}")
    if nan_sales > 0:
        problems.append(f'Sales has {nan_sales} missing/non-numeric values')
    if sales_mismatch > 0:
        problems.append(f'Sales mismatches found for {sales_mismatch} rows (outside tolerance)')
else:
    problems.append('One or more columns required for Sales validation (Quantity, Unit_Price, Discount, Sales) are missing')

section('Problems summary')
if problems:
    print('Problems detected:')
    for p in problems:
        print(' -', p)
else:
    print('No problems detected in the checks above. The raw dataset appears consistent with expectations.')

# Prepare cleaning step: convert types and address issues found. We will NOT silently drop rows without explaining.
section('Cleaning actions (with justification)')

df = df_raw.copy()

# 1) Convert Order_Date to datetime (coerce invalids to NaT) and report
if 'Order_Date' in df.columns:
    df['Order_Date'] = pd.to_datetime(df['Order_Date'], errors='coerce', format='%Y-%m-%d')
    invalid_dates_after = df['Order_Date'].isna().sum()
    if invalid_dates_after > 0:
        print(f'Action: {invalid_dates_after} Order_Date values could not be parsed and are set to NaT')
        print('Justification: We keep rows but mark invalid dates as missing so you can decide how to handle them later')

# 2) Ensure numeric types for Quantity, Unit_Price, Discount, Sales
numeric_cols = ['Quantity', 'Unit_Price', 'Discount', 'Sales']
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# 3) Handle Quantity non-positive or missing: report and keep rows (business decision left to you). We WILL NOT silently delete.
if 'Quantity' in df.columns:
    qty_nonpos = (df['Quantity'].isna()) | (df['Quantity'] <= 0)
    count_qty_nonpos = int(qty_nonpos.sum())
    if count_qty_nonpos > 0:
        print(f'Action: Found {count_qty_nonpos} rows where Quantity is missing or non-positive. These rows are kept for now but flagged in a new column quantity_issue')
        df['quantity_issue'] = qty_nonpos

# 4) Handle Unit_Price missing/negative: report and flag
if 'Unit_Price' in df.columns:
    up_invalid = (df['Unit_Price'].isna()) | (df['Unit_Price'] < 0)
    count_up_invalid = int(up_invalid.sum())
    if count_up_invalid > 0:
        print(f'Action: Found {count_up_invalid} rows where Unit_Price is missing or negative. These rows are kept but flagged in unit_price_issue')
        df['unit_price_issue'] = up_invalid

# 5) Handle Discount out of expected range: flag
if 'Discount' in df.columns:
    disc_invalid = (df['Discount'].isna()) | (df['Discount'] < DISCOUNT_MIN) | (df['Discount'] > DISCOUNT_MAX)
    count_disc_invalid = int(disc_invalid.sum())
    if count_disc_invalid > 0:
        print(f'Action: Found {count_disc_invalid} rows where Discount is missing or outside [{DISCOUNT_MIN}, {DISCOUNT_MAX}]. Flagging in discount_issue')
        df['discount_issue'] = disc_invalid

# 6) Sales mismatch: flag rows where Sales doesn't match expected calculation within tolerance
if all(col in df.columns for col in ['Quantity', 'Unit_Price', 'Discount', 'Sales']):
    expected_sales = df['Quantity'] * df['Unit_Price'] * (1 - df['Discount'])
    sales_mismatch_mask = ~np.isclose(df['Sales'].fillna(-999999), expected_sales.fillna(-999999), atol=tolerance)
    count_sales_mismatch = int(sales_mismatch_mask.sum())
    if count_sales_mismatch > 0:
        print(f'Action: Found {count_sales_mismatch} rows with Sales mismatch (flagging in sales_mismatch)')
        df['sales_mismatch'] = sales_mismatch_mask

# 7) Remove exact duplicate rows (all columns identical). Justification: exact duplicates are identical records and likely created by mistake
exact_dup_mask = df.duplicated()
exact_dup_count = int(exact_dup_mask.sum())
if exact_dup_count > 0:
    print(f"Action: Removing {exact_dup_count} exact duplicate rows (identical in all columns). Justification: exact duplicates provide no new information and are likely accidental duplicates.)")
    df = df[~exact_dup_mask].reset_index(drop=True)
else:
    print('No exact duplicate rows to remove')

# 8) Handle duplicate Order_IDs: if multiple rows share same Order_ID (but differ in other fields) we keep the first occurrence and drop others, but we log how many were dropped and why
if 'Order_ID' in df.columns:
    dup_order_id_mask = df['Order_ID'].duplicated(keep='first')
    dup_order_id_count_after = int(dup_order_id_mask.sum())
    if dup_order_id_count_after > 0:
        print(f"Action: Found {dup_order_id_count_after} rows with duplicated Order_ID values. We will keep the first occurrence for each Order_ID and drop the later ones.")
        # Save a copy of dropped rows for audit
        dropped_by_order_id = df[dup_order_id_mask].copy()
        df = df[~dup_order_id_mask].reset_index(drop=True)
        # Optionally, save dropped rows for inspection
        audit_path = os.path.join('data', 'dropped_duplicate_order_ids.csv')
        os.makedirs('data', exist_ok=True)
        try:
            dropped_by_order_id.to_csv(audit_path, index=False)
            print(f'Action: Saved the dropped duplicate-order-id rows to {audit_path} so you can inspect what was removed')
        except Exception as e:
            print('Warning: Failed to save audit file for dropped duplicate Order_IDs:', e)
    else:
        print('No duplicated Order_IDs found (good)')

# Final conversions: ensure Quantity is integer where possible
if 'Quantity' in df.columns:
    # Some Quantity entries may be NaN or non-integer; keep as integer where possible
    df['Quantity'] = df['Quantity'].round().astype('Int64')  # pandas nullable integer

# Ensure Sales is float with two decimal places
if 'Sales' in df.columns:
    df['Sales'] = df['Sales'].round(2)

# Save cleaned dataset (do not overwrite raw)
cleaned_path = os.path.join('data', 'ecommerce_sales_cleaned.csv')
os.makedirs('data', exist_ok=True)
try:
    df.to_csv(cleaned_path, index=False)
    print(f'Cleaned dataset saved to {cleaned_path}')
except Exception as e:
    print('Failed to save cleaned dataset:', e)
    sys.exit(1)

# Final validation on cleaned data
section('Final validation on cleaned dataset')
print('Cleaned dataset shape:', df.shape)
print('Columns and dtypes:')
print(df.dtypes)
print('\nAny remaining missing values per column:')
print(df.isna().sum())

# Confirm Order_ID uniqueness
if 'Order_ID' in df.columns:
    remaining_dup_order_id = int(df['Order_ID'].duplicated().sum())
    print('\nRemaining duplicate Order_ID count (should be 0):', remaining_dup_order_id)

# Confirm number of rows did not exceed original (sanity)
print('\nOriginal rows:', df_raw.shape[0], 'Cleaned rows:', df.shape[0])

section('Summary (before and after)')
print('Before: rows=', df_raw.shape[0], 'columns=', df_raw.shape[1])
print('After:  rows=', df.shape[0], 'columns=', df.shape[1])

print('\nCleaning complete. The cleaned file is in data/ecommerce_sales_cleaned.csv. Review the flagged issue columns (quantity_issue, unit_price_issue, discount_issue, sales_mismatch) if present to decide on further action.')

# End of script
