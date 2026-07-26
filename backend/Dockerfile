FROM python:3.12-slim

# ---------------------------------------------------------
# Environment
# ---------------------------------------------------------

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ---------------------------------------------------------
# System Packages
# ---------------------------------------------------------

RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    libmagic1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------
# Working Directory
# ---------------------------------------------------------

WORKDIR /app

# ---------------------------------------------------------
# Install Python Packages
# ---------------------------------------------------------

COPY backend/requirements.txt .

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------
# Copy Project
# ---------------------------------------------------------

COPY backend/ .

# ---------------------------------------------------------
# Create Upload Directory
# ---------------------------------------------------------

RUN mkdir -p /app/uploads

# ---------------------------------------------------------
# Expose Port
# ---------------------------------------------------------

EXPOSE 5000

# ---------------------------------------------------------
# Start Application
# ---------------------------------------------------------

CMD ["sh", "-c", "python wait_for_db.py && flask db upgrade && gunicorn -w 4 -b 0.0.0.0:5000 app:app"]