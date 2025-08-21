#!/usr/bin/env bash

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
while ! nc -z postgres 5432; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done
echo "PostgreSQL is ready!"

# Initialize the database
echo "Initializing Airflow database..."
airflow db migrate

# Create an admin user (only if it doesn't exist)
echo "Creating admin user..."
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password admin || echo "User already exists"

echo "Starting Airflow $1..."
# Execute the command
exec airflow "$@"