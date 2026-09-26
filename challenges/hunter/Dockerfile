FROM python:3.11-slim

WORKDIR /app

# Install system dependencies: gcc for SUID binary, Chromium for admin bot
RUN apt-get update && \
    apt-get install -y gcc chromium chromium-driver sudo && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY templates/ templates/

# Copy and compile SUID binary (FLAG 4 challenge)
COPY suid_binary.c /tmp/suid_binary.c
RUN gcc /tmp/suid_binary.c -o /usr/local/bin/backup_tool && \
    chown root:root /usr/local/bin/backup_tool && \
    chmod 4755 /usr/local/bin/backup_tool && \
    rm /tmp/suid_binary.c

# Set flags as environment variables
ARG FLAG1=DUNO{b8020ed30dd2a6b8295e87f2dacf57b3}
ARG FLAG2=DUNO{48cb5c91efbf1b3ef6270caf56e76a14}
ARG FLAG3=DUNO{a7ab83a097b666b412340d03edbbdbfd}
ARG FLAG4=DUNO{980be85a17a8c38602ae88d37edc4b11}

ENV FLAG1=${FLAG1}
ENV FLAG2=${FLAG2}
ENV FLAG3=${FLAG3}
ENV FLAG4=${FLAG4}

# Write FLAG4 to /root/flag4.txt (requires SUID binary to read)
RUN echo "${FLAG4}" > /root/flag4.txt && \
    chmod 600 /root/flag4.txt

# Create non-root user (must be done AFTER compiling and setting SUID bit)
RUN useradd -m -u 1000 -s /bin/bash ctfuser && \
    chown -R ctfuser:ctfuser /app && \
    chown -R ctfuser:ctfuser /home/ctfuser

# Allow ctfuser to run chromium (needed for Selenium admin bot)
RUN mkdir -p /home/ctfuser/.config /home/ctfuser/.cache && \
    chown -R ctfuser:ctfuser /home/ctfuser/.config /home/ctfuser/.cache

# Switch to ctfuser
USER ctfuser

# Expose port
EXPOSE 4002

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:4002/').read()" || exit 1

# Run the application
CMD ["python", "app.py"]
