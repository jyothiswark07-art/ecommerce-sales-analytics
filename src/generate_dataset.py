"""
src/generate_dataset.py

Generate a reproducible synthetic e-commerce sales dataset and save to data/ecommerce_sales.csv.

What this script does (short):
- Creates 1,000 synthetic order records with these columns:
  Order_ID, Order_Date, Product, Category, Quantity, Unit_Price, Region, Sales
- Sales is calculated as: Quantity * Unit_Price (no discounts in this simple dataset)
- Uses a fixed random seed so results are reproducible
- Writes the CSV using a relative path (data/ecommerce_sales.csv) so the script works when run from the project root

How to run (in VS Code terminal, from the project root):
    python src/generate_dataset.py

If your system's Python command is "python3", use:
    python3 src/generate_dataset.py

Do not run this script from another working directory unless you update the output path.

Notes for beginners:
- If pandas is not installed in your environment, install it first with:
    python -m pip install pandas

"""

from pathlib import Path
import random
from datetime import datetime, timedelta
import pandas as pd

# ---------------- Configuration ----------------
RANDOM_SEED = 2026
N_ROWS = 1000
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"  # project_root/data
OUTPUT_FILE = OUTPUT_DIR / "ecommerce_sales.csv"

# Product catalog (product: category)
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

# Typical base prices for products (sample values)
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

REGIONS = ["North", "South", "East", "West", "Central"]

# Date range for orders
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2026, 9, 30)
TOTAL_DAYS = (END_DATE - START_DATE).days

# ---------------- Helpers ----------------

def random_date():
    """Return a random date string in YYYY-MM-DD within the configured range."""
    offset = random.randint(0, TOTAL_DAYS)
    return (START_DATE + timedelta(days=offset)).date().isoformat()


# ---------------- Generate rows ----------------

def generate_rows(n, seed=RANDOM_SEED):
    """Generate n synthetic rows; returns a list of dicts."""
    random.seed(seed)

    rows = []
    product_names = list(PRODUCTS_CATEGORIES.keys())
    for i in range(1, n + 1):
        order_id = f"ORD-{i:06d}"
        order_date = random_date()
        product = random.choice(product_names)
        category = PRODUCTS_CATEGORIES[product]
        # Quantity between 1 and 5
        quantity = random.choices([1, 2, 3, 4, 5], weights=[60, 20, 10, 6, 4])[0]
        # Unit price uses base price with small jitter +/- 10%
        base_price = PRODUCT_PRICES.get(product, 100.0)
        jitter = random.uniform(-0.10, 0.10)
        unit_price = round(base_price * (1 + jitter), 2)
        region = random.choice(REGIONS)
        sales = round(quantity * unit_price, 2)

        rows.append({
            "Order_ID": order_id,
            "Order_Date": order_date,
            "Product": product,
            "Category": category,
            "Quantity": quantity,
            "Unit_Price": unit_price,
            "Region": region,
            "Sales": sales
        })
    return rows


# ---------------- Save CSV ----------------

def save_to_csv(rows, path=OUTPUT_FILE):
    """Save rows (list of dicts) to CSV at path (Path). Creates parent dir if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    # Ensure column order is stable
    cols = ["Order_ID", "Order_Date", "Product", "Category", "Quantity", "Unit_Price", "Region", "Sales"]
    df = df[cols]
    df.to_csv(path, index=False)
    return df


# ---------------- Basic validation ----------------

def validate_df(df, expected_n=N_ROWS):
    """Run simple checks and return (ok, messages)."""
    messages = []
    ok = True
    if df.shape[0] != expected_n:
        ok = False
        messages.append(f"Row count mismatch: expected {expected_n} rows, got {df.shape[0]}")
    required_cols = ["Order_ID", "Order_Date", "Product", "Category", "Quantity", "Unit_Price", "Region", "Sales"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        ok = False
        messages.append(f"Missing columns: {missing}")
    dup_count = df["Order_ID"].duplicated().sum()
    if dup_count > 0:
        ok = False
        messages.append(f"Duplicate Order_ID values found: {dup_count}")
    # Check Sales formula for a few samples
    sample = df.sample(min(5, len(df)), random_state=1)
    for _, row in sample.iterrows():
        expected = round(row["Quantity"] * row["Unit_Price"], 2)
        if abs(row["Sales"] - expected) > 0.01:
            ok = False
            messages.append(f"Sales mismatch for Order_ID {row['Order_ID']}: {row['Sales']} vs expected {expected}")
    return ok, messages


# ---------------- Main ----------------

if __name__ == "__main__":
    rows = generate_rows(N_ROWS)
    df = save_to_csv(rows)
    print(f"Saved {len(df)} rows to {OUTPUT_FILE}")

    ok, msgs = validate_df(df)
    if ok:
        print("Basic validation passed: row count, columns, and Order_ID uniqueness look good.")
    else:
        print("Validation issues found:")
        for m in msgs:
            print(" -", m)
