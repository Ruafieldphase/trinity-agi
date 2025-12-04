#!/usr/bin/env python3
"""Fix VS Code settings.json - aggressive cleanup"""
import os
import json

settings_path = os.path.expandvars(r'%APPDATA%\Code\User\settings.json')
print(f"Reading: {settings_path}\n")

# Read as bytes
with open(settings_path, 'rb') as f:
    data = f.read()

# Remove BOM
if data.startswith(b'\xef\xbb\xbf'):
    data = data[3:]

# Fix corrupted Korean path
old_bytes = b'chatgpt-?\xeb\xba\xa3\xeb\x82\xab?\xeb\x8c\x80\xec\xa4\x8e\xef\xa7\xa3\xec\xa2\x8f\xeb\xb8\xb0?\xea\xb3\xb7\xed\x85\x87??'
new_bytes = 'chatgpt-자연어대화철학공학'.encode('utf-8')
data = data.replace(old_bytes, new_bytes)

# Fix escapes
data = data.replace(new_bytes + b'\\\\\\luon_watch', new_bytes + b'\\\\\\\\luon_watch')
data = data.replace(new_bytes + b'\\luon_watch', new_bytes + b'\\\\luon_watch')
data = data.replace(new_bytes + b'--interval', new_bytes + b'\\\\--interval')

# Decode
content = data.decode('utf-8')

# Fix backtick-n
content = content.replace('`n', '\n')

# Now the aggressive part: find and remove ALL curl commands that span multiple lines
# We'll look for patterns and delete them entirely, then add clean versions

# Remove all corrupted curl entries (they all start with specific patterns)
import re

# Pattern 1: Multi-line curl to 8081
pattern1 = r'"curl\.exe -X POST http://localhost:8081/chat[^"]*?\\"\s*\}\'":\s*\{[^}]*?"approve"[^}]*?\},'
content = re.sub(pattern1, '', content, flags=re.DOTALL)

# Pattern 2: Multi-line curl to 8080 completions
pattern2 = r'"curl\.exe http://localhost:8080/v1/chat/completions[^"]*?\}\'":[\s\S]*?"matchCommandLine":\s*true[\s\S]*?\},'
content = re.sub(pattern2, '', content, flags=re.DOTALL)

# Now find a good insertion point (after the Test-NetConnection line) and insert clean versions
insertion_marker = '"Start-Sleep -Seconds 3; Test-NetConnection -ComputerName localhost -Port 8081 -InformationLevel Quiet": {\n      "approve": true,\n      "matchCommandLine": true\n    },'

clean_curls = '''    "curl.exe -X POST http://localhost:8081/chat -H \\"Content-Type: application/json\\" -d '{\\\\"message\\\\": \\\\"안녕하세요\\\\"}''": {
      "approve": true,
      "matchCommandLine": true
    },
    "curl.exe http://localhost:8080/v1/chat/completions -X POST -H \\"Content-Type: application/json\\" -d '{\\\\"model\\\\":\\\\"local-model\\\\",\\\\"messages\\\\":[{\\\\"role\\\\":\\\\"user\\\\",\\\\"content\\\\":\\\\"테스트\\\\"}],\\\\"max_tokens\\\\\":10}'": {
      "approve": true,
      "matchCommandLine": true
    },
    "curl.exe -X POST http://localhost:8081/chat -H \\"Content-Type: application/json\\" -d '{\\\\"message\\\\": \\\\"코페르니쿠스의 구조를 설명하세요\\\\"}''": {
      "approve": true,
      "matchCommandLine": true
    },'''

if insertion_marker in content:
    content = content.replace(insertion_marker, insertion_marker + '\n' + clean_curls)
    print("✓ Inserted clean curl commands")
else:
    print("⚠ Could not find insertion point")

# Validate
print("\nValidating JSON...")
try:
    json.loads(content)
    print("✅ JSON validation: PASS\n")
except json.JSONDecodeError as e:
    print(f"❌ JSON validation: FAIL - Line {e.lineno}: {e.msg}")
    exit(1)

# Write
with open(settings_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print(f"✅ settings.json fixed!")
