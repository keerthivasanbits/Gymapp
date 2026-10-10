FROM python:3.10-slim

# Prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install Tkinter GUI, build essentials, and Xvfb dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-tk \
    tk \
    tk-dev \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxft2 \
    libxss1 \
    xvfb \
    xauth \
    && rm -rf /var/lib/apt/lists/*

# Create and switch to non-root user
RUN useradd -m -s /bin/bash appuser
USER appuser

WORKDIR /home/appuser/app

# Set up virtual environment and update PATH
ENV PATH="/home/appuser/app/.venv/bin:$PATH"

# Copy requirements and install dependencies
COPY --chown=appuser:appuser requirements.txt .
RUN python -m venv .venv && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY --chown=appuser:appuser . .

# Default command to run the application
CMD ["python", "aceestver_gymapp.py"]