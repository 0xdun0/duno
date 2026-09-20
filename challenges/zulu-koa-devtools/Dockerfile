FROM node:18-slim

WORKDIR /app

# Runtime deps: sudo (privesc challenge), curl (health check)
RUN apt-get update && \
    apt-get install -y --no-install-recommends sudo curl && \
    rm -rf /var/lib/apt/lists/*

# Install Node dependencies
COPY package.json .
RUN npm install --production --no-audit --no-fund

COPY app.js .

# Fake .git directory (source code / history exposure)
# Cannot commit real .git to repo — fake_git/ is renamed at build time.
# FLAG1 placeholder is replaced with actual value via sed.
ARG FLAG1=g1t_cred_l34k3d
COPY fake_git/ .git/
RUN sed -i "s/PLACEHOLDER_FLAG1/${FLAG1}/g" .git/logs/HEAD

# Create non-root application user
RUN useradd -m -s /bin/bash ctfuser

# Sudo misconfiguration — CTF privilege escalation target
# VULNERABLE: ctfuser runs node as root without password (GTFOBins)
# Exploit: sudo /usr/local/bin/node -e 'require("child_process").spawn("/bin/sh",["-i"],{stdio:"inherit"})'
RUN echo "ctfuser ALL=(root) NOPASSWD: /usr/local/bin/node" > /etc/sudoers.d/ctfuser && \
    chmod 0440 /etc/sudoers.d/ctfuser

# Write FLAG3 to root home (must be done as root, before USER ctfuser)
ARG FLAG3=nod3_sud0_r00t
RUN echo "${FLAG3}" > /root/flag.txt && \
    chmod 600 /root/flag.txt

# Set ownership (FLAG2 is written by app.js at startup via process.env.FLAG2)
RUN chown -R ctfuser:ctfuser /app

ARG FLAG2=k0a_h0stnam3_byp4ss
ENV FLAG2=${FLAG2}

USER ctfuser

EXPOSE 4022

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -sf http://localhost:4022/ > /dev/null || exit 1

CMD ["node", "app.js"]
