Stock Market Data Pipeline

A beginner-friendly, Dockerized data pipeline using Apache Airflow to fetch, process, and store stock market data. This project demonstrates modern data engineering practices with comprehensive error handling and monitoring.

## Features

- Automated Data Fetching: Retrieves stock data from Alpha Vantage API every hour
- Robust Error Handling: Graceful handling of API failures with demo data fallback
- Dockerized Deployment: Complete pipeline runs with a single command
- PostgreSQL Storage: Efficient data storage with conflict resolution
- Monitoring & Logging: Comprehensive logging for easy debugging
- Beginner Friendly: Extensively commented code and step-by-step instructions

## Architecture

     Airflow           Alpha Vantage       PostgreSQL
    Scheduler     ───   API            ──  Database  

##  Project Structure

stock-pipeline/
├── docker-compose.yml          # Main orchestration file
├── Dockerfile                  # Custom Airflow image
├── requirements.txt            # Python dependencies
├── init.sql                    # Database initialization
├── README.md                   # This file
├── scripts/
│   ├── entrypoint.sh          # Airflow initialization script
│   └── stock_data_fetcher.py  # Main data processing logic
├── dags/
│   └── stock_pipeline.py      # Airflow DAG definition
├── logs/                      # Airflow logs (created at runtime)
└── plugins/                   # Airflow plugins (optional)


## Quick Start

### Prerequisites

- **Docker** and **Docker Compose** installed on your system
- At least **4GB RAM** available for Docker

### Step 1: Clone and Setup

```bash
# Create project directory
mkdir stock-pipeline
cd stock-pipeline

# Create all necessary directories
mkdir -p dags scripts logs plugins
```

### Step 2: Get Your API Key

1. Visit [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
2. Sign up for a free API key
3. Copy your API key (you'll need it in Step 3)

### Step 3: Configure Environment

Edit the `docker-compose.yml` file and replace the placeholder values:

```yaml
# Replace this line:
- ALPHA_VANTAGE_API_KEY=your_api_key_here
# With your actual API key:
- ALPHA_VANTAGE_API_KEY=YOUR_ACTUAL_API_KEY

# Generate a new Fernet key:
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
- AIRFLOW__CORE__FERNET_KEY=your_fernet_key_here
```

### Step 4: Make Scripts Executable

```bash
chmod +x scripts/entrypoint.sh
```

### Step 5: Launch the Pipeline

```bash
# Build and start all services
docker-compose up --build
```

### Step 6: Access Airflow UI

1. Wait for all services to start (2-3 minutes)
2. Open your browser and go to: `http://localhost:8080`
3. Login with:
   - **Username**: `admin`
   - **Password**: `admin`

### Step 7: Enable the DAG

1. In the Airflow UI, find the `stock_market_pipeline` DAG
2. Toggle the switch to **ON** to enable it
3. Click on the DAG name to view details
4. Click **Trigger DAG** to run it manually

## Monitoring and Troubleshooting

### Check Service Status

```bash
# View running containers
docker-compose ps

# View logs for all services
docker-compose logs

# View logs for specific service
docker-compose logs airflow-scheduler
docker-compose logs postgres
```

### Database Access

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U airflow -d stock_data

# View stored data
SELECT * FROM stock_prices ORDER BY timestamp DESC LIMIT 10;

# Check data summary by symbol
SELECT symbol, COUNT(*) as records, MAX(timestamp) as latest 
FROM stock_prices 
GROUP BY symbol;
```

### Common Issues and Solutions

#### 1. **Services Won't Start**
```bash
# Check Docker resources
docker system df

# Clean up if needed
docker-compose down
docker system prune -f
docker-compose up --build
```

#### 2. **API Rate Limit Exceeded**
The pipeline automatically falls back to demo data when the API limit is reached. This is normal for free accounts.

#### 3. **Permission Errors**
```bash
# Fix script permissions
chmod +x scripts/entrypoint.sh

# Fix directory permissions
sudo chown -R $USER:$USER logs/
```

#### 4. **Database Connection Issues**
```bash
# Restart PostgreSQL
docker-compose restart postgres

# Check database logs
docker-compose logs postgres
```

## Understanding the Data

### Database Schema

```sql
CREATE TABLE stock_prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,           -- Stock symbol (AAPL, GOOGL, etc.)
    timestamp TIMESTAMP NOT NULL,          -- Data timestamp
    open_price DECIMAL(10, 2),            -- Opening price
    high_price DECIMAL(10, 2),            -- Highest price in period
    low_price DECIMAL(10, 2),             -- Lowest price in period
    close_price DECIMAL(10, 2),           -- Closing price
    volume BIGINT,                        -- Trading volume
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, timestamp)              -- Prevent duplicates
);
```

### Sample Queries

```sql
-- Get latest prices for all stocks
SELECT DISTINCT ON (symbol) symbol, timestamp, close_price
FROM stock_prices
ORDER BY symbol, timestamp DESC;

-- Calculate daily price changes
SELECT 
    symbol,
    timestamp::date as date,
    MIN(low_price) as daily_low,
    MAX(high_price) as daily_high,
    AVG(close_price) as avg_price
FROM stock_prices
GROUP BY symbol, timestamp::date
ORDER BY date DESC;

-- Find most volatile stocks (highest price swings)
SELECT 
    symbol,
    AVG(high_price - low_price) as avg_volatility
FROM stock_prices
GROUP BY symbol
ORDER BY avg_volatility DESC;
```

##  w Customization

### Adding More Stocks

Edit `dags/stock_pipeline.py`:

```python
# Modify this list to add/remove stocks
STOCK_SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA']
```

### Changing Schedule

Edit the DAG schedule in `dags/stock_pipeline.py`:

```python
# For different intervals
schedule_interval=timedelta(minutes=30),  # Every 30 minutes
schedule_interval='0 9-16 * * 1-5',      # Business hours only
schedule_interval='@daily',               # Once daily
```

### API Configuration

The pipeline uses Alpha Vantage's `TIME_SERIES_INTRADAY` function. You can modify the API parameters in `scripts/stock_data_fetcher.py`:

```python
params = {
    'function': 'TIME_SERIES_DAILY',      # Daily data instead of hourly
    'symbol': symbol,
    'apikey': api_key,
    'outputsize': 'full'                  # Get more historical data
}
```

## Security Best Practices

1. **Environment Variables**: API keys are stored in environment variables, not in code
2. **Database Credentials**: Use strong passwords in production
3. **Network Isolation**: Services communicate within Docker network
4. **Access Control**: Airflow UI requires authentication

### Production Recommendations

```yaml
# In production, use secrets management
secrets:
  api_key:
    external: true
  db_password:
    external: true

# Use external databases
external_links:
  - postgres_production
```

### Monitoring

```bash
# View resource usage
docker stats

# Monitor task performance
docker-compose logs airflow-scheduler | grep "Task"
``` 