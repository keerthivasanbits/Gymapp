FROM python:3.10-slim

# Install only essential dependencies for Tkinter GUI
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-tk \
    tk \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxft2 \
    libxss1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m appuser
USER appuser

# Set working directory
WORKDIR /home/appuser/app

# Copy application code
COPY --chown=appuser:appuser . .

# Install Python dependencies if needed
COPY requirements.txt .
RUN python -m venv .venv && \
    .venv/bin/pip install --no-cache-dir -r requirements.txt && \
    .venv/bin/pip install pytest

COPY . .

# Run the Tkinter app
CMD ["python", "aceestver-1.0.py"]
