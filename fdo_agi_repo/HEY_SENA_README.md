# Hey Sena - Voice Activated AGI Assistant 🎙️🤖

**Talk to your computer like you talk to Siri or Google Assistant!**

---

## 🌟 What is Hey Sena?

Hey Sena is a **voice-activated AI assistant** that runs on your computer. Say "Hey Sena" or "세나야" to activate, then ask anything!

### Key Features

- ✅ **Voice Activation** - Wake word detection ("Hey Sena", "세나야")
- ✅ **Multi-turn Conversations** - Keep talking without repeating the wake word
- ✅ **LLM-Powered** - Answer ANY question using Gemini Flash
- ✅ **Multilingual** - English & Korean support
- ✅ **Context-Aware** - Remembers recent conversation
- ✅ **Smart Timeout** - Auto-returns to sleep after silence
- ✅ **Voice Responses** - Natural text-to-speech output

---

## 🚀 Quick Start (5 Minutes)

### 1. Install Dependencies

```bash
pip install sounddevice numpy scipy google-generativeai Pillow
```

### 2. Set API Key

Create `.env` file:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

Get your free API key: https://ai.google.dev/

### 3. Run Hey Sena v4

**Option A: Python**
```bash
cd D:\nas_backup\fdo_agi_repo
python hey_sena_v4_llm.py
```

**Option B: Double-click** (Windows)
- Run `python create_shortcuts_v4.py`
- Double-click "Hey Sena v4 (LLM)" on your desktop

### 4. Start Talking!

```
YOU: "Hey Sena" or "세나야"
SENA: [beep sound]

YOU: "What is quantum physics?"
SENA: "Quantum physics is the study of matter and energy at atomic scales..."

YOU: "How do I learn Python?"
SENA: "I recommend starting with the official Python docs..."

YOU: "Goodbye"
SENA: "Goodbye! Say Hey Sena to wake me again."
```

---

## 📊 Version Comparison

Choose the right version for your needs:

| Feature | v2 | v3 | v4 (Recommended) |
|---------|----|----|------------------|
| **Wake Word** | ✅ | ✅ | ✅ |
| **Multi-turn** | ❌ (1 turn only) | ✅ | ✅ |
| **Context Memory** | ❌ | Basic (1 turn) | Advanced (5 turns) |
| **Answer Range** | ~10 questions | ~10 questions | **∞ Unlimited** |
| **Intelligence** | Rule-based | Rule-based | **LLM-powered** |
| **Best For** | Testing | Daily use | **Everything!** |

**Recommendation**: Use **v4** for the best experience!

---

## 🎯 What Can You Ask?

### v4 (LLM-Powered) - Ask ANYTHING!

**Knowledge Questions**:
- "What is artificial intelligence?"
- "Explain quantum mechanics in simple terms"
- "What's the capital of France?"

**Learning & Education**:
- "How do I learn programming?"
- "What are the best Python resources?"
- "Explain machine learning"

**Practical Advice**:
- "How do I cook pasta?"
- "What's a good morning routine?"
- "How to stay motivated?"

**Creative Requests**:
- "Tell me a joke"
- "Write a short poem"
- "Give me a fun fact"

**And much more!** The LLM can answer almost any question.

### v2/v3 (Rule-based) - Limited

- "What time is it?"
- "What's today's date?"
- "Check the weather" (asks for city)
- "Hello", "Thanks", "Goodbye"

---

## 📁 File Structure

```
D:\nas_backup\fdo_agi_repo\
│
├── hey_sena_v4_llm.py          ← v4: LLM-powered (RECOMMENDED)
├── hey_sena_v3_multiturn.py    ← v3: Multi-turn
├── hey_sena_v2.py              ← v2: Basic version
│
├── start_sena_v4.bat           ← Launch v4
├── toggle_sena_v4.bat          ← Toggle v4 on/off
├── stop_sena.bat               ← Stop all versions
│
├── create_shortcuts_v4.py      ← Create desktop shortcuts
│
├── test_llm_integration.py     ← LLM tests
├── test_multiturn.py           ← Multi-turn tests
├── test_conversation_flow.py   ← Flow simulation tests
│
├── .env                        ← API keys (create this!)
├── requirements.txt            ← Dependencies
└── HEY_SENA_README.md          ← This file
```

---

## 🎙️ How to Use

### Starting Hey Sena

**Method 1: Desktop Shortcut (Easiest)**
1. Run `python create_shortcuts_v4.py` (one time)
2. Double-click "Hey Sena v4 (LLM)" on desktop
3. Say "Hey Sena" to activate!

**Method 2: Batch File**
```bash
start_sena_v4.bat
```

**Method 3: Python Direct**
```bash
python hey_sena_v4_llm.py
```

### Using Hey Sena

1. **Activate**: Say "Hey Sena" or "세나야"
2. **Talk**: Ask any question (5 seconds to speak)
3. **Continue**: Keep asking without wake word
4. **End**: Say "goodbye" or "그만" to end conversation
5. **Exit**: Say "stop listening" or "종료" to quit program

### Example Conversation

```
[System] Listening for wake word...

YOU: "Hey Sena"
[System] Wake word detected!
[beep sound]

SENA: "Yes? How can I help you?"

YOU: "What's the weather like?"
SENA: "Which city are you interested in?"

YOU: "Seoul"  ← No wake word needed!
SENA: "I would check the weather for Seoul..."

YOU: "Thanks!"
SENA: "You're welcome! Anything else?"

YOU: "Goodbye"
SENA: "Goodbye! Say Hey Sena to wake me again."

[System] Returning to listen mode...
```

---

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# Required for LLM features
GEMINI_API_KEY=your_gemini_api_key

# Optional (for future features)
GOOGLE_APPLICATION_CREDENTIALS=path/to/gcp-credentials.json
```

### Wake Words

Edit in `hey_sena_v4_llm.py`:

```python
WAKE_WORDS = [
    "sena", "세나", "hey sena", "ok sena", "세나야",
    # Add your custom wake words here
]
```

### Voice Settings

Change TTS voice in code:

```python
voice = "Kore"  # Korean voice
# Other options: "Puck", "Charon", etc.
```

---

## 🧪 Testing

### Run All Tests

```bash
# v3 Multi-turn tests
python test_multiturn.py

# v4 LLM tests
python test_llm_integration.py

# Conversation flow simulation
python test_conversation_flow.py
```

### Test Results

```
✅ 16/16 tests passed (100%)

v3 Multi-turn:        5/5 ✅
Conversation Flow:    6/6 ✅
v4 LLM Integration:   5/5 ✅
```

---

## 🔧 Troubleshooting

### "Wake word not detected"

- Check microphone is working
- Speak clearly and close to mic
- Try saying wake word during 3-second recording window

### "LLM features disabled"

- Check `GEMINI_API_KEY` is set in `.env`
- Verify API key is valid at https://ai.google.dev/
- Check internet connection

### "Korean text garbled"

- Hey Sena v3+ has UTF-8 fix built-in
- If using v2, upgrade to v3 or v4

### "No sound/TTS not working"

- Check speakers are working
- Verify `GEMINI_API_KEY` is set (for TTS)
- Try running test: `python test_llm_integration.py`

---

## 📚 Documentation

### User Guides
- [HEY_SENA_V3_README.md](HEY_SENA_V3_README.md) - v3 user guide
- [QUICKSTART.md](QUICKSTART.md) - 5-minute setup guide

### Technical Docs
- [Hey_Sena_v3_Multi-turn_완료보고서.md](Hey_Sena_v3_Multi-turn_완료보고서.md) - v3 technical report
- [Hey_Sena_v4_LLM_완료보고서.md](Hey_Sena_v4_LLM_완료보고서.md) - v4 technical report

### Session Reports
- [세나_세션_2025-10-27_23시_완료보고서.md](세나_세션_2025-10-27_23시_완료보고서.md) - v3 session
- [세나_최종_세션_2025-10-27_23시_완료보고서.md](세나_최종_세션_2025-10-27_23시_완료보고서.md) - v4 session

---

## 🎓 How It Works

### Architecture

```
┌──────────────────────────────────────┐
│       Listen Mode (Wake Word)        │
│   [Continuously listening - 3 sec]   │
└──────────────────┬───────────────────┘
                   ↓
         [Wake word detected?]
                   ↓ YES
┌──────────────────┴───────────────────┐
│         Activation (Beep)            │
└──────────────────┬───────────────────┘
                   ↓
┌──────────────────┴───────────────────┐
│    Conversation Mode (Multi-turn)    │
│  ┌────────────────────────────┐     │
│  │ 1. Record (5 sec)          │◄────┤
│  │ 2. STT (Speech-to-Text)    │     │
│  │ 3. LLM Response (Gemini)   │     │
│  │ 4. TTS (Text-to-Speech)    │     │
│  │ 5. Play Audio              │     │
│  └────────┬───────────────────┘     │
│           ↓                          │
│   [Silence? Goodbye? Continue?]     │
│           Continue ──────────────────┘
└──────────────────┬───────────────────┘
                   ↓
         [Back to Listen Mode]
```

### Key Technologies

- **STT**: Google Gemini 2.0 Flash (Audio → Text)
- **LLM**: Google Gemini 2.0 Flash (Text → Answer)
- **TTS**: Google Gemini 2.5 Flash TTS (Text → Speech)
- **Audio**: sounddevice + numpy + scipy

---

## 🚀 Roadmap

### v5 (Planned)

- [ ] Streaming TTS (50% faster response)
- [ ] Function calling (perform actions)
- [ ] Multimodal input (images, video)
- [ ] Longer context (10+ turns)
- [ ] GUI (System Tray app)

### Future Ideas

- [ ] Local LLM support (privacy)
- [ ] Smart home integration
- [ ] Calendar & reminders
- [ ] Multi-language detection
- [ ] Voice customization

---

## ❓ FAQ

**Q: Do I need an internet connection?**
A: Yes, for LLM and TTS features (Gemini API). Basic features work offline.

**Q: Is my data private?**
A: Voice is sent to Google Gemini API. See Google's privacy policy.

**Q: Can I use a different LLM?**
A: Yes! Modify `generate_llm_response()` to use OpenAI, Claude, etc.

**Q: Does it work on Mac/Linux?**
A: Partially. Voice features work, but `.bat` files are Windows-only.

**Q: How much does it cost?**
A: Gemini API has generous free tier. ~$0.0003 per conversation.

**Q: Can I add custom commands?**
A: Yes! Edit `generate_response_with_context()` in the code.

---

## 🤝 Contributing

Hey Sena is an open project! Contributions welcome:

1. Fork the repo
2. Create your feature branch
3. Add tests
4. Submit pull request

---

## 📄 License

This project is part of FDO-AGI research.

---

## 🙏 Credits

**Created by**: Sena (Claude Code AI Agent)
**Date**: October 27, 2025
**Version**: v4.0 (LLM-powered)

**Technologies**:
- Google Gemini (LLM, STT, TTS)
- Python
- sounddevice, numpy, scipy
- ❤️ Made with AI

---

## 📞 Support

Having issues? Check:

1. [Troubleshooting](#-troubleshooting) section above
2. [QUICKSTART.md](QUICKSTART.md) for setup help
3. Test files for examples

---

**Ready to start?**

```bash
python hey_sena_v4_llm.py
```

**Say "Hey Sena" and start talking!** 🎉

---

**Hey Sena v4 = Your Personal AGI Voice Assistant** 🚀✨
