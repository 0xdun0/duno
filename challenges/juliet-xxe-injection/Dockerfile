FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (libxml2/libxslt for lxml, sudo for privesc)
RUN apt-get update && \
    apt-get install -y --no-install-recommends sudo libxml2-dev libxslt-dev gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY templates/ templates/

# Set flags
ARG FLAG1=xxe_d1sc0v3r3d
ARG FLAG2=f1l3_r34d_succ3ss
ARG FLAG3=ssrf_t0_1nt3rn4l
ARG FLAG4=xxe_rc3_ch41n3d
ARG FLAG5=f1nd_pr1v_3sc_r00t
ENV FLAG1=${FLAG1}
ENV FLAG2=${FLAG2}
ENV FLAG3=${FLAG3}
ENV FLAG4=${FLAG4}
ENV FLAG5=${FLAG5}

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash ctfuser && \
    echo "ctfuser:ctfuser" | chpasswd

# Configure sudo for privilege escalation (GTFOBins: find)
RUN echo "ctfuser ALL=(ALL) NOPASSWD: /usr/bin/find" > /etc/sudoers.d/ctfuser && \
    chmod 0440 /etc/sudoers.d/ctfuser

# Create flag files
# FLAG4 is written at runtime by app.py init_flags() to /home/ctfuser/flag4.txt
# FLAG5 must be created here (root-owned, app runs as ctfuser)
RUN echo "${FLAG5}" > /root/flag5.txt && \
    chmod 600 /root/flag5.txt

# Create directories for flag files (writable by ctfuser at runtime)
RUN mkdir -p /opt/eversec/secrets && \
    chown -R ctfuser:ctfuser /opt/eversec

# Set ownership
RUN chown -R ctfuser:ctfuser /app

# Switch to non-root user
USER ctfuser

# Expose port
EXPOSE 4005

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:4005/').read()" || exit 1

# Run the application
CMD ["python", "app.py"]
