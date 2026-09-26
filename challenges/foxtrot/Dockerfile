FROM python:3.11-alpine

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY templates/ templates/
COPY static/ static/

# Set flags as environment variables
ARG FLAG1=DUNO{39aec5873a512caf0e82d1ceb8238527}
ARG FLAG2=DUNO{99814af7b6dc97953a6c298cc4731602}
ARG FLAG3=DUNO{fd1f291eed8b80e33380ad1eab6455cf}
ARG FLAG4=DUNO{2df9b7f215d63f7a57db5bb3754f154d}
ENV FLAG1=${FLAG1}
ENV FLAG2=${FLAG2}
ENV FLAG3=${FLAG3}
ENV FLAG4=${FLAG4}

# Run as non-root user
RUN adduser -D -u 1000 ctfuser && \
    chown -R ctfuser:ctfuser /app
USER ctfuser

# Expose port
EXPOSE 4001

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:4001/login').read()" || exit 1

# Run the application
CMD ["python", "app.py"]
