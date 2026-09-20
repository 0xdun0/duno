"""
EverSec Log Analysis Platform
Yankee - Log4Shell (CVE-2021-44228) CTF Challenge

Architecture:
  - This Flask app is the player-facing web interface.
  - All HTTP requests forward user-controlled headers (X-Forwarded-For, User-Agent)
    and search queries to the internal Java audit logger (localhost:8080).
  - The Java logger uses Log4j 2.14.1, which is vulnerable to CVE-2021-44228.
  - An internal JNDI/LDAP server (localhost:1389) and HTTP exploit server
    (localhost:9999) are managed by jndi_server.py.
"""
import os
import json
import urllib.request
import urllib.error
from flask import Flask, render_template, request, jsonify, Response

app = Flask(__name__)

FLAG1 = os.environ.get('FLAG1', 'dev_flag1')
FLAG2 = os.environ.get('FLAG2', 'dev_flag2')


def write_flag_files():
    """Write FLAG2 at startup from env var. FLAG3 is baked into /root/ at build time."""
    try:
        with open('/app/flag2.txt', 'w') as f:
            f.write(FLAG2)
    except Exception as e:
        print(f'[app] Warning: could not write flag2.txt: {e}')


def proxy_to_audit_logger(xff=None, ua=None, query=None):
    """
    Forward user inputs to the vulnerable Java audit logger on localhost:8080.
    The logger passes these values to Log4j, which evaluates ${jndi:...} expressions.
    """
    payload = {}
    if xff:   payload['xff']   = xff
    if ua:    payload['ua']    = ua
    if query: payload['query'] = query
    if not payload:
        return

    try:
        data = json.dumps(payload, separators=(',', ':')).encode()
        req  = urllib.request.Request(
            'http://127.0.0.1:8080/log',
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        app.logger.debug(f'Audit logger call failed: {e}')


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    xff = request.headers.get('X-Forwarded-For', '')
    ua  = request.headers.get('User-Agent', '')
    proxy_to_audit_logger(xff=xff, ua=ua)
    return render_template('index.html')


@app.route('/search')
def search():
    query = request.args.get('q', '')
    xff   = request.headers.get('X-Forwarded-For', '')
    ua    = request.headers.get('User-Agent', '')
    proxy_to_audit_logger(xff=xff, ua=ua, query=query)

    # Mock search results — cosmetic only
    results = []
    if query:
        results = [
            {'time': '2026-04-07 09:12:03', 'level': 'WARN',
             'event': 'Multiple failed auth attempts from 10.0.1.47 (SSH brute force suspected)'},
            {'time': '2026-04-07 09:14:51', 'level': 'INFO',
             'event': 'Service restarted: reverse-proxy (pid 14421)'},
            {'time': '2026-04-07 09:21:38', 'level': 'CRIT',
             'event': 'Firewall policy violation — 1,204 packets dropped (dst 0.0.0.0/0 port 445)'},
            {'time': '2026-04-07 09:33:17', 'level': 'WARN',
             'event': 'Unusual outbound connection from WORKSTATION-07 to 185.220.101.x'},
        ]
    return render_template('search.html', query=query, results=results)


@app.route('/robots.txt')
def robots():
    content = (
        'User-agent: *\n'
        'Disallow: /debug/log-preview\n'
        'Disallow: /internal/callbacks\n'
        'Disallow: /internal/diagnostic-output\n'
    )
    return Response(content, mimetype='text/plain')


@app.route('/api/status')
def api_status():
    return jsonify({
        'service':       'EverSec Log Analysis Platform',
        'version':       '2.0.0',
        'audit_backend': 'Apache Log4j 2.14.1',
        'status':        'operational',
        'uptime':        'running',
    })


@app.route('/debug/log-preview')
def log_preview():
    """
    Shows recent Java audit log lines.
    Players use this to confirm which inputs are being logged (the discovery step).
    """
    logs = []
    try:
        req = urllib.request.Request('http://127.0.0.1:8080/log-preview')
        with urllib.request.urlopen(req, timeout=5) as resp:
            logs = json.loads(resp.read())
    except Exception:
        logs = ['[Audit logger initializing — try again in a moment]']
    return render_template('log_preview.html', logs=logs)


@app.route('/internal/callbacks')
def jndi_log():
    """
    Shows recent callbacks received by the internal audit service.
    FLAG1 appears here when a ${jndi:...} payload triggers a callback.
    Auto-clears every 3 minutes.
    """
    data = {'entries': [], 'next_clear': 'unknown', 'last_cleared': 'unknown'}
    try:
        req = urllib.request.Request('http://127.0.0.1:9999/callbacks')
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
    except Exception:
        pass
    return render_template('jndi_log.html', data=data)


@app.route('/internal/diagnostic-output')
def rce_log():
    """
    Shows diagnostic output collected by the audit service.
    FLAG2 (FlagReader) and FLAG3 (PrivEsc) appear here after class loading.
    Auto-clears every 3 minutes.
    """
    data = {'entries': [], 'next_clear': 'unknown', 'last_cleared': 'unknown'}
    try:
        req = urllib.request.Request('http://127.0.0.1:9999/rce-outputs')
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
    except Exception:
        pass
    return render_template('rce_log.html', data=data)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    write_flag_files()
    app.run(host='0.0.0.0', port=4020, debug=False)
