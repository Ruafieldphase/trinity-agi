# Hey Sena - Quick Start Guide ⚡

**Get started in 5 minutes!**

---

## Step 1: Install (2 minutes)

```bash
pip install sounddevice numpy scipy google-generativeai Pillow
```

---

## Step 2: Get API Key (1 minute)

1. Go to https://ai.google.dev/
2. Click "Get API key"
3. Copy your key

---

## Step 3: Configure (30 seconds)

Create `.env` file in `D:\nas_backup\fdo_agi_repo\`:

```
GEMINI_API_KEY=paste_your_key_here
```

---

## Step 4: Run (30 seconds)

```bash
cd D:\nas_backup\fdo_agi_repo
python hey_sena_v4_llm.py
```

---

## Step 5: Talk! (1 minute)

```
YOU: "Hey Sena"
SENA: [beep]

YOU: "What is Python?"
SENA: "Python is a programming language..."

YOU: "Thanks!"
SENA: "You're welcome!"

YOU: "Goodbye"
```

---

## Done! 🎉

That's it! You now have a working voice assistant.

### What's Next?

**Try asking**:
- "How do I learn programming?"
- "Explain quantum physics"
- "Tell me a joke"
- "What time is it?"

**Read more**:
- [HEY_SENA_README.md](HEY_SENA_README.md) - Full documentation
- [HEY_SENA_V3_README.md](HEY_SENA_V3_README.md) - User guide

---

## Troubleshooting

### "Can't find sounddevice"
```bash
pip install sounddevice
```

### "GEMINI_API_KEY not set"
- Check `.env` file exists
- Make sure no spaces around `=`
- Example: `GEMINI_API_KEY=abc123` ✅
- Wrong: `GEMINI_API_KEY = abc123` ❌

### "Wake word not detected"
- Speak clearly
- Say "Hey Sena" or "세나야"
- Check microphone is working

### "No sound"
- Check speakers/headphones
- Volume up
- Try saying something first

---

## Advanced Setup (Optional)

### Desktop Shortcuts

```bash
python create_shortcuts_v4.py
```

Now double-click "Hey Sena v4 (LLM)" on your desktop!

### Test It Works

```bash
python test_llm_integration.py
```

Should show: `🎉 All LLM integration tests passed!`

---

## Quick Reference

| Command | Action |
|---------|--------|
| "Hey Sena" | Activate |
| "세나야" | Activate (Korean) |
| "Goodbye" | End conversation |
| "Stop listening" | Exit program |

---

**Ready? Say "Hey Sena" and start talking!** 🚀
