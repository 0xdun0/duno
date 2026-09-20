# Junior Dev Challenge v4 - API Key Rotation

**Status:** ✅ Complete

## Player Description

URGENT: EverSec Security Alert! 🚨

Our monitoring system detected that approximately 30% of our API keys got posted to GitHub (rookie mistake). As our newest Junior Developer, we need you to rotate these keys ASAP! We have a sophisticated key rotation system: keys need a specific prefix and a checksum. Don't worry about reading documentation - just figure it out! You have 1.5 seconds to complete this task because our CEO is on a call with investors and keeps saying "it'll be fixed any minute now." No pressure! Remember: at EverSec, we don't believe in work-life balance, we believe in PANIC-DRIVEN DEVELOPMENT! 💪

## Technical Description

**Category:** Scripting / DevSecOps
**Difficulty:** Medium
**Points:** 200

A DevSecOps scripting challenge where you must identify and rotate compromised API keys across multiple service configurations. The time limit forces you to write a script rather than manually processing the data.

## Challenge Information

- **Port:** 3000
- **URL:** http://localhost:3000
- **Help Page:** http://localhost:3000/help

## Objective

Your company has detected a security breach - some API keys have been compromised! You need to:
1. Identify all compromised keys (those starting with `COMP_`)
2. Generate new valid replacement keys
3. Update the configurations
4. Submit within the time limit

## API Endpoints

### GET `/configs`
Returns 100 service configurations, each containing:
- `service_name`: Name of the service
- `api_key`: API key (may be compromised)
- `environment`: `production` or `staging`
- `rate_limit`: Rate limit value

### POST `/validate`
Submit an array of updated configurations (only those with compromised keys that you fixed).

## API Key Format

All API keys must follow this format:
```
PREFIX_RANDOM32CHARS_CHECKSUM
```

- **PREFIX**: Must be `PROD` for production services
- **RANDOM32CHARS**: Exactly 32 uppercase alphanumeric characters
- **CHECKSUM**: First 4 hex characters of MD5 hash of the random part

Example: `PROD_A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6_A3F1`

## Requirements

- Identify all keys starting with `COMP_` (compromised)
- Generate new valid keys with `PROD_` prefix
- Maintain correct checksum (MD5-based)
- Keep all other config fields unchanged
- Submit within **1.5 seconds** of fetching configs

## Setup

### Using Docker Compose (Recommended)

From the project root directory:

```bash
docker compose up -d junior-dev-v4
```

The challenge will be available at http://localhost:3000

### Using Docker Directly

From this directory:

```bash
docker build -t junior-dev-v4 .
docker run -p 3000:3000 junior-dev-v4
```

### Local Development

```bash
pip install -r requirements.txt
python app.py
```

## Solution

<details>
<summary>Click to reveal solution</summary>

### Understanding the Challenge

The application generates 100 service configurations, with approximately 30% having compromised API keys (starting with `COMP_`). You must:

1. Fetch the configs
2. Filter for compromised keys
3. Generate new valid keys
4. Submit within 1.5 seconds

### Key Generation Algorithm

Each API key has three parts separated by underscores:

1. **Prefix**: `PROD` for production keys
2. **Random Part**: 32 random uppercase alphanumeric characters
3. **Checksum**: First 4 hex characters of MD5(random_part)

The checksum validation happens in `app.py:82`:
```python
expected_checksum = hashlib.md5(random_part.encode()).hexdigest()[:4].upper()
```

### Solution Script (Python)

```python
#!/usr/bin/env python3
import requests
import hashlib
import random
import string

BASE_URL = "http://localhost:3000"

def generate_api_key():
    """Generate a valid API key with PROD prefix."""
    prefix = "PROD"

    # Generate 32 random uppercase alphanumeric characters
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=32))

    # Calculate checksum (first 4 chars of MD5 hash)
    checksum = hashlib.md5(random_part.encode()).hexdigest()[:4].upper()

    return f"{prefix}_{random_part}_{checksum}"

def solve_challenge():
    # Step 1: Fetch configurations
    print("[*] Fetching service configurations...")
    response = requests.get(f"{BASE_URL}/configs")
    configs = response.json()

    print(f"[+] Received {len(configs)} configurations")

    # Step 2: Identify and rotate compromised keys
    rotated_configs = []

    for config in configs:
        if config['api_key'].startswith('COMP_'):
            # This key is compromised, rotate it
            config['api_key'] = generate_api_key()
            rotated_configs.append(config)

    print(f"[+] Found {len(rotated_configs)} compromised keys")
    print(f"[*] Rotating and submitting...")

    # Step 3: Submit rotated configs
    response = requests.post(
        f"{BASE_URL}/validate",
        json=rotated_configs
    )

    result = response.json()
    print(f"\n[+] Response: {result}")

    if 'flag' in result:
        print(f"\n🚩 FLAG: {result['flag']}")
        print(f"⏱️  Time: {result['time']}")
    else:
        print(f"\n[!] Challenge failed: {result}")

if __name__ == "__main__":
    solve_challenge()
```

### Running the Solution

```bash
python solution.py
```

### Expected Output

```
[*] Fetching service configurations...
[+] Received 100 configurations
[+] Found 28 compromised keys
[*] Rotating and submitting...

[+] Response: {'message': 'Excellent work! All 28 compromised keys rotated successfully!', 'flag': 'FLAG{k3y_r0t4t10n_m4st3r}', 'time': '0.12s', 'status': 'success'}

🚩 FLAG: FLAG{k3y_r0t4t10n_m4st3r}
⏱️  Time: 0.12s
```

### Alternative Solutions

**Using curl and jq (bash):**

```bash
#!/bin/bash

# Fetch configs
configs=$(curl -s http://localhost:3000/configs)

# Filter and rotate (requires custom key generation)
# This approach is more complex due to MD5 calculation in bash

# Submit
curl -X POST http://localhost:3000/validate \
  -H "Content-Type: application/json" \
  -d "$rotated_configs"
```

**Using JavaScript/Node.js:**

```javascript
const crypto = require('crypto');
const axios = require('axios');

function generateApiKey() {
    const prefix = 'PROD';
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    const randomPart = Array.from({length: 32}, () =>
        chars[Math.floor(Math.random() * chars.length)]
    ).join('');

    const checksum = crypto.createHash('md5')
        .update(randomPart)
        .digest('hex')
        .substring(0, 4)
        .toUpperCase();

    return `${prefix}_${randomPart}_${checksum}`;
}

async function solveChallenge() {
    // Fetch configs
    const { data: configs } = await axios.get('http://localhost:3000/configs');

    // Rotate compromised keys
    const rotated = configs
        .filter(c => c.api_key.startsWith('COMP_'))
        .map(c => ({ ...c, api_key: generateApiKey() }));

    // Submit
    const result = await axios.post('http://localhost:3000/validate', rotated);
    console.log(result.data);
}

solveChallenge();
```

</details>

## Learning Objectives

After completing this challenge, you should understand:

1. **API Key Security**: Importance of rotating compromised keys quickly
2. **Checksum Validation**: How checksums prevent key tampering
3. **Scripting for Automation**: Time-critical security tasks require automation
4. **Data Processing**: Filtering, transforming, and submitting structured data
5. **DevSecOps Practices**: Rapid incident response and key management

## Common Pitfalls

1. **Incorrect Checksum**: Make sure to use MD5 hash of the random part (not the whole key)
2. **Wrong Prefix**: Production keys must use `PROD_`, not `COMP_` or other prefixes
3. **Submitting All Configs**: Only submit configs that had compromised keys
4. **Time Limit**: Don't try to do this manually - write a script!
5. **Key Length**: The random part must be exactly 32 characters

## Hints

> These hints are for CTF administrators helping stuck players. Share them progressively — start with Hint 1.

<details>
<summary>Hint 1</summary>

There's a 1.5-second time limit on submission. Read that again. Manual is not an option — this challenge requires automation.

</details>

<details>
<summary>Hint 2</summary>

Before writing your script, study the key format carefully. There's a pattern with a prefix, a random body, and a checksum. Understand the validation rules before you generate keys.

</details>

<details>
<summary>Hint 3</summary>

The checksum is computed with MD5. Which part of the key goes into the hash — the full string, or just one specific portion of it?

</details>

## References

- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [API Key Management Best Practices](https://cloud.google.com/docs/authentication/api-keys)
- [Python hashlib Documentation](https://docs.python.org/3/library/hashlib.html)
