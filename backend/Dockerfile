# Use an official Python runtime
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# 1. Install System Compilers (Muscles)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libpq-dev build-essential curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 2. Install Python Libraries
COPY requirements.txt .
RUN pip install --upgrade pip
# --- FIXED: Install the missing library PERMANENTLY ---
RUN pip install "pydantic[email]"
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy Application
COPY . .
EXPOSE 8000

# 4. Start
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]