# E-Commerce Sales Analytics Dashboard

A beginner-friendly portfolio project for exploring synthetic e-commerce sales data with Python, SQL, and an interactive Streamlit dashboard.

> **Project status:** Dataset generation, cleaning, exploratory analysis, MySQL analysis queries, and the local Streamlit dashboard are implemented.

## Objectives

- Prepare and validate a reproducible synthetic e-commerce dataset.
- Calculate sales and profit measures with documented business rules.
- Explore sales trends and business performance using Python and SQL.
- Present the results in an interactive dashboard.

## Technologies

- Python, Pandas, and NumPy for data preparation and analysis
- Plotly for interactive charts
- Streamlit for the interactive dashboard
- MySQL-compatible SQL for future database analysis

## Project structure

```text
.
├── datasets/       # Synthetic raw and cleaned CSV data
├── docs/           # Data and cleaning decision notes
├── outputs/        # Cleaning/EDA JSON results and interactive HTML charts
├── scripts/        # Python data generation and analysis scripts
├── sql/            # MySQL 8+ analysis queries
├── app.py          # Interactive Streamlit dashboard
├── .gitignore
├── requirements.txt
└── README.md
```

## Installation

Use Python 3.10 or newer. From this project folder, create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Generate and analyze the sample data

```powershell
python scripts/generate_dataset.py
python scripts/analyze_sales.py
```

The generator uses a fixed random seed and saves 800 fictional order rows to `datasets/ecommerce_sales.csv`. The analysis reads this raw CSV without changing it, cleans a copy into `datasets/ecommerce_sales_cleaned.csv`, writes its row/value counts to `outputs/cleaning_report.json`, and calculates EDA results in `outputs/eda_summary.json`. It also saves eight interactive Plotly charts as HTML files in `outputs/`; open those files in a web browser.

See [dataset notes](docs/dataset_notes.md) and [cleaning and EDA notes](docs/cleaning_and_eda_notes.md) for the business rules and cleaning decisions.

## SQL analysis (MySQL 8+)

The SQL file creates the `ecommerce_analytics` database and an `ecommerce_sales` table, then provides commented queries for sales/profit KPIs, customers, monthly trends and growth, product/category/region/segment performance, payment/status breakdowns, average order value, and product ranking within categories. To run it, first generate the cleaned CSV with `python scripts/analyze_sales.py`, create the schema/table in MySQL, import `datasets/ecommerce_sales_cleaned.csv` using Workbench's Table Data Import Wizard, then execute the query blocks in `sql/ecommerce_analysis.sql`.

See [the beginner MySQL guide](docs/mysql_sql_guide.md) for setup, import, execution, assumptions, and troubleshooting. Queries treat order status as descriptive and include all rows' financial amounts. Average order value uses total revenue divided by distinct orders, which fits this sample's one-row-per-order structure.

## Launch the dashboard in VS Code on Windows

1. Open this project folder in VS Code (**File → Open Folder**).
2. Open a terminal in VS Code (**Terminal → New Terminal**) and make sure its current directory is the project root (the folder containing `app.py`).
3. If you have not installed the project packages, run:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install --upgrade pip
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

   These commands use the virtual environment directly, so activation is optional.
4. If the cleaned file is missing, create it first with `python scripts/analyze_sales.py`.
5. Start Streamlit:

   ```powershell
   .\.venv\Scripts\python.exe -m streamlit run app.py
   ```

   If you installed packages into your regular Python rather than `.venv`, use `python -m streamlit run app.py`. Streamlit prints a local URL (usually `http://localhost:8501`); open it in your browser. Press **Ctrl+C** in the terminal to stop the local app.

The sidebar filters by inclusive order date range, region, category, customer segment, and order status. KPI cards, all charts, the data table, and CSV download use the selected rows. To check the filters, change one filter at a time and confirm the row count, KPI values, charts, and downloaded CSV update; then select a narrow date/region combination with no matching rows to see the empty-result message. Use **Reset** in Streamlit's menu to restore the initial view.

Average order value is filtered revenue divided by distinct filtered `Order_ID`s (one row per order in this sample). Profit margin is filtered profit divided by filtered revenue; it displays zero when revenue is zero. No deployment is configured; this app is intended to run locally.

The sample dataset does not specify a currency, so the dashboard displays amounts in dataset units without adding a currency symbol.

## Current sample findings

These values are calculated by the analysis script from the current synthetic dataset, not hardcoded into the analysis:

- Revenue: 74,839.62; cost: 42,593.66; profit: 32,245.96.
- 800 unique orders and 275 unique customers; average order value: 93.55; profit margin: 43.09%.
- Electronics is the highest-revenue category (26,795.16); Smart Watch is the highest-revenue product (12,661.35).
- August has the highest monthly revenue (11,387.61), and North has the highest regional revenue (17,528.63).

These are sample-data results only and do not describe a real business. Cancelled/returned rows retain their generated financial values as documented in the data rules.

## Features

Implemented: reproducible synthetic data, documented cleaning, calculated EDA summaries, interactive chart files, MySQL 8+ queries, and a local Streamlit dashboard with filters and CSV export.

## Data and limitations

The project uses generated sample data only. It contains no real company, customer, or transaction information. The sample is for demonstrating analysis workflows and should not be interpreted as evidence about an actual business. Average order value currently treats each unique order ID as one row/order.

## Portfolio description

Built a reproducible e-commerce sales analytics project using Python, Pandas, NumPy, Plotly, Streamlit, and MySQL 8+. Generated and validated 800 synthetic order records, documented data-quality rules, calculated sales and profitability KPIs, created interactive exploratory charts, wrote SQL analysis queries using CTEs and window functions, and built a local dashboard with dynamic filters and CSV export.
