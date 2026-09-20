FROM nginx:alpine

# Build arguments for flag injection
ARG FLAG1=s0urc3_m4ps_t3ll_s3cr3ts
ARG FLAG2=4p1_k3y_1n_s0urc3_c0d3
ARG FLAG3=g1t_h1st0ry_r3v34ls_s3cr3ts
ARG FLAG4=3nv_f1l3_s3cr3ts_3xp0s3d
ARG FLAG5=b4ckup_c0nf1g_l34k3d

WORKDIR /usr/share/nginx/html

# Copy all public files
COPY public/ .

# Copy fake_git as .git directory (exposed vulnerability)
# Using fake_git to avoid confusion with repo's actual .git
COPY fake_git/ .git/

# Inject flag values into static files
RUN sed -i "s/s0urc3_m4ps_t3ll_s3cr3ts/${FLAG1}/g" app.js.map && \
    sed -i "s/4p1_k3y_1n_s0urc3_c0d3/${FLAG2}/g" app.js && \
    sed -i "s/4p1_k3y_1n_s0urc3_c0d3/${FLAG2}/g" app.js.map && \
    sed -i "s/g1t_h1st0ry_r3v34ls_s3cr3ts/${FLAG3}/g" .git/logs/HEAD && \
    sed -i "s/3nv_f1l3_s3cr3ts_3xp0s3d/${FLAG4}/g" .env && \
    sed -i "s/b4ckup_c0nf1g_l34k3d/${FLAG5}/g" backup/config.bak

# Create nginx config to serve files including .git, .env, and backup/
RUN echo 'server {' > /etc/nginx/conf.d/default.conf && \
    echo '    listen 4004;' >> /etc/nginx/conf.d/default.conf && \
    echo '    server_name localhost;' >> /etc/nginx/conf.d/default.conf && \
    echo '    root /usr/share/nginx/html;' >> /etc/nginx/conf.d/default.conf && \
    echo '    index index.html;' >> /etc/nginx/conf.d/default.conf && \
    echo '' >> /etc/nginx/conf.d/default.conf && \
    echo '    location / {' >> /etc/nginx/conf.d/default.conf && \
    echo '        try_files $uri $uri/ =404;' >> /etc/nginx/conf.d/default.conf && \
    echo '    }' >> /etc/nginx/conf.d/default.conf && \
    echo '' >> /etc/nginx/conf.d/default.conf && \
    echo '    # Exposed .git directory (vulnerable - should be blocked in production)' >> /etc/nginx/conf.d/default.conf && \
    echo '    location ~ /\.git {' >> /etc/nginx/conf.d/default.conf && \
    echo '        autoindex on;' >> /etc/nginx/conf.d/default.conf && \
    echo '    }' >> /etc/nginx/conf.d/default.conf && \
    echo '' >> /etc/nginx/conf.d/default.conf && \
    echo '    # Exposed .env file (vulnerable - should be blocked in production)' >> /etc/nginx/conf.d/default.conf && \
    echo '    location ~ /\.env {' >> /etc/nginx/conf.d/default.conf && \
    echo '        default_type text/plain;' >> /etc/nginx/conf.d/default.conf && \
    echo '    }' >> /etc/nginx/conf.d/default.conf && \
    echo '' >> /etc/nginx/conf.d/default.conf && \
    echo '    # Expose source maps' >> /etc/nginx/conf.d/default.conf && \
    echo '    location ~ \.map$ {' >> /etc/nginx/conf.d/default.conf && \
    echo '        add_header Access-Control-Allow-Origin *;' >> /etc/nginx/conf.d/default.conf && \
    echo '    }' >> /etc/nginx/conf.d/default.conf && \
    echo '}' >> /etc/nginx/conf.d/default.conf

EXPOSE 4004

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://127.0.0.1:4004/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
