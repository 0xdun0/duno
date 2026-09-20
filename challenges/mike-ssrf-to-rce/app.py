"""EverSec URL Health Checker"""

from flask import Flask, render_template, request, jsonify
import requests
import os
import subprocess
import threading
import time
from urllib.parse import urlparse

app = Flask(__name__)

FLAG1 = os.environ.get('FLAG1', '')
FLAG2 = os.environ.get('FLAG2', '')
FLAG3 = os.environ.get('FLAG3', '')
FLAG4 = os.environ.get('FLAG4', '')

command_results = {}

@app.route('/')
def index():
    """Main page with URL health checker"""
    return render_template('index.html')

@app.route('/check', methods=['POST'])
def check_url():
    """Check URL health."""
    try:
        data = request.get_json()
        url = data.get('url', '')

        if not url:
            return jsonify({'error': 'URL is required'}), 400

        try:
            response = requests.get(url, timeout=5, allow_redirects=False)

            return jsonify({
                'success': True,
                'status_code': response.status_code,
                'content_length': len(response.content),
                'headers': dict(response.headers),
                'body': response.text[:1000]
            })

        except requests.exceptions.RequestException as e:
            return jsonify({
                'success': False,
                'error': f'Request failed: {str(e)}'
            }), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def run_internal_info_service():
    """Internal information service on port 5001"""
    from flask import Flask
    internal_app = Flask(__name__)

    @internal_app.route('/')
    def info():
        return f"""
        <html>
        <head><title>Internal Info Service</title></head>
        <body>
            <h1>🔒 Internal Information Service</h1>
            <p>This service is only accessible from localhost.</p>
            <p><strong>Service Status:</strong> Running</p>
            <p><strong>Version:</strong> 1.0.0</p>
            <hr>
            <p><strong>FLAG 1:</strong> {FLAG1}</p>
        </body>
        </html>
        """

    internal_app.run(host='127.0.0.1', port=5001, debug=False)

def run_internal_admin_panel():
    """Internal admin panel on port 5002"""
    from flask import Flask, request as internal_request
    admin_app = Flask(__name__)

    @admin_app.route('/')
    def admin_home():
        """Admin panel home."""
        return """
        <html>
        <head><title>EverSec Admin Panel</title></head>
        <body style="font-family: Arial, sans-serif; margin: 40px;">
            <h1>🛡️ EverSec Admin Panel</h1>
            <p>Welcome to the internal administration interface.</p>

            <p style="color: #666; font-style: italic;">
                Access Level: Limited<br>
                Version: 2.1.0<br>
            </p>

            <h2>Available Endpoints:</h2>
            <ul>
                <li><code>GET /status</code> - System status</li>
                <li><code>POST /execute</code> - Execute system commands</li>
            </ul>
        </body>
        </html>
        """

    @admin_app.route('/status')
    def admin_status():
        """Basic status endpoint."""
        return jsonify({
            'service': 'EverSec Admin Panel',
            'status': 'running',
            'version': '2.1.0',
            'endpoints': ['/', '/status', '/execute']
        })

    @admin_app.route('/config')
    def admin_config():
        """Configuration endpoint."""
        debug_key = internal_request.args.get('debug', '')

        if debug_key == 'true' or debug_key == '1':
            return jsonify({
                'config': {
                    'service': 'EverSec Admin Panel',
                    'debug_mode': True,
                    'internal_api': 'localhost:5002',
                    'flag': FLAG2
                },
                'flag_2': FLAG2
            })
        else:
            return jsonify({
                'config': {
                    'service': 'EverSec Admin Panel',
                    'debug_mode': False,
                    'version': '2.1.0'
                },
                'hint': 'Try adding ?debug=true to access full configuration'
            })

    @admin_app.route('/robots.txt')
    def admin_robots():
        """robots.txt"""
        return """User-agent: *
Disallow: /config
Disallow: /execute
Disallow: /admin
"""

    @admin_app.route('/execute', methods=['GET', 'POST'])
    def admin_execute():
        """Command execution endpoint."""
        try:
            command = ''

            command = internal_request.args.get('command', '')

            if not command and internal_request.is_json:
                data = internal_request.get_json()
                command = data.get('command', '')

            if not command:
                command = internal_request.form.get('command', '')

            if not command:
                return jsonify({'error': 'Command is required'}), 400

            try:
                result = subprocess.check_output(
                    command,
                    shell=True,
                    stderr=subprocess.STDOUT,
                    timeout=5
                ).decode()

                if 'flag3.txt' in command or FLAG3 in result:
                    return jsonify({
                        'success': True,
                        'output': result,
                        'flag': FLAG3
                    })

                return jsonify({
                    'success': True,
                    'output': result
                })

            except subprocess.CalledProcessError as e:
                return jsonify({
                    'success': False,
                    'error': f'Command failed: {e.output.decode()}'
                }), 500

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    admin_app.run(host='127.0.0.1', port=5002, debug=False)

if __name__ == '__main__':
    threading.Thread(target=run_internal_info_service, daemon=True).start()
    threading.Thread(target=run_internal_admin_panel, daemon=True).start()

    time.sleep(1)

    app.run(host='0.0.0.0', port=4010, debug=False)
