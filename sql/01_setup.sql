-- 01_setup.sql
-- Create database / schema and the base revenue table

-- Make sure we are in the right database & schema
CREATE DATABASE IF NOT EXISTS EDW_2_DB;
CREATE SCHEMA IF NOT EXISTS EDW_2_DB.REASONING;

USE DATABASE EDW_2_DB;
USE SCHEMA REASONING;

-- Base fact table for revenue data
CREATE OR REPLACE TABLE REVENUE_TABLE (
    QUARTER STRING,
    REGION  STRING,
    PRODUCT STRING,
    REVENUE NUMBER,
    COST    NUMBER
);
