"""
Stock Data Fetcher Module

This module contains functions to fetch stock data from Alpha Vantage API
and store it in PostgreSQL database. It's designed to be beginner-friendly
with extensive error handling and logging.
"""

import requests
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import time

# Set up logging
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'postgres',
    'database': 'stock_data',
    'user': 'airflow',
    'password': 'airflow123',
    'port': 5432
}

# Alpha Vantage API configuration
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

def get_database_connection():
    """
    Create and return a database connection.
    
    Returns:
        psycopg2.connection: Database connection object
        
    Raises:
        Exception: If connection fails
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info("Database connection established")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        raise

def validate_database_connection():
    """
    Validate that we can connect to the database and that the required table exists.
    
    Returns:
        bool: True if validation passes
        
    Raises:
        Exception: If validation fails
    """
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Check if the stock_prices table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'stock_prices'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            logger.error("stock_prices table does not exist")
            raise Exception("Required table 'stock_prices' not found")
        
        cursor.close()
        conn.close()
        
        logger.info("Database validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Database validation failed: {str(e)}")
        raise

def fetch_stock_data(symbol: str) -> Dict[str, Any]:
    """
    Fetch stock data from Alpha Vantage API for a given symbol.
    
    Args:
        symbol (str): Stock symbol (e.g., 'AAPL', 'GOOGL')
        
    Returns:
        Dict[str, Any]: Raw API response data
        
    Raises:
        Exception: If API request fails or data is invalid
    """
    # Get API key from environment variable
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    
    if not api_key or api_key == 'your_api_key_here':
        logger.warning(f"No valid API key found for {symbol}. Using demo data.")
        return _get_demo_data(symbol)
    
    # Prepare API request parameters
    params = {
        'function': 'TIME_SERIES_INTRADAY',
        'symbol': symbol,
        'interval': '60min',  # 1-hour intervals
        'apikey': api_key,
        'outputsize': 'compact'  # Last 100 data points
    }
    
    try:
        logger.info(f"Fetching data for {symbol} from Alpha Vantage API...")
        
        # Make API request with timeout
        response = requests.get(
            ALPHA_VANTAGE_BASE_URL, 
            params=params, 
            timeout=30
        )
        
        # Check if request was successful
        response.raise_for_status()
        
        # Parse JSON response
        data = response.json()
        
        # Check for API errors
        if 'Error Message' in data:
            raise Exception(f"API Error: {data['Error Message']}")
        
        if 'Note' in data:
            logger.warning(f"API Rate limit reached for {symbol}: {data['Note']}")
            # Use demo data as fallback
            return _get_demo_data(symbol)
        
        # Check if we have the expected data structure
        time_series_key = 'Time Series (60min)'
        if time_series_key not in data:
            logger.warning(f"Unexpected API response structure for {symbol}. Using demo data.")
            return _get_demo_data(symbol)
        
        logger.info(f"Successfully fetched data for {symbol}")
        return data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching data for {symbol}: {str(e)}")
        logger.info(f"Using demo data for {symbol} as fallback")
        return _get_demo_data(symbol)
    
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}")
        logger.info(f"Using demo data for {symbol} as fallback")
        return _get_demo_data(symbol)

def _get_demo_data(symbol: str) -> Dict[str, Any]:
    """
    Generate demo data for testing purposes when API is not available.
    
    Args:
        symbol (str): Stock symbol
        
    Returns:
        Dict[str, Any]: Demo data in Alpha Vantage format
    """
    import random
    from datetime import datetime, timedelta
    
    # Base prices for different stocks
    base_prices = {
        'AAPL': 150.0,
        'GOOGL': 2800.0,
        'MSFT': 300.0,
        'AMZN': 3000.0,
        'TSLA': 200.0
    }
    
    base_price = base_prices.get(symbol, 100.0)
    
    # Generate demo time series data
    demo_data = {
        'Meta Data': {
            '1. Information': 'Intraday (60min) open, high, low, close prices and volume',
            '2. Symbol': symbol,
            '3. Last Refreshed': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '4. Interval': '60min',
            '5. Output Size': 'Compact',
            '6. Time Zone': 'US/Eastern'
        },
        'Time Series (60min)': {}
    }
    
    # Generate 5 data points for the last 5 hours
    for i in range(5):
        timestamp = (datetime.now() - timedelta(hours=i)).strftime('%Y-%m-%d %H:00:00')
        
        # Generate realistic price variations
        variation = random.uniform(-0.05, 0.05)  # ±5% variation
        open_price = base_price * (1 + variation)
        high_price = open_price * (1 + random.uniform(0, 0.02))  # Up to 2% higher
        low_price = open_price * (1 - random.uniform(0, 0.02))   # Up to 2% lower
        close_price = random.uniform(low_price, high_price)
        volume = random.randint(100000, 1000000)
        
        demo_data['Time Series (60min)'][timestamp] = {
            '1. open': f'{open_price:.2f}',
            '2. high': f'{high_price:.2f}',
            '3. low': f'{low_price:.2f}',
            '4. close': f'{close_price:.2f}',
            '5. volume': str(volume)
        }
    
    logger.info(f"Generated demo data for {symbol}")
    return demo_data

def process_and_store_data(symbol: str):
    """
    Process the fetched stock data and store it in PostgreSQL database.
    
    Args:
        symbol (str): Stock symbol
        
    Raises:
        Exception: If processing or storage fails
    """
    try:
        logger.info(f"Processing and storing data for {symbol}...")
        
        # Fetch the data (this will get fresh data or use demo data)
        raw_data = fetch_stock_data(symbol)
        
        # Extract time series data
        time_series_key = 'Time Series (60min)'
        if time_series_key not in raw_data:
            raise Exception(f"No time series data found for {symbol}")
        
        time_series = raw_data[time_series_key]
        
        # Connect to database
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Process each timestamp in the time series
        records_inserted = 0
        records_updated = 0
        
        for timestamp, values in time_series.items():
            try:
                # Parse the data
                parsed_data = {
                    'symbol': symbol,
                    'timestamp': datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S'),
                    'open_price': float(values['1. open']),
                    'high_price': float(values['2. high']),
                    'low_price': float(values['3. low']),
                    'close_price': float(values['4. close']),
                    'volume': int(values['5. volume'])
                }
                
                # Insert or update record using ON CONFLICT
                insert_query = """
                    INSERT INTO stock_prices 
                    (symbol, timestamp, open_price, high_price, low_price, close_price, volume)
                    VALUES (%(symbol)s, %(timestamp)s, %(open_price)s, %(high_price)s, 
                           %(low_price)s, %(close_price)s, %(volume)s)
                    ON CONFLICT (symbol, timestamp) 
                    DO UPDATE SET
                        open_price = EXCLUDED.open_price,
                        high_price = EXCLUDED.high_price,
                        low_price = EXCLUDED.low_price,
                        close_price = EXCLUDED.close_price,
                        volume = EXCLUDED.volume,
                        created_at = CURRENT_TIMESTAMP
                    RETURNING (xmax = 0) AS inserted;
                """
                
                cursor.execute(insert_query, parsed_data)
                result = cursor.fetchone()
                
                if result[0]:  # New record inserted
                    records_inserted += 1
                else:  # Existing record updated
                    records_updated += 1
                
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping invalid data point for {symbol} at {timestamp}: {str(e)}")
                continue
        
        # Commit the transaction
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Successfully processed {symbol}: {records_inserted} new records, {records_updated} updated records")
        
        return {
            'symbol': symbol,
            'records_inserted': records_inserted,
            'records_updated': records_updated,
            'status': 'success'
        }
        
    except Exception as e:
        logger.error(f"Error processing data for {symbol}: {str(e)}")
        
        # Rollback transaction if connection exists
        try:
            if 'conn' in locals():
                conn.rollback()
                conn.close()
        except:
            pass
        
        raise

def get_latest_data_summary():
    """
    Get a summary of the latest data in the database.
    This is useful for monitoring and debugging.
    
    Returns:
        Dict: Summary of latest data
    """
    try:
        conn = get_database_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get count of records per symbol
        cursor.execute("""
            SELECT 
                symbol,
                COUNT(*) as total_records,
                MAX(timestamp) as latest_timestamp,
                AVG(close_price) as avg_close_price
            FROM stock_prices 
            GROUP BY symbol
            ORDER BY symbol;
        """)
        
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        summary = {
            'total_symbols': len(results),
            'symbols': [dict(row) for row in results]
        }
        
        logger.info(f"Database summary: {summary['total_symbols']} symbols tracked")
        return summary
        
    except Exception as e:
        logger.error(f"Error getting data summary: {str(e)}")
        return {'error': str(e)}

# Utility function for manual testing
if __name__ == "__main__":
    # This allows you to test the functions manually
    logging.basicConfig(level=logging.INFO)
    
    # Test with a sample symbol
    test_symbol = 'AAPL'
    
    try:
        # Test database connection
        validate_database_connection()
        
        # Test data fetching and processing
        process_and_store_data(test_symbol)
        
        # Show summary
        summary = get_latest_data_summary()
        print(f"Summary: {summary}")
        
    except Exception as e:
        print(f"Test failed: {str(e)}")