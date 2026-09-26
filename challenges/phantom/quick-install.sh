#!/bin/bash
# Quick installation script for Drupalgeddon challenge
# This automates the Drupal installation wizard

set -e

CONTAINER="ctf-drupalgeddon"
URL="http://localhost:4009"

echo "[+] Drupalgeddon Quick Install Script"
echo "========================================"
echo ""

# Check if container is running
if ! docker ps | grep -q "$CONTAINER"; then
    echo "[!] Container $CONTAINER is not running"
    echo "[*] Starting container..."
    docker compose up -d drupalgeddon
    sleep 3
fi

echo "[*] Installing Drupal 7.57 via PHP CLI..."

# Execute installation directly in container
docker exec $CONTAINER bash -c 'cd /var/www/html && php -d error_reporting=0 << "EOPHP"
<?php
$_SERVER["HTTP_HOST"] = "localhost";
$_SERVER["REMOTE_ADDR"] = "127.0.0.1";
$_SERVER["REQUEST_METHOD"] = "POST";
$_SERVER["SCRIPT_NAME"] = "/install.php";

define("DRUPAL_ROOT", getcwd());
require_once DRUPAL_ROOT . "/includes/install.core.inc";

$settings = array(
    "parameters" => array(
        "profile" => "minimal",
        "locale" => "en",
    ),
    "forms" => array(
        "install_settings_form" => array(
            "driver" => "sqlite",
            "sqlite" => array(
                "database" => "sites/default/files/.ht.sqlite",
            ),
        ),
        "install_configure_form" => array(
            "site_name" => "EverSec CMS",
            "site_mail" => "admin@eversec.local",
            "account" => array(
                "name" => "admin",
                "mail" => "admin@eversec.local",
                "pass" => array(
                    "pass1" => "admin123!",
                    "pass2" => "admin123!",
                ),
            ),
            "update_status_module" => array(
                1 => FALSE,
                2 => FALSE,
            ),
            "clean_url" => FALSE,
        ),
    ),
);

try {
    install_drupal($settings);
    echo "Installation successful\n";
} catch (Exception $e) {
    echo "Installation completed with notices\n";
}
?>
EOPHP
' 2>&1 | grep -v "Notice:\|Warning:\|Deprecated:" || true

echo ""
echo "[+] Installation complete!"
echo ""
echo "Site URL: $URL"
echo "Username: admin"
echo "Password: admin123!"
echo ""
echo "[*] Testing access..."
RESPONSE=$(curl -sI "$URL" | head -1)
echo "$RESPONSE"

if echo "$RESPONSE" | grep -q "200\|302"; then
    echo ""
    echo "✓ Drupal is ready for exploitation!"
    echo ""
    echo "Next steps:"
    echo "  1. Access $URL"
    echo "  2. Follow the exploitation guide in README.md"
    echo "  3. Retrieve all 3 flags!"
else
    echo ""
    echo "[!] Installation may have issues. Check logs:"
    echo "    docker compose logs drupalgeddon"
fi
