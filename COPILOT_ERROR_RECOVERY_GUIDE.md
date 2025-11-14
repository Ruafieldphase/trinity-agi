# Copilot Error Recovery - Quick Start Guide

## 🚨 Problem: Copilot 400 Invalid Request Body Loop

When you see:
```
요청에 실패했습니다. 다시 시도하세요.
Reason: Request Failed: 400 {"error":{"message":"","code":"invalid_request_body"}}
```

## 🛠️ Immediate Actions

### Option 1: Activate Automated Recovery (Recommended)
```powershell
# From workspace root
.\scripts\copilot_error_recovery.ps1 -ActivateFallback
```

This will:
1. Log the error pattern
2. Check if Lubit (OpenAI Codex) or Sian (Gemini CLI) bridges exist
3. Activate the first available fallback agent
4. Attempt recovery suggestions via clipboard context

### Option 2: Manual CLI Bridge (If Auto-Fail)

#### Using Lubit (OpenAI Codex):
```powershell
# Copy error context to clipboard first, then:
python fdo_agi_repo\integrations\openai_codex_bridge.py --mode error-recovery --context clipboard
```

#### Using Sian (Gemini CLI):
```powershell
# Copy error context to clipboard first, then:
python fdo_agi_repo\integrations\gemini_cli_bridge.py --mode error-recovery --context clipboard
```

### Option 3: Manual Paste (User-Driven)
1. Copy the error message + recent context
2. Open external CLI tool (e.g., `lubit` terminal or `sian` terminal)
3. Paste context and request diagnosis
4. Apply suggested fix manually

## 🔍 Common Root Causes

1. **Request Body Too Large**
   - Fix: Reduce context window (use `@workspace /file:` instead of full workspace scan)
   - Fix: Split large edits into smaller chunks

2. **Malformed JSON in Tool Call**
   - Fix: Check `multi_replace_string_in_file` for unescaped quotes
   - Fix: Validate JSON structure before submission

3. **Encoding Issues (특히 한글)**
   - Fix: Ensure UTF-8 encoding in all file operations
   - Fix: Check `$env:PYTHONIOENCODING='utf-8'` in PowerShell

4. **Rate Limiting Cascade**
   - Fix: Exponential backoff (wait 5s, 15s, 30s between retries)
   - Fix: Switch to lower-tier model temporarily

## 📊 Monitoring Recovery Success

Check logs:
```powershell
# Copilot recovery log
code outputs\copilot_error_recovery_log.jsonl

# Lubit log (if activated)
code outputs\lubit_recovery_log.jsonl

# Sian log (if activated)
code outputs\sian_recovery_log.jsonl
```

## 🔄 Fallback Agent Architecture

```
Copilot Error (400)
    ↓
copilot_error_recovery.ps1
    ↓
┌─────────────────┬─────────────────┐
│  Lubit (OpenAI) │  Sian (Gemini)  │ ← Fallback CLI Agents
└─────────────────┴─────────────────┘
    ↓
Recovery Suggestions → User applies manually
```

## 🎯 Success Criteria

- ✅ Error logged with timestamp and pattern
- ✅ Fallback agent activated (if available)
- ✅ Recovery suggestion generated within 30s
- ✅ User can apply fix without full context reload

## 🚀 Next Steps (If Bridges Missing)

Run scaffold creator:
```powershell
.\scripts\create_fallback_bridges.ps1
```

This will:
1. Create `.env` template for API keys
2. Install required Python packages (`openai`, `google-generativeai`, `pyperclip`)
3. Validate bridge connectivity
4. Add VS Code tasks for quick access

## 📝 Example Recovery Flow

```powershell
# 1. Error occurs
# 2. Activate recovery
.\scripts\copilot_error_recovery.ps1 -ActivateFallback

# 3. Check suggestion
code outputs\lubit_recovery_log.jsonl

# 4. Apply fix (example: reduce context)
# Instead of: @workspace /new
# Use: @workspace /file:specific_file.py

# 5. Retry original request
# Copilot should now succeed
```

## ⚡ Emergency Manual Paste Protocol

If all automation fails:
1. **Copy** this error info:
   - Request ID: 92c42d5a-b059-430e-8f65-64ce6ce90e77
   - Error: `invalid_request_body`
   - Recent context: (last 500 chars from editor)

2. **Paste** into external AI tool (ChatGPT, Claude, etc.)

3. **Ask**: "Diagnose this VS Code Copilot API error and suggest fix"

4. **Apply** suggested fix manually

5. **Log** outcome in `outputs/manual_recovery_log.md`

## 📌 Integration with Existing Systems

This recovery system integrates with:
- `AUTONOMOUS_GOAL_SYSTEM_OPERATIONAL.md` (error resilience)
- `ADAPTIVE_RHYTHM_ORCHESTRATOR_COMPLETE.md` (degraded-mode fallback)
- `AGI_AUTONOMOUS_RECOVERY_COMPLETE_20251106.md` (self-healing loop)

All recovery attempts are logged to `resonance_ledger.jsonl` as `copilot_error_recovery` events.
