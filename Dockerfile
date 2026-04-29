# ---------- BUILD STAGE ----------
FROM python:3.9-slim AS builder

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ---------- RUNTIME STAGE ----------
FROM python:3.9-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy app source
COPY app/aceest_fitness.py .

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Create volume mount point for SQLite DB persistence
VOLUME ["/app/data"]

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"

# Run with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "60", "aceest_fitness:app"]