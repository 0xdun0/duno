FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends sudo && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY templates/ templates/

# Create ctfuser
RUN useradd -m -u 1000 -s /bin/bash ctfuser && \
    echo "ctfuser:ctfuser" | chpasswd

# Configure sudoers for privilege escalation challenge (GTFOBins: awk)
RUN echo "ctfuser ALL=(ALL) NOPASSWD: /usr/bin/awk" > /etc/sudoers.d/ctfuser && \
    chmod 0440 /etc/sudoers.d/ctfuser

# Create flag files (flags set via environment variables at runtime)
ARG FLAG1=test_flag1
ARG FLAG2=test_flag2
ARG FLAG3=test_flag3
ARG FLAG4=test_flag4
ARG FLAG5=test_flag5

ENV FLAG1=${FLAG1}
ENV FLAG2=${FLAG2}
ENV FLAG3=${FLAG3}
ENV FLAG4=${FLAG4}
ENV FLAG5=${FLAG5}

# FLAG3: Path traversal target (readable by all)
RUN echo "${FLAG3}" > /app/flag3.txt && chmod 644 /app/flag3.txt

# FLAG4: Command injection target (readable by ctfuser)
RUN echo "${FLAG4}" > /home/ctfuser/flag4.txt && \
    chown ctfuser:ctfuser /home/ctfuser/flag4.txt && \
    chmod 600 /home/ctfuser/flag4.txt

# FLAG5: Root privilege escalation target (readable only by root)
RUN echo "${FLAG5}" > /root/flag5.txt && chmod 600 /root/flag5.txt

# Create logs directory for app.py
RUN mkdir -p /app/logs && chown ctfuser:ctfuser /app/logs

# Switch to ctfuser
USER ctfuser

# Expose port
EXPOSE 4003

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:4003/api/status').read()" || exit 1

# Run the application
CMD ["python", "app.py"]
