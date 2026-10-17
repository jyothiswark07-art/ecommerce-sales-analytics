# Cleaning and EDA decisions

Run `python scripts/analyze_sales.py` from the project root. The script reads `datasets/ecommerce_sales.csv` and writes a separate `datasets/ecommerce_sales_cleaned.csv`; it never writes to the raw CSV.

## Cleaning rules

- Check all 15 required columns. Stop with a clear error if a column is absent.
- Remove exact duplicate rows, then remove repeated `Order_ID` rows while retaining the first occurrence. This project's data model has one product/order line per order ID.
- Trim text fields and remove records with blank required fields.
- Parse dates strictly; remove rows with dates that cannot be parsed.
- Convert numeric fields to numbers. Remove rows with non-numeric/non-finite inputs, quantity that is zero, negative, or not a whole number, non-positive unit price, discount below 0 or at least 1, or negative cost.
- Recalculate `Revenue = Quantity × Unit_Price × (1 − Discount)` rounded to cents. Correct mismatching revenue rather than discarding otherwise usable rows.
- Retain non-negative `Cost` from the source because the per-unit cost rate is not included in the CSV. Recalculate `Profit = Revenue − Cost` rounded to cents.
- Keep order status as descriptive. Revenue/cost/profit are not adjusted for cancelled or returned statuses, matching the synthetic data notes.

`outputs/cleaning_report.json` records checked, removed, and corrected rows/values, source data types, and source missing/duplicate counts. `outputs/eda_summary.json` stores calculated KPIs and grouped results. Eight standalone interactive Plotly HTML charts are written to `outputs/`.

## EDA definitions

- Unique orders: distinct `Order_ID` values.
- Average order value: total revenue divided by unique orders. In this sample each row is one order.
- Profit margin: total profit divided by total revenue, multiplied by 100.
- Monthly/category/product/region/segment results sum revenue and profit. Payment and status breakdowns count unique orders and also show revenue.
