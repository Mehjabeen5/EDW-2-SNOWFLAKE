CREATE OR REPLACE TABLE EDW_2_DB.PUBLIC.REVENUE_DATA AS
WITH T (QUARTER, REGION, PRODUCT, REVENUE, COST) AS (
    SELECT * FROM VALUES
    ('2024-Q1', 'East', 'Product A', 120000, 90000),
    ('2024-Q1', 'West', 'Product B', 150000, 130000),
    ('2024-Q2', 'East', 'Product A', 95000, 88000),
    ('2024-Q2', 'West', 'Product B', 110000, 120000),
    ('2024-Q3', 'East', 'Product A', 70000, 85000),
    ('2024-Q3', 'West', 'Product B', 130000, 115000),
    ('2024-Q4', 'East', 'Product A', 160000, 100000),
    ('2024-Q4', 'West', 'Product B', 140000, 120000)
)
SELECT * FROM T;
