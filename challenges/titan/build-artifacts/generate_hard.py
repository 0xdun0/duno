#!/usr/bin/env python3
"""
Generate the Hard tier DFIR archive: "Exfil and Burn" (WS-FINANCE-01)
Produces romeo-hard-exfil-burn.tar.gz with realistic Volatility 3 output.

Flags:
  FLAG1: 1nj3ct3d_sh3llc0d3_x0r  (vol3-malfind.txt — XOR key 0x42)
  FLAG2: 3xf1l_4rch1v3_r3c0v3r3d (extracted/staging/data.b64 — base64 decode)
  FLAG3: t1m3st0mp_d3t3ct3d       (cross-reference timeliner vs mftparser)
  FLAG4: dns_3xf1l_r3c0nstruct3d  (extracted/dns_queries.pcap.txt — base32 subdomains)
"""

import os
import tarfile
import io
import base64
import struct

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'files')
ARCHIVE_NAME = 'romeo-hard-exfil-burn.tar.gz'

FLAG1 = '1nj3ct3d_sh3llc0d3_x0r'
FLAG2 = '3xf1l_4rch1v3_r3c0v3r3d'
FLAG3 = 't1m3st0mp_d3t3ct3d'
FLAG4 = 'dns_3xf1l_r3c0nstruct3d'

XOR_KEY = 0x42


def xor_encode(plaintext, key):
    """XOR encode a string and return hex representation."""
    encoded = bytes([b ^ key for b in plaintext.encode()])
    return encoded.hex()


def base32_encode_chunked(plaintext, chunk_size=5):
    """Encode plaintext as base32 and split into DNS-label-sized chunks."""
    encoded = base64.b32encode(plaintext.encode()).decode().rstrip('=').lower()
    return [encoded[i:i+chunk_size] for i in range(0, len(encoded), chunk_size)]


# ── XOR the flag for malfind output ──────────────────────────────────────────
FLAG1_XOR_HEX = xor_encode(FLAG1, XOR_KEY)

# ── Base32 chunks for DNS exfil ──────────────────────────────────────────────
FLAG4_CHUNKS = base32_encode_chunked(FLAG4, 8)

# ── Artifact content ──────────────────────────────────────────────────────────

README_ANALYST = """\
================================================================================
  EVERSEC INCIDENT RESPONSE — CASE #2026-0417
  Operation Midnight Raven — Day 3: "Exfil and Burn"
  Host: WS-FINANCE-01 (10.10.15.103)
  Analyst: M. Chen | Capture Time: 2026-03-17 09:15:00 UTC
================================================================================

SITUATION REPORT:
This is the final system compromised in the Operation Midnight Raven campaign.
WS-FINANCE-01 belongs to a senior financial analyst with access to quarterly
earnings reports, M&A documents, and payroll data.

The threat actor appears to have staged data for exfiltration and attempted
to cover their tracks using anti-forensics techniques. Memory was captured
before the attacker could fully clean up.

Volatility 3 plugins executed against the raw image:

  vol3-pslist.txt       Process listing
  vol3-pstree.txt       Process tree
  vol3-netscan.txt      Network connections
  vol3-malfind.txt      Injected code detection (suspicious memory regions)
  vol3-timeliner.txt    Combined timeline of system activity
  vol3-mftparser.txt    MFT (Master File Table) entries

Extracted artifacts:
  extracted/staging/data.b64         Base64 blob found in attacker staging dir
  extracted/dns_queries.pcap.txt     DNS query log from packet capture

YOUR OBJECTIVES:
  1. Analyze injected code regions — decode any obfuscated payloads
  2. Recover staged exfiltration data
  3. Detect anti-forensics activity (timestamp manipulation)
  4. Reconstruct covert data exfiltration channels

ANALYST NOTES:
  - The malfind output shows suspicious memory regions. The attacker uses
    single-byte XOR encoding (key unknown) on sensitive strings.
  - A base64 blob was recovered from C:\\Users\\j.park\\AppData\\Local\\Temp\\staging\\
  - DNS logs show unusual query patterns to a subdomain of exfil.midnightraven.net
  - Some file timestamps don't add up — compare timeliner and MFT data carefully

Submit flag values discovered during your analysis.
Good hunting.
"""

VOL3_PSLIST = """\
Volatility 3 Framework 2.5.2
Formatting...done.

PID\tPPID\tImageFileName\tOffset(V)\tThreads\tHandles\tSessionId\tWow64\tCreateTime\tExitTime
4\t0\tSystem\t0xfa8000c7a040\t112\t-\t-\tFalse\t2026-03-17 07:30:01.000000\tN/A
88\t4\tRegistry\t0xfa8000d12080\t4\t-\t-\tFalse\t2026-03-17 07:30:01.000000\tN/A
396\t4\tsmss.exe\t0xfa8001a42300\t2\t29\t-\tFalse\t2026-03-17 07:30:04.000000\tN/A
484\t476\tcsrss.exe\t0xfa8001b78340\t10\t458\t0\tFalse\t2026-03-17 07:30:06.000000\tN/A
560\t476\twininit.exe\t0xfa8001bc8080\t3\t75\t0\tFalse\t2026-03-17 07:30:07.000000\tN/A
568\t552\tcsrss.exe\t0xfa8001bd4300\t12\t398\t1\tFalse\t2026-03-17 07:30:07.000000\tN/A
616\t552\twinlogon.exe\t0xfa8001c15080\t5\t118\t1\tFalse\t2026-03-17 07:30:08.000000\tN/A
672\t560\tservices.exe\t0xfa8001c5a300\t8\t218\t0\tFalse\t2026-03-17 07:30:08.000000\tN/A
684\t560\tlsass.exe\t0xfa8001c64080\t7\t748\t0\tFalse\t2026-03-17 07:30:08.000000\tN/A
692\t560\tlsm.exe\t0xfa8001c6a300\t10\t142\t0\tFalse\t2026-03-17 07:30:08.000000\tN/A
788\t672\tsvchost.exe\t0xfa8001d0e300\t12\t358\t0\tFalse\t2026-03-17 07:30:10.000000\tN/A
860\t672\tsvchost.exe\t0xfa8001d62080\t8\t274\t0\tFalse\t2026-03-17 07:30:11.000000\tN/A
936\t672\tsvchost.exe\t0xfa8001da8340\t21\t515\t0\tFalse\t2026-03-17 07:30:12.000000\tN/A
1016\t672\tsvchost.exe\t0xfa8001dec300\t15\t462\t0\tFalse\t2026-03-17 07:30:13.000000\tN/A
1080\t672\tsvchost.exe\t0xfa8001e18080\t34\t968\t0\tFalse\t2026-03-17 07:30:14.000000\tN/A
1192\t672\tsvchost.exe\t0xfa8001e86300\t17\t494\t0\tFalse\t2026-03-17 07:30:15.000000\tN/A
1380\t672\tspoolsv.exe\t0xfa8001f4e340\t13\t275\t0\tFalse\t2026-03-17 07:30:17.000000\tN/A
1424\t672\tsvchost.exe\t0xfa8001f76080\t18\t302\t0\tFalse\t2026-03-17 07:30:17.000000\tN/A
1740\t672\tMsMpEng.exe\t0xfa800208e340\t22\t408\t0\tFalse\t2026-03-17 07:30:21.000000\tN/A
2520\t2496\texplorer.exe\t0xfa80023c6080\t36\t1098\t1\tFalse\t2026-03-17 07:31:42.000000\tN/A
2632\t2520\tvmtoolsd.exe\t0xfa8002442300\t8\t172\t1\tFalse\t2026-03-17 07:31:44.000000\tN/A
2720\t2520\tOUTLOOK.EXE\t0xfa800248e080\t32\t872\t1\tFalse\t2026-03-17 07:32:08.000000\tN/A
2864\t2520\tEXCEL.EXE\t0xfa8002522340\t18\t542\t1\tFalse\t2026-03-17 07:33:15.000000\tN/A
3008\t2520\tmsedge.exe\t0xfa80025be080\t38\t848\t1\tFalse\t2026-03-17 07:34:22.000000\tN/A
3184\t3008\tmsedge.exe\t0xfa800268e340\t8\t178\t1\tFalse\t2026-03-17 07:34:24.000000\tN/A
3516\t788\tWmiPrvSE.exe\t0xfa8002842080\t8\t198\t0\tFalse\t2026-03-17 08:02:44.000000\tN/A
3648\t788\tnotepad.exe\t0xfa800298a080\t1\t58\t1\tFalse\t2026-03-17 08:05:12.000000\tN/A
3824\t3516\tpowershell.exe\t0xfa8002a4e340\t14\t438\t0\tFalse\t2026-03-17 08:12:18.000000\tN/A
3952\t3824\tconhost.exe\t0xfa8002ae8080\t2\t44\t0\tFalse\t2026-03-17 08:12:19.000000\tN/A
4044\t3824\t7z.exe\t0xfa8002b52300\t1\t28\t0\tFalse\t2026-03-17 08:18:42.000000\t2026-03-17 08:18:44.000000
4128\t3824\tcertutil.exe\t0xfa8002bc2080\t1\t22\t0\tFalse\t2026-03-17 08:19:01.000000\t2026-03-17 08:19:02.000000
4264\t3824\tnslookup.exe\t0xfa8002c48340\t2\t38\t0\tFalse\t2026-03-17 08:22:15.000000\tN/A
4388\t3824\ttimestomp.exe\t0xfa8002cd2080\t1\t18\t0\tFalse\t2026-03-17 08:45:33.000000\t2026-03-17 08:45:34.000000
4456\t3824\tcmd.exe\t0xfa8002d18300\t1\t22\t0\tFalse\t2026-03-17 08:48:12.000000\tN/A
"""

VOL3_PSTREE = """\
Volatility 3 Framework 2.5.2
Formatting...done.

PID\tPPID\tImageFileName\tOffset(V)\tThreads\tHandles\tSessionId\tWow64\tCreateTime
4\t0\tSystem\t0xfa8000c7a040\t112\t-\t-\tFalse\t2026-03-17 07:30:01.000000
. 88\t4\tRegistry\t0xfa8000d12080\t4\t-\t-\tFalse\t2026-03-17 07:30:01.000000
. 396\t4\tsmss.exe\t0xfa8001a42300\t2\t29\t-\tFalse\t2026-03-17 07:30:04.000000
484\t476\tcsrss.exe\t0xfa8001b78340\t10\t458\t0\tFalse\t2026-03-17 07:30:06.000000
560\t476\twininit.exe\t0xfa8001bc8080\t3\t75\t0\tFalse\t2026-03-17 07:30:07.000000
.. 672\t560\tservices.exe\t0xfa8001c5a300\t8\t218\t0\tFalse\t2026-03-17 07:30:08.000000
... 788\t672\tsvchost.exe\t0xfa8001d0e300\t12\t358\t0\tFalse\t2026-03-17 07:30:10.000000
.... 3516\t788\tWmiPrvSE.exe\t0xfa8002842080\t8\t198\t0\tFalse\t2026-03-17 08:02:44.000000
..... 3824\t3516\tpowershell.exe\t0xfa8002a4e340\t14\t438\t0\tFalse\t2026-03-17 08:12:18.000000
...... 3952\t3824\tconhost.exe\t0xfa8002ae8080\t2\t44\t0\tFalse\t2026-03-17 08:12:19.000000
...... 4044\t3824\t7z.exe\t0xfa8002b52300\t1\t28\t0\tFalse\t2026-03-17 08:18:42.000000
...... 4128\t3824\tcertutil.exe\t0xfa8002bc2080\t1\t22\t0\tFalse\t2026-03-17 08:19:01.000000
...... 4264\t3824\tnslookup.exe\t0xfa8002c48340\t2\t38\t0\tFalse\t2026-03-17 08:22:15.000000
...... 4388\t3824\ttimestomp.exe\t0xfa8002cd2080\t1\t18\t0\tFalse\t2026-03-17 08:45:33.000000
...... 4456\t3824\tcmd.exe\t0xfa8002d18300\t1\t22\t0\tFalse\t2026-03-17 08:48:12.000000
.... 3648\t788\tnotepad.exe\t0xfa800298a080\t1\t58\t1\tFalse\t2026-03-17 08:05:12.000000
... 860\t672\tsvchost.exe\t0xfa8001d62080\t8\t274\t0\tFalse\t2026-03-17 07:30:11.000000
... 936\t672\tsvchost.exe\t0xfa8001da8340\t21\t515\t0\tFalse\t2026-03-17 07:30:12.000000
... 1016\t672\tsvchost.exe\t0xfa8001dec300\t15\t462\t0\tFalse\t2026-03-17 07:30:13.000000
... 1080\t672\tsvchost.exe\t0xfa8001e18080\t34\t968\t0\tFalse\t2026-03-17 07:30:14.000000
... 1192\t672\tsvchost.exe\t0xfa8001e86300\t17\t494\t0\tFalse\t2026-03-17 07:30:15.000000
... 1380\t672\tspoolsv.exe\t0xfa8001f4e340\t13\t275\t0\tFalse\t2026-03-17 07:30:17.000000
... 1424\t672\tsvchost.exe\t0xfa8001f76080\t18\t302\t0\tFalse\t2026-03-17 07:30:17.000000
... 1740\t672\tMsMpEng.exe\t0xfa800208e340\t22\t408\t0\tFalse\t2026-03-17 07:30:21.000000
.. 684\t560\tlsass.exe\t0xfa8001c64080\t7\t748\t0\tFalse\t2026-03-17 07:30:08.000000
.. 692\t560\tlsm.exe\t0xfa8001c6a300\t10\t142\t0\tFalse\t2026-03-17 07:30:08.000000
568\t552\tcsrss.exe\t0xfa8001bd4300\t12\t398\t1\tFalse\t2026-03-17 07:30:07.000000
616\t552\twinlogon.exe\t0xfa8001c15080\t5\t118\t1\tFalse\t2026-03-17 07:30:08.000000
2520\t2496\texplorer.exe\t0xfa80023c6080\t36\t1098\t1\tFalse\t2026-03-17 07:31:42.000000
. 2632\t2520\tvmtoolsd.exe\t0xfa8002442300\t8\t172\t1\tFalse\t2026-03-17 07:31:44.000000
. 2720\t2520\tOUTLOOK.EXE\t0xfa800248e080\t32\t872\t1\tFalse\t2026-03-17 07:32:08.000000
. 2864\t2520\tEXCEL.EXE\t0xfa8002522340\t18\t542\t1\tFalse\t2026-03-17 07:33:15.000000
. 3008\t2520\tmsedge.exe\t0xfa80025be080\t38\t848\t1\tFalse\t2026-03-17 07:34:22.000000
.. 3184\t3008\tmsedge.exe\t0xfa800268e340\t8\t178\t1\tFalse\t2026-03-17 07:34:24.000000
"""

VOL3_NETSCAN = """\
Volatility 3 Framework 2.5.2
Formatting...done.

Offset\tProto\tLocalAddr\tLocalPort\tForeignAddr\tForeignPort\tState\tPID\tOwner\tCreated
0xe80000842a20\tTCPv4\t0.0.0.0\t135\t0.0.0.0\t0\tLISTENING\t788\tsvchost.exe\t2026-03-17 07:30:10.000000
0xe80000856f50\tTCPv4\t0.0.0.0\t445\t0.0.0.0\t0\tLISTENING\t4\tSystem\t2026-03-17 07:30:01.000000
0xe80000862a20\tTCPv4\t0.0.0.0\t5985\t0.0.0.0\t0\tLISTENING\t4\tSystem\t2026-03-17 07:30:01.000000
0xe80000894f50\tTCPv4\t10.10.15.103\t139\t0.0.0.0\t0\tLISTENING\t4\tSystem\t2026-03-17 07:30:01.000000
0xe800008a2a20\tTCPv4\t10.10.15.103\t49412\t185.141.27.93\t443\tESTABLISHED\t3824\tpowershell.exe\t2026-03-17 08:12:22.000000
0xe800008b4f50\tTCPv4\t10.10.15.103\t50201\t40.126.32.140\t443\tESTABLISHED\t2720\tOUTLOOK.EXE\t2026-03-17 07:32:14.000000
0xe800008c6a20\tTCPv4\t10.10.15.103\t50202\t13.107.42.14\t443\tESTABLISHED\t3008\tmsedge.exe\t2026-03-17 07:34:28.000000
0xe80000912f50\tTCPv4\t10.10.15.103\t50318\t10.10.15.77\t445\tCLOSE_WAIT\t4\tSystem\t2026-03-17 08:08:12.000000
0xe80000934a20\tUDPv4\t10.10.15.103\t53214\t91.215.85.120\t53\tN/A\t4264\tnslookup.exe\t2026-03-17 08:22:15.000000
0xe80000948f50\tUDPv4\t0.0.0.0\t5355\t*\t0\t\t1192\tsvchost.exe\t2026-03-17 07:30:15.000000
0xe80000962a20\tUDPv4\t10.10.15.103\t137\t*\t0\t\t4\tSystem\t2026-03-17 07:30:01.000000
0xe80000978f50\tUDPv4\t10.10.15.103\t138\t*\t0\t\t4\tSystem\t2026-03-17 07:30:01.000000
"""

# ── Malfind: XOR-encoded FLAG1 in injected shellcode region ──────────────────
# Build realistic hex dump with the XOR'd flag embedded in the shellcode
def build_malfind():
    # Pre-shellcode bytes (realistic x86 NOP sled + setup)
    pre_bytes = bytes([
        0x90, 0x90, 0x90, 0x90,  # NOP sled
        0x55,                     # push ebp
        0x89, 0xe5,               # mov ebp, esp
        0x83, 0xec, 0x20,         # sub esp, 0x20
        0x31, 0xc0,               # xor eax, eax
        0x50,                     # push eax
        0x68, 0x2f, 0x2f, 0x73, 0x68,  # push "//sh"
        0x68, 0x2f, 0x62, 0x69, 0x6e,  # push "/bin"
        0xb0, 0x0b,               # mov al, 0x0b
        0x89, 0xe3,               # mov ebx, esp
        0xcd, 0x80,               # int 0x80
    ])

    # XOR-encoded flag
    xor_bytes = bytes([b ^ XOR_KEY for b in FLAG1.encode()])

    # Post-shellcode bytes
    post_bytes = bytes([
        0x00, 0x00, 0x00, 0x00,
        0xc3,                     # ret
        0x90, 0x90, 0x90, 0x90,
        0x00, 0x00, 0x00, 0x00,
        0xff, 0xff, 0xff, 0xff,
    ])

    all_bytes = pre_bytes + xor_bytes + post_bytes

    # Format as Volatility 3 malfind hex dump
    lines = []
    base_addr = 0x00400000
    for i in range(0, len(all_bytes), 16):
        chunk = all_bytes[i:i+16]
        hex_part = ' '.join(f'{b:02x}' for b in chunk)
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        lines.append(f'0x{base_addr + i:08x}  {hex_part:<48s}  {ascii_part}')

    return '\n'.join(lines)


SHELLCODE_HEX_DUMP = build_malfind()

VOL3_MALFIND = f"""\
Volatility 3 Framework 2.5.2
Formatting...done.

PID\tProcess\tStart VPN\tEnd VPN\tTag\tProtection\tCommitCharge\tPrivateMemory\tFile output\tHexdump\tDisasm

3824\tpowershell.exe\t0x00400000\t0x00401000\tVadS\tPAGE_EXECUTE_READWRITE\t1\t1\tDisabled

Process: powershell.exe (PID 3824)
  Address: 0x00400000 - 0x00401000
  Protection: PAGE_EXECUTE_READWRITE
  Tag: VadS (Private Memory)
  Flags: CommitCharge: 1, PrivateMemory: 1

  NOTE: PAGE_EXECUTE_READWRITE on private memory is a strong indicator of
  injected code. Legitimate code sections are typically PAGE_EXECUTE_READ.

  Hex dump:

{SHELLCODE_HEX_DUMP}

  XOR analysis hint: Single-byte XOR encoding detected in region 0x0040001d-0x00400032.
  Common XOR keys for this threat actor: 0x41, 0x42, 0x43, 0x55, 0xAA, 0xFF


4264\tnslookup.exe\t0x00410000\t0x00411000\tVadS\tPAGE_EXECUTE_READWRITE\t1\t1\tDisabled

Process: nslookup.exe (PID 4264)
  Address: 0x00410000 - 0x00411000
  Protection: PAGE_EXECUTE_READWRITE
  Tag: VadS (Private Memory)
  Flags: CommitCharge: 1, PrivateMemory: 1

  Hex dump:

0x00410000  48 8b 05 00 00 00 00 48  89 c1 ff 15 00 00 00 00  H......H........
0x00410010  48 83 c4 28 c3 90 90 90  90 90 90 90 90 90 90 90  H..(...........
0x00410020  00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  ................
0x00410030  00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  ................
"""

# ── Base64 blob for FLAG2 ────────────────────────────────────────────────────
# Simulates a 7z archive listing that was base64-encoded for staging
ARCHIVE_LISTING = f"""\
7-Zip [64] 21.07 : Copyright (c) 1999-2021 Igor Pavlov : 2021-12-26

Listing archive: C:\\Users\\j.park\\AppData\\Local\\Temp\\staging\\exfil_data.7z

   Date      Time    Attr         Size   Compressed  Name
------------------- ----- ------------ ------------  ------------------------
2026-03-17 08:15:22 ....A       284672       142336  quarterly_earnings_q1_2026.xlsx
2026-03-17 08:15:22 ....A       512000       256000  ma_target_valuation.xlsx
2026-03-17 08:15:22 ....A       148992        74496  payroll_summary_march.csv
2026-03-17 08:15:22 ....A        62208        31104  board_meeting_notes_draft.docx
2026-03-17 08:15:22 ....A           24           24  {FLAG2}
2026-03-17 08:15:22 ....A       892416       446208  investor_presentation_v3.pptx
------------------- ----- ------------ ------------  ------------------------
2026-03-17 08:15:22            1900312       950168  6 files
"""

DATA_B64 = base64.b64encode(ARCHIVE_LISTING.encode()).decode()
# Wrap at 76 chars like real base64 output
DATA_B64_WRAPPED = '\n'.join(DATA_B64[i:i+76] for i in range(0, len(DATA_B64), 76))

# ── Timeline and MFT for FLAG3 (timestomping detection) ─────────────────────

VOL3_TIMELINER = """\
Volatility 3 Framework 2.5.2
Formatting...done.

Created\tModified\tAccessed\tChanged\tSource\tType\tDescription
2026-03-17 07:30:01.000000\t2026-03-17 07:30:01.000000\t2026-03-17 07:30:01.000000\t2026-03-17 07:30:01.000000\tPETimeDateStamp\tTimeliner\tPE Creation\tSystem (4)
2026-03-17 07:30:04.000000\t2026-03-17 07:30:04.000000\t2026-03-17 07:30:04.000000\t2026-03-17 07:30:04.000000\tProcess\tTimeliner\tsmss.exe (396) created
2026-03-17 07:30:06.000000\t2026-03-17 07:30:06.000000\t2026-03-17 07:30:06.000000\t2026-03-17 07:30:06.000000\tProcess\tTimeliner\tcsrss.exe (484) created
2026-03-17 07:30:08.000000\t2026-03-17 07:30:08.000000\t2026-03-17 07:30:08.000000\t2026-03-17 07:30:08.000000\tProcess\tTimeliner\tservices.exe (672) created
2026-03-17 07:30:08.000000\t2026-03-17 07:30:08.000000\t2026-03-17 07:30:08.000000\t2026-03-17 07:30:08.000000\tProcess\tTimeliner\tlsass.exe (684) created
2026-03-17 07:31:42.000000\t2026-03-17 07:31:42.000000\t2026-03-17 07:31:42.000000\t2026-03-17 07:31:42.000000\tProcess\tTimeliner\texplorer.exe (2520) created
2026-03-17 07:32:08.000000\t2026-03-17 07:32:08.000000\t2026-03-17 07:32:08.000000\t2026-03-17 07:32:08.000000\tProcess\tTimeliner\tOUTLOOK.EXE (2720) created
2026-03-17 07:33:15.000000\t2026-03-17 07:33:15.000000\t2026-03-17 07:33:15.000000\t2026-03-17 07:33:15.000000\tProcess\tTimeliner\tEXCEL.EXE (2864) created
2026-03-17 08:02:44.000000\t2026-03-17 08:02:44.000000\t2026-03-17 08:02:44.000000\t2026-03-17 08:02:44.000000\tProcess\tTimeliner\tWmiPrvSE.exe (3516) created
2026-03-17 08:12:18.000000\t2026-03-17 08:12:18.000000\t2026-03-17 08:12:18.000000\t2026-03-17 08:12:18.000000\tProcess\tTimeliner\tpowershell.exe (3824) created
2026-03-17 08:18:42.000000\t2026-03-17 08:18:42.000000\t2026-03-17 08:18:42.000000\t2026-03-17 08:18:42.000000\tProcess\tTimeliner\t7z.exe (4044) created
2026-03-17 08:19:01.000000\t2026-03-17 08:19:01.000000\t2026-03-17 08:19:01.000000\t2026-03-17 08:19:01.000000\tProcess\tTimeliner\tcertutil.exe (4128) created
2026-03-17 08:22:15.000000\t2026-03-17 08:22:15.000000\t2026-03-17 08:22:15.000000\t2026-03-17 08:22:15.000000\tProcess\tTimeliner\tnslookup.exe (4264) created
2026-03-17 08:45:33.000000\t2026-03-17 08:45:33.000000\t2026-03-17 08:45:33.000000\t2026-03-17 08:45:33.000000\tProcess\tTimeliner\ttimestomp.exe (4388) created
2026-03-17 08:48:12.000000\t2026-03-17 08:48:12.000000\t2026-03-17 08:48:12.000000\t2026-03-17 08:48:12.000000\tProcess\tTimeliner\tcmd.exe (4456) created
2026-01-15 10:22:14.000000\t2026-01-15 10:22:14.000000\t2026-01-15 10:22:14.000000\t2026-01-15 10:22:14.000000\tFile\tTimeliner\tC:\\Windows\\System32\\drivers\\""" + FLAG3 + """.sys
2026-03-17 07:30:10.000000\t2026-03-17 07:30:10.000000\t2026-03-17 07:30:10.000000\t2026-03-17 07:30:10.000000\tFile\tTimeliner\tC:\\Windows\\System32\\svchost.exe
2026-03-17 07:30:08.000000\t2026-03-17 07:30:08.000000\t2026-03-17 07:30:08.000000\t2026-03-17 07:30:08.000000\tFile\tTimeliner\tC:\\Windows\\System32\\lsass.exe
2026-03-17 08:15:22.000000\t2026-03-17 08:15:22.000000\t2026-03-17 08:15:22.000000\t2026-03-17 08:15:22.000000\tFile\tTimeliner\tC:\\Users\\j.park\\AppData\\Local\\Temp\\staging\\exfil_data.7z
"""

VOL3_MFTPARSER = """\
Volatility 3 Framework 2.5.2
Formatting...done.

MFT Entry\tAttribute\tRecord Type\tRecord Number\tLink count\tCreated\tModified\tMFT Modified\tAccessed\tFilename
48231\t$FILE_NAME\t0x30\t48231\t1\t2026-03-17 07:30:10.000000\t2026-03-17 07:30:10.000000\t2026-03-17 07:30:10.000000\t2026-03-17 07:30:10.000000\tWindows\\System32\\svchost.exe
48232\t$STANDARD_INFORMATION\t0x10\t48232\t1\t2026-03-17 07:30:10.000000\t2026-03-17 07:30:10.000000\t2026-03-17 07:30:10.000000\t2026-03-17 07:30:10.000000\tWindows\\System32\\svchost.exe
51847\t$FILE_NAME\t0x30\t51847\t1\t2026-03-17 07:30:08.000000\t2026-03-17 07:30:08.000000\t2026-03-17 07:30:08.000000\t2026-03-17 07:30:08.000000\tWindows\\System32\\lsass.exe
51848\t$STANDARD_INFORMATION\t0x10\t51848\t1\t2026-03-17 07:30:08.000000\t2026-03-17 07:30:08.000000\t2026-03-17 07:30:08.000000\t2026-03-17 07:30:08.000000\tWindows\\System32\\lsass.exe
62104\t$FILE_NAME\t0x30\t62104\t1\t2026-03-17 08:45:18.000000\t2026-03-17 08:45:18.000000\t2026-03-17 08:45:18.000000\t2026-03-17 08:45:18.000000\tWindows\\System32\\drivers\\""" + FLAG3 + """.sys
62105\t$STANDARD_INFORMATION\t0x10\t62105\t1\t2026-01-15 10:22:14.000000\t2026-01-15 10:22:14.000000\t2026-03-17 08:45:18.000000\t2026-01-15 10:22:14.000000\tWindows\\System32\\drivers\\""" + FLAG3 + """.sys
73218\t$FILE_NAME\t0x30\t73218\t1\t2026-03-17 08:15:22.000000\t2026-03-17 08:15:22.000000\t2026-03-17 08:15:22.000000\t2026-03-17 08:15:22.000000\tUsers\\j.park\\AppData\\Local\\Temp\\staging\\exfil_data.7z
73219\t$STANDARD_INFORMATION\t0x10\t73219\t1\t2026-03-17 08:15:22.000000\t2026-03-17 08:15:22.000000\t2026-03-17 08:15:22.000000\t2026-03-17 08:15:22.000000\tUsers\\j.park\\AppData\\Local\\Temp\\staging\\exfil_data.7z
48901\t$FILE_NAME\t0x30\t48901\t1\t2026-03-17 07:30:01.000000\t2026-03-17 07:30:01.000000\t2026-03-17 07:30:01.000000\t2026-03-17 07:30:01.000000\tWindows\\System32\\ntoskrnl.exe
48902\t$STANDARD_INFORMATION\t0x10\t48902\t1\t2026-03-17 07:30:01.000000\t2026-03-17 07:30:01.000000\t2026-03-17 07:30:01.000000\t2026-03-17 07:30:01.000000\tWindows\\System32\\ntoskrnl.exe
"""

# ── DNS exfiltration log for FLAG4 ───────────────────────────────────────────

def build_dns_log():
    """Build DNS query log with base32-encoded flag in subdomains."""
    lines = []
    lines.append('# DNS query log extracted from packet capture')
    lines.append('# Source: WS-FINANCE-01 (10.10.15.103)')
    lines.append('# Capture period: 2026-03-17 08:22:15 - 2026-03-17 08:38:42')
    lines.append('# Format: Timestamp | Source | Query | Type | Response')
    lines.append('#' + '-' * 90)
    lines.append('')

    # Normal DNS queries first
    normal_queries = [
        ('2026-03-17 08:22:15.124', '10.10.15.103', 'outlook.office365.com', 'A', '52.96.86.18'),
        ('2026-03-17 08:22:16.342', '10.10.15.103', 'login.microsoftonline.com', 'A', '40.126.32.140'),
        ('2026-03-17 08:22:18.891', '10.10.15.103', 'edge.microsoft.com', 'A', '13.107.42.14'),
        ('2026-03-17 08:22:22.445', '10.10.15.103', 'dc-eversec-01.eversec.local', 'A', '10.10.15.10'),
        ('2026-03-17 08:22:25.112', '10.10.15.103', 'fileserver.eversec.local', 'A', '10.10.15.20'),
    ]

    for ts, src, query, qtype, resp in normal_queries:
        lines.append(f'{ts} | {src} | {query} | {qtype} | {resp}')

    lines.append('')
    lines.append('# --- Unusual query pattern begins below ---')
    lines.append('# Note: All queries below resolve to the same external DNS server (91.215.85.120)')
    lines.append('# The subdomain labels appear to be encoded data')
    lines.append('')

    # Base32-encoded flag chunks as DNS subdomains
    base_time = 1710665000  # Epoch for 2026-03-17 08:23:xx
    for i, chunk in enumerate(FLAG4_CHUNKS):
        ts_sec = base_time + (i * 3) + 20  # 3 seconds apart
        import datetime
        dt = datetime.datetime(2026, 3, 17, 8, 23 + (i * 3) // 60, (20 + i * 3) % 60, 0)
        ts = dt.strftime('%Y-%m-%d %H:%M:%S') + f'.{(i * 127 + 342) % 1000:03d}'
        query = f'{chunk}.{i:02d}.exfil.midnightraven.net'
        lines.append(f'{ts} | 10.10.15.103 | {query} | TXT | NOERROR')

    lines.append('')

    # More normal queries after
    post_queries = [
        ('2026-03-17 08:35:12.667', '10.10.15.103', 'time.windows.com', 'A', '168.61.215.74'),
        ('2026-03-17 08:36:44.221', '10.10.15.103', 'wpad.eversec.local', 'A', 'NXDOMAIN'),
        ('2026-03-17 08:38:01.889', '10.10.15.103', 'dc-eversec-01.eversec.local', 'A', '10.10.15.10'),
        ('2026-03-17 08:38:42.112', '10.10.15.103', 'update.microsoft.com', 'A', '13.107.4.52'),
    ]

    for ts, src, query, qtype, resp in post_queries:
        lines.append(f'{ts} | {src} | {query} | {qtype} | {resp}')

    return '\n'.join(lines)


DNS_QUERIES = build_dns_log()


def add_file(tar, name, content):
    """Add a text file to the tar archive."""
    data = content.encode('utf-8')
    info = tarfile.TarInfo(name=name)
    info.size = len(data)
    tar.addfile(info, io.BytesIO(data))


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, ARCHIVE_NAME)

    prefix = 'romeo-hard-exfil-burn'

    with tarfile.open(output_path, 'w:gz') as tar:
        add_file(tar, f'{prefix}/README-ANALYST.txt', README_ANALYST)
        add_file(tar, f'{prefix}/vol3-pslist.txt', VOL3_PSLIST)
        add_file(tar, f'{prefix}/vol3-pstree.txt', VOL3_PSTREE)
        add_file(tar, f'{prefix}/vol3-netscan.txt', VOL3_NETSCAN)
        add_file(tar, f'{prefix}/vol3-malfind.txt', VOL3_MALFIND)
        add_file(tar, f'{prefix}/vol3-timeliner.txt', VOL3_TIMELINER)
        add_file(tar, f'{prefix}/vol3-mftparser.txt', VOL3_MFTPARSER)
        add_file(tar, f'{prefix}/extracted/staging/data.b64', DATA_B64)
        add_file(tar, f'{prefix}/extracted/dns_queries.pcap.txt', DNS_QUERIES)

    print(f'[+] Created {output_path}')
    print(f'    Files: 9')
    print(f'    Size: {os.path.getsize(output_path):,} bytes')
    print()
    print('Flags embedded:')
    print(f'  FLAG1: {FLAG1}  (vol3-malfind.txt — XOR decode with key 0x42)')
    print(f'  FLAG2: {FLAG2}  (extracted/staging/data.b64 — base64 decode, find filename)')
    print(f'  FLAG3: {FLAG3}  (timeliner vs mftparser — timestomped .sys file)')
    print(f'  FLAG4: {FLAG4}  (dns_queries.pcap.txt — base32 decode subdomains)')
    print()

    # Verification
    print('Verification:')
    xor_decoded = ''.join(chr(b ^ XOR_KEY) for b in bytes.fromhex(FLAG1_XOR_HEX))
    print(f'  FLAG1 XOR verify: {xor_decoded}')

    import base64 as b64
    decoded_listing = b64.b64decode(DATA_B64).decode()
    if FLAG2 in decoded_listing:
        print(f'  FLAG2 b64 verify: found in decoded listing')

    print(f'  FLAG3 timestomp: timeliner shows 2026-01-15, mftparser $FILE_NAME shows 2026-03-17 08:45:18')

    reconstructed = ''.join(FLAG4_CHUNKS)
    # Pad for base32
    padding = (8 - len(reconstructed) % 8) % 8
    decoded = base64.b32decode(reconstructed.upper() + '=' * padding).decode()
    print(f'  FLAG4 DNS verify: {decoded}')


if __name__ == '__main__':
    main()
