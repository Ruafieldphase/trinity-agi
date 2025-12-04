#!/usr/bin/env python3
"""
FDO-AGI Voice Chat (Simplified)
Works without pyaudio - uses sounddevice (easier to install)
"""
import os
import sys
from pathlib import Path
import time

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

def check_dependencies():
    """Check if required audio libraries are available"""
    print("=" * 60)
    print("Checking Audio Dependencies")
    print("=" * 60)

    missing = []

    # Check sounddevice
    try:
        import sounddevice
        print("[OK] sounddevice installed")
    except ImportError:
        print("[MISSING] sounddevice not installed")
        missing.append("sounddevice")

    # Check numpy
    try:
        import numpy
        print("[OK] numpy installed")
    except ImportError:
        print("[MISSING] numpy not installed")
        missing.append("numpy")

    # Check scipy
    try:
        import scipy
        print("[OK] scipy installed")
    except ImportError:
        print("[MISSING] scipy not installed")
        missing.append("scipy")

    if missing:
        print("\n" + "=" * 60)
        print("MISSING DEPENDENCIES")
        print("=" * 60)
        print("\nTo install missing dependencies:")
        print(f"  pip install {' '.join(missing)}")
        print()
        return False

    print("\n[SUCCESS] All dependencies available!")
    return True

def record_audio_sd(filename="user_input.wav", duration=5, sample_rate=16000):
    """Record audio using sounddevice"""
    try:
        import sounddevice as sd
        import numpy as np
        from scipy.io.wavfile import write

        print(f"\n[MIC] Recording for {duration} seconds...")
        print("      Speak now!")

        # Record
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype='int16'
        )

        # Show progress
        for i in range(duration):
            time.sleep(1)
            print(".", end="", flush=True)

        sd.wait()  # Wait until recording is finished

        print("\n[OK] Recording complete!")

        # Save to WAV file
        write(filename, sample_rate, recording)

        file_size = os.path.getsize(filename)
        print(f"[SAVED] {filename} ({file_size:,} bytes)")

        return True

    except Exception as e:
        print(f"[ERROR] Recording failed: {str(e)}")
        return False

def play_audio_sd(filename):
    """Play audio using sounddevice"""
    try:
        import sounddevice as sd
        from scipy.io.wavfile import read

        print(f"\n[SPEAKER] Playing {filename}...")

        # Read WAV file
        sample_rate, data = read(filename)

        # Play
        sd.play(data, sample_rate)
        sd.wait()  # Wait until playback is finished

        print("[OK] Playback complete!")
        return True

    except Exception as e:
        print(f"[ERROR] Playback failed: {str(e)}")
        return False

def voice_chat_session():
    """Run an interactive voice chat session"""
    print("\n" + "=" * 60)
    print("FDO-AGI Voice Chat Session")
    print("=" * 60)
    print("\nInstructions:")
    print("  1. Press Enter when ready to speak")
    print("  2. Speak your message (5 seconds)")
    print("  3. AGI will transcribe and respond")
    print("  4. AGI's response will play through speaker")
    print("  5. Say 'goodbye' or 'exit' to end")
    print("\nPress Enter to start...")
    input()

    cfg = {
        "audio_enabled": True,
        "tts_enabled": True,
    }
    registry = ToolRegistry(cfg)

    turn = 0

    while True:
        turn += 1
        print("\n" + "=" * 60)
        print(f"Turn {turn}")
        print("=" * 60)

        # Record user input
        user_audio_file = f"user_turn_{turn}.wav"

        if not record_audio_sd(user_audio_file, duration=5):
            print("[ERROR] Could not record audio. Exiting.")
            break

        # Transcribe user speech
        print("\n[STT] Transcribing your speech...")
        stt_result = registry.call("audio", {
            "audio_path": user_audio_file,
            "prompt": "Transcribe this speech accurately"
        })

        if not stt_result.get("ok"):
            print(f"[ERROR] Transcription failed: {stt_result.get('error')}")
            if os.path.exists(user_audio_file):
                os.remove(user_audio_file)
            continue

        user_text = stt_result.get("text", "").strip()
        print(f"\n[YOU SAID] \"{user_text}\"")

        # Check for exit command
        if any(word in user_text.lower() for word in ["goodbye", "exit", "quit", "bye"]):
            print("\n[AGI] Goodbye! It was nice talking to you.")

            # Generate goodbye speech
            goodbye_file = "agi_goodbye.wav"
            tts_result = registry.call("tts", {
                "text": "Goodbye! It was nice talking to you.",
                "output_path": goodbye_file,
                "voice": "Kore"
            })

            if tts_result.get("ok"):
                play_audio_sd(goodbye_file)
                if os.path.exists(goodbye_file):
                    os.remove(goodbye_file)

            if os.path.exists(user_audio_file):
                os.remove(user_audio_file)
            break

        # Generate AGI response
        agi_response = generate_agi_response(user_text)
        print(f"[AGI RESPONDS] \"{agi_response}\"")

        # Generate AGI speech
        print("\n[TTS] Generating AGI speech...")
        agi_audio_file = f"agi_turn_{turn}.wav"

        tts_result = registry.call("tts", {
            "text": agi_response,
            "output_path": agi_audio_file,
            "voice": "Kore"
        })

        if not tts_result.get("ok"):
            print(f"[ERROR] TTS failed: {tts_result.get('error')}")
            if os.path.exists(user_audio_file):
                os.remove(user_audio_file)
            continue

        # Play AGI response
        play_audio_sd(agi_audio_file)

        # Cleanup
        if os.path.exists(user_audio_file):
            os.remove(user_audio_file)
        if os.path.exists(agi_audio_file):
            os.remove(agi_audio_file)

        print("\n[TURN COMPLETE] Press Enter for next turn...")
        input()

    print("\n" + "=" * 60)
    print("Voice Chat Session Ended")
    print("=" * 60)

def generate_agi_response(user_text):
    """Generate AGI response (simple logic for demo)"""

    user_lower = user_text.lower()

    if "hello" in user_lower or "hi" in user_lower:
        return "Hello! How can I help you today?"

    elif "how are you" in user_lower:
        return "I'm doing great! Thank you for asking. How are you?"

    elif "what" in user_lower and "name" in user_lower:
        return "I am FDO-AGI, a multimodal artificial general intelligence system."

    elif "weather" in user_lower:
        return "I can check the weather for you. Which city are you interested in?"

    elif "thank" in user_lower:
        return "You're welcome! Is there anything else I can help you with?"

    elif "seoul" in user_lower or "korea" in user_lower:
        return "Seoul is a beautiful city! I can help you with information about Seoul if you'd like."

    else:
        return f"I heard you say: {user_text}. That's interesting! Could you tell me more?"

def main():
    print("\n" + "=" * 60)
    print("FDO-AGI Voice Chat System (Simplified)")
    print("Real-time Microphone Conversation")
    print("=" * 60 + "\n")

    # Check dependencies
    if not check_dependencies():
        print("\n[INFO] To install dependencies:")
        print("  pip install sounddevice numpy scipy")
        print("\n[EXIT] Please install missing dependencies first.")
        return 1

    print("\n" + "=" * 60)
    print("System Ready!")
    print("=" * 60)

    try:
        voice_chat_session()
        return 0
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Voice chat stopped by user.")
        return 0
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
