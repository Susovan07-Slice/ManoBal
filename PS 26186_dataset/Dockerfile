FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install minimal OS runtime dependencies (OpenMP for LightGBM, curl for healthcheck)
# Use HTTPS for Debian package repositories for secure network compatibility
RUN [ -f /etc/apt/sources.list.d/debian.sources ] && sed -i 's|http://|https://|g' /etc/apt/sources.list.d/debian.sources || true; \
    [ -f /etc/apt/sources.list ] && sed -i 's|http://|https://|g' /etc/apt/sources.list || true; \
    apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*


# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application codebase and artifacts
COPY api/ ./api/
COPY core/ ./core/
COPY db/ ./db/
COPY ml_pipeline/ ./ml_pipeline/
COPY models/ ./models/
COPY schemas/ ./schemas/
COPY services/ ./services/
COPY src/ ./src/
COPY tests/ ./tests/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY docker-entrypoint.sh .

# Ensure Linux LF line endings and executable permission
RUN sed -i 's/\r$//' docker-entrypoint.sh && chmod +x docker-entrypoint.sh

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

ENTRYPOINT ["./docker-entrypoint.sh"]
