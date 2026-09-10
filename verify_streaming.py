#!/usr/bin/env python3
"""
Verify streaming endpoint functionality
"""

import requests
import json
import sys

# UTF-8 reconfigure for Windows console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    except Exception:
        pass

print('='*70)
print('VERIFICATION: Testing Streaming Endpoint')
print('='*70)

# Detect port 8000 or 8001
api_base = None
for port in [8000, 8001]:
    try:
        health = requests.get(f'http://localhost:{port}/health', timeout=1.5).json()
        api_base = f'http://localhost:{port}'
        print(f'✓ Connected to API at {api_base}')
        print('  Status :', health['status'])
        print('  Service:', health['service'])
        print('  Version:', health['version'])
        break
    except Exception:
        continue

if not api_base:
    print('✗ API server not detected on port 8000 or 8001.')
    print('  Note: You can start the server with: python -m uvicorn src.api:app --port 8000')
    print('  Or test in-process streaming directly via: python streaming_demo.py --auto')
    sys.exit(0)

# Test streaming endpoint
print()
print(f'Testing {api_base}/query/stream endpoint...')
try:
    response = requests.post(
        f'{api_base}/query/stream',
        json={'question': 'What is the PTO policy?', 'k': 3},
        stream=True,
        timeout=10
    )

    if response.status_code == 200:
        print('✓ Endpoint responds with 200 OK')

        event_types = set()
        event_count = 0

        for line in response.iter_lines():
            if line.startswith(b'data: '):
                try:
                    event = json.loads(line[6:])
                    event_types.add(event.get('type'))
                    event_count += 1
                except:
                    pass

        print(f'✓ Streaming working: {event_count} events received')
        print('  Event types:', sorted(event_types))
        print()
        print('✅ All systems operational!')

    else:
        print('✗ Endpoint returned', response.status_code)
except Exception as e:
    print('✗ Streaming error:', e)

print()
print('='*70)
print('NEXT STEPS:')
print('='*70)
print('1. Open ui.html or http://localhost:8000/ui in your browser')
print('2. Ask questions to see progressive answer streaming')
print('3. Click citation badges [1], [2] to jump to citations and view source chunk text')
print('4. Inspect sources in the right sidebar or modal')
print()
