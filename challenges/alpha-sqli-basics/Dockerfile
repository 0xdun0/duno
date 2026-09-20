# Alpha - SQLi Basics (Multi-Stage Challenge)
# Progressive SQL injection with RCE and privilege escalation

FROM python:3.11-alpine

# Install system dependencies for ping and privilege escalation
RUN apk add --no-cache \
    iputils \
    sudo \
    shadow \
    && rm -rf /var/cache/apk/*

# Create non-root user for the application
RUN adduser -D -u 1000 ctfuser && \
    echo "ctfuser:ctfuser" | chpasswd

# Set up sudo misconfiguration for privilege escalation (FLAG5)
# GTFOBins: python3 can be used to read files with sudo
RUN echo "ctfuser ALL=(ALL) NOPASSWD: /usr/bin/find" > /etc/sudoers.d/ctfuser && \
    chmod 0440 /etc/sudoers.d/ctfuser

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Set flags as environment variables (overridden in docker-compose.yml)
ENV FLAG1="sql1_b4s1c_byp4ss"
ENV FLAG2="un10n_d4t4_3xtr4ct"
ENV FLAG3="4dm1n_p4n3l_4cc3ss"
ENV FLAG4="c0mm4nd_1nj3ct10n_rc3"
ENV FLAG5="pr1v3sc_t0_r00t"

# Create FLAG5 in root directory (only readable by root)
RUN echo "${FLAG5}" > /root/flag5.txt && \
    chmod 600 /root/flag5.txt

# Create home directory for ctfuser
RUN mkdir -p /home/ctfuser && chown ctfuser:ctfuser /home/ctfuser

# Expose port 5000
EXPOSE 5000

# Switch to ctfuser for running the application
USER ctfuser

# Run the application
CMD ["python", "app.py"]
