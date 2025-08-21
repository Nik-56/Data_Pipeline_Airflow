-- Create a separate database for stock data
CREATE DATABASE stock_data;

-- Connect to the stock_data database and create tables
\c stock_data;

-- Create the stock_prices table
CREATE TABLE IF NOT EXISTS stock_prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open_price DECIMAL(10, 2),
    high_price DECIMAL(10, 2),
    low_price DECIMAL(10, 2),
    close_price DECIMAL(10, 2),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, timestamp)
);

-- Create an index for better query performance
CREATE INDEX IF NOT EXISTS idx_stock_symbol_timestamp ON stock_prices(symbol, timestamp);

-- Insert some sample data for testing
INSERT INTO stock_prices (symbol, timestamp, open_price, high_price, low_price, close_price, volume)
VALUES 
    ('AAPL', '2024-01-01 00:00:00', 150.00, 155.00, 149.00, 152.50, 1000000),
    ('GOOGL', '2024-01-01 00:00:00', 2800.00, 2850.00, 2790.00, 2820.00, 500000)
ON CONFLICT (symbol, timestamp) DO NOTHING;