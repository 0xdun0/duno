FROM php:8.3-apache

LABEL maintainer="EverSec CTF Team"

# Set environment variables for flags
ARG FLAG1=cr4ftcms_rc3_v14_xx3
ARG FLAG2=r00t_pr1v3sc_4ch13v3d

# Install PHP extensions and dependencies required by CraftCMS
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libjpeg62-turbo-dev \
        libpng-dev \
        libfreetype6-dev \
        libonig-dev \
        libicu-dev \
        libzip-dev \
        sudo \
        curl \
    && docker-php-ext-install bcmath gd mbstring pdo_mysql intl zip \
    && curl -#sSL -o /usr/local/bin/composer https://getcomposer.org/download/2.9.3/composer.phar \
    && chmod +x /usr/local/bin/composer \
    && rm -rf /var/lib/apt/lists/*

# Install CraftCMS 5.6.16 (vulnerable version)
RUN set -ex \
    && curl -#sSL https://github.com/craftcms/craft/archive/refs/tags/5.4.0.tar.gz | tar xz --strip-components=1 -C /var/www/html \
    && cd /var/www/html \
    && sed -i 's|"craftcms/cms": "^5.0.0"|"craftcms/cms": "5.6.16"|g' composer.json \
    && sed -i 's|"craftcms/cms": "^5.0.0"|"craftcms/cms": "5.6.16"|g' composer.json.default \
    && composer config audit.block-insecure false \
    && composer install --no-scripts \
    && mv .env.example.dev .env \
    && rm composer.json \
    && mv composer.json.default composer.json \
    && composer dump-autoload -o \
    && CRAFT_ALLOW_SUPERUSER=1 php craft setup --interactive 0 \
    && chown -R www-data:www-data /var/www/html \
    && sed -i 's|DocumentRoot /var/www/html|DocumentRoot /var/www/html/web|g' /etc/apache2/sites-enabled/000-default.conf \
    && a2enmod rewrite

# PHP configuration
RUN set -ex \
    && { \
        echo "max_execution_time = 300"; \
        echo "ignore_user_abort = On"; \
    } > /usr/local/etc/php/conf.d/overrides.ini

# Create FLAG 1 in www-data's home directory
# This flag is accessible after achieving RCE via CVE-2025-32432
RUN mkdir -p /var/www && \
    echo "${FLAG1}" > /var/www/flag1.txt && \
    chown www-data:www-data /var/www/flag1.txt && \
    chmod 644 /var/www/flag1.txt

# Create FLAG 2 in /flag.txt owned by root
# This flag requires privilege escalation to access
RUN echo "${FLAG2}" > /flag.txt && \
    chown root:root /flag.txt && \
    chmod 600 /flag.txt

# Set up privilege escalation vector: sudo with NOPASSWD for /usr/bin/find
# This is a common misconfiguration that allows privesc via GTFOBins
# www-data can run: sudo find /flag.txt -exec cat {} \;
RUN echo "www-data ALL=(root) NOPASSWD: /usr/bin/find" >> /etc/sudoers

# Verify the sudoers configuration is valid
RUN visudo -c

# Copy entrypoint and asset-seeding script
COPY entrypoint.sh /entrypoint.sh
COPY seed_asset.php /seed_asset.php
RUN chmod +x /entrypoint.sh

# Expose port 80
EXPOSE 80

# Use entrypoint to fix .env, install CraftCMS, and seed test asset on first boot
ENTRYPOINT ["/entrypoint.sh"]
