FROM python:3.11-slim

# Install SSH server, sudo, and less (GNU version for GTFOBins privesc)
RUN apt-get update && \
    apt-get install -y openssh-server sudo less && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Configure sshd
RUN mkdir -p /var/run/sshd && \
    echo 'PermitRootLogin no' >> /etc/ssh/sshd_config && \
    echo 'PasswordAuthentication no' >> /etc/ssh/sshd_config && \
    echo 'PubkeyAuthentication yes' >> /etc/ssh/sshd_config

# Create ctfuser with home directory and bash shell
RUN useradd -m -s /bin/bash -u 1000 ctfuser

# Generate SSH keypair for ctfuser
RUN mkdir -p /home/ctfuser/.ssh && \
    ssh-keygen -t rsa -b 2048 -f /home/ctfuser/.ssh/id_rsa -N "" && \
    cp /home/ctfuser/.ssh/id_rsa.pub /home/ctfuser/.ssh/authorized_keys && \
    chown -R ctfuser:ctfuser /home/ctfuser/.ssh && \
    chmod 700 /home/ctfuser/.ssh && \
    chmod 600 /home/ctfuser/.ssh/id_rsa && \
    chmod 644 /home/ctfuser/.ssh/id_rsa.pub && \
    chmod 644 /home/ctfuser/.ssh/authorized_keys

# Sudoers: allow ctfuser to start SSH service (required by start.sh)
RUN echo "ctfuser ALL=(root) NOPASSWD: /usr/sbin/service ssh start" > /etc/sudoers.d/sshservice && \
    chmod 0440 /etc/sudoers.d/sshservice

# Sudoers: GTFOBins privesc vulnerability - less with NOPASSWD
RUN echo "ctfuser ALL=(root) NOPASSWD: /usr/bin/less" > /etc/sudoers.d/ctfuser && \
    chmod 0440 /etc/sudoers.d/ctfuser

# Set up application directory
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY templates/ templates/
COPY data/ data/
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Write FLAG5 to /root/flag5.txt (must be done as root before switching user)
ARG FLAG5=l3ss_1s_m0r3_r00t
RUN echo -n "$FLAG5" > /root/flag5.txt && \
    chmod 600 /root/flag5.txt

# Set ownership of app directory to ctfuser
RUN chown -R ctfuser:ctfuser /app

EXPOSE 4000 22

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:4000/login').read()" || exit 1

USER ctfuser

CMD ["/start.sh"]
