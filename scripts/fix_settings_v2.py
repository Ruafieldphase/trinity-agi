#!/usr/bin/env python3
"""Fix VS Code settings.json - byte-level approach"""
import os
import json

settings_path = os.path.expandvars(r'%APPDATA%\Code\User\settings.json')

print(f"Reading: {settings_path}")
with open(settings_path, 'rb') as f:
    data = f.read()

# Remove BOM
if data.startswith(b'\xef\xbb\xbf'):
    data = data[3:]
    print("✓ Removed UTF-8 BOM")

# Fix corrupted Korean path
old_bytes = b'chatgpt-?\xeb\xba\xa3\xeb\x82\xab?\xeb\x8c\x80\xec\xa4\x8e\xef\xa7\xa3\xec\xa2\x8f\xeb\xb8\xb0?\xea\xb3\xb7\xed\x85\x87??'
new_bytes = 'chatgpt-자연어대화철학공학'.encode('utf-8')
count = data.count(old_bytes)
if count > 0:
    data = data.replace(old_bytes, new_bytes)
    print(f"✓ Fixed corrupted Korean path: {count} occurrences")

# Fix invalid escape: \\\luon_watch -> \\\\luon_watch
old_escape = new_bytes + b'\\\\\\luon_watch'
new_escape = new_bytes + b'\\\\\\\\luon_watch'
count = data.count(old_escape)
if count > 0:
    data = data.replace(old_escape, new_escape)
    print(f"✓ Fixed invalid escape \\\\\\luon_watch: {count} occurrences")

# Also fix the version with only 2 backslashes: \\luon -> \\\\luon
old_escape2 = new_bytes + b'\\luon_watch'
new_escape2 = new_bytes + b'\\\\luon_watch'
count2 = data.count(old_escape2)
if count2 > 0:
    data = data.replace(old_escape2, new_escape2)
    print(f"✓ Fixed invalid escape \\luon_watch: {count2} occurrences")

# Fix missing separator: 공학--interval -> 공학\\--interval
old_sep = new_bytes + b'--interval'
new_sep = new_bytes + b'\\\\--interval'
count = data.count(old_sep)
if count > 0:
    data = data.replace(old_sep, new_sep)
    print(f"✓ Fixed missing separator before --interval: {count} occurrences")

# Decode to string
content = data.decode('utf-8')

# Fix multi-line curl commands using string operations
import re

# First curl: 안녕하세요 - already fixed, but contains literal `\n` instead of newline
content = content.replace('{`n      "approve": true,`n      "matchCommandLine": true`n    }', '{\n      "approve": true,\n      "matchCommandLine": true\n    }')
print("✓ Fixed newline escaping in first curl")

# Second curl: 테스트 - still multi-line
pattern2 = (
    r'"curl\.exe http://localhost:8080/v1/chat/completions -X POST -H \\"Content-Type: application/json\\" '
    r'-d \'\{[^}]+\}\'": \{[^}]+\}'
)
replacement2 = (
    r'"curl.exe http://localhost:8080/v1/chat/completions -X POST -H \"Content-Type: application/json\" '
    r'-d \'{\\\"model\\\":\\\"local-model\\\",\\\"messages\\\":[{\\\"role\\\":\\\"user\\\",\\\"content\\\":\\\"테스트\\\"}],\\\"max_tokens\\\":10}\'": {\n      "approve": true,\n      "matchCommandLine": true\n    }'
)
content = re.sub(pattern2, replacement2, content, count=1, flags=re.DOTALL)
print("✓ Fixed second curl command (테스트)")

# Third curl: 코페르니쿠스 - still multi-line and has corrupted text
pattern3 = (
    r'"curl\.exe -X POST http://localhost:8081/chat -H \\"Content-Type: application/json\\" '
    r'-d \'\{\\\"message\\\": \\\"[^"]+\\\"\}\'": \{[^}]+\}'
)
# Find all occurrences to target the right one
matches = list(re.finditer(pattern3, content, re.DOTALL))
if len(matches) >= 2:
    # Replace second occurrence (첫 occurrence는 이미 안녕하세요로 수정됨)
    match = matches[1]
    replacement3 = (
        r'"curl.exe -X POST http://localhost:8081/chat -H \"Content-Type: application/json\" '
        r'-d \'{\\\"message\\\": \\\"코페르니쿠스의 구조를 설명하세요\\\"}\'": {\n      "approve": true,\n      "matchCommandLine": true\n    }'
    )
    content = content[:match.start()] + replacement3 + content[match.end():]
    print(f"✓ Fixed third curl command (코페르니쿠스)")
else:
    print(f"⚠ Warning: Found {len(matches)} curl patterns, expected at least 2")

# Validate JSON
try:
    json.loads(content)
    print("\n✅ JSON validation: PASS")
except json.JSONDecodeError as e:
    print(f"\n❌ JSON validation: FAIL")
    print(f"   Line {e.lineno}, column {e.colno}: {e.msg}")
    # Show context
    lines = content.split('\n')
    if e.lineno > 0 and e.lineno <= len(lines):
        start = max(0, e.lineno - 3)
        end = min(len(lines), e.lineno + 2)
        print(f"\n   Context (lines {start+1}-{end}):")
        for i in range(start, end):
            marker = " >>>" if i == e.lineno - 1 else "    "
            print(f"   {marker} {i+1:4d}: {lines[i][:100]}")
    exit(1)

# Write fixed content
print(f"\nWriting: {settings_path}")
with open(settings_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print("✅ settings.json fixed successfully!")
