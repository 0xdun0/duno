## Solution

### FLAG 1 - Adjacent Document Access (100 pts)

**Skill**: Basic IDOR - changing a single parameter

1. Find credentials (check the page source)
2. Log in and observe your assigned documents (IDs 1042, 1043)
3. View document 1043 - notice the URL: `/document/1043`
4. Try the next ID: `/document/1044`
5. Document 1044 is a confidential penetration test report containing FLAG1

**Flag**: `DUNO{39aec5873a512caf0e82d1ceb8238527}`

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

**Flag**: `DUNO{99814af7b6dc97953a6c298cc4731602}`

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

**Flag**: `DUNO{fd1f291eed8b80e33380ad1eab6455cf}`

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

**Flag**: `DUNO{2df9b7f215d63f7a57db5bb3754f154d}`