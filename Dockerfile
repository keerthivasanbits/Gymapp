FROM python:3.10-slim

# Install system dependencies for Tkinter and headless display (Xvfb)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-tk \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user and app directory
RUN useradd -m appuser
WORKDIR /home/appuser/app
RUN chown -R appuser:appuser /home/appuser/app

# Switch to non-root user
USER appuser
ENV PATH="/home/appuser/.local/bin:${PATH}"
ENV PYTHONUNBUFFERED=1
ENV MPLBACKEND=Agg

# Install Python dependencies
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir --user --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser . .

# Run Tkinter app under a virtual display
CMD ["xvfb-run", "-a", "python", "aceestver_gymapp.py"]