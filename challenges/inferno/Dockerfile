FROM nginx:alpine

# Build arguments for flag injection
ARG FLAG1=DUNO{35c8761ee56e8e9be0e007372359c53b}
ARG FLAG2=DUNO{585f55d476046e2baf410aec24e5f67c}
ARG FLAG3=DUNO{43dc0ab5f66439fe1fdb95235d128c00}
ARG FLAG4=DUNO{3db0237a88449d6e6a86e7313e622335}
ARG FLAG5=DUNO{af292b8d8043bedf123a6c12e3a378c3}

WORKDIR /usr/share/nginx/html

# Copy all public files
COPY public/ .

# Copy fake_git as .git directory (exposed vulnerability)
# Using fake_git to avoid confusion with repo's actual .git
COPY fake_git/ .git/

# Inject flag values into static files
RUN sed -i "s/DUNO{35c8761ee56e8e9be0e007372359c53b}/${FLAG1}/g" app.js.map && \
    sed -i "s/DUNO{585f55d476046e2baf410aec24e5f67c}/${FLAG2}/g" app.js && \
    sed -i "s/DUNO{585f55d476046e2baf410aec24e5f67c}/${FLAG2}/g" app.js.map && \
    sed -i "s/DUNO{43dc0ab5f66439fe1fdb95235d128c00}/${FLAG3}/g" .git/logs/HEAD && \
    sed -i "s/DUNO{3db0237a88449d6e6a86e7313e622335}/${FLAG4}/g" .env && \
    sed -i "s/DUNO{af292b8d8043bedf123a6c12e3a378c3}/${FLAG5}/g" backup/config.bak

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
