FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends sudo && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY templates/ templates/

# Set flags
ARG FLAG1=ssrf_1nt3rn4l_4cc3ss
ARG FLAG2=4dm1n_p4n3l_pwn3d
ARG FLAG3=ssrf_t0_rc3_ch41n3d
ARG FLAG4=ssrf_sud0_pr1v3sc
ENV FLAG1=${FLAG1}
ENV FLAG2=${FLAG2}
ENV FLAG3=${FLAG3}
ENV FLAG4=${FLAG4}

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash ctfuser && \
    echo "ctfuser:ctfuser" | chpasswd

# Configure sudo for privilege escalation (GTFOBins: python3)
RUN echo "ctfuser ALL=(ALL) NOPASSWD: /usr/bin/python3" > /etc/sudoers.d/ctfuser && \
    chmod 0440 /etc/sudoers.d/ctfuser

# Create flag files
RUN echo "${FLAG3}" > /tmp/flag3.txt && \
    chmod 644 /tmp/flag3.txt && \
    echo "${FLAG4}" > /root/flag4.txt && \
    chmod 600 /root/flag4.txt

# Set ownership
RUN chown -R ctfuser:ctfuser /app

# Switch to non-root user
USER ctfuser

# Expose port
EXPOSE 4010

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:4010')"

# Run application
CMD ["python", "app.py"]
