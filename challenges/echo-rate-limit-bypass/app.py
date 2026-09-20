from flask import Flask, request, jsonify, render_template
from datetime import datetime, timedelta
import os
import subprocess

app = Flask(__name__)

# Simple in-memory rate limiting storage
# Format: {ip_address: [timestamp1, timestamp2, ...]}
rate_limit_storage = {}

# Configuration
RATE_LIMIT = 5  # requests per window
RATE_WINDOW = 60  # seconds
CORRECT_PIN = "7394"  # 4-digit PIN for the challenge

# Flags loaded from environment only (not hardcoded to prevent leakage via path traversal)
FLAG1 = os.environ.get('FLAG1', 'test_flag1')
FLAG2 = os.environ.get('FLAG2', 'test_flag2')

# Authenticated sessions (simple token store)
auth_tokens = {}

def get_client_ip():
    """
    Get client IP address, checking X-Forwarded-For header first.
    This is the vulnerability - we trust the X-Forwarded-For header!
    """
    # VULNERABLE: Trusting X-Forwarded-For without validation
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        # Take the first IP in the list
        return forwarded_for.split(',')[0].strip()

    # Fall back to actual remote address
    return request.remote_addr

def is_rate_limited(ip):
    """
    Check if the IP address has exceeded the rate limit.
    Returns True if rate limited, False otherwise.
    """
    now = datetime.now()

    # Clean up old entries for this IP
    if ip in rate_limit_storage:
        rate_limit_storage[ip] = [
            ts for ts in rate_limit_storage[ip]
            if now - ts < timedelta(seconds=RATE_WINDOW)
        ]
    else:
        rate_limit_storage[ip] = []

    # Check if rate limit exceeded
    if len(rate_limit_storage[ip]) >= RATE_LIMIT:
        return True

    # Add current timestamp
    rate_limit_storage[ip].append(now)
    return False

@app.route('/')
def index():
    """Serve the main page with API documentation."""
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    """
    Login API endpoint with rate limiting.
    Expects JSON: {"pin": "1234"}
    """
    client_ip = get_client_ip()

    # Check rate limit
    if is_rate_limited(client_ip):
        return jsonify({
            'success': False,
            'error': 'Rate limit exceeded. Too many requests from your IP. Try again in 60 seconds.',
            'source_ip': client_ip
        }), 429

    # Get PIN from request
    data = request.get_json()
    if not data or 'pin' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing PIN in request body'
        }), 400

    pin = str(data['pin'])

    # Check if PIN is correct
    if pin == CORRECT_PIN:
        import secrets
        token = secrets.token_hex(16)
        auth_tokens[token] = {'ip': client_ip, 'authenticated': True}
        return jsonify({
            'success': True,
            'message': 'Authentication successful!',
            'flag': FLAG1,
            'token': token,
            'attempts_from_ip': len(rate_limit_storage.get(client_ip, []))
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': 'Invalid PIN',
            'attempts_from_ip': len(rate_limit_storage.get(client_ip, []))
        }), 401

@app.route('/api/status', methods=['GET'])
def api_status():
    """Check API status and your current rate limit status."""
    client_ip = get_client_ip()

    # Count recent requests
    now = datetime.now()
    if client_ip in rate_limit_storage:
        recent_requests = [
            ts for ts in rate_limit_storage[client_ip]
            if now - ts < timedelta(seconds=RATE_WINDOW)
        ]
        remaining = max(0, RATE_LIMIT - len(recent_requests))
    else:
        remaining = RATE_LIMIT

    return jsonify({
        'status': 'online',
        'your_ip': client_ip,
        'rate_limit': f'{RATE_LIMIT} requests per {RATE_WINDOW} seconds',
        'requests_remaining': remaining
    }), 200

@app.route('/api/admin', methods=['GET'])
def api_admin():
    """
    Admin endpoint - requires valid auth token from successful login.
    Returns FLAG2 when accessed with a valid token.
    """
    token = request.headers.get('Authorization', '').replace('Bearer ', '')

    if not token or token not in auth_tokens:
        return jsonify({
            'success': False,
            'error': 'Unauthorized. Provide a valid Bearer token.'
        }), 401

    return jsonify({
        'success': True,
        'message': 'Admin access granted.',
        'flag': FLAG2,
        'admin_data': {
            'total_users': 42,
            'active_sessions': len(auth_tokens),
            'system': 'EverSec Auth Gateway v2.1'
        }
    }), 200

@app.route('/wordlist.txt')
def wordlist():
    """
    Provide a wordlist of common PINs for participants.
    This helps them understand they need to brute force, but the wordlist
    is too large to do within the rate limit without bypassing it.

    1,800 PINs = 6 hours at 5 attempts/minute (makes bypass mandatory)
    """
    # Generate common PINs (including the correct one)
    common_pins = [
        "1234", "0000", "1111", "1212", "7777", "1004", "2000", "4444",
        "2222", "6969", "9999", "3333", "5555", "6666", "1122", "1313",
        "8888", "4321", "2001", "1010", CORRECT_PIN,  # Include correct PIN
    ]

    # Add more random PINs to make it 1,800 total (6 hours to brute force)
    import random
    random.seed(42)  # Fixed seed for consistency
    while len(common_pins) < 1800:
        pin = f"{random.randint(0, 9999):04d}"
        if pin not in common_pins:
            common_pins.append(pin)

    # Shuffle so the correct one isn't obvious
    random.seed(42)
    random.shuffle(common_pins)

    return '\n'.join(common_pins), 200, {'Content-Type': 'text/plain'}

@app.route('/api/logs', methods=['GET'])
def api_logs():
    """
    Admin log viewer - requires valid auth token.
    VULNERABLE: Path traversal via 'file' parameter.
    """
    token = request.headers.get('Authorization', '').replace('Bearer ', '')

    if not token or token not in auth_tokens:
        return jsonify({
            'success': False,
            'error': 'Unauthorized. Provide a valid Bearer token.'
        }), 401

    # Get requested log file (defaults to app.log)
    log_file = request.args.get('file', 'app.log')

    # VULNERABLE: No path sanitization! Allows path traversal
    log_path = f'/app/logs/{log_file}'

    try:
        with open(log_path, 'r') as f:
            content = f.read()
        return jsonify({
            'success': True,
            'file': log_file,
            'content': content
        }), 200
    except FileNotFoundError:
        return jsonify({
            'success': False,
            'error': f'Log file not found: {log_file}'
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to read log file'
        }), 500

@app.route('/api/health', methods=['POST'])
def api_health():
    """
    System health check endpoint - requires valid auth token.
    VULNERABLE: Command injection via 'check' parameter.
    """
    token = request.headers.get('Authorization', '').replace('Bearer ', '')

    if not token or token not in auth_tokens:
        return jsonify({
            'success': False,
            'error': 'Unauthorized. Provide a valid Bearer token.'
        }), 401

    data = request.get_json()
    if not data or 'check' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing "check" parameter. Valid values: disk, memory, network'
        }), 400

    check_type = data['check']

    # VULNERABLE: Command injection via shell=True and unsanitized input
    # Players can inject commands via check_type parameter
    try:
        # Intentionally vulnerable - directly interpolates user input
        result = subprocess.run(
            f'df -h | head -n 3 && echo "---" && {check_type}',
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )

        return jsonify({
            'success': True,
            'check': check_type,
            'output': result.stdout,
            'stderr': result.stderr
        }), 200
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Health check timed out'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Health check failed'
        }), 500

if __name__ == '__main__':
    # Create logs directory and sample log file
    os.makedirs('/app/logs', exist_ok=True)
    with open('/app/logs/app.log', 'w') as f:
        f.write('[2026-01-30 10:15:23] INFO: Application started\n')
        f.write('[2026-01-30 10:16:45] INFO: Rate limiter initialized\n')
        f.write('[2026-01-30 10:17:12] WARNING: Failed login from 192.168.1.100\n')
        f.write('[2026-01-30 10:18:33] INFO: Successful authentication from 10.0.0.5\n')
        f.write('[2026-01-30 10:19:01] WARNING: Rate limit exceeded for 172.16.0.1\n')

    app.run(host='0.0.0.0', port=4003, debug=False)
