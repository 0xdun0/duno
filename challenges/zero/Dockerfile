# ============================================================
# Yankee - Log4Shell (CVE-2021-44228)
# EverSec Log Analysis Platform
#
# Multi-stage build:
#   Stage 1 (java-builder): Builds the vulnerable audit-logger JAR using Maven
#                           and compiles the exploit classes (FlagReader, PrivEsc)
#   Stage 2 (runtime):      Python 3.11-slim with Java 11 JRE
# ============================================================

# ------------------------------------------------------------
# Stage 1: Java build
# ------------------------------------------------------------
FROM maven:3.9-eclipse-temurin-11 AS java-builder

WORKDIR /build

# Copy Maven project and fetch dependencies in a cacheable layer
COPY audit_logger/pom.xml ./pom.xml
RUN mvn dependency:go-offline -q

# Build the fat JAR (log4j-core:2.14.1 + log4j-api:2.14.1 bundled)
COPY audit_logger/src ./src
RUN mvn package -q -DskipTests

# Compile the exploit classes standalone (no Maven package needed)
COPY exploit_classes/FlagReader.java ./FlagReader.java
COPY exploit_classes/PrivEsc.java ./PrivEsc.java
RUN javac FlagReader.java PrivEsc.java

# ------------------------------------------------------------
# Stage 2: Runtime
# ------------------------------------------------------------
FROM python:3.11-slim

# Install Java JRE and sudo (Java 11 bytecode compatible with Java 17+)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        default-jre-headless \
        sudo \
        curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Python dependencies
RUN pip install --no-cache-dir flask==3.0.0

# Create non-root application user
RUN useradd -m -u 1000 -s /bin/bash ctfuser

# Privilege escalation path for FLAG3:
# ctfuser can run python3 as root without a password (GTFOBins vector)
RUN echo "ctfuser ALL=(root) NOPASSWD: /usr/local/bin/python3" \
        > /etc/sudoers.d/ctfuser && \
    chmod 0440 /etc/sudoers.d/ctfuser

# Create application directories
RUN mkdir -p /app/classes /app/templates
WORKDIR /app

# Copy Java artifacts from builder stage
COPY --from=java-builder /build/target/audit-logger-2.0.0.jar /app/audit-logger.jar
COPY --from=java-builder /build/FlagReader.class /app/classes/FlagReader.class
COPY --from=java-builder /build/PrivEsc.class    /app/classes/PrivEsc.class

# Copy Python application
COPY app.py        /app/app.py
COPY jndi_server.py /app/jndi_server.py
COPY start.sh      /app/start.sh
COPY templates/    /app/templates/

# Set ownership and permissions
RUN chown -R ctfuser:ctfuser /app && \
    chmod +x /app/start.sh

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:4020/ || exit 1

EXPOSE 4020

# start.sh runs as root, writes FLAG3 to /root/flag3.txt, then drops to ctfuser
CMD ["/app/start.sh"]
