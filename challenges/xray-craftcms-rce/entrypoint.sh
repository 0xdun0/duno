#!/bin/bash
# Entrypoint for Xray (CraftCMS CVE-2025-32432)
# Fixes .env DB config at runtime, installs CraftCMS, seeds test asset.
set -e

CRAFT_DIR="/var/www/html"
MARKER="${CRAFT_DIR}/storage/.ctf_installed"

if [ ! -f "$MARKER" ]; then
    echo "[xray] First run: configuring CraftCMS..."
    cd "$CRAFT_DIR"

    # The .env baked into the image has wrong DB settings (127.0.0.1, blank creds).
    # bootstrap.php uses createUnsafeMutable() so .env beats Docker env vars —
    # fix .env directly before any PHP runs.
    DB_SERVER="${CRAFT_DB_SERVER:-mysql}"
    DB_PORT="${CRAFT_DB_PORT:-3306}"
    DB_DATABASE="${CRAFT_DB_DATABASE:-craftcms}"
    DB_USER="${CRAFT_DB_USER:-craft}"
    DB_PASSWORD="${CRAFT_DB_PASSWORD:-CraftCMS_CTF_2026}"

    sed -i "s|^CRAFT_DB_SERVER=.*|CRAFT_DB_SERVER=${DB_SERVER}|"     .env
    sed -i "s|^CRAFT_DB_PORT=.*|CRAFT_DB_PORT=${DB_PORT}|"           .env
    sed -i "s|^CRAFT_DB_DATABASE=.*|CRAFT_DB_DATABASE=${DB_DATABASE}|" .env
    sed -i "s|^CRAFT_DB_USER=.*|CRAFT_DB_USER=${DB_USER}|"           .env
    sed -i "s|^CRAFT_DB_PASSWORD=.*|CRAFT_DB_PASSWORD=${DB_PASSWORD}|" .env
    echo "[xray] .env patched: DB_SERVER=${DB_SERVER} DB_DATABASE=${DB_DATABASE}"

    echo "[xray] Waiting for MySQL at ${DB_SERVER}:${DB_PORT}..."
    until php -r "
try {
    new PDO('mysql:host=${DB_SERVER};port=${DB_PORT};dbname=${DB_DATABASE}',
            '${DB_USER}', '${DB_PASSWORD}');
    exit(0);
} catch (Exception \$e) { exit(1); }
" 2>/dev/null; do
        echo "[xray] MySQL not ready yet, retrying..."
        sleep 3
    done
    echo "[xray] MySQL ready."

    echo "[xray] Installing CraftCMS..."
    php craft install \
        --interactive=0 \
        --email=admin@eversec.local \
        --username=admin \
        --password=admin123 \
        --site-name="EverSec Brand Portal" \
        --site-url="http://localhost" \
        --language=en-US
    echo "[xray] CraftCMS installed."

    echo "[xray] Seeding test asset (assetId=1 for exploit)..."
    php /seed_asset.php && echo "[xray] Asset seeded." \
        || echo "[xray] WARNING: Asset seeding failed — exploit may require manual upload."

    # php craft install and seed_asset.php run as root (entrypoint user),
    # creating storage/runtime subdirs owned by root. Apache runs as www-data
    # and must be able to write compiled_classes/, temp/, assets/, etc.
    chown -R www-data:www-data "${CRAFT_DIR}/storage"
    echo "[xray] Storage ownership fixed (www-data)."

    touch "$MARKER"
    echo "[xray] Setup complete. Starting Apache..."
fi

exec apache2-foreground "$@"
