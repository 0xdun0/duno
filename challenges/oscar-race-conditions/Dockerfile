FROM python:3.11-alpine

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY templates/ templates/

# Create non-root user
RUN adduser -D -u 1000 ctfuser && \
    chown -R ctfuser:ctfuser /app && \
    mkdir -p /tmp && \
    chown ctfuser:ctfuser /tmp

# Switch to non-root user
USER ctfuser

# Expose port
EXPOSE 4011

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:4011')"

# Run application
CMD ["python", "app.py"]
