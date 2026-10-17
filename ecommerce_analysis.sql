-- E-Commerce Sales Analysis (MySQL 8.0+)
-- Import datasets/ecommerce_sales_cleaned.csv into this table first; instructions are in
-- docs/mysql_sql_guide.md. Each result-producing SELECT below answers one business question.
--
-- Accounting assumption: Order_Status is descriptive. Dataset revenue, cost, and profit
-- are kept as generated for every status, including Cancelled and Returned. These queries
-- therefore do not exclude or zero out rows by status.
-- AOV assumption: one row/unique Order_ID is one order in this sample. AOV is total
-- revenue divided by distinct Order_ID count. This is valid for this dataset's one-row-per-order model.

CREATE DATABASE IF NOT EXISTS ecommerce_analytics;
USE ecommerce_analytics;

CREATE TABLE IF NOT EXISTS ecommerce_sales (
    Order_ID VARCHAR(20) NOT NULL PRIMARY KEY,
    Order_Date DATE NOT NULL,
    Customer_ID VARCHAR(20) NOT NULL,
    Region VARCHAR(40) NOT NULL,
    Customer_Segment VARCHAR(40) NOT NULL,
    Product VARCHAR(100) NOT NULL,
    Category VARCHAR(60) NOT NULL,
    Quantity INT NOT NULL,
    Unit_Price DECIMAL(10, 2) NOT NULL,
    Discount DECIMAL(5, 4) NOT NULL,
    Revenue DECIMAL(12, 2) NOT NULL,
    Cost DECIMAL(12, 2) NOT NULL,
    Profit DECIMAL(12, 2) NOT NULL,
    Payment_Method VARCHAR(50) NOT NULL,
    Order_Status VARCHAR(30) NOT NULL
);

-- 1. Overall financial performance. NULLIF protects margin from division by zero.
SELECT
    ROUND(SUM(Revenue), 2) AS total_revenue,
    ROUND(SUM(Cost), 2) AS total_cost,
    ROUND(SUM(Profit), 2) AS total_profit,
    ROUND(100.0 * SUM(Profit) / NULLIF(SUM(Revenue), 0), 2) AS profit_margin_percent
FROM ecommerce_sales;

-- 2. Number of orders and customers (IDs are counted distinctly).
SELECT
    COUNT(DISTINCT Order_ID) AS total_orders,
    COUNT(DISTINCT Customer_ID) AS unique_customers
FROM ecommerce_sales;

-- 3. Monthly revenue and profit trend.
SELECT
    DATE_FORMAT(Order_Date, '%Y-%m') AS sales_month,
    ROUND(SUM(Revenue), 2) AS monthly_revenue,
    ROUND(SUM(Profit), 2) AS monthly_profit
FROM ecommerce_sales
GROUP BY DATE_FORMAT(Order_Date, '%Y-%m')
ORDER BY sales_month;

-- 4. Revenue and profit by product category.
SELECT
    Category,
    ROUND(SUM(Revenue), 2) AS total_revenue,
    ROUND(SUM(Profit), 2) AS total_profit
FROM ecommerce_sales
GROUP BY Category
ORDER BY total_revenue DESC;

-- 5. Top 10 products ranked by revenue.
SELECT
    Product,
    Category,
    SUM(Quantity) AS units_sold,
    ROUND(SUM(Revenue), 2) AS total_revenue,
    ROUND(SUM(Profit), 2) AS total_profit
FROM ecommerce_sales
GROUP BY Product, Category
ORDER BY total_revenue DESC
LIMIT 10;

-- 6. Top 10 customers by total revenue.
SELECT
    Customer_ID,
    COUNT(DISTINCT Order_ID) AS order_count,
    ROUND(SUM(Revenue), 2) AS total_revenue,
    ROUND(SUM(Profit), 2) AS total_profit
FROM ecommerce_sales
GROUP BY Customer_ID
ORDER BY total_revenue DESC
LIMIT 10;

-- 7. Regional sales and profit comparison.
SELECT
    Region,
    COUNT(DISTINCT Order_ID) AS order_count,
    ROUND(SUM(Revenue), 2) AS total_revenue,
    ROUND(SUM(Profit), 2) AS total_profit,
    ROUND(100.0 * SUM(Profit) / NULLIF(SUM(Revenue), 0), 2) AS profit_margin_percent
FROM ecommerce_sales
GROUP BY Region
ORDER BY total_revenue DESC;

-- 8. Revenue and profit by customer segment.
SELECT
    Customer_Segment,
    COUNT(DISTINCT Order_ID) AS order_count,
    ROUND(SUM(Revenue), 2) AS total_revenue,
    ROUND(SUM(Profit), 2) AS total_profit
FROM ecommerce_sales
GROUP BY Customer_Segment
ORDER BY total_revenue DESC;

-- 9. Payment method distribution, with safe percentage calculation.
WITH payment_counts AS (
    SELECT Payment_Method, COUNT(DISTINCT Order_ID) AS order_count
    FROM ecommerce_sales
    GROUP BY Payment_Method
)
SELECT
    Payment_Method,
    order_count,
    ROUND(100.0 * order_count / NULLIF(SUM(order_count) OVER (), 0), 2) AS order_percentage
FROM payment_counts
ORDER BY order_count DESC;

-- 10. Order status counts and share of all orders. Financial amounts remain unadjusted.
WITH status_counts AS (
    SELECT Order_Status, COUNT(DISTINCT Order_ID) AS order_count
    FROM ecommerce_sales
    GROUP BY Order_Status
)
SELECT
    Order_Status,
    order_count,
    ROUND(100.0 * order_count / NULLIF(SUM(order_count) OVER (), 0), 2) AS order_percentage
FROM status_counts
ORDER BY order_count DESC;

-- 11. Average order value. For this data, each unique order has exactly one row.
SELECT
    ROUND(SUM(Revenue) / NULLIF(COUNT(DISTINCT Order_ID), 0), 2) AS average_order_value
FROM ecommerce_sales;

-- 12. Rank products by revenue inside each category (MySQL 8 window function).
WITH product_revenue AS (
    SELECT Category, Product, SUM(Revenue) AS total_revenue
    FROM ecommerce_sales
    GROUP BY Category, Product
)
SELECT
    Category,
    Product,
    ROUND(total_revenue, 2) AS total_revenue,
    RANK() OVER (PARTITION BY Category ORDER BY total_revenue DESC) AS category_revenue_rank
FROM product_revenue
ORDER BY Category, category_revenue_rank, Product;

-- 13. Month-over-month revenue change and growth. First month has no prior month (NULL).
WITH monthly_revenue AS (
    SELECT
        CAST(DATE_FORMAT(Order_Date, '%Y-%m-01') AS DATE) AS sales_month,
        SUM(Revenue) AS revenue
    FROM ecommerce_sales
    GROUP BY CAST(DATE_FORMAT(Order_Date, '%Y-%m-01') AS DATE)
), monthly_with_previous AS (
    SELECT
        sales_month,
        revenue,
        LAG(revenue) OVER (ORDER BY sales_month) AS previous_month_revenue
    FROM monthly_revenue
)
SELECT
    DATE_FORMAT(sales_month, '%Y-%m') AS sales_month,
    ROUND(revenue, 2) AS revenue,
    ROUND(previous_month_revenue, 2) AS previous_month_revenue,
    ROUND(revenue - previous_month_revenue, 2) AS revenue_change,
    ROUND(100.0 * (revenue - previous_month_revenue) / NULLIF(previous_month_revenue, 0), 2) AS revenue_growth_percent
FROM monthly_with_previous
ORDER BY sales_month;
