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
ENV FLAG1="DUNO{2ba1f54dc306e6cdebad3519cdc95245}"
ENV FLAG2="DUNO{f1e496aecf2521e916a8f18e96250388}"
ENV FLAG3="DUNO{3b4b347ccc4536ce9b5ea81a8bfde8df}"
ENV FLAG4="DUNO{94a848cc9a286237c497c31b15a32d39}"
ENV FLAG5="DUNO{a326842229f911f386e0c629ee413465}"

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
