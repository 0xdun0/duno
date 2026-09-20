import base64
import json
import os
from flask import Flask, request, render_template_string, redirect

app = Flask(__name__)

FLAG1 = os.environ.get('FLAG1', 'DUNO{5d41402abc4b2a76b9719d911017c592}')
FLAG2 = os.environ.get('FLAG2', 'DUNO{7c6a180b36896a0a8c02787eeafb0e4c}')
FLAG3 = os.environ.get('FLAG3', 'DUNO{9e107d9d372bb6826bd81d3542a419d6}')

USERS = {
    "user": "password123",
    "alice": "alice2024",
    "bob": "bob!secure"
}


def base64_url_decode(input_str):
    """Decode base64url encoded string."""
    padding = 4 - len(input_str) % 4
    if padding != 4:
        input_str += '=' * padding
    input_str = input_str.replace('-', '+').replace('_', '/')
    return base64.b64decode(input_str)


def base64_url_encode(input_bytes):
    """Encode bytes to base64url format."""
    encoded = base64.b64encode(input_bytes).decode('utf-8')
    return encoded.replace('+', '-').replace('/', '_').replace('=', '')


def create_jwt(username, role="user"):
    """Create a JWT token."""
    header = {
        "alg": "none",
        "typ": "JWT"
    }

    payload = {
        "username": username,
        "role": role
    }

    header_encoded = base64_url_encode(json.dumps(header).encode('utf-8'))
    payload_encoded = base64_url_encode(json.dumps(payload).encode('utf-8'))

    token = f"{header_encoded}.{payload_encoded}."

    return token


def decode_jwt(token):
    """Decode a JWT token and extract payload."""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None

        payload_encoded = parts[1]
        payload_json = base64_url_decode(payload_encoded)
        payload = json.loads(payload_json)

        return payload
    except Exception as e:
        return None


# HTML Templates
LOGIN_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>[Bravo] Corporate Portal - Login</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
            width: 380px;
        }
        .logo-container {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo {
            font-size: 32px;
            font-weight: bold;
            color: #1e3c72;
        }
        .logo-subtitle {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        h1 {
            color: #333;
            margin-top: 0;
            text-align: center;
            font-size: 24px;
        }
        input[type="text"], input[type="password"] {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
            box-sizing: border-box;
            font-size: 14px;
        }
        button {
            width: 100%;
            background: #1e3c72;
            color: white;
            padding: 12px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 10px;
        }
        button:hover {
            background: #2a5298;
        }
        .error {
            color: #d32f2f;
            text-align: center;
            margin-top: 10px;
        }
        .footer {
            text-align: center;
            color: #999;
            font-size: 11px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo-container">
            <div class="logo">🛡️ Corporate</div>
            <div class="logo-subtitle">Security Operations Portal</div>
        </div>
        <h1>Employee Access</h1>

        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Sign In</button>
        </form>

        {% if error %}
        <p class="error">{{ error }}</p>
        {% endif %}

        <div class="footer">
            Corporate Security Solutions &copy; 2026<br>
            For authorized personnel only
        </div>
    </div>
    <!-- TODO: Remove before production deployment
         Dev credentials: user / password123
    -->
</body>
</html>
"""

DASHBOARD_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>[Bravo] Corporate Portal - Dashboard</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f0f2f5;
            margin: 0;
            padding: 0;
        }
        .navbar {
            background: #1e3c72;
            color: white;
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .navbar-brand {
            font-size: 20px;
            font-weight: bold;
        }
        .navbar-user {
            font-size: 14px;
        }
        .container {
            max-width: 1200px;
            margin: 30px auto;
            padding: 0 20px;
        }
        .card {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 25px;
            margin-bottom: 20px;
        }
        h2 {
            color: #1e3c72;
            margin-top: 0;
            font-size: 22px;
        }
        .info-grid {
            display: grid;
            grid-template-columns: 200px 1fr;
            gap: 15px;
            margin: 20px 0;
        }
        .info-label {
            font-weight: 600;
            color: #555;
        }
        .info-value {
            color: #333;
        }
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }
        .badge-user {
            background: #e3f2fd;
            color: #1976d2;
        }
        .badge-admin {
            background: #fff3e0;
            color: #f57c00;
        }
        .admin-section {
            background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
            padding: 25px;
            border-radius: 8px;
            border-left: 4px solid #ff9800;
        }
        .access-denied {
            background: #ffebee;
            padding: 25px;
            border-radius: 8px;
            border-left: 4px solid #d32f2f;
            color: #c62828;
        }
        .flag-container {
            background: #4caf50;
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            font-size: 18px;
            font-weight: bold;
            margin: 20px 0;
            font-family: 'Courier New', monospace;
        }
        .btn {
            display: inline-block;
            background: #1e3c72;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 5px;
            margin-top: 15px;
            font-size: 14px;
        }
        .btn:hover {
            background: #2a5298;
        }
        .token-box {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 15px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            word-break: break-all;
            color: #495057;
            margin: 15px 0;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <div class="navbar-brand">🛡️ Corporate Portal</div>
        <div class="navbar-user">{{ username }} | <span class="badge {{ 'badge-admin' if role == 'admin' else 'badge-user' }}">{{ role.upper() }}</span></div>
    </div>

    <div class="container">
        <div class="card">
            <h2>Account Information</h2>
            <div class="info-grid">
                <div class="info-label">Username:</div>
                <div class="info-value">{{ username }}</div>

                <div class="info-label">Role:</div>
                <div class="info-value"><span class="badge {{ 'badge-admin' if role == 'admin' else 'badge-user' }}">{{ role.upper() }}</span></div>

                <div class="info-label">Session Token:</div>
                <div class="info-value">
                    <div class="token-box">{{ token }}</div>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>Administrative Functions</h2>

            {% if role == "admin" %}
            <div class="admin-section">
                <h3 style="margin-top: 0;">✓ Admin Access Granted</h3>
                <p>You have elevated privileges and can access sensitive security data.</p>
            </div>
            {% else %}
            <div class="access-denied">
                <h3 style="margin-top: 0;">⚠ Access Restricted</h3>
                <p>Administrative functions require elevated privileges.</p>
                <p style="margin-bottom: 0;">Contact your system administrator for access requests.</p>
            </div>
            {% endif %}
        </div>

        <a href="/logout" class="btn">Sign Out</a>
    </div>
</body>
</html>
"""


@app.route('/')
def index():
    """Home page."""
    token = request.cookies.get('token')

    if token:
        payload = decode_jwt(token)
        if payload:
            return render_template_string(
                DASHBOARD_PAGE,
                username=payload.get('username'),
                role=payload.get('role'),
                token=token
            )

    return render_template_string(LOGIN_PAGE, error=None)


@app.route('/login', methods=['POST'])
def login():
    """Handle login and create JWT token."""
    username = request.form.get('username')
    password = request.form.get('password')

    if username in USERS and USERS[username] == password:
        token = create_jwt(username, role="user")

        response = app.make_response(render_template_string(
            DASHBOARD_PAGE,
            username=username,
            role="user",
            token=token
        ))
        response.set_cookie('token', token)
        return response

    return render_template_string(LOGIN_PAGE, error="Invalid credentials")


@app.route('/logout')
def logout():
    """Clear token and redirect to login."""
    response = app.make_response(render_template_string(LOGIN_PAGE, error=None))
    response.set_cookie('token', '', expires=0)
    return response


@app.route('/admin/panel')
def admin_panel():
    """Admin panel."""
    token = request.cookies.get('token')

    if not token:
        return redirect('/')

    payload = decode_jwt(token)
    if not payload or payload.get('role') != 'admin':
        return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>[Bravo] Access Denied</title>
                <style>
                    body {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background: #f0f2f5;
                        margin: 0;
                        padding: 40px;
                    }
                    .container {
                        max-width: 600px;
                        margin: 0 auto;
                        background: white;
                        padding: 40px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }
                    h1 { color: #d32f2f; }
                    a {
                        color: #1e3c72;
                        text-decoration: none;
                    }
                    a:hover { text-decoration: underline; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>⚠ Access Denied</h1>
                    <p>Admin privileges required to access this panel.</p>
                    <p><a href="/">← Back to Dashboard</a></p>
                </div>
            </body>
            </html>
        """)

    return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>[Bravo] Corporate Admin Panel</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: #f0f2f5;
                    margin: 0;
                    padding: 0;
                }
                .navbar {
                    background: #1e3c72;
                    color: white;
                    padding: 15px 30px;
                }
                .navbar-brand {
                    font-size: 20px;
                    font-weight: bold;
                }
                .container {
                    max-width: 1200px;
                    margin: 30px auto;
                    padding: 0 20px;
                }
                .card {
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    padding: 25px;
                    margin-bottom: 20px;
                }
                h1, h2 {
                    color: #1e3c72;
                    margin-top: 0;
                }
                .flag-container {
                    background: #4caf50;
                    color: white;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                    font-size: 18px;
                    font-weight: bold;
                    margin: 20px 0;
                    font-family: 'Courier New', monospace;
                }
                .menu {
                    list-style: none;
                    padding: 0;
                }
                .menu li {
                    padding: 15px;
                    border-bottom: 1px solid #eee;
                }
                .menu li:last-child {
                    border-bottom: none;
                }
                .menu a {
                    color: #1e3c72;
                    text-decoration: none;
                    font-size: 16px;
                }
                .menu a:hover {
                    color: #2a5298;
                    text-decoration: underline;
                }
                .btn {
                    display: inline-block;
                    background: #1e3c72;
                    color: white;
                    padding: 10px 20px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 15px;
                }
                .btn:hover {
                    background: #2a5298;
                }
            </style>
        </head>
        <body>
            <div class="navbar">
                <div class="navbar-brand">🛡️ Corporate Admin Control Panel</div>
            </div>

            <div class="container">
                <div class="card">
                    <h1>Welcome, {{ username }}</h1>
                    <p>You have successfully accessed the administrator control panel.</p>

                    <div class="flag-container">
                        FLAG 1: {{ flag1 }}
                    </div>
                </div>

                <div class="card">
                    <h2>Administrative Tools</h2>
                    <ul class="menu">
                        <li><a href="/admin/template">Notification Template Editor</a> - Preview notification templates</li>
                        <li><a href="/admin/users">User Management</a> - Manage user accounts</li>
                        <li><a href="/admin/logs">System Logs</a> - View security audit logs</li>
                        <li><a href="/admin/settings">System Settings</a> - Configure portal settings</li>
                    </ul>
                </div>

                <a href="/" class="btn">← Back to Dashboard</a>
            </div>
        </body>
        </html>
    """, username=payload.get('username'), flag1=FLAG1)


MAINTENANCE_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>[Bravo] Maintenance - Corporate Admin</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f0f2f5;
            margin: 0;
            padding: 40px;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 { color: #f57c00; }
        a { color: #1e3c72; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Under Maintenance</h1>
        <p>This module is currently undergoing scheduled maintenance. Please check back later.</p>
        <p><a href="/admin/panel">&larr; Back to Admin Panel</a></p>
    </div>
</body>
</html>
"""


@app.route('/admin/users')
@app.route('/admin/logs')
@app.route('/admin/settings')
def admin_stub():
    """Stub pages for admin menu items."""
    token = request.cookies.get('token')
    if not token:
        return redirect('/')
    payload = decode_jwt(token)
    if not payload or payload.get('role') != 'admin':
        return "Access Denied", 403
    return MAINTENANCE_PAGE


@app.route('/admin/template', methods=['GET', 'POST'])
def template_preview():
    """Template preview tool."""
    token = request.cookies.get('token')

    if not token:
        return redirect('/')

    payload = decode_jwt(token)
    if not payload or payload.get('role') != 'admin':
        return "Access Denied", 403

    if request.method == 'POST':
        template = request.form.get('template', '')

        try:
            rendered = render_template_string(template)
            return render_template_string("""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>[Bravo] Notification Preview - Corporate Admin</title>
                    <style>
                        body {
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                            background: #f0f2f5;
                            margin: 0;
                            padding: 0;
                        }
                        .navbar {
                            background: #1e3c72;
                            color: white;
                            padding: 15px 30px;
                        }
                        .container {
                            max-width: 1200px;
                            margin: 30px auto;
                            padding: 0 20px;
                        }
                        .card {
                            background: white;
                            border-radius: 8px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                            padding: 25px;
                            margin-bottom: 20px;
                        }
                        .result-box {
                            border: 2px solid #4caf50;
                            padding: 20px;
                            margin: 20px 0;
                            border-radius: 5px;
                            background: #f9fff9;
                        }
                        .btn {
                            display: inline-block;
                            background: #1e3c72;
                            color: white;
                            padding: 10px 20px;
                            text-decoration: none;
                            border-radius: 5px;
                            margin-top: 15px;
                        }
                        .btn:hover {
                            background: #2a5298;
                        }
                    </style>
                </head>
                <body>
                    <div class="navbar">
                        <div>Corporate Admin - Template Preview</div>
                    </div>
                    <div class="container">
                        <div class="card">
                            <h1>Notification Preview</h1>
                            <div class="result-box">
                                {{ rendered|safe }}
                            </div>
                            <a href="/admin/template" class="btn">← Back to Editor</a>
                            <a href="/admin/panel" class="btn">Admin Panel</a>
                        </div>
                    </div>
                </body>
                </html>
            """, rendered=rendered)
        except Exception as e:
            return render_template_string("""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>[Bravo] Template Error - Corporate Admin</title>
                    <style>
                        body {
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                            background: #f0f2f5;
                            padding: 40px;
                        }
                        .container {
                            max-width: 800px;
                            margin: 0 auto;
                            background: white;
                            padding: 40px;
                            border-radius: 8px;
                        }
                        h1 { color: #d32f2f; }
                        .error {
                            background: #ffebee;
                            padding: 15px;
                            border-left: 4px solid #d32f2f;
                            border-radius: 5px;
                            font-family: 'Courier New', monospace;
                        }
                        .btn {
                            display: inline-block;
                            background: #1e3c72;
                            color: white;
                            padding: 10px 20px;
                            text-decoration: none;
                            border-radius: 5px;
                            margin-top: 15px;
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>Template Rendering Error</h1>
                        <div class="error">{{ error }}</div>
                        <a href="/admin/template" class="btn">← Back to Editor</a>
                    </div>
                </body>
                </html>
            """, error=str(e))

    # GET request - show template editor
    return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>[Bravo] Notification Template Editor - Corporate Admin</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: #f0f2f5;
                    margin: 0;
                    padding: 0;
                }
                .navbar {
                    background: #1e3c72;
                    color: white;
                    padding: 15px 30px;
                }
                .container {
                    max-width: 1200px;
                    margin: 30px auto;
                    padding: 0 20px;
                }
                .card {
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    padding: 25px;
                    margin-bottom: 20px;
                }
                h1, h2 { color: #1e3c72; margin-top: 0; }
                textarea {
                    width: 100%;
                    min-height: 300px;
                    padding: 15px;
                    font-family: 'Courier New', monospace;
                    font-size: 14px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    box-sizing: border-box;
                }
                button {
                    background: #4caf50;
                    color: white;
                    padding: 12px 30px;
                    border: none;
                    border-radius: 5px;
                    font-size: 16px;
                    cursor: pointer;
                    margin-top: 15px;
                }
                button:hover {
                    background: #45a049;
                }
                .btn {
                    display: inline-block;
                    background: #1e3c72;
                    color: white;
                    padding: 10px 20px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 15px;
                    margin-left: 10px;
                }
                .btn:hover {
                    background: #2a5298;
                }
            </style>
        </head>
        <body>
            <div class="navbar">
                <div>Corporate Admin - Notification Templates</div>
            </div>

            <div class="container">
                <div class="card">
                    <h1>Notification Template Editor</h1>
                    <p>Preview notification templates before sending them to employees. Enter your template markup below and click Preview to see how it will render.</p>

                    <form method="POST">
                        <textarea name="template" placeholder="Enter your notification template here...

Example:
<h1>Hello, employee!</h1>
<p>This is a test notification from the Corporate security team.</p>"></textarea><br>
                        <button type="submit">Preview Template</button>
                        <a href="/admin/panel" class="btn">← Back to Admin Panel</a>
                    </form>
                </div>
            </div>
        </body>
        </html>
    """)


if __name__ == '__main__':
    try:
        with open('/app/flag2.txt', 'w') as f:
            f.write(f"{FLAG2}\n")
    except Exception as e:
        pass

    app.run(host='0.0.0.0', port=5002, debug=False)
