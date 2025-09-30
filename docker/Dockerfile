# Use official Python base image
FROM python:3.11-slim

# Reduce noisy pyc files and get unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN apt-get update && apt-get upgrade -y && apt-get clean \
    && pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app/ /app/app

# Copy Alembic migration files and config
COPY migration/ /app/migration

# Optional: Copy helper script for migrations
COPY run_migrations.py /app/run_migrations.py
COPY generate_migration.py /app/generate_migration.py

# Expose FastAPI port
EXPOSE 8000

# Run the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]