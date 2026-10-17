"""
generate_dataset.py

Generates a realistic synthetic e-commerce sales dataset for learning and portfolio use.

What this file does (short):
- Uses Python's built-in `random` and `datetime` modules plus `pandas` to create 1,000 synthetic order records.
- Columns: Order_ID, Order_Date, Customer_ID, Product, Category, Quantity, Unit_Price, Discount, Payment_Method, Region, Sales
- Discount is represented as a decimal (e.g. 0.10 = 10% off).
- Sales is calculated as: Quantity * Unit_Price * (1 - Discount)
- Saves the result to data/ecommerce_sales.csv and runs basic validation.

Why this is useful:
- You need realistic-looking data to practice data cleaning, SQL, visualization and a Streamlit dashboard
- This dataset is labeled as synthetic and is NOT real company data. Use it for learning only.

How to run:
- From the project root (where this file lives), run:
    python generate_dataset.py

Expected output when run:
- The script will print progress, validation results, and the path to the saved CSV (data/ecommerce_sales.csv).

Notes for beginners:
- If you don't have pandas installed, install it into your project's virtual environment with:
    python -m pip install pandas

"""

import random
import pandas as pd
from datetime import datetime, timedelta

# Fixed random seed so the dataset is reproducible
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# Number of rows to generate
N_ROWS = 1000

# Define lists of realistic sample values (Indian context for Region)
PRODUCTS_CATEGORIES = {
    "Wireless Headphones": "Electronics",
    "Smart Watch": "Electronics",
    "Bluetooth Speaker": "Electronics",
    "Coffee Maker": "Home & Kitchen",
    "Desk Lamp": "Home & Kitchen",
    "Blender": "Home & Kitchen",
    "Running Shoes": "Clothing",
    "Cotton T-Shirt": "Clothing",
    "Backpack": "Clothing",
    "Yoga Mat": "Sports & Outdoors",
    "Water Bottle": "Sports & Outdoors",
    "Camping Lantern": "Sports & Outdoors",
    "Board Game": "Toys & Games",
    "Puzzle Set": "Toys & Games",
    "Building Set": "Toys & Games"
}

# Typical unit prices for products (INR-like values). Prices are illustrative and synthetic.
PRODUCT_PRICES = {
    "Wireless Headphones": 2999.0,
    "Smart Watch": 6999.0,
    "Bluetooth Speaker": 1999.0,
    "Coffee Maker": 5299.0,
    "Desk Lamp": 1199.0,
    "Blender": 3999.0,
    "Running Shoes": 3499.0,
    "Cotton T-Shirt": 899.0,
    "Backpack": 1499.0,
    "Yoga Mat": 1499.0,
    "Water Bottle": 499.0,
    "Camping Lantern": 1299.0,
    "Board Game": 1499.0,
    "Puzzle Set": 499.0,
    "Building Set": 3999.0
}

PAYMENT_METHODS = [
    "Credit Card",
    "Debit Card",
    "UPI",
    "Net Banking",
    "Cash on Delivery"
]

REGIONS = ["North", "South", "East", "West", "Central"]

# Discounts are represented as decimal fractions (e.g. 0.10 means 10% off)
POSSIBLE_DISCOUNTS = [0.0, 0.05, 0.10, 0.15, 0.20]
DISCOUNT_WEIGHTS = [0.6, 0.15, 0.15, 0.07, 0.03]  # most orders have no discount

# Date range for Order_Date (ISO format). Keep recent-ish dates so visualizations look realistic.
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2026, 9, 30)
TOTAL_DAYS = (END_DATE - START_DATE).days

# Helper to generate a random date in the range
def random_date():
    offset_days = random.randint(0, TOTAL_DAYS)
    d = START_DATE + timedelta(days=offset_days)
    # Keep date format as YYYY-MM-DD (ISO) which is easy to parse in analysis tools
    return d.date().isoformat()

# Build rows
rows = []
for i in range(1, N_ROWS + 1):
    order_id = f"ORD-{i:06d}"
    order_date = random_date()
    customer_id = f"CUS-{random.randint(1, 9999):04d}"

    product = random.choice(list(PRODUCTS_CATEGORIES.keys()))
    category = PRODUCTS_CATEGORIES[product]

    # Quantity between 1 and 5 (small online order sizes)
    quantity = random.choices([1, 2, 3, 4, 5], weights=[60, 20, 10, 6, 4])[0]

    # Use the base price but add a small random jitter to make prices look less uniform
    base_price = PRODUCT_PRICES[product]
    # jitter up to +/- 10% to simulate different models / sellers
    jitter = random.uniform(-0.10, 0.10)
    unit_price = round(base_price * (1 + jitter), 2)

    discount = random.choices(POSSIBLE_DISCOUNTS, weights=DISCOUNT_WEIGHTS)[0]

    payment_method = random.choice(PAYMENT_METHODS)
    region = random.choice(REGIONS)

    # Sales calculation (final amount paid): Quantity * Unit_Price * (1 - Discount)
    sales = round(quantity * unit_price * (1 - discount), 2)

    rows.append({
        "Order_ID": order_id,
        "Order_Date": order_date,
        "Customer_ID": customer_id,
        "Product": product,
        "Category": category,
        "Quantity": quantity,
        "Unit_Price": unit_price,
        "Discount": discount,
        "Payment_Method": payment_method,
        "Region": region,
        "Sales": sales
    })

# Create DataFrame
df = pd.DataFrame(rows)

# Basic validation checks
expected_columns = ["Order_ID", "Order_Date", "Customer_ID", "Product", "Category",
                    "Quantity", "Unit_Price", "Discount", "Payment_Method", "Region", "Sales"]

validation_passed = True
messages = []

# 1) Row count
if df.shape[0] != N_ROWS:
    validation_passed = False
    messages.append(f"Row count mismatch: expected {N_ROWS} rows but got {df.shape[0]}")
else:
    messages.append(f"Row count OK: {df.shape[0]} rows")

# 2) Columns
missing_cols = [c for c in expected_columns if c not in df.columns]
if missing_cols:
    validation_passed = False
    messages.append(f"Missing expected columns: {missing_cols}")
else:
    messages.append("All expected columns present")

# 3) Duplicate Order_ID
dupe_count = df["Order_ID"].duplicated().sum()
if dupe_count > 0:
    validation_passed = False
    messages.append(f"Duplicate Order_ID values found: {dupe_count} duplicates")
else:
    messages.append("No duplicate Order_ID values")

# Save to CSV (create data/ directory if needed)
output_path = "data/ecommerce_sales.csv"

try:
    df.to_csv(output_path, index=False)
    messages.append(f"Saved synthetic dataset to {output_path}")
except Exception as e:
    validation_passed = False
    messages.append(f"Failed to save CSV: {e}")

# Final report for the user (beginner-friendly)
print("\nSYNTHETIC E-COMMERCE SALES DATASET GENERATOR — REPORT")
print("This dataset is synthetic and intended for learning and portfolio use only.")
print("Do not present it as real company data.")
print("Random seed used:", RANDOM_SEED)
print("\nValidation results:")
for m in messages:
    print(" -", m)

if validation_passed:
    print("\nAll validations passed. You're ready to use data/ecommerce_sales.csv for analysis.")
else:
    print("\nOne or more validations failed. See messages above and fix the issues before proceeding.")

# End of script
