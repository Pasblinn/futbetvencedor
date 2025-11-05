-- Create database and user if they don't exist
CREATE DATABASE IF NOT EXISTS football_analytics;
CREATE USER IF NOT EXISTS 'football_user'@'%' IDENTIFIED BY 'football_pass';
GRANT ALL PRIVILEGES ON football_analytics.* TO 'football_user'@'%';
FLUSH PRIVILEGES;

-- Create extensions if using PostgreSQL
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- CREATE EXTENSION IF NOT EXISTS "pg_trgm";