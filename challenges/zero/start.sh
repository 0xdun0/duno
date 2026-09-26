#!/bin/bash
# start.sh — Launch all three processes for the Yankee Log4Shell challenge
# Runs as root initially to write root-owned flag files, then drops to ctfuser.

set -e

# Write FLAG2 at runtime from env (keeps flag out of image layers)
echo "${FLAG2:-dev_flag2}" > /app/flag2.txt
chown ctfuser:ctfuser /app/flag2.txt

# Write FLAG3 as root so it can only be read via sudo python3 (the privesc path).
# If FLAG3 env var is not set, use a dev placeholder.
echo "${FLAG3:-dev_flag3}" > /root/flag3.txt
chmod 600 /root/flag3.txt

# Drop to ctfuser for all subsequent processes
exec su ctfuser -s /bin/bash -c '
    echo "[start.sh] Starting JNDI/LDAP exploit server..."
    python3 /app/jndi_server.py &
    JNDI_PID=$!

    sleep 2

    echo "[start.sh] Starting Java audit logger (Log4j 2.14.1)..."
    java \
        -Dcom.sun.jndi.ldap.object.trustURLCodebase=true \
        -Dcom.sun.jndi.rmi.object.trustURLCodebase=true \
        -jar /app/audit-logger.jar &
    JAVA_PID=$!

    sleep 3

    echo "[start.sh] Starting Flask web application..."
    python3 /app/app.py

    kill $JNDI_PID $JAVA_PID 2>/dev/null || true
'
