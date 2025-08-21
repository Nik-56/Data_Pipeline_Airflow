FROM apache/airflow:2.8.0-python3.10

USER root

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    netcat-openbsd \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Install Python packages
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Copy application files (NOT logs directory)
COPY dags/ /opt/airflow/dags/
COPY scripts/ /opt/airflow/scripts/
COPY plugins/ /opt/airflow/plugins/

# Copy entrypoint script
COPY scripts/entrypoint.sh /opt/airflow/scripts/entrypoint.sh

# Make entrypoint executable
USER root
RUN chmod +x /opt/airflow/scripts/entrypoint.sh

# Add scripts to PYTHONPATH
ENV PYTHONPATH=/opt/airflow:/opt/airflow/scripts

USER airflow