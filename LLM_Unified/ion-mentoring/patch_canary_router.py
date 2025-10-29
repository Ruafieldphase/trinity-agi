"""Patch main.py to add canary monitoring router"""

filepath = r"d:\nas_backup\LLM_Unified\ion-mentoring\app\main.py"

# Read file (try multiple encodings)
encodings = ["utf-8", "cp949", "euc-kr", "utf-8-sig"]
lines = None
used_encoding = None

for enc in encodings:
    try:
        with open(filepath, "r", encoding=enc) as f:
            lines = f.readlines()
        used_encoding = enc
        print(f"✅ File read successfully with encoding: {enc}")
        break
    except UnicodeDecodeError:
        continue

if lines is None:
    print("❌ Could not read file with any known encoding!")
    exit(1)

# Find the line with "# Phase 4 라우터 등록"
insert_index = None
for i, line in enumerate(lines):
    if "# Phase 4" in line and "라우터 등록" in line:
        insert_index = i
        break

if insert_index is None:
    print("Could not find insertion point!")
    exit(1)

# Insert canary router code BEFORE Phase 4 router
canary_code = [
    "# Canary Monitoring 라우터 등록\n",
    "try:\n",
    "    from app.api.canary_monitoring import router as canary_monitoring_router\n",
    "    app.include_router(canary_monitoring_router)\n",
    "    logger.info('✅ Canary monitoring router registered successfully')\n",
    "except Exception as e:\n",
    "    logger.error(f'❌ Failed to register canary monitoring router: {e}')\n",
    "\n",
]

# Insert at the found position
lines[insert_index:insert_index] = canary_code

# Write back (use same encoding)
with open(filepath, "w", encoding=used_encoding) as f:
    f.writelines(lines)

print(f"✅ Successfully patched {filepath}")
print(f"   Inserted {len(canary_code)} lines at line {insert_index + 1}")
