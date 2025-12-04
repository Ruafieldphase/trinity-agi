#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hey Sena v2 - Improved Voice Activated AGI Assistant
- Longer recording for better wake word detection
- Debug output to show what's heard
- Better exit handling (no Ctrl+C conflict)
"""
import os
import sys
from pathlib import Path
import time

# Fix Windows console encoding - AGGRESSIVE FIX
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

    # Force UTF-8 by replacing stdout/stderr streams entirely
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

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

# Wake words
WAKE_WORDS = [
    "sena", "세나", "hey sena", "ok sena", "세나야",
    "헤이 세나", "오케이 세나", "안녕 세나", "센아"
]

# Exit commands (말로 종료)
EXIT_COMMANDS = [
    "stop listening", "exit program", "shut down",
    "종료", "프로그램 종료", "나가기"
]

def play_beep(frequency=1000, duration=0.2):
    """Play activation beep"""
    try:
        import sounddevice as sd
        import numpy as np

        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration))
        beep = np.sin(2 * np.pi * frequency * t) * 0.3
        sd.play(beep, sample_rate)
        sd.wait()
    except Exception as e:
        print(f"[BEEP] (sound failed: {e})")

def record_audio(duration=3, sample_rate=16000):
    """Record audio from microphone"""
    try:
        import sounddevice as sd
        import numpy as np
        from scipy.io.wavfile import write
        import tempfile

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        filename = temp_file.name
        temp_file.close()

        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype='int16'
        )
        sd.wait()

        write(filename, sample_rate, recording)
        return filename

    except Exception as e:
        print(f"[ERROR] Recording failed: {str(e)}")
        return None

def play_audio(filename):
    """Play audio file"""
    try:
        import sounddevice as sd
        from scipy.io.wavfile import read

        sample_rate, data = read(filename)
        sd.play(data, sample_rate)
        sd.wait()
        return True

    except Exception as e:
        print(f"[ERROR] Playback failed: {str(e)}")
        return False

def transcribe_audio(audio_file, registry):
    """Transcribe audio file"""
    result = registry.call("audio", {
        "audio_path": audio_file,
        "prompt": "Transcribe this short audio clip"
    })

    if not result.get("ok"):
        return None

    return result.get("text", "").lower().strip()

def detect_wake_word(text):
    """Check if text contains wake word"""
    for wake_word in WAKE_WORDS:
        if wake_word in text:
            return True
    return False

def detect_exit_command(text):
    """Check if text contains exit command"""
    for exit_cmd in EXIT_COMMANDS:
        if exit_cmd in text:
            return True
    return False

def listen_mode(registry):
    """Continuous listening mode"""
    print("\n[LISTEN MODE] Listening for wake word...")
    print("Say: 'Hey Sena' or '세나야' to activate")
    print("Say: 'Stop listening' or '종료' to exit program")
    print()

    listen_count = 0

    while True:
        listen_count += 1

        # Record (3 seconds for better detection)
        audio_file = record_audio(duration=3)

        if not audio_file:
            time.sleep(0.5)
            continue

        # Transcribe
        text = transcribe_audio(audio_file, registry)

        # Cleanup
        try:
            os.remove(audio_file)
        except:
            pass

        if not text:
            print(".", end="", flush=True)
            time.sleep(0.1)
            continue

        # Show what was heard (every 3rd time to avoid spam)
        if listen_count % 3 == 0:
            print(f"\n[HEARD] \"{text}\"", end=" ")

        # Check for exit command
        if detect_exit_command(text):
            print(f"\n\n[EXIT] Exit command detected!")
            print("Shutting down Hey Sena...")
            return False  # Exit program

        # Check for wake word
        if detect_wake_word(text):
            print(f"\n\n[ACTIVATED] Wake word detected: '{text}'")
            play_beep()
            return True  # Go to conversation mode

        print(".", end="", flush=True)
        time.sleep(0.1)

def conversation_mode(registry):
    """Active conversation mode"""
    print("\n[ACTIVE] Listening to your request...")
    print("(Speak now - 5 seconds)")

    audio_file = record_audio(duration=5)

    if not audio_file:
        print("[ERROR] Could not record. Returning to listen mode.")
        return True

    # Transcribe
    print("\n[PROCESSING] Transcribing...")
    text = transcribe_audio(audio_file, registry)

    try:
        os.remove(audio_file)
    except:
        pass

    if not text:
        print("[ERROR] Could not transcribe. Try again.")
        return True

    # Show what was heard
    print(f"\n[YOU SAID] \"{text}\"")

    # Check for goodbye
    if any(word in text for word in ["goodbye", "bye", "stop", "exit", "종료"]):
        print("[SENA] Goodbye! Say 'Hey Sena' to wake me again.")

        goodbye_file = "sena_goodbye.wav"
        tts_result = registry.call("tts", {
            "text": "Goodbye! Say Hey Sena to wake me again.",
            "output_path": goodbye_file,
            "voice": "Kore"
        })

        if tts_result.get("ok"):
            play_audio(goodbye_file)
            try:
                os.remove(goodbye_file)
            except:
                pass

        return True  # Back to listen mode

    # Generate response
    response_text = generate_response(text)
    print(f"[SENA] {response_text}")

    # TTS
    print("\n[TTS] Generating response...")
    response_file = "sena_response.wav"

    tts_result = registry.call("tts", {
        "text": response_text,
        "output_path": response_file,
        "voice": "Kore"
    })

    if not tts_result.get("ok"):
        print(f"[ERROR] TTS failed: {tts_result.get('error')}")
        return True

    # Play
    play_audio(response_file)

    try:
        os.remove(response_file)
    except:
        pass

    print("\n[COMPLETE] Returning to listen mode...")
    time.sleep(0.5)

    return True

def generate_response(user_text):
    """Generate AGI response"""
    # Remove wake words
    user_lower = user_text.lower()
    for wake_word in WAKE_WORDS:
        user_lower = user_lower.replace(wake_word, "").strip()

    if not user_lower or len(user_lower) < 3:
        return "Yes? How can I help you?"

    if "hello" in user_lower or "hi" in user_lower:
        return "Hello! How can I help you today?"

    elif "how are you" in user_lower:
        return "I'm doing great! Thank you for asking."

    elif "what" in user_lower and ("name" in user_lower or "who" in user_lower):
        return "I am Sena, your FDO-AGI assistant."

    elif "time" in user_lower:
        from datetime import datetime
        now = datetime.now()
        return f"The current time is {now.strftime('%I:%M %p')}."

    elif "date" in user_lower or "today" in user_lower:
        from datetime import datetime
        now = datetime.now()
        return f"Today is {now.strftime('%A, %B %d, %Y')}."

    elif "weather" in user_lower or "날씨" in user_lower:
        return "I can check the weather for you. Which city are you interested in?"

    elif "thanks" in user_lower or "thank you" in user_lower or "고마" in user_lower:
        return "You're welcome! Anything else I can help with?"

    else:
        return f"I heard you say: {user_text}. How can I help you with that?"

def main():
    print("\n" + "=" * 60)
    print("Hey Sena v2 - Voice Activated AGI Assistant")
    print("=" * 60)
    print("\nIMPROVEMENTS:")
    print("  [+] Better wake word detection (3 sec recording)")
    print("  [+] Shows what it hears (debug mode)")
    print("  [+] Exit by saying 'Stop listening' or '종료'")
    print("  [+] No Ctrl+C needed!")
    print()

    # Check dependencies
    try:
        import sounddevice
        import numpy
        import scipy
    except ImportError:
        print("\n[ERROR] Missing dependencies!")
        print("Please install: pip install sounddevice numpy scipy")
        return 1

    # Initialize
    cfg = {
        "audio_enabled": True,
        "tts_enabled": True,
    }
    registry = ToolRegistry(cfg)

    print("=" * 60)
    print("System Ready!")
    print("=" * 60)

    try:
        while True:
            # Listen for wake word
            should_continue = listen_mode(registry)

            if not should_continue:
                # Exit command detected
                break

            # Conversation mode
            conversation_mode(registry)

    except KeyboardInterrupt:
        print("\n\n[STOPPED] Hey Sena stopped.")
        print("Goodbye!")

    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    print("\n" + "=" * 60)
    print("Hey Sena Shut Down")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
