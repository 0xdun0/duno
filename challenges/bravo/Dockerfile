# Dockerfile for Weak JWT Challenge
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install sudo
RUN apt-get update && \
    apt-get install -y sudo && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Create ctfuser
RUN useradd -m -u 1000 -s /bin/bash ctfuser

# Configure sudo with GTFOBin vulnerabilities
# VULNERABILITY: Allows ctfuser to run env and python3 as root without password
RUN echo "ctfuser ALL=(ALL) NOPASSWD: /usr/bin/env, /usr/bin/python3" >> /etc/sudoers

# Set up flags from build arguments (Formato Híbrido: DUNO{hash})
ARG FLAG1=DUNO{DUNO{69a329523ce1ec88bf63061863d9cb14}}
ARG FLAG2=DUNO{DUNO{816b09aa255516ec745de7b215e2e158}}
ARG FLAG3=DUNO{DUNO{883c631dbcaca4373e1428a73c6cb19d}}

ENV FLAG1=${FLAG1}
ENV FLAG2=${FLAG2}
ENV FLAG3=${FLAG3}

# Write FLAG3 to root directory (requires root access to read)
RUN echo "${FLAG3}" > /root/flag3.txt && \
    chmod 600 /root/flag3.txt

# Change ownership of app directory to ctfuser
RUN chown -R ctfuser:ctfuser /app

# Switch to ctfuser
USER ctfuser

# Expose port 5002
EXPOSE 5002

# Run the application
CMD ["python", "app.py"]
