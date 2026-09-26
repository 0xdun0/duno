#!/bin/bash
# Entrypoint for November (Drupalgeddon2 / CVE-2018-7600)
#
# Strategy: start Apache in background, drive the Drupal HTTP installer via
# curl (the official way), then bring Apache back to the foreground.
#
set -e

MARKER="/var/www/html/sites/default/files/.installed"
SETTINGS="/var/www/html/sites/default/settings.php"

if [ ! -f "$MARKER" ]; then
    echo "[*] First run: preparing Drupal 7..."

    # settings.php must exist before the installer can write to it
    if [ ! -f "$SETTINGS" ]; then
        cp /var/www/html/sites/default/default.settings.php "$SETTINGS"
        chmod 666 "$SETTINGS"
    fi

    # Start Apache in background so we can drive the HTTP installer
    echo "[*] Starting Apache temporarily..."
    apache2ctl start

    # Wait for Apache to be ready
    until curl -sf -o /dev/null http://localhost/; do
        echo "[*] Waiting for Apache..."
        sleep 2
    done
    echo "[+] Apache ready."

    echo "[*] Running Drupal installer via HTTP..."
    bash /install_via_http.sh

    # Stop background Apache — exec below will restart it properly
    apache2ctl stop 2>/dev/null || true
    sleep 1

    touch "$MARKER"
    echo "[+] Drupal installed. Starting Apache in foreground..."
fi

exec apache2-foreground "$@"
