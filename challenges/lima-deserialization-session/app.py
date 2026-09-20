from flask import Flask, render_template, request, make_response, redirect, url_for
import pickle
import base64
import os
from datetime import datetime

app = Flask(__name__)

FLAG1 = os.environ.get('FLAG1', '')
FLAG2 = os.environ.get('FLAG2', '')
FLAG3 = os.environ.get('FLAG3', '')

def init_flags():
    """Initialize flag files"""
    with open('/home/ctfuser/flag2.txt', 'w') as f:
        f.write(f"{FLAG2}\n")

class UserSession:
    """User session object"""
    def __init__(self, username, role='user', authenticated=False):
        self.username = username
        self.role = role
        self.authenticated = authenticated
        self.created_at = datetime.now().isoformat()

    def __repr__(self):
        return f"<UserSession {self.username} ({self.role})>"

def serialize_session(session_obj):
    """Serialize session object to base64-encoded format"""
    pickled = pickle.dumps(session_obj)
    return base64.b64encode(pickled).decode('utf-8')

def deserialize_session(session_data):
    """Deserialize session from base64-encoded format"""
    try:
        decoded = base64.b64decode(session_data)
        session_obj = pickle.loads(decoded)
        return session_obj
    except Exception:
        return None

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        if username and password and username == password:
            session_obj = UserSession(username=username, role='user', authenticated=True)

            if username == 'admin':
                session_obj.role = 'administrator'

            session_cookie = serialize_session(session_obj)

            response = make_response(redirect(url_for('dashboard')))
            response.set_cookie('session', session_cookie, max_age=3600)

            return response
        else:
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard - requires valid session"""
    session_cookie = request.cookies.get('session')

    if not session_cookie:
        return redirect(url_for('login'))

    session_obj = deserialize_session(session_cookie)

    if not session_obj or not hasattr(session_obj, 'authenticated') or not session_obj.authenticated:
        return redirect(url_for('login'))

    flag1_hint = None
    if hasattr(session_obj, 'role') and session_obj.role == 'administrator':
        flag1_hint = FLAG1

    return render_template('dashboard.html',
                         username=session_obj.username,
                         role=session_obj.role,
                         created_at=session_obj.created_at,
                         flag1=flag1_hint)

@app.route('/api/validate', methods=['POST'])
def api_validate():
    """API endpoint to validate session cookie"""
    try:
        data = request.get_json()
        if not data or 'session' not in data:
            return {'error': 'Session data required'}, 400

        session_data = data['session']
        session_obj = deserialize_session(session_data)

        if not session_obj:
            return {'error': 'Invalid session data'}, 400

        result = {
            'valid': True,
            'username': getattr(session_obj, 'username', 'Unknown'),
            'role': getattr(session_obj, 'role', 'user'),
            'authenticated': getattr(session_obj, 'authenticated', False)
        }

        if getattr(session_obj, 'role', '') == 'administrator':
            result['flag'] = FLAG1

        return result

    except Exception as e:
        return {'error': f'Validation error: {str(e)}'}, 500

@app.route('/api/execute', methods=['POST'])
def api_execute():
    """Execute commands via the session cookie endpoint."""
    try:
        data = request.get_json()
        if not data or 'session' not in data:
            return {'error': 'Session data required'}, 400

        session_data = data['session']
        decoded = base64.b64decode(session_data)
        result = pickle.loads(decoded)  # VULNERABLE: arbitrary code execution

        if isinstance(result, bytes):
            return {'output': result.decode('utf-8', errors='replace')}
        return {'output': str(result)}

    except Exception as e:
        return {'error': f'Execution error: {str(e)}'}, 500

@app.route('/logout')
def logout():
    """Logout"""
    response = make_response(redirect(url_for('index')))
    response.set_cookie('session', '', expires=0)
    return response

@app.route('/api/docs')
def api_docs():
    """API documentation"""
    return render_template('api_docs.html')

@app.route('/examples')
def examples():
    """Show examples of session format"""
    example_session = UserSession(username='john', role='user', authenticated=True)
    example_cookie = serialize_session(example_session)

    return render_template('examples.html', example_cookie=example_cookie)

if __name__ == '__main__':
    init_flags()
    app.run(host='0.0.0.0', port=4008, debug=False)
