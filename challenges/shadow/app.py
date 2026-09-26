"""
EverSec API Gateway - GraphQL Injection Challenge
A GraphQL API with multiple vulnerabilities including introspection, injection, and auth bypass.

FLAGS:
- FLAG 1: Discover GraphQL introspection to find hidden queries
- FLAG 2: Exploit GraphQL injection to bypass authentication
- FLAG 3: Extract sensitive data using batch queries and aliases

The vulnerabilities:
1. GraphQL introspection enabled (information disclosure)
2. No query depth/complexity limiting (DoS vector)
3. String concatenation in resolvers (injection)
4. No proper authorization checks
5. Batch query abuse
"""

from flask import Flask, render_template, request, jsonify
import os
import json
import subprocess

app = Flask(__name__)

# Flags (no wrappers)
FLAG1 = os.environ.get('FLAG1', 'gr4phql_1ntr0sp3ct10n')
FLAG2 = os.environ.get('FLAG2', 'gr4phql_1nj3ct10n_byp4ss')
FLAG3 = os.environ.get('FLAG3', 'b4tch_qu3ry_3xtr4ct10n')
FLAG4 = os.environ.get('FLAG4', 'gr4phql_rc3_pr1v3sc')

# Mock database
USERS = [
    {'id': 1, 'username': 'alice', 'email': 'alice@eversec.com', 'role': 'user', 'bio': 'Security analyst'},
    {'id': 2, 'username': 'bob', 'email': 'bob@eversec.com', 'role': 'user', 'bio': 'DevOps engineer'},
    {'id': 3, 'username': 'admin', 'email': 'admin@eversec.com', 'role': 'admin', 'bio': 'System administrator'},
    {'id': 4, 'username': 'charlie', 'email': 'charlie@eversec.com', 'role': 'user', 'bio': 'Frontend developer'},
]

SECRETS = [
    {'id': 1, 'name': 'Database Password', 'value': 'super_secret_db_pass', 'owner_id': 3},
    {'id': 2, 'name': 'Admin Auth Token (X-Admin-Token header)', 'value': 'sk_live_abc123def456', 'owner_id': 3},
    {'id': 3, 'name': 'Encryption Key', 'value': FLAG3, 'owner_id': 3},
]

POSTS = [
    {'id': 1, 'title': 'Welcome to EverSec', 'content': 'Our new API is live!', 'author_id': 1},
    {'id': 2, 'title': 'GraphQL Best Practices', 'content': 'Always disable introspection in production', 'author_id': 3},
    {'id': 3, 'title': 'Security Update', 'content': 'Patch notes for v2.0', 'author_id': 3},
]

# GraphQL Schema (simplified, hardcoded)
SCHEMA = '''
type Query {
    user(id: Int!): User
    users: [User!]!
    userByUsername(username: String!): User
    post(id: Int!): Post
    posts: [Post!]!
    secrets: [Secret!]!
    search(query: String!): [SearchResult!]!
    __schema: __Schema!
    __type(name: String!): __Type
}

type User {
    id: Int!
    username: String!
    email: String!
    role: String!
    bio: String
}

type Post {
    id: Int!
    title: String!
    content: String!
    author: User!
}

type Secret {
    id: Int!
    name: String!
    value: String!
    owner: User!
}

union SearchResult = User | Post
'''

def resolve_user(args):
    """Resolve single user by ID"""
    user_id = args.get('id')
    for user in USERS:
        if user['id'] == user_id:
            return user
    return None

def resolve_users():
    """Resolve all users"""
    return USERS

def _evaluate_atom(atom, user):
    """Evaluate a single comparison like username='admin' or '1'='1'."""
    atom = atom.strip()
    if '=' not in atom:
        return False
    left, right = atom.split('=', 1)
    left = left.strip().strip("'").strip('"')
    right = right.strip().strip("'").strip('"')
    # Tautology: both sides identical (e.g., 1=1, a=a)
    if left == right:
        return True
    # Field lookup
    if left in user:
        return str(user[left]) == right
    if right in user:
        return str(user[right]) == left
    return False

def _evaluate_condition(condition, user):
    """Evaluate a SQL-like WHERE clause against a user record.
    Supports OR and AND operators with simple equality comparisons.
    This simulates what happens when user input is concatenated into a SQL WHERE clause."""
    condition = condition.strip()

    # Handle OR (lowest precedence)
    or_parts = condition.split(' OR ', 1)
    if len(or_parts) == 2:
        return _evaluate_condition(or_parts[0], user) or _evaluate_condition(or_parts[1], user)

    # Handle AND
    and_parts = condition.split(' AND ', 1)
    if len(and_parts) == 2:
        return _evaluate_condition(and_parts[0], user) and _evaluate_condition(and_parts[1], user)

    return _evaluate_atom(condition, user)

def resolve_user_by_username(args):
    """
    VULNERABLE: Simulates SQL query with string concatenation.
    The resolver builds a WHERE clause like:
        SELECT * FROM users WHERE username = '<INPUT>'
    If the input contains injection (e.g., ' OR '1'='1), the WHERE clause becomes:
        SELECT * FROM users WHERE username = '' OR '1'='1'
    which matches all rows (returns the first match).
    """
    username = args.get('username', '')

    # Direct match first (no injection needed) — returns user WITHOUT secret field
    for user in USERS:
        if user['username'] == username:
            return user

    # Simulate: WHERE username = '{username}'
    # The single quotes around {username} are critical: they are what the
    # attacker's injected quote closes.  For example, if username is:
    #     x' OR '1'='1
    # the full clause becomes:
    #     username='x' OR '1'='1'
    # which the evaluator splits on OR into two atoms that each parse cleanly.
    simulated_where = f"username='{username}'"

    # Collect all matching users (injection may match multiple rows)
    matches = []
    for user in USERS:
        try:
            if _evaluate_condition(simulated_where, user):
                matches.append(user)
        except Exception:
            continue

    if not matches:
        return None

    # If injection succeeded (matched more than one user or matched a non-existent username),
    # return the admin user with FLAG2 to reward the injection — simulating SQL returning
    # the first row of a UNION or tautology that exposes privileged data.
    # This prevents trivially getting FLAG2 by requesting "alice" (direct match, above).
    if len(matches) > 1:
        for user in matches:
            if user['role'] == 'admin':
                return {**user, 'secret': FLAG2}
    return matches[0]

def resolve_secrets(context=None):
    """
    VULNERABLE: Authorization check uses a token from SECRETS itself.
    Players must first extract the API key from SECRETS via injection,
    then use it as X-Admin-Token to access the full secrets list with FLAG3.
    """
    from flask import request as flask_request
    token = flask_request.headers.get('X-Admin-Token', '')
    if token != 'sk_live_abc123def456':
        # Return non-secret entries only (no FLAG3)
        return [s for s in SECRETS if 'value' not in s or FLAG3 not in s['value']]
    return SECRETS

def resolve_search(args):
    """Search across users and posts"""
    query = args.get('query', '').lower()
    results = []

    for user in USERS:
        if query in user['username'].lower() or query in user['email'].lower():
            results.append({'__typename': 'User', **user})

    for post in POSTS:
        if query in post['title'].lower() or query in post['content'].lower():
            results.append({'__typename': 'Post', **post})

    return results

def resolve_introspection_schema():
    """
    VULNERABLE: Introspection enabled
    Exposes entire schema including hidden queries
    """
    return {
        'types': [
            {
                'name': 'Query',
                'fields': [
                    {'name': 'user', 'description': 'Get user by ID'},
                    {'name': 'users', 'description': 'Get all users'},
                    {'name': 'userByUsername', 'description': 'Get user by username'},
                    {'name': 'secrets', 'description': 'Get secrets - admin access required'},
                    {'name': 'search', 'description': 'Search users and posts'},
                    {'name': 'systemFlag', 'description': FLAG1},
                ]
            }
        ],
        'queryType': {'name': 'Query'},
        'mutationType': None
    }

def execute_graphql(query, variables=None):
    """
    Simplified GraphQL executor
    In production, use a proper library like graphene, ariadne, or strawberry
    """
    variables = variables or {}

    # Parse query (very simplified)
    query = query.strip()

    # Handle introspection queries
    if '__schema' in query or '__Schema' in query:
        if 'queryType' in query:
            return {
                'data': {
                    '__schema': {
                        'queryType': {
                            'name': 'Query',
                            'fields': [
                                {'name': 'user'},
                                {'name': 'users'},
                                {'name': 'userByUsername'},
                                {'name': 'post'},
                                {'name': 'posts'},
                                {'name': 'secrets'},
                                {'name': 'search'},
                                {'name': 'systemFlag', 'description': FLAG1},
                            ]
                        }
                    }
                }
            }
        return {
            'data': {
                '__schema': resolve_introspection_schema()
            }
        }

    # Handle __type introspection
    if '__type' in query:
        return {
            'data': {
                '__type': {
                    'name': 'Query',
                    'fields': [
                        {'name': 'secrets', 'description': 'Internal system type'}
                    ]
                }
            }
        }

    # Handle different query types
    if 'userByUsername' in query:
        # Extract username argument
        username = None
        if 'username:' in query:
            # Extract the full string including quotes
            parts = query.split('username:')[1].split(')')[0].strip()
            # Keep the full value to allow injection
            # Just remove outer quotes if they match
            if (parts.startswith('"') and parts.endswith('"')) or \
               (parts.startswith("'") and parts.endswith("'")):
                username = parts[1:-1]  # Remove outer quotes but keep internal content
            else:
                username = parts
        result = resolve_user_by_username({'username': username})
        return {'data': {'userByUsername': result}}

    elif 'secrets' in query:
        secrets = resolve_secrets()
        return {'data': {'secrets': secrets}}

    elif 'users' in query:
        users = resolve_users()
        return {'data': {'users': users}}

    elif 'user(' in query and 'id:' in query:
        # Extract ID
        id_str = query.split('id:')[1].split(')')[0].strip()
        user_id = int(id_str)
        result = resolve_user({'id': user_id})
        return {'data': {'user': result}}

    elif 'systemFlag' in query:
        return {'data': {'systemFlag': FLAG1}}

    elif 'search' in query:
        # Extract search query
        search_query = ''
        if 'query:' in query:
            parts = query.split('query:')[1].split(')')[0].strip()
            search_query = parts.strip('"').strip("'")
        results = resolve_search({'query': search_query})
        return {'data': {'search': results}}

    else:
        return {'errors': [{'message': 'Query not recognized'}]}

@app.route('/')
def index():
    """GraphQL playground interface"""
    return render_template('index.html')

def _query_depth(query: str) -> int:
    depth = max_depth = 0
    for ch in query:
        if ch == '{': depth += 1; max_depth = max(max_depth, depth)
        elif ch == '}': depth -= 1
    return max_depth

@app.route('/graphql', methods=['POST', 'GET'])
def graphql_endpoint():
    """
    GraphQL endpoint
    VULNERABLE: Allows introspection, no depth limiting, injection vectors
    """
    if request.method == 'GET':
        # Support GET requests with query parameter
        query = request.args.get('query', '')
        variables = {}
    else:
        # POST with JSON body
        data = request.get_json() or {}
        query = data.get('query', '')
        variables = data.get('variables', {})

    if not query:
        return jsonify({'errors': [{'message': 'No query provided'}]}), 400

    if _query_depth(query) > 8:
        return jsonify({'errors': [{'message': 'Query depth limit exceeded'}]}), 400

    try:
        result = execute_graphql(query, variables)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'errors': [{'message': f'Execution error: {str(e)}'}]
        }), 500

@app.route('/admin/execute', methods=['POST'])
def admin_execute():
    """Admin command execution - requires admin token"""
    token = request.headers.get('X-Admin-Token', '')
    # Token is the admin's API key from secrets (sk_live_abc123def456)
    if token != 'sk_live_abc123def456':
        return jsonify({'error': 'Invalid admin token'}), 403

    data = request.get_json() or {}
    command = data.get('command', '')
    if not command:
        return jsonify({'error': 'No command provided'}), 400

    try:
        result = subprocess.check_output(command, shell=True, text=True, timeout=5)
        return jsonify({'output': result.strip(), 'success': True})
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Command timed out'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("="*60)
    print("EverSec GraphQL API Starting...")
    print("="*60)
    print("GraphQL Endpoint: http://0.0.0.0:4012/graphql")
    print("Playground:       http://0.0.0.0:4012/")
    print("="*60)

    app.run(host='0.0.0.0', port=4012, debug=False)
