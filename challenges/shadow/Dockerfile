FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends sudo perl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY templates/ templates/

# Set flags
ARG FLAG1=gr4phql_1ntr0sp3ct10n
ARG FLAG2=gr4phql_1nj3ct10n_byp4ss
ARG FLAG3=b4tch_qu3ry_3xtr4ct10n
ARG FLAG4=gr4phql_rc3_pr1v3sc
ENV FLAG1=${FLAG1}
ENV FLAG2=${FLAG2}
ENV FLAG3=${FLAG3}
ENV FLAG4=${FLAG4}

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash ctfuser && \
    echo "ctfuser:ctfuser" | chpasswd

# Configure sudo for privilege escalation (GTFOBins: perl)
RUN echo "ctfuser ALL=(ALL) NOPASSWD: /usr/bin/perl" > /etc/sudoers.d/ctfuser && \
    chmod 0440 /etc/sudoers.d/ctfuser

# Create flag files
RUN echo "${FLAG4}" > /root/flag4.txt && \
    chmod 600 /root/flag4.txt

# Set ownership
RUN chown -R ctfuser:ctfuser /app

# Switch to non-root user
USER ctfuser

# Expose port
EXPOSE 4012

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:4012')"

# Run application
CMD ["python", "app.py"]
