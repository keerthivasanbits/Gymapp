FROM python:3.10-slim

# Install Tkinter GUI and Xvfb dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-tk \
    tk \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxft2 \
    libxss1 \
    xvfb \
    xauth \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m appuser
USER appuser

WORKDIR /home/appuser/app

# Install dependencies in virtualenv first (for better layer caching)
COPY --chown=appuser:appuser requirements.txt .
RUN python -m venv .venv && \
    .venv/bin/pip install --no-cache-dir -r requirements.txt && \
    .venv/bin/pip install pytest

# Copy application source code
COPY --chown=appuser:appuser . .

CMD [".venv/bin/python", "aceestver_gymapp.py"]