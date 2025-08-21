Stock Market Data Pipeline

Dockerized data pipeline using Apache Airflow to fetch, process, and store stock market data. This project demonstrates modern data engineering practices with comprehensive error handling and monitoring.

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
|   ├── scheduler/
|   └── webserver/ 
|   └── worker/
└── plugins/                   # Airflow plugins (optional)


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
