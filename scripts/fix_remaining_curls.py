#!/usr/bin/env python3
"""Fix remaining multi-line curl commands in settings.json"""
import os
import json

path = os.path.expandvars(r'%APPDATA%\Code\User\settings.json')
print(f"Reading: {path}")

with open(path, 'rb') as f:
    data = f.read()

# Handle BOM
if data.startswith(b'\xef\xbb\xbf'):
    data = data[3:]

# Try to decode, replacing errors
try:
    content = data.decode('utf-8')
except UnicodeDecodeError:
    content = data.decode('utf-8', errors='replace')
    print("⚠ Used error replacement for invalid UTF-8 bytes")

# Fix second multi-line curl (8080)
old_curl2 = """"curl.exe http://localhost:8080/v1/chat/completions -X POST -H \\"Content-Type: application/json\\" -d '{\\\\"model\\\\":\\\\"local-model\\\\",\\\\"messages\\\\":[{\\\\"role\\\\":\\\\"user\\\\",\\\\"content\\\\":\\\\"?뚯뒪??\\"
}
],\\\\"max_tokens\\\\\":10}'": {
"approve": true,
"matchCommandLine": true
},"""

new_curl2 = """"curl.exe http://localhost:8080/v1/chat/completions -X POST -H \\"Content-Type: application/json\\" -d '{\\\\"model\\\\":\\\\"local-model\\\\",\\\\"messages\\\\":[{\\\\"role\\\\":\\\\"user\\\\",\\\\"content\\\\":\\\\"테스트\\\\"}],\\\\"max_tokens\\\\\":10}'": {
      "approve": true,
      "matchCommandLine": true
    },"""

if old_curl2 in content:
    content = content.replace(old_curl2, new_curl2)
    print("✓ Fixed second curl (8080)")
else:
    print("⚠ Second curl not found with exact match")

# Fix third curl (코페르니쿠스)
old_curl3 = """"curl.exe -X POST http://localhost:8081/chat -H \\"Content-Type: application/json\\" -d '{\\\\"message\\\\": \\\\"???쒖뒪?쒖쓽 援ъ"瑜??ㅻ챸?댁쨾\\\\\\\"}'": {
"approve": true,
"matchCommandLine": true
},"""

new_curl3 = """"curl.exe -X POST http://localhost:8081/chat -H \\"Content-Type: application/json\\" -d '{\\\\"message\\\\": \\\\"코페르니쿠스의 구조를 설명하세요\\\\\\\"}'": {
      "approve": true,
      "matchCommandLine": true
    },"""

if old_curl3 in content:
    content = content.replace(old_curl3, new_curl3)
    print("✓ Fixed third curl (코페르니쿠스)")
else:
    print("⚠ Third curl not found with exact match")

# Fix fourth multi-line curl
old_curl4 = """"Start-Sleep -Seconds 3; curl.exe -X POST http://localhost:8081/chat -H \\"Content-Type: application/json\\" -d '{\\\\"message\\\\": \\\\"?덈뀞?섏꽭?? ?ㅻ뒛 ?좎뵪 ?대븣??\\\\\\\"}'": {
"approve": true,
"matchCommandLine": true
},"""

new_curl4 = """"Start-Sleep -Seconds 3; curl.exe -X POST http://localhost:8081/chat -H \\"Content-Type: application/json\\" -d '{\\\\"message\\\\": \\\\"안녕하세요 오늘 지냈어요\\\\\\\"}'": {
      "approve": true,
      "matchCommandLine": true
    },"""

if old_curl4 in content:
    content = content.replace(old_curl4, new_curl4)
    print("✓ Fixed fourth curl")
else:
    print("⚠ Fourth curl not found")

# Fix fifth multi-line curl
old_curl5 = """"Start-Sleep -Seconds 2; curl.exe -X POST http://localhost:8081/chat -H \\"Content-Type: application/json\\" -d '{\\\\"message\\\\": \\\\"?덈뀞?섏꽭??\\"
}'": {"approve": true,"matchCommandLine": true
},"""

new_curl5 = """"Start-Sleep -Seconds 2; curl.exe -X POST http://localhost:8081/chat -H \\"Content-Type: application/json\\" -d '{\\\\"message\\\\": \\\\"안녕하세요\\\\\\\"}'": {
      "approve": true,
      "matchCommandLine": true
    },"""

if old_curl5 in content:
    content = content.replace(old_curl5, new_curl5)
    print("✓ Fixed fifth curl")
else:
    print("⚠ Fifth curl not found")

# Validate JSON
print("\nValidating JSON...")
try:
    json.loads(content)
    print("✅ JSON validation: PASS")
except json.JSONDecodeError as e:
    print(f"❌ JSON validation: FAIL - Line {e.lineno}: {e.msg}")
    exit(1)

# Write back
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n✅ Fixed settings.json!")
