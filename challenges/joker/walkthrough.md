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

[+] Response: {'message': 'Excellent work! All 28 compromised keys rotated successfully!', 'flag': 'DUNO{fcb7e564f903636f74699c35e08a0163}', 'time': '0.12s', 'status': 'success'}

🚩 FLAG: DUNO{fcb7e564f903636f74699c35e08a0163}
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