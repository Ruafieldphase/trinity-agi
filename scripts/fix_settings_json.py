#!/usr/bin/env python3
"""Fix VS Code settings.json multi-line curl commands"""
import json
import os
import re

settings_path = os.path.expandvars(r'%APPDATA%\Code\User\settings.json')

print(f"Reading: {settings_path}")
# Read as bytes first to handle BOM and corrupted encoding
with open(settings_path, 'rb') as f:
    data = f.read()

# Remove BOM if present
if data.startswith(b'\xef\xbb\xbf'):
    data = data[3:]
    print("Removed UTF-8 BOM")

# Fix corrupted Korean path bytes
# Original: chatgpt-?\xeb\xba\xa3\xeb\x82\xab?\xeb\x8c\x80\xec\xa4\x8e\xef\xa7\xa3\xec\xa2\x8f\xeb\xb8\xb0?\xea\xb3\xb7\xed\x85\x87??
# Target: chatgpt-자연어대화철학공학
old_bytes = b'chatgpt-?\xeb\xba\xa3\xeb\x82\xab?\xeb\x8c\x80\xec\xa4\x8e\xef\xa7\xa3\xec\xa2\x8f\xeb\xb8\xb0?\xea\xb3\xb7\xed\x85\x87??'
new_bytes = 'chatgpt-자연어대화철학공학'.encode('utf-8')
count_before = data.count(old_bytes)
data = data.replace(old_bytes, new_bytes)
print(f"Replaced corrupted path bytes: {count_before} occurrences")

# Fix invalid escape sequence: \\\luon_watch -> \\\\luon_watch
data = data.replace(new_bytes + b'\\\\\\luon_watch', new_bytes + b'\\\\\\\\luon_watch')

# Convert back to string
content = data.decode('utf-8')

# Fix first curl command (안녕하세요)
content = re.sub(
    r'"curl\.exe -X POST http://localhost:8081/chat -H \\"Content-Type: application/json\\" -d \'\{\\\\\"message\\\\\": \\\\\".*?\\"[\s\n]+\}\'":\s*\{\s*"approve":\s*true,\s*"matchCommandLine":\s*true[\s\n]+\}',
    r'"curl.exe -X POST http://localhost:8081/chat -H \"Content-Type: application/json\" -d \'{\\\"message\\\": \\\"안녕하세요\\\"}\'": {\n      "approve": true,\n      "matchCommandLine": true\n    }',
    content,
    flags=re.MULTILINE | re.DOTALL
)

# Fix second curl command (테스트)
content = re.sub(
    r'"curl\.exe http://localhost:8080/v1/chat/completions -X POST -H \\"Content-Type: application/json\\" -d \'\{\\\\\"model.*?max_tokens\\\\\":10\}\'":\s*\{[\s\n]+"approve":\s*true,[\s\n]+"matchCommandLine":\s*true[\s\n]+\}',
    r'"curl.exe http://localhost:8080/v1/chat/completions -X POST -H \"Content-Type: application/json\" -d \'{\\\"model\\\":\\\"local-model\\\",\\\"messages\\\":[{\\\"role\\\":\\\"user\\\",\\\"content\\\":\\\"테스트\\\"}],\\\"max_tokens\\\":10}\'": {\n      "approve": true,\n      "matchCommandLine": true\n    }',
    content,
    flags=re.MULTILINE | re.DOTALL
)

# Fix third curl command (코페르니쿠스)
content = re.sub(
    r'"curl\.exe -X POST http://localhost:8081/chat -H \\"Content-Type: application/json\\" -d \'\{\\\\\"message\\\\\":\s*\\\\\".*?援ъ.*?\\\"}\'": \{[\s\n]+"approve": true,[\s\n]+"matchCommandLine": true[\s\n]+\}',
    r'"curl.exe -X POST http://localhost:8081/chat -H \"Content-Type: application/json\" -d \'{\\\"message\\\": \\\"코페르니쿠스의 구조를 설명하세요\\\"}\'": {\n      "approve": true,\n      "matchCommandLine": true\n    }',
    content,
    flags=re.MULTILINE | re.DOTALL
)

# Fix corrupted Korean path: chatgpt-?뺣낫?대줎泥좏븰?곷텇?? -> chatgpt-자연어대화철학공학
old_path = 'chatgpt-?뺣낫?대줎泥좏븰?곷텇??'
new_path = 'chatgpt-자연어대화철학공학'
count_before = content.count(old_path)
content = content.replace(old_path, new_path)
count_after = content.count(new_path)
print(f"Replaced corrupted path: {count_before} occurrences -> {count_after} total")

# Fix invalid escape sequences: \luon_watch -> \\luon_watch (need to fix the backslash before 'l')
# In JSON files, we need 4 backslashes to represent 2 actual backslashes
# Current: \\chatgpt-자연어대화철학공학\luon_watch (3 backslashes before \l is invalid)
# Target: \\chatgpt-자연어대화철학공학\\luon_watch (4 backslashes = 2 actual)
pattern1 = new_path + r'\luon_watch'
replacement1 = new_path + r'\\luon_watch'
count1 = content.count(pattern1)
content = content.replace(pattern1, replacement1)
print(f"Fixed invalid escape \\luon_watch: {count1} occurrences")

# Fix missing path separator before --interval
pattern2 = new_path + '--interval'
replacement2 = new_path + '\\\\--interval'
count2 = content.count(pattern2)
content = content.replace(pattern2, replacement2)
print(f"Fixed missing separator before --interval: {count2} occurrences")

# Validate JSON before writing
try:
    json.loads(content)
    print("✅ JSON validation: PASS")
except json.JSONDecodeError as e:
    print(f"❌ JSON validation: FAIL - {e}")
    print(f"Error at line {e.lineno}, column {e.colno}")
    exit(1)

print(f"Writing fixed content to: {settings_path}")
with open(settings_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print("✅ settings.json fixed successfully")
