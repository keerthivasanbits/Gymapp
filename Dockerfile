FROM python:3.10-slim

# Install Tkinter + xvfb in one step
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

# Set working directory
WORKDIR /home/appuser/app

# Copy requirements first (better caching)
COPY --chown=appuser:appuser requirements.txt .

# Install dependencies globally (no venv needed in Docker)
RUN pip install --no-cache-dir --user -r requirements.txt && \
    pip install --no-cache-dir --user pytest matplotlib fpdf

# Add local user bin to PATH so python/pytest can be found directly
ENV PATH="/home/appuser/.local/bin:$PATH"

# Copy application code
COPY --chown=appuser:appuser . .

# Default command (uses system/user Python directly)
CMD ["python", "aceest_app.py"]