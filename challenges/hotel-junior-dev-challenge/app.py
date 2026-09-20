"""
Junior Dev Challenge v4 - API Key Rotation
A time-based scripting challenge focused on identifying and rotating compromised API keys.
Users must detect compromised keys, generate valid replacements, and update configurations.
"""

import random
import string
import time
import hashlib
import os
from flask import Flask, request, jsonify, session

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'hotel-ctf-key-2026')

# Service names for configuration generation
SERVICE_NAMES = [
    'auth-service', 'payment-gateway', 'email-service', 'sms-provider',
    'analytics-api', 'cdn-service', 'database-proxy', 'cache-layer',
    'search-engine', 'file-storage', 'notification-hub', 'metrics-collector',
    'logging-service', 'monitoring-api', 'backup-service', 'queue-manager',
    'api-gateway', 'load-balancer', 'dns-service', 'firewall-api'
]


def generate_api_key(prefix='PROD', compromised=False):
    """
    Generate an API key with the following format:
    PREFIX_RANDOM32CHARS_CHECKSUM

    - PREFIX: 'PROD' for production or 'COMP' for compromised
    - RANDOM32CHARS: 32 alphanumeric characters (uppercase)
    - CHECKSUM: Last 4 characters are MD5 hash of the random part (first 4 hex chars)

    Example: PROD_A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6_A3F1
    """
    if compromised:
        prefix = 'COMP'

    # Generate 32 random alphanumeric characters
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=32))

    # Calculate checksum (first 4 chars of MD5 hash)
    checksum = hashlib.md5(random_part.encode()).hexdigest()[:4].upper()

    return f"{prefix}_{random_part}_{checksum}"


def validate_api_key(key):
    """
    Validate an API key format and checksum.

    Returns: (is_valid, error_message)
    """
    parts = key.split('_')

    # Check format: PREFIX_RANDOM_CHECKSUM
    if len(parts) != 3:
        return False, "Key must have format: PREFIX_RANDOM_CHECKSUM"

    prefix, random_part, checksum = parts

    # Check prefix
    if prefix not in ['PROD', 'DEV', 'TEST']:
        return False, f"Invalid prefix '{prefix}'. Must be PROD, DEV, or TEST"

    # Check random part length
    if len(random_part) != 32:
        return False, f"Random part must be 32 characters, got {len(random_part)}"

    # Check random part is alphanumeric uppercase
    if not random_part.isalnum() or not random_part.isupper():
        return False, "Random part must be uppercase alphanumeric"

    # Check checksum length
    if len(checksum) != 4:
        return False, f"Checksum must be 4 characters, got {len(checksum)}"

    # Validate checksum
    expected_checksum = hashlib.md5(random_part.encode()).hexdigest()[:4].upper()
    if checksum != expected_checksum:
        return False, f"Invalid checksum. Expected {expected_checksum}, got {checksum}"

    return True, ""


def generate_service_config(service_name, include_compromised=False):
    """Generate a service configuration with API keys."""
    is_compromised = include_compromised and random.random() < 0.3  # 30% chance if allowed

    return {
        'service_name': service_name,
        'api_key': generate_api_key(compromised=is_compromised),
        'environment': random.choice(['production', 'staging']),
        'rate_limit': random.randint(100, 10000)
    }


@app.route('/')
def index():
    """Homepage with snarky message."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {
                background-color: #000080;
                color: #ffffff;
                font-family: "Comic Sans MS", cursive;
                text-align: center;
                background-image: url('https://web.archive.org/web/20090830073013/http://geocities.com/Area51/Corridor/5177/stars.gif');
            }
            .container {
                background-color: #000000;
                border: 5px solid #ff00ff;
                margin: 20px auto;
                padding: 20px;
                width: 80%;
                max-width: 800px;
            }
            h1 {
                color: #ffff00;
                text-shadow: 2px 2px #ff0000;
                animation: blink 1s infinite;
            }
            @keyframes blink {
                0% { opacity: 1; }
                50% { opacity: 0; }
                100% { opacity: 1; }
            }
            .snark {
                font-size: 2em;
                color: #ff00ff;
                text-shadow: 2px 2px #00ff00;
                margin: 50px 0;
            }
        </style>
    </head>
    <body>
        <!-- API documentation available at /help -->
        <div class="container">
            <h1>🤔 Hmm...</h1>
            <div class="snark">
                You're not even trying, are you?<br>
                Look a little harder! 🔍
            </div>
        </div>
    </body>
    </html>
    """


@app.route('/help')
def help_endpoint():
    """Help page with challenge instructions."""
    help_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>[Hotel] EverSec DevSecOps Challenge v4</title>
        <style>
            body {
                background-color: #000080;
                color: #ffffff;
                font-family: "Comic Sans MS", cursive;
                text-align: center;
                background-image: url('https://web.archive.org/web/20090830073013/http://geocities.com/Area51/Corridor/5177/stars.gif');
            }
            .container {
                background-color: #000000;
                border: 5px solid #ff00ff;
                margin: 20px auto;
                padding: 20px;
                width: 80%;
                max-width: 800px;
            }
            h1 {
                color: #ffff00;
                text-shadow: 2px 2px #ff0000;
                animation: blink 1s infinite;
            }
            .blink {
                animation: blink 1s infinite;
            }
            @keyframes blink {
                0% { opacity: 1; }
                50% { opacity: 0; }
                100% { opacity: 1; }
            }
            .marquee {
                background-color: #ff0000;
                color: #ffff00;
                padding: 10px;
                margin: 20px 0;
            }
            .step {
                background-color: #0000ff;
                border: 3px solid #00ff00;
                margin: 10px 0;
                padding: 10px;
                text-align: left;
            }
            .counter {
                position: fixed;
                bottom: 10px;
                right: 10px;
                background-color: #000000;
                color: #00ff00;
                padding: 5px;
                border: 2px solid #ff00ff;
            }
            code {
                background-color: #222;
                padding: 2px 5px;
                color: #0f0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌟 EverSec DevSecOps API Key Rotation Challenge v4! 🌟</h1>

            <div class="marquee">
                <marquee scrollamount="5">🔥 UNDER CONSTRUCTION - BEST VIEWED IN NETSCAPE NAVIGATOR 4.0 🔥</marquee>
            </div>

            <div style="background-color: #ff0000; color: #ffff00; padding: 15px; margin: 20px 0; border: 3px dashed #ffffff; animation: blink 2s infinite;">
                <h2 style="margin: 0;">⚠️ SECURITY BREACH DETECTED ⚠️</h2>
                <p style="font-size: 1.2em; margin: 10px 0;">Compromised API keys found in production!</p>
                <p style="font-size: 1.2em; margin: 10px 0;">Rotate them NOW or face data breach! 🔥</p>
                <p style="font-size: 1.2em; margin: 10px 0;">Your DevSecOps career depends on it! 💀</p>
            </div>

            <div class="step">
                <h2>📡 Step 1: Get Service Configurations</h2>
                <p>Make a GET request to <code>/configs</code> to receive 100 service configurations!</p>
                <p>Each config contains: service_name, api_key, environment, rate_limit</p>
            </div>

            <div class="step">
                <h2>🔍 Step 2: Identify Compromised Keys</h2>
                <p>Find all API keys starting with <code>COMP_</code> - these were exposed in the breach!</p>
                <p>These keys must be rotated immediately! 🚨</p>
            </div>

            <div class="step">
                <h2>🔑 Step 3: Generate New Keys</h2>
                <p>For each compromised key, generate a replacement following this format:</p>
                <pre style="background: #222; padding: 10px; color: #0f0;">
PREFIX_RANDOM32CHARS_CHECKSUM

PREFIX: Must be 'PROD' (for production)
RANDOM32CHARS: Exactly 32 uppercase alphanumeric characters
CHECKSUM: First 4 hex characters of MD5(RANDOM32CHARS)

Example: PROD_A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6_A3F1
                </pre>
            </div>

            <div class="step">
                <h2>📊 Step 4: Update Configurations</h2>
                <p>Replace compromised keys with your new keys in the service configs!</p>
                <p>Keep all other fields (service_name, environment, rate_limit) unchanged!</p>
            </div>

            <div class="step">
                <h2>🚀 Step 5: Submit Updated Configs</h2>
                <p>POST to <code>/validate</code> with JSON array of updated configurations!</p>
                <p>Only include configs that had compromised keys (the ones you fixed)!</p>
            </div>

            <div class="step">
                <h2>⏰ Step 6: Beat the Clock!</h2>
                <p>You have exactly <strong>1.5 seconds</strong> to rotate and submit!</p>
                <p>Manual key generation is impossible - write a script! 💻</p>
            </div>

            <div class="step">
                <h2>✅ Validation Checklist</h2>
                <ul>
                    <li>All COMP_ keys are replaced with PROD_ keys</li>
                    <li>New keys have correct format (PREFIX_32CHARS_4CHAR)</li>
                    <li>Checksums are valid MD5 hashes</li>
                    <li>All other config fields match originals</li>
                    <li>Only rotated configs are submitted</li>
                </ul>
            </div>

            <p class="blink">Good luck, DevSecOps engineer! Secure those keys! 🎮</p>
        </div>

        <div class="counter">
            Visitors: 000001
        </div>
    </body>
    </html>
    """
    return help_html


@app.route('/configs', methods=['GET'])
def configs():
    """Generate and return service configurations with some compromised keys."""
    # Generate 100 configs, some with compromised keys
    configs_list = []
    for i in range(100):
        service_name = SERVICE_NAMES[i % len(SERVICE_NAMES)] + f"-{i // len(SERVICE_NAMES) + 1}"
        # Make ~30% of keys compromised
        config = generate_service_config(service_name, include_compromised=True)
        configs_list.append(config)

    session['start_time'] = time.time()
    return jsonify(configs_list)


@app.route('/validate', methods=['POST'])
def validate():
    """
    Validate the rotated API keys.

    Expected: JSON array of configs with rotated keys (only the ones that were compromised)
    """
    if 'start_time' not in session:
        return jsonify({"error": "You must fetch configs first! Call /configs endpoint."}), 400

    end_time = time.time()
    elapsed_time = end_time - session['start_time']

    data = request.json

    if not isinstance(data, list):
        return jsonify({"error": "Expected a JSON array of configurations!"}), 400

    if len(data) == 0:
        return jsonify({"error": "No configurations submitted! Did you find any compromised keys?"}), 400

    # Validate each configuration
    for config in data:
        # Check required fields
        required_fields = ['service_name', 'api_key', 'environment', 'rate_limit']
        if not all(field in config for field in required_fields):
            return jsonify({
                "error": f"Missing required fields in config! Need: {required_fields}"
            }), 400

        api_key = config['api_key']

        # Check that the key is not compromised (should have been rotated)
        if api_key.startswith('COMP_'):
            return jsonify({
                "error": f"Found unrotated compromised key for {config['service_name']}! You must rotate all COMP_ keys!"
            }), 400

        # Validate the new key format and checksum
        is_valid, error_msg = validate_api_key(api_key)
        if not is_valid:
            return jsonify({
                "error": f"Invalid API key for {config['service_name']}: {error_msg}"
            }), 400

        # Check that production keys use PROD prefix
        if config['environment'] == 'production' and not api_key.startswith('PROD_'):
            return jsonify({
                "error": f"Production services must use PROD_ prefix! Found: {api_key[:4]}"
            }), 400

    # Check time limit
    if elapsed_time > 1.5:
        return jsonify({
            "message": f"Keys rotated correctly, but too slow! Time: {elapsed_time:.2f}s (limit: 1.5s)",
            "status": "failed"
        }), 200

    # Success!
    flag = "k3y_r0t4t10n_m4st3r"
    return jsonify({
        "message": f"Excellent work! All {len(data)} compromised keys rotated successfully!",
        "flag": flag,
        "time": f"{elapsed_time:.2f}s",
        "status": "success"
    }), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=False)
