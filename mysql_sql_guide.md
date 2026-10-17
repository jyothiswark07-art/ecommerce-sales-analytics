# MySQL and SQL query guide

This guide uses MySQL 8.0 or newer because the analysis file uses common table expressions (CTEs) and window functions such as `RANK()`, `LAG()`, and `SUM() OVER()`.

## 1. Install or access MySQL

You need a running MySQL 8+ server and a SQL client. For a beginner, the easiest option is to install **MySQL Community Server** together with **MySQL Workbench** from the official MySQL downloads. If MySQL is already provided by a school, employer, or cloud database, use those connection details instead. Keep the server running and note its host, port (usually 3306), username, and password. The project does not include or store credentials.

## 2. Create the database and table

Open MySQL Workbench and connect to your MySQL server. Open `sql/ecommerce_analysis.sql` from this project and execute the first `CREATE DATABASE`, `USE`, and `CREATE TABLE` statements. They create the `ecommerce_analytics` database and a table whose column names and types match the cleaned CSV.

Alternatively, in a terminal opened at the project folder, connect with the MySQL command-line client (it will prompt for the password):

```powershell
mysql -h localhost -P 3306 -u your_mysql_user -p
```

Then run the database/table setup statements from the SQL file in the client. Replace `your_mysql_user` with your MySQL username; do not put your password in a command or save it in the project.

## 3. Import the cleaned CSV with MySQL Workbench

Use the **cleaned** file, not the raw one: `datasets/ecommerce_sales_cleaned.csv`.

1. In Workbench, select the `ecommerce_analytics` schema.
2. In the Navigator, right-click the schema and choose **Table Data Import Wizard**.
3. Select `datasets/ecommerce_sales_cleaned.csv` and continue.
4. Choose the existing `ecommerce_sales` table (do not create a second table), verify that the first row is treated as column headers, and map each column to the matching table column.
5. Start the import and confirm that rows were imported.

The import wizard is the recommended beginner method and avoids MySQL server file-permission settings. If an import error says the table already has rows, clear the table before retrying only if you intend to replace its contents:

```sql
TRUNCATE TABLE ecommerce_analytics.ecommerce_sales;
```

## 4. Run the analysis queries

Open `sql/ecommerce_analysis.sql` in Workbench. After importing the CSV, execute the `SELECT` query blocks individually (select a block and click the lightning-bolt execute button). Each query has a comment explaining its business question. The setup statements near the beginning can be run once; the analysis queries can be rerun whenever the table data changes.

The file contains queries for overall financial KPIs, order and customer counts, monthly trends, category/product/customer/region/segment summaries, payment and status distributions, average order value, within-category product rankings, and month-over-month revenue growth.

## 5. Understand the assumptions

- Each row in this sample is one order line and every `Order_ID` is unique. Therefore, average order value is defined as `SUM(Revenue) / COUNT(DISTINCT Order_ID)`. For a future dataset with multiple item rows per order, first total revenue per order and then average those order totals; do not use this query unchanged.
- `Order_Status` is descriptive. The supplied financial values are retained for Cancelled and Returned rows, so the totals include them. Filter statuses only if your accounting rules require it and clearly state that choice.
- `Discount` is a fraction (for example, `0.10` means 10%). Revenue is already calculated after discount in the dataset.
- Margin and percentage formulas use `NULLIF(..., 0)` so a zero denominator returns `NULL` instead of causing a division-by-zero error.
- The dataset is fictional sample data; results are not evidence about a real business.

## Troubleshooting

- **Unknown database/table:** run the setup statements first and confirm that Workbench is using `ecommerce_analytics`.
- **Unknown column:** keep the table column names as shown in the CSV header and SQL `CREATE TABLE` statement. The names use underscores and exact capitalization as supplied.
- **Cannot connect:** confirm MySQL Server is installed/running, host and port are correct, and your account can connect.
- **Import date/type errors:** run `python scripts/analyze_sales.py` first and import `datasets/ecommerce_sales_cleaned.csv`, which stores dates as `YYYY-MM-DD` and validated numeric fields.
- **Duplicate primary key:** the table is designed for one row per unique `Order_ID`; clear existing imported rows before a full replacement import, if appropriate.
