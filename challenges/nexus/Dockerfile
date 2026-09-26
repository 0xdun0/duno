FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends sudo vim && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY templates/ templates/

# Set flags as environment variables (no wrappers)
ARG FLAG1=d3s3r14l1z4t10n_d3t3ct3d
ARG FLAG2=p1ckl3_rc3_4ch13v3d
ARG FLAG3=v1m_pr1v_3sc_r00t
ENV FLAG1=${FLAG1}
ENV FLAG2=${FLAG2}
ENV FLAG3=${FLAG3}

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash ctfuser && \
    echo "ctfuser:ctfuser" | chpasswd

# Configure sudo — vim GTFOBins privesc vulnerability
RUN echo "ctfuser ALL=(ALL) NOPASSWD: /usr/bin/vim" > /etc/sudoers.d/ctfuser && \
    chmod 0440 /etc/sudoers.d/ctfuser

# Write FLAG3 to root-only file (requires privesc to read)
RUN echo "${FLAG3}" > /root/flag3.txt && \
    chmod 600 /root/flag3.txt

# Write FLAG2 to ctfuser home (accessible after RCE)
RUN echo "${FLAG2}" > /home/ctfuser/flag2.txt && \
    chown ctfuser:ctfuser /home/ctfuser/flag2.txt

# Set ownership and switch to non-root user
RUN chown -R ctfuser:ctfuser /app
USER ctfuser

# Expose port
EXPOSE 4008

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:4008/').read()" || exit 1

# Run the application
CMD ["python", "app.py"]
