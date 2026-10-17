-- sql/ecommerce_analysis.sql
-- SQL analysis queries for the E-Commerce Sales Analytics project
-- MySQL 8+ compatible
--
-- Table expected: ecommerce_sales
-- Columns expected (exact names):
--   Order_ID VARCHAR, Order_Date DATE, Customer_ID VARCHAR, Product VARCHAR,
--   Category VARCHAR, Quantity INT, Unit_Price DECIMAL(10,2), Discount DECIMAL(4,2),
--   Payment_Method VARCHAR, Region VARCHAR, Sales DECIMAL(12,2)
--
-- IMPORTANT: this file contains SELECT queries and explanatory comments only.
-- Run these queries in your MySQL client against the database/table where you loaded
-- the cleaned CSV (see sql/README.md for import instructions).

-- =====================
-- 1) Total revenue and total orders
-- Use SUM(Sales) for revenue and COUNT(DISTINCT Order_ID) for number of unique orders
-- Avoids double-counting if the dataset contains one row per order-line
-- =====================

SELECT
  SUM(Sales) AS total_revenue,
  COUNT(DISTINCT Order_ID) AS total_orders
FROM ecommerce_sales;

-- =====================
-- 2) Total units sold and average order value (AOV)
-- Total units: SUM(Quantity)
-- AOV: compute order-level revenue first (SUM(Sales) per Order_ID) then average
-- =====================

-- Total units sold
SELECT SUM(Quantity) AS total_units_sold FROM ecommerce_sales;

-- Average order value (AOV) - order-level aggregation to avoid double-counting
WITH order_revenue AS (
  SELECT Order_ID, SUM(Sales) AS order_total
  FROM ecommerce_sales
  GROUP BY Order_ID
)
SELECT
  AVG(order_total) AS average_order_value
FROM order_revenue;

-- =====================
-- 3) Revenue by product category
-- =====================

SELECT
  Category,
  SUM(Sales) AS revenue
FROM ecommerce_sales
GROUP BY Category
ORDER BY revenue DESC;

-- =====================
-- 4) Top 10 products by revenue
-- =====================

SELECT
  Product,
  SUM(Sales) AS revenue
FROM ecommerce_sales
GROUP BY Product
ORDER BY revenue DESC
LIMIT 10;

-- =====================
-- 5) Top 5 regions by revenue
-- =====================

SELECT
  Region,
  SUM(Sales) AS revenue
FROM ecommerce_sales
GROUP BY Region
ORDER BY revenue DESC
LIMIT 5;

-- =====================
-- 6) Monthly revenue trends
-- Use DATE_FORMAT(Order_Date, '%Y-%m') to group by month (string) or create first-of-month using
-- DATE_FORMAT and STR_TO_DATE if you need date type. We order by the month key to show trend.
-- =====================

SELECT
  DATE_FORMAT(Order_Date, '%Y-%m') AS year_month,
  SUM(Sales) AS revenue
FROM ecommerce_sales
WHERE Order_Date IS NOT NULL
GROUP BY year_month
ORDER BY year_month;

-- =====================
-- 7) Revenue by payment method
-- =====================

SELECT
  Payment_Method,
  SUM(Sales) AS revenue
FROM ecommerce_sales
GROUP BY Payment_Method
ORDER BY revenue DESC;

-- =====================
-- 8) Unique customers and customer order counts
-- =====================

-- Unique customers
SELECT COUNT(DISTINCT Customer_ID) AS unique_customers FROM ecommerce_sales;

-- Customer order counts and revenue (top customers)
SELECT
  Customer_ID,
  COUNT(DISTINCT Order_ID) AS orders_count,
  SUM(Sales) AS revenue
FROM ecommerce_sales
GROUP BY Customer_ID
ORDER BY orders_count DESC, revenue DESC
LIMIT 20;

-- =====================
-- 9) Repeat customers (customers with more than one order)
-- =====================

SELECT
  Customer_ID,
  COUNT(DISTINCT Order_ID) AS orders_count
FROM ecommerce_sales
GROUP BY Customer_ID
HAVING orders_count > 1
ORDER BY orders_count DESC;

-- =====================
-- 10) Orders above average order value
-- Compute average order value using order-level totals and list orders above average
-- =====================

WITH order_totals AS (
  SELECT Order_ID, SUM(Sales) AS order_total
  FROM ecommerce_sales
  GROUP BY Order_ID
),
avg_order AS (
  SELECT AVG(order_total) AS avg_aov FROM order_totals
)
SELECT ot.Order_ID, ot.order_total
FROM order_totals ot
CROSS JOIN avg_order ao
WHERE ot.order_total > ao.avg_aov
ORDER BY ot.order_total DESC;

-- =====================
-- 11) Revenue contribution percentage by category
-- =====================

SELECT
  Category,
  SUM(Sales) AS revenue,
  ROUND(SUM(Sales) / (SELECT SUM(Sales) FROM ecommerce_sales) * 100, 2) AS pct_of_total
FROM ecommerce_sales
GROUP BY Category
ORDER BY revenue DESC;

-- =====================
-- 12) Month-over-month revenue change using window functions (MySQL 8+)
-- We compute revenue per month, then use LAG() to calculate change and percent change
-- =====================

WITH monthly AS (
  SELECT
    DATE_FORMAT(Order_Date, '%Y-%m') AS year_month,
    SUM(Sales) AS revenue
  FROM ecommerce_sales
  WHERE Order_Date IS NOT NULL
  GROUP BY year_month
)
SELECT
  year_month,
  revenue,
  revenue - LAG(revenue) OVER (ORDER BY year_month) AS mom_change,
  ROUND((revenue - LAG(revenue) OVER (ORDER BY year_month)) / NULLIF(LAG(revenue) OVER (ORDER BY year_month),0) * 100, 2) AS mom_pct_change
FROM monthly
ORDER BY year_month;

-- =====================
-- 13) Ranking products within each category using ROW_NUMBER (top N products per category)
-- =====================

WITH prod_rev AS (
  SELECT Category, Product, SUM(Sales) AS revenue
  FROM ecommerce_sales
  GROUP BY Category, Product
),
ranked AS (
  SELECT
    Category,
    Product,
    revenue,
    ROW_NUMBER() OVER (PARTITION BY Category ORDER BY revenue DESC) AS rn
  FROM prod_rev
)
SELECT * FROM ranked WHERE rn <= 5 ORDER BY Category, rn;

-- =====================
-- Explanations of common SQL concepts used in the queries above
--
-- COUNT(*) vs COUNT(DISTINCT Customer_ID):
--   COUNT(*) returns the number of rows in the result set (counts duplicates and NULLs as rows).
--   COUNT(DISTINCT Customer_ID) returns the number of unique customer IDs (ignores duplicates). Use DISTINCT when you want unique counts.
--
-- WHERE vs HAVING:
--   WHERE filters rows before aggregation (applies to individual rows). HAVING filters groups after aggregation (applies to GROUP BY results).
--   Example: WHERE Order_Date IS NOT NULL filters out rows with missing dates before grouping by month.
--            HAVING orders_count > 1 filters customer groups that have more than one order after grouping.
--
-- GROUP BY vs Window Functions:
--   GROUP BY aggregates rows into groups and returns one row per group (e.g., SUM(Sales) per Product).
--   Window functions compute values across a set of rows related to the current row without reducing the number of rows (e.g., LAG, ROW_NUMBER, RANK).
--   Window functions are useful for running totals, rankings, and month-over-month comparisons where you need both row-level and group-level information.
--
-- End of file
