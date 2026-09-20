from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

MONGO_HOST = os.environ.get('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.environ.get('MONGO_PORT', 27017))

FLAG1 = os.environ.get('FLAG1', '')
FLAG2 = os.environ.get('FLAG2', '')
FLAG3 = os.environ.get('FLAG3', '')
FLAG4 = os.environ.get('FLAG4', '')

def get_db():
    """Get MongoDB database connection"""
    client = MongoClient(MONGO_HOST, MONGO_PORT, serverSelectionTimeoutMS=3000)
    return client['eversec_db']

def init_db():
    """Initialize database with sample data"""
    db = get_db()

    db.users.delete_many({})

    users = [
        {
            'username': 'admin',
            'password': 'SecureAdminP4ss!2026',
            'email': '[email protected]',
            'role': 'administrator',
            'department': 'IT Security',
            'secret': FLAG2
        },
        {
            'username': 'jsmith',
            'password': 'Password123!',
            'email': '[email protected]',
            'role': 'user',
            'department': 'Engineering'
        },
        {
            'username': 'mjones',
            'password': 'Welcome2024!',
            'email': '[email protected]',
            'role': 'user',
            'department': 'Sales'
        },
        {
            'username': 'rbrown',
            'password': 'Summer2025!',
            'email': '[email protected]',
            'role': 'user',
            'department': 'Marketing'
        },
        {
            'username': 'test',
            'password': 'test123',
            'email': '[email protected]',
            'role': 'user',
            'department': 'Testing'
        }
    ]

    db.users.insert_many(users)

@app.route('/')
def index():
    """Home page"""
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Invalid request format'}), 400

            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return jsonify({'error': 'Username and password required'}), 400

            db = get_db()
            user = db.users.find_one({'username': username, 'password': password})

            if user:
                session['username'] = user['username']
                session['role'] = user['role']

                if user['role'] == 'administrator':
                    return jsonify({
                        'success': True,
                        'message': 'Login successful!',
                        'role': user['role'],
                        'flag': FLAG1
                    })
                else:
                    return jsonify({
                        'success': True,
                        'message': 'Login successful!',
                        'role': user['role']
                    })
            else:
                return jsonify({'error': 'Invalid credentials'}), 401

        except Exception as e:
            import pymongo.errors
            if isinstance(e, pymongo.errors.ServerSelectionTimeoutError):
                return jsonify({'error': 'Database unavailable'}), 503
            return jsonify({'error': f'Login error: {str(e)}'}), 500

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    """User dashboard"""
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    role = session.get('role', 'user')

    return render_template('dashboard.html', username=username, role=role, flag1=FLAG1)

@app.route('/api/search', methods=['POST'])
def search_users():
    """Search users"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request format'}), 400

        search_query = data.get('username', '')

        db = get_db()
        query = {'username': search_query}

        users = list(db.users.find(query, {'password': 0}))

        for user in users:
            user['_id'] = str(user['_id'])

        return jsonify({'users': users, 'count': len(users)})

    except Exception as e:
        import pymongo.errors
        if isinstance(e, pymongo.errors.ServerSelectionTimeoutError):
            return jsonify({'error': 'Database unavailable'}), 503
        return jsonify({'error': f'Search error: {str(e)}'}), 500

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/api/docs')
def api_docs():
    """API documentation"""
    docs = {
        'endpoints': {
            '/login': {
                'method': 'POST',
                'description': 'Authenticate user',
                'body': {
                    'username': 'string',
                    'password': 'string'
                },
                'example': {
                    'username': 'test',
                    'password': 'test123'
                }
            },
            '/api/search': {
                'method': 'POST',
                'description': 'Search for users by username',
                'authentication': 'Required (session)',
                'body': {
                    'username': 'string'
                },
                'example': {
                    'username': 'jsmith'
                }
            }
        },
        'note': 'All requests should be sent as JSON with Content-Type: application/json'
    }
    return jsonify(docs)


@app.route('/api/backup', methods=['POST'])
def backup_data():
    """Backup endpoint."""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized. Please login first.'}), 401

    try:
        data = request.get_json()
        filename = data.get('filename', 'backup.json')

        backup_path = f'/tmp/{filename}'

        db = get_db()
        users = list(db.users.find({}, {'password': 0}))

        for user in users:
            if '_id' in user:
                user['_id'] = str(user['_id'])

        import json
        with open(backup_path, 'w') as f:
            json.dump(users, f, indent=2, default=str)

        return jsonify({
            'success': True,
            'message': 'Backup created successfully',
            'path': backup_path,
            'records': len(users)
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/execute', methods=['POST'])
def execute_command():
    """Command execution endpoint."""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized. Please login first.'}), 401

    db = get_db()
    user = db.users.find_one({'username': session.get('username')})

    if not user or user.get('role') != 'administrator':
        return jsonify({'error': 'Admin access required'}), 403

    try:
        data = request.get_json()
        command = data.get('command', '')

        if not command:
            return jsonify({'error': 'No command provided'}), 400

        import subprocess
        result = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)

        return jsonify({
            'success': True,
            'output': result
        })
    except subprocess.CalledProcessError as e:
        return jsonify({
            'success': False,
            'output': e.output,
            'error': str(e)
        }), 500
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


if __name__ == '__main__':
    init_db()

    try:
        with open('/home/ctfuser/flag3.txt', 'w') as f:
            f.write(f"{FLAG3}\n")
    except Exception:
        pass

    app.run(host='0.0.0.0', port=4007, debug=False)
