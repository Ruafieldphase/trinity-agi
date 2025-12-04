#!/usr/bin/env python3
"""
Hey Sena - Voice Activated AGI Assistant
Works like Siri or Google Assistant
Say "Hey Sena" or "세나야" to activate
"""
import os
import sys
from pathlib import Path
import time
import threading

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

# Wake words that activate the assistant
WAKE_WORDS = [
    "sena", "세나", "hey sena", "ok sena", "세나야",
    "헤이 세나", "오케이 세나", "안녕 세나"
]

def check_dependencies():
    """Check if required libraries are available"""
    try:
        import sounddevice
        import numpy
        import scipy
        return True
    except ImportError:
        print("\n[ERROR] Missing dependencies!")
        print("Please install: pip install sounddevice numpy scipy")
        return False

def play_beep(frequency=1000, duration=0.2):
    """Play activation beep sound"""
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

        # Create temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        filename = temp_file.name
        temp_file.close()

        # Record
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype='int16'
        )
        sd.wait()

        # Save
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

def detect_wake_word(audio_file, registry):
    """Detect wake word in audio file"""
    # Transcribe audio
    result = registry.call("audio", {
        "audio_path": audio_file,
        "prompt": "Transcribe this short audio clip"
    })

    if not result.get("ok"):
        return False, ""

    text = result.get("text", "").lower().strip()

    # Check for wake words
    for wake_word in WAKE_WORDS:
        if wake_word in text:
            return True, text

    return False, text

def generate_response(user_text):
    """Generate AGI response (can be enhanced with LLM)"""
    user_lower = user_text.lower()

    # Remove wake word from query
    for wake_word in WAKE_WORDS:
        user_lower = user_lower.replace(wake_word, "").strip()

    if not user_lower or len(user_lower) < 3:
        return "Yes? How can I help you?"

    # Simple response logic
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

    elif "weather" in user_lower:
        return "I can check the weather for you. Which city are you interested in?"

    elif "thanks" in user_lower or "thank you" in user_lower:
        return "You're welcome! Anything else I can help with?"

    elif "bye" in user_lower or "goodbye" in user_lower:
        return "Goodbye! Say 'Hey Sena' anytime you need me."

    else:
        return f"I heard you say: {user_text}. How can I help you with that?"

def listen_mode(registry):
    """Continuous listening mode - detects wake word"""
    print("\n[LISTEN MODE] Listening for wake word...")
    print("Say: 'Hey Sena' or '세나야' to activate")
    print()

    while True:
        # Record short clip (2 seconds)
        print(".", end="", flush=True)
        audio_file = record_audio(duration=2)

        if not audio_file:
            time.sleep(0.5)
            continue

        # Check for wake word
        detected, text = detect_wake_word(audio_file, registry)

        # Cleanup temp file
        try:
            os.remove(audio_file)
        except:
            pass

        if detected:
            print(f"\n\n[ACTIVATED] Wake word detected: '{text}'")
            play_beep()  # Activation sound
            return True

        time.sleep(0.1)  # Small delay

def conversation_mode(registry):
    """Active conversation mode"""
    print("\n[ACTIVE] Listening to your request...")
    print("(Speak now - 5 seconds)")

    # Record user request (longer duration)
    audio_file = record_audio(duration=5)

    if not audio_file:
        print("[ERROR] Could not record. Returning to listen mode.")
        return True  # Continue listening

    # Transcribe
    print("\n[PROCESSING] Transcribing...")
    result = registry.call("audio", {
        "audio_path": audio_file,
        "prompt": "Transcribe this speech accurately"
    })

    try:
        os.remove(audio_file)
    except:
        pass

    if not result.get("ok"):
        print(f"[ERROR] Transcription failed: {result.get('error')}")
        return True

    user_text = result.get("text", "").strip()
    print(f"\n[YOU] {user_text}")

    # Check for exit
    if any(word in user_text.lower() for word in ["goodbye", "bye", "stop", "exit"]):
        print("[SENA] Goodbye! Say 'Hey Sena' to wake me up again.")

        # Generate goodbye speech
        goodbye_file = "sena_goodbye.wav"
        tts_result = registry.call("tts", {
            "text": "Goodbye! Say Hey Sena to wake me up again.",
            "output_path": goodbye_file,
            "voice": "Kore"
        })

        if tts_result.get("ok"):
            play_audio(goodbye_file)
            try:
                os.remove(goodbye_file)
            except:
                pass

        return True  # Continue listening (not exit program)

    # Generate response
    response_text = generate_response(user_text)
    print(f"[SENA] {response_text}")

    # Generate speech
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

    # Play response
    play_audio(response_file)

    try:
        os.remove(response_file)
    except:
        pass

    print("\n[COMPLETE] Returning to listen mode...")
    time.sleep(0.5)

    return True  # Continue listening

def main():
    print("\n" + "=" * 60)
    print("Hey Sena - Voice Activated AGI Assistant")
    print("=" * 60)
    print("\nWorks like Siri or Google Assistant!")
    print("Say 'Hey Sena' or '세나야' to activate\n")

    # Check dependencies
    if not check_dependencies():
        return 1

    # Initialize registry
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
            listen_mode(registry)

            # Enter conversation mode
            conversation_mode(registry)

    except KeyboardInterrupt:
        print("\n\n[STOPPED] Hey Sena stopped by user.")
        print("Goodbye!")
        return 0

    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
