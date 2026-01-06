#!/usr/bin/env python3
"""Fix VS Code settings.json - comprehensive fix v3"""
import os
import json
import re

settings_path = os.path.expandvars(r'%APPDATA%\Code\User\settings.json')
print(f"Reading: {settings_path}\n")

# Read as bytes
with open(settings_path, 'rb') as f:
    data = f.read()

# Remove BOM
if data.startswith(b'\xef\xbb\xbf'):
    data = data[3:]
    print("✓ Removed UTF-8 BOM")

# Fix corrupted Korean path bytes
old_bytes = b'chatgpt-?\xeb\xba\xa3\xeb\x82\xab?\xeb\x8c\x80\xec\xa4\x8e\xef\xa7\xa3\xec\xa2\x8f\xeb\xb8\xb0?\xea\xb3\xb7\xed\x85\x87??'
new_bytes = 'chatgpt-자연어대화철학공학'.encode('utf-8')
count = data.count(old_bytes)
if count > 0:
    data = data.replace(old_bytes, new_bytes)
    print(f"✓ Fixed corrupted Korean path: {count} occurrences")

# Fix invalid escapes
fixes = [
    (new_bytes + b'\\\\\\luon_watch', new_bytes + b'\\\\\\\\luon_watch', "\\\\\\luon_watch"),
    (new_bytes + b'\\luon_watch', new_bytes + b'\\\\luon_watch', "\\luon_watch"),
]
for old, new, desc in fixes:
    count = data.count(old)
    if count > 0:
        data = data.replace(old, new)
        print(f"✓ Fixed invalid escape {desc}: {count} occurrences")

# Fix missing separator
old_sep = new_bytes + b'--interval'
new_sep = new_bytes + b'\\\\--interval'
count = data.count(old_sep)
if count > 0:
    data = data.replace(old_sep, new_sep)
    print(f"✓ Fixed missing separator: {count} occurrences")

# Decode to string
content = data.decode('utf-8')

# Fix PowerShell backtick-n to real newlines
content = content.replace('`n', '\n')
print("✓ Fixed PowerShell escape sequences (`n -> \\n)")

# Now fix all multi-line curl commands by finding and replacing them directly
lines = content.split('\n')
fixed_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Check if this is a multi-line curl command (doesn't end with proper JSON)
    if '"curl.exe' in line and not line.rstrip().endswith('},'):
        # This is likely a multi-line command, collect it
        collected = [line]
        i += 1
        while i < len(lines):
            collected.append(lines[i])
            if '},' in lines[i] or (i < len(lines)-1 and not lines[i].strip().startswith(']')):
                break
            i += 1
        
        full_command = '\n'.join(collected)
        
        # Try to extract and fix this command
        if '8081/chat' in full_command and '메시지' not in full_command:
            # First or third curl to 8081
            if '안녕하세요' not in full_command:
                # It's one of the corrupted ones, fix it
                if i < 390:  # Approximate line number check
                    # Earlier one -> 안녕하세요
                    fixed = '    "curl.exe -X POST http://localhost:8081/chat -H \\"Content-Type: application/json\\" -d \'{\\\\\\"message\\\\\\": \\\\\\"안녕하세요\\\\\\"}\'": {\n      "approve": true,\n      "matchCommandLine": true\n    },'
                else:
                    # Later one -> 코페르니쿠스
                    fixed = '    "curl.exe -X POST http://localhost:8081/chat -H \\"Content-Type: application/json\\" -d \'{\\\\\\"message\\\\\\": \\\\\\"코페르니쿠스의 구조를 설명하세요\\\\\\"}\'": {\n      "approve": true,\n      "matchCommandLine": true\n    },'
                fixed_lines.append(fixed)
                print(f"✓ Fixed multi-line curl at line {len(fixed_lines)}")
            else:
                fixed_lines.append(line)
        elif '8080/v1/chat/completions' in full_command:
            # Second curl to 8080
            fixed = '    "curl.exe http://localhost:8080/v1/chat/completions -X POST -H \\"Content-Type: application/json\\" -d \'{\\\\\\"model\\\\\\":\\\\\\"local-model\\\\\\",\\\\\\"messages\\\\\\":[{\\\\\\"role\\\\\\":\\\\\\"user\\\\\\",\\\\\\"content\\\\\\":\\\\\\"테스트\\\\\\"}],\\\\\\"max_tokens\\\\\\\":10}\'": {\n      "approve": true,\n      "matchCommandLine": true\n    },'
            fixed_lines.append(fixed)
            print(f"✓ Fixed multi-line curl (8080) at line {len(fixed_lines)}")
        else:
            # Keep as-is
            fixed_lines.append(line)
    else:
        fixed_lines.append(line)
    
    i += 1

content = '\n'.join(fixed_lines)

# Validate JSON
print("\nValidating JSON...")
try:
    json.loads(content)
    print("✅ JSON validation: PASS\n")
except json.JSONDecodeError as e:
    print(f"❌ JSON validation: FAIL")
    print(f"   Line {e.lineno}, column {e.colno}: {e.msg}\n")
    lines = content.split('\n')
    start = max(0, e.lineno - 3)
    end = min(len(lines), e.lineno + 2)
    for i in range(start, end):
        marker = " >>>" if i == e.lineno - 1 else "    "
        print(f"   {marker} {i+1:4d}: {lines[i][:120]}")
    print("\nNote: Not writing file due to validation error")
    exit(1)

# Write fixed content
print(f"Writing: {settings_path}")
with open(settings_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print("✅ settings.json fixed successfully!")
