FROM python:3.11-alpine

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY templates/ templates/
COPY static/ static/

# Set flags as environment variables
ARG FLAG1=1d0r_bur1ed_tr34sur3
ARG FLAG2=3num3r4t3_4ll_th3_th1ngs
ARG FLAG3=d3l3t3d_but_n0t_g0n3
ARG FLAG4=1d0r_us3r_pr0f1l3_pwn3d
ENV FLAG1=${FLAG1}
ENV FLAG2=${FLAG2}
ENV FLAG3=${FLAG3}
ENV FLAG4=${FLAG4}

# Run as non-root user
RUN adduser -D -u 1000 ctfuser && \
    chown -R ctfuser:ctfuser /app
USER ctfuser

# Expose port
EXPOSE 4001

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:4001/login').read()" || exit 1

# Run the application
CMD ["python", "app.py"]
