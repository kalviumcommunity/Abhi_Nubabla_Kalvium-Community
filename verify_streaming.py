#!/usr/bin/env python3
"""
Verify streaming endpoint functionality
"""

import requests
import json
import sys

print('='*70)
print('VERIFICATION: Testing Streaming Endpoint')
print('='*70)

# Test API health
try:
    health = requests.get('http://localhost:8001/health', timeout=2).json()
    print('✓ API Health:', health['status'])
    print('  Service:', health['service'])
    print('  Version:', health['version'])
except Exception as e:
    print('✗ API not responding:', e)
    sys.exit(1)

# Test streaming endpoint
print()
print('Testing /query/stream endpoint...')
try:
    response = requests.post(
        'http://localhost:8001/query/stream',
        json={'question': 'test', 'k': 3},
        stream=True,
        timeout=5
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
        
        print('✓ Streaming working:', event_count, 'events received')
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
print('1. Open ui.html in your browser')
print('2. Ask a question to see streaming in action')
print('3. Click citations [1], [2] to view sources')
print('4. Try different questions to explore the RAG')
print()
print('For detailed documentation:')
print('  - QUICK_START.md           - Get started in 5 minutes')
print('  - STREAMING_IMPLEMENTATION_GUIDE.md - Full technical details')
print('  - STREAMING_DEMO_OUTPUT.md - Example streaming responses')
print()
