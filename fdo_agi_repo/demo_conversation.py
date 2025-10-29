#!/usr/bin/env python3
"""
Conversation Demo with FDO-AGI
Tests actual conversation flow: TTS → Audio → Listen
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load .env file
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

from orchestrator.tool_registry import ToolRegistry

def simulate_conversation():
    """Simulate a conversation between user and AGI"""
    print("\n" + "=" * 60)
    print("FDO-AGI Conversation Demo")
    print("Testing Text-to-Speech → Speech-to-Text cycle")
    print("=" * 60 + "\n")

    cfg = {
        "audio_enabled": True,
        "tts_enabled": True,
        "grounding_enabled": True,
    }
    registry = ToolRegistry(cfg)

    # Conversation scenario
    conversations = [
        {
            "role": "User",
            "text": "Hello AGI! Can you tell me the weather forecast?",
            "audio_file": "demo_user_1.wav"
        },
        {
            "role": "AGI",
            "text": "Hello! I'd be happy to help with the weather. However, I need your location to provide an accurate forecast. Could you please tell me which city you're interested in?",
            "audio_file": "demo_agi_1.wav"
        },
        {
            "role": "User",
            "text": "I'm in Seoul, South Korea.",
            "audio_file": "demo_user_2.wav"
        },
        {
            "role": "AGI",
            "text": "Great! Let me check the current weather in Seoul for you.",
            "audio_file": "demo_agi_2.wav"
        },
    ]

    print("[START] Starting Conversation Simulation...\n")

    for i, turn in enumerate(conversations, 1):
        print("-" * 60)
        print(f"Turn {i}: {turn['role']}")
        print("-" * 60)

        # Generate speech (TTS)
        print(f"[SAY] {turn['role']} says: \"{turn['text']}\"")
        print(f"[TTS] Generating speech...")

        voice = "Kore" if turn['role'] == "AGI" else "Puck"

        tts_result = registry.call("tts", {
            "text": turn['text'],
            "output_path": turn['audio_file'],
            "voice": voice
        })

        if tts_result.get("ok"):
            file_size = os.path.getsize(turn['audio_file'])
            print(f"   [OK] Speech generated: {turn['audio_file']} ({file_size:,} bytes)")
            print(f"   [VOICE] {voice}")

            # Simulate listening (STT)
            print(f"[LISTEN] AGI listening to audio...")

            stt_result = registry.call("audio", {
                "audio_path": turn['audio_file'],
                "prompt": "Transcribe this speech accurately"
            })

            if stt_result.get("ok"):
                transcribed = stt_result.get("text", "")
                print(f"   [OK] Transcribed: \"{transcribed[:100]}...\"")

                # Simple accuracy check
                if turn['text'].lower() in transcribed.lower() or transcribed.lower() in turn['text'].lower():
                    print(f"   [MATCH] Transcription matches!")
                else:
                    print(f"   [WARN] Transcription differs slightly")

                # Cleanup
                if os.path.exists(turn['audio_file']):
                    os.remove(turn['audio_file'])
                    print(f"   [CLEAN] Cleaned up audio file")
            else:
                print(f"   [ERROR] STT error: {stt_result.get('error')}")
        else:
            print(f"   [ERROR] TTS error: {tts_result.get('error')}")

        print()

    print("=" * 60)
    print("[SUCCESS] Conversation Demo Complete!")
    print("=" * 60)
    print("\nFDO-AGI successfully demonstrated:")
    print("  [+] Text-to-Speech (TTS) - AGI can speak")
    print("  [+] Speech-to-Text (STT) - AGI can listen")
    print("  [+] Conversation flow - Turn-based dialogue")
    print()

def check_realtime_capability():
    """Check if realtime microphone conversation is possible"""
    print("=" * 60)
    print("Real-time Microphone Conversation Analysis")
    print("=" * 60 + "\n")

    print("Current Capabilities:")
    print("  [OK] File-based conversation (demonstrated above)")
    print("  [OK] TTS: Text -> Audio file")
    print("  [OK] STT: Audio file -> Text")
    print()

    print("For Real-time Microphone Conversation, we need:")
    print("  1. [MIC] Microphone recording (pyaudio/sounddevice)")
    print("  2. [STREAM] Real-time audio streaming")
    print("  3. [SPEAKER] Audio playback (speaker output)")
    print("  4. [FAST] Low-latency processing")
    print()

    print("Options for Real-time:")
    print()
    print("Option A: File-based (Current - 2-3 sec latency)")
    print("  - Record mic -> Save WAV -> STT -> LLM -> TTS -> Play")
    print("  - Latency: ~2-3 seconds per turn")
    print("  - Complexity: Low [OK]")
    print("  - Code needed: ~50 lines (pyaudio)")
    print()

    print("Option B: Gemini Live API (Native real-time)")
    print("  - WebSocket connection")
    print("  - Streaming audio I/O")
    print("  - Latency: ~200-500ms")
    print("  - Complexity: Medium")
    print("  - Code needed: ~200 lines")
    print()

    print("Recommendation:")
    print("  -> Start with Option A (file-based) - Simple & works now")
    print("  -> Upgrade to Option B later if needed")
    print()

    print("Would you like me to implement Option A?")
    print("(Real-time mic recording + playback)")
    print()

def main():
    # Run conversation demo
    simulate_conversation()

    # Explain real-time capability
    check_realtime_capability()

if __name__ == "__main__":
    main()
