"""
Stock Market Data Pipeline DAG

This DAG fetches stock market data from Alpha Vantage API and stores it in PostgreSQL.
It's designed to be beginner-friendly with extensive comments and error handling.
"""

from datetime import datetime, timedelta
import logging
import os

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.models import Variable

# Import our custom functions
from scripts.stock_data_fetcher import (
    fetch_stock_data,
    process_and_store_data,
    validate_database_connection
)

# Set up logging
logger = logging.getLogger(__name__)

# Default arguments for the DAG
default_args = {
    'owner': 'data-engineer',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,  # Retry failed tasks 2 times
    'retry_delay': timedelta(minutes=5),  # Wait 5 minutes between retries
}

# Create the DAG
dag = DAG(
    'stock_market_pipeline',
    default_args=default_args,
    description='A beginner-friendly stock market data pipeline',
    schedule_interval=timedelta(hours=1),  # Run every hour
    catchup=False,  # Don't run for past dates
    max_active_runs=1,  # Only one instance running at a time
    tags=['stock', 'data-pipeline', 'beginner'],
)

# List of stock symbols to fetch (you can modify this list)
STOCK_SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']

def check_environment_variables():
    """
    Check if all required environment variables are set.
    This is a good practice for data pipelines.
    """
    required_vars = ['ALPHA_VANTAGE_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    logger.info("All required environment variables are set")
    return True

def log_pipeline_start():
    """
    Log the start of the pipeline execution.
    """
    logger.info("Starting Stock Market Data Pipeline")
    logger.info(f"Fetching data for symbols: {STOCK_SYMBOLS}")
    return "Pipeline started successfully"

def log_pipeline_end():
    """
    Log the successful completion of the pipeline.
    """
    logger.info("Stock Market Data Pipeline completed successfully")
    return "Pipeline completed successfully"

# Task 1: Check environment variables
check_env_task = PythonOperator(
    task_id='check_environment_variables',
    python_callable=check_environment_variables,
    dag=dag,
)

# Task 2: Log pipeline start
log_start_task = PythonOperator(
    task_id='log_pipeline_start',
    python_callable=log_pipeline_start,
    dag=dag,
)

# Task 3: Validate database connection
validate_db_task = PythonOperator(
    task_id='validate_database_connection',
    python_callable=validate_database_connection,
    dag=dag,
)

# Task 4: Create tasks for each stock symbol
fetch_tasks = []
process_tasks = []

for symbol in STOCK_SYMBOLS:
    # Fetch data task for each symbol
    fetch_task = PythonOperator(
        task_id=f'fetch_data_{symbol}',
        python_callable=fetch_stock_data,
        op_args=[symbol],  # Pass symbol as argument
        dag=dag,
    )
    fetch_tasks.append(fetch_task)
    
    # Process and store data task for each symbol
    process_task = PythonOperator(
        task_id=f'process_and_store_{symbol}',
        python_callable=process_and_store_data,
        op_args=[symbol],  # Pass symbol as argument
        dag=dag,
    )
    process_tasks.append(process_task)
    
    # Set dependency: fetch before process for each symbol
    fetch_task >> process_task

# Task 5: Log pipeline completion
log_end_task = PythonOperator(
    task_id='log_pipeline_end',
    python_callable=log_pipeline_end,
    dag=dag,
)

# Define task dependencies
# Start tasks
check_env_task >> log_start_task >> validate_db_task

# Connect validation to all fetch tasks
for fetch_task in fetch_tasks:
    validate_db_task >> fetch_task

# Connect all process tasks to the end task
for process_task in process_tasks:
    process_task >> log_end_task