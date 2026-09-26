#!/bin/bash
# Drive the Drupal 7 web installer via curl, then apply post-install fixes
# so that CVE-2018-7600 (file/ajax exploit path) works for anonymous users.
# Called from entrypoint.sh after Apache is running.
set -e

BASE="http://localhost"
JAR="/tmp/drupal_cookies.txt"
DB_FILE="/var/www/html/sites/default/files/.ht.sqlite"
W="/tmp/d7_"   # working file prefix

echo "[*] Starting Drupal 7 HTTP install..." >&2

# Fetch page, save to file, return HTTP code
dfetch() {
    local method="$1" path="$2" out="$3" data="$4"
    if [ "$method" = "POST" ]; then
        curl -s -L -c "$JAR" -b "$JAR" \
             --max-redirs 10 --connect-timeout 10 --max-time 30 \
             -d "$data" -o "$out" -w "%{http_code}" "${BASE}${path}"
    else
        curl -s -L -c "$JAR" -b "$JAR" \
             --max-redirs 10 --connect-timeout 10 --max-time 30 \
             -o "$out" -w "%{http_code}" "${BASE}${path}"
    fi
}

# Extract a named hidden form field value from an HTML file
fval() { grep -o "name=\"${1}\" value=\"[^\"]*\"" "$2" 2>/dev/null | head -1 | sed 's/.*value="//;s/"//'; }

# ── Step 1: GET install.php ───────────────────────────────────────────────
echo "[*] GET install.php..." >&2
dfetch GET "/install.php" "${W}1.html" > /dev/null

# ── Step 2: POST profile = minimal ───────────────────────────────────────
echo "[*] POST profile=minimal..." >&2
FBid=$(fval form_build_id "${W}1.html")
FId=$(fval form_id "${W}1.html"); [ -z "$FId" ] && FId="install_select_profile_form"
dfetch POST "/install.php" "${W}2.html" \
    "profile=minimal&form_build_id=${FBid}&form_id=${FId}&op=Save+and+continue" > /dev/null

# ── Step 3: POST locale = en ──────────────────────────────────────────────
echo "[*] POST locale=en..." >&2
FBid=$(fval form_build_id "${W}2.html")
FId=$(fval form_id "${W}2.html"); [ -z "$FId" ] && FId="install_select_locale_form"
dfetch POST "/install.php?profile=minimal" "${W}3.html" \
    "locale=en&form_build_id=${FBid}&form_id=${FId}&op=Save+and+continue" > /dev/null

# ── Step 4: GET fresh DB config form (needs its own form_build_id) ────────
echo "[*] GET DB config form..." >&2
dfetch GET "/install.php?profile=minimal&locale=en" "${W}4.html" > /dev/null

# ── Step 5: POST SQLite database settings ────────────────────────────────
echo "[*] POST SQLite settings..." >&2
FBid=$(fval form_build_id "${W}4.html")
FId=$(fval form_id "${W}4.html"); [ -z "$FId" ] && FId="install_settings_form"
CODE=$(dfetch POST "/install.php?profile=minimal&locale=en" "${W}5.html" \
    "driver=sqlite&sqlite%5Bdatabase%5D=sites%2Fdefault%2Ffiles%2F.ht.sqlite&form_build_id=${FBid}&form_id=${FId}&op=Save+and+continue")
echo "[*] DB config POST → HTTP ${CODE}" >&2

# ── Step 6: Wait for module installation ─────────────────────────────────
echo "[*] Waiting for module install (up to 120s)..." >&2
for i in $(seq 1 40); do
    sleep 3
    dfetch GET "/install.php?profile=minimal&locale=en" "${W}6.html" > /dev/null
    if grep -qi "site name\|configure\|install_configure" "${W}6.html"; then
        echo "[+] Configure form ready after $((i * 3))s." >&2; break
    fi
    if grep -qi "congratulations\|successfully installed" "${W}6.html"; then
        echo "[+] Install already complete!" >&2; break
    fi
done

if ! grep -qi "site name\|configure\|install_configure\|congratulations\|successfully" "${W}6.html"; then
    echo "[!] Timed out waiting for configure form" >&2
    head -30 "${W}6.html" >&2; exit 1
fi

# ── Step 7: POST site configuration ──────────────────────────────────────
echo "[*] POST site config (admin / admin123!)..." >&2
FBid=$(fval form_build_id "${W}6.html")
FId=$(fval form_id "${W}6.html"); [ -z "$FId" ] && FId="install_configure_form"
dfetch POST "/install.php?profile=minimal&locale=en" "${W}7.html" \
    "site_name=EverSec+CMS&site_mail=admin%40eversec.local&account%5Bname%5D=admin&account%5Bmail%5D=admin%40eversec.local&account%5Bpass%5D%5Bpass1%5D=admin123%21&account%5Bpass%5D%5Bpass2%5D=admin123%21&update_status_module%5B1%5D=0&update_status_module%5B2%5D=0&clean_url=0&form_build_id=${FBid}&form_id=${FId}&op=Save+and+continue" \
    > /dev/null
sleep 2

# ── Verify DB exists ──────────────────────────────────────────────────────
if [ ! -f "$DB_FILE" ] || [ ! -s "$DB_FILE" ]; then
    echo "[!] DB file not found after install: $DB_FILE" >&2; exit 1
fi
echo "[+] DB created: $DB_FILE ($(wc -c < "$DB_FILE") bytes)" >&2

# ── Post-install fixes for CVE-2018-7600 exploit path ────────────────────
echo "[*] Applying post-install fixes..." >&2
cd /var/www/html && php -d error_reporting=0 << 'PHPEOF'
<?php
$_SERVER["REMOTE_ADDR"] = "127.0.0.1";
$_SERVER["HTTP_HOST"]   = "localhost";
define("DRUPAL_ROOT", getcwd());
require_once "includes/bootstrap.inc";

// Bootstrap only to DATABASE level first so we can update before caches load
drupal_bootstrap(DRUPAL_BOOTSTRAP_DATABASE);

// 1. Enable file module in DB
db_update("system")
  ->fields(array("status" => 1))
  ->condition("name", "file")
  ->execute();

// 2. Clear bootstrap cache so full bootstrap picks up the updated module list
db_delete("cache_bootstrap")->execute();
db_delete("cache")->execute();
db_delete("cache_menu")->execute();

// Now do a full bootstrap — it will see file module as enabled
drupal_bootstrap(DRUPAL_BOOTSTRAP_FULL);
echo "[*] file module enabled, caches cleared, full bootstrap done\n";

// 3. Rebuild the menu — file_menu() is now available
menu_rebuild();
$r = db_query("SELECT COUNT(*) FROM menu_router WHERE path = :p",
              array(":p" => "file/ajax"))->fetchField();
echo "[*] menu rebuilt — file/ajax routes: $r\n";

// 4. Grant anonymous users 'access content' (minimal profile omits this)
db_merge("role_permission")
  ->key(array("rid" => 1, "permission" => "access content", "module" => "node"))
  ->execute();
echo "[*] anonymous granted 'access content'\n";

// 5. Clear the rebuild-needed flag so Apache won't re-rebuild on first request
variable_set("menu_rebuild_needed", FALSE);
echo "[*] menu_rebuild_needed cleared\n";
PHPEOF

echo "[+] Post-install fixes applied." >&2
echo "[+] Drupal installation complete!" >&2
