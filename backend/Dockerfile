# Multi-stage build for CMS Automation Backend with Playwright support
# Optimized for Google Cloud Run deployment

# ============================================================================
# Stage 1: Builder - Install dependencies
# ============================================================================
FROM python:3.11-slim as builder

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.7.1

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Configure Poetry to not create virtual env (we're in a container)
RUN poetry config virtualenvs.create false

# Install dependencies (without dev dependencies for production)
RUN poetry install --no-dev --no-interaction --no-ansi

# ============================================================================
# Stage 2: Runtime - Final image with Playwright
# ============================================================================
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    # Disable Playwright telemetry
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0

# Install system dependencies for Playwright (Chromium)
RUN apt-get update && apt-get install -y \
    # Core dependencies
    wget \
    gnupg \
    ca-certificates \
    libpq-dev \
    # Font rendering
    fonts-liberation \
    fonts-noto-color-emoji \
    # Audio/Video
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    # Graphics
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    # X11
    libnspr4 \
    libnss3 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    # Utilities
    xdg-utils \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Install Playwright and browsers
RUN pip install --no-cache-dir playwright==1.55.0 && \
    playwright install chromium && \
    playwright install-deps chromium

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app /var/log/cms-automation && \
    chown -R appuser:appuser /app /var/log/cms-automation

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser . .

# Copy and setup entrypoint script
COPY --chown=appuser:appuser entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Switch to non-root user
USER appuser

# Health check (only for API service)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || true

# Expose port
EXPOSE 8000

# Start application using entrypoint script
# SERVICE_TYPE environment variable determines what to run:
# - api: API Server (default)
# - worker: Celery Worker
# - beat: Celery Beat Scheduler
CMD ["/app/entrypoint.sh"]
