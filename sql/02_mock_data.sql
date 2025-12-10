-- 02_mock_data.sql
-- Load mock revenue data into REVENUE_TABLE

USE DATABASE EDW_2_DB;
USE SCHEMA REASONING;

-- Start clean each time
TRUNCATE TABLE REVENUE_TABLE;

INSERT INTO REVENUE_TABLE (QUARTER, REGION, PRODUCT, REVENUE, COST) VALUES
    -- Q2
    ('2024-Q2', 'West', 'Product A', 180000, 120000),
    ('2024-Q2', 'East', 'Product B', 140000, 100000),

    -- Q3
    ('2024-Q3', 'West', 'Product B', 490000, 300000),
    ('2024-Q3', 'East', 'Product A', 310000, 210000),

    -- Q4
    ('2024-Q4', 'West', 'Product A', 300000, 190000),
    ('2024-Q4', 'East', 'Product B', 200000, 140000);
