FROM python:3.11-alpine

WORKDIR /app

# Install sudo for privilege escalation challenge
RUN apk add --no-cache sudo

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create symlink so sudoers path matches actual Python location in Alpine
RUN ln -sf /usr/local/bin/python3 /usr/bin/python3

# Copy application files
COPY app.py .
COPY templates/ templates/

# Create ctfuser with a dummy password (required for sudo even with NOPASSWD)
RUN adduser -D -u 1000 ctfuser && \
    echo "ctfuser:ctfuser" | chpasswd

# Configure sudo with GTFOBin vulnerabilities (FLAG 4 challenge)
# VULNERABLE: Allows file writes as root through path manipulation
RUN echo "ctfuser ALL=(ALL) NOPASSWD: /usr/local/bin/python3, /usr/bin/python3" > /etc/sudoers.d/ctfuser && \
    chmod 0440 /etc/sudoers.d/ctfuser

# Set flags as environment variables
ARG FLAG1=n0sql_4uth_byp4ss
ARG FLAG2=n0sql_d4t4_dump3d
ARG FLAG3=n0sql_js_3x3cut10n
ARG FLAG4=m0ng0_pr1v_3sc_r00t

ENV FLAG1=${FLAG1}
ENV FLAG2=${FLAG2}
ENV FLAG3=${FLAG3}
ENV FLAG4=${FLAG4}

# MongoDB connection details (set via docker-compose)
ENV MONGO_HOST=mongodb
ENV MONGO_PORT=27017

# Write FLAG4 to /root/flag4.txt (requires privilege escalation)
RUN echo "${FLAG4}" > /root/flag4.txt && \
    chmod 600 /root/flag4.txt

# Change ownership and switch user
RUN chown -R ctfuser:ctfuser /app && \
    mkdir -p /home/ctfuser && \
    chown -R ctfuser:ctfuser /home/ctfuser

USER ctfuser

# Expose port
EXPOSE 4007

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:4007/').read()" || exit 1

# Run the application
CMD ["python", "app.py"]
