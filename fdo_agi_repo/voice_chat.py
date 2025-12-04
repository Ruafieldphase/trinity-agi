#!/usr/bin/env python3
"""
FDO-AGI Voice Chat
Real-time voice conversation with microphone and speaker
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

    # Check pyaudio
    try:
        import pyaudio
        print("[OK] pyaudio installed")
    except ImportError:
        print("[MISSING] pyaudio not installed")
        missing.append("pyaudio")

    # Check wave (standard library)
    try:
        import wave
        print("[OK] wave module available")
    except ImportError:
        print("[ERROR] wave module missing (should be standard)")

    if missing:
        print("\n" + "=" * 60)
        print("MISSING DEPENDENCIES")
        print("=" * 60)
        print("\nTo install missing dependencies:")
        print(f"  pip install {' '.join(missing)}")
        print("\nNote: On Windows, if pip install pyaudio fails:")
        print("  1. Download wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/")
        print("  2. pip install PyAudio-0.2.11-cp3xx-cp3xx-win_amd64.whl")
        print()
        return False

    print("\n[SUCCESS] All dependencies available!")
    return True

def record_audio(filename="user_input.wav", duration=5, sample_rate=16000):
    """Record audio from microphone"""
    try:
        import pyaudio
        import wave

        print(f"\n[MIC] Recording for {duration} seconds...")
        print("      Speak now!")

        # Initialize PyAudio
        p = pyaudio.PyAudio()

        # Open stream
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            frames_per_buffer=1024
        )

        frames = []

        # Record
        for i in range(0, int(sample_rate / 1024 * duration)):
            data = stream.read(1024)
            frames.append(data)

            # Progress indicator
            if i % 10 == 0:
                print(".", end="", flush=True)

        print("\n[OK] Recording complete!")

        # Stop and close stream
        stream.stop_stream()
        stream.close()
        p.terminate()

        # Save to file
        wf = wave.open(filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(frames))
        wf.close()

        file_size = os.path.getsize(filename)
        print(f"[SAVED] {filename} ({file_size:,} bytes)")

        return True

    except Exception as e:
        print(f"[ERROR] Recording failed: {str(e)}")
        return False

def play_audio(filename):
    """Play audio file through speaker"""
    try:
        import pyaudio
        import wave

        print(f"\n[SPEAKER] Playing {filename}...")

        # Open WAV file
        wf = wave.open(filename, 'rb')

        # Initialize PyAudio
        p = pyaudio.PyAudio()

        # Open stream
        stream = p.open(
            format=p.get_format_from_width(wf.getsampwidth()),
            channels=wf.getnchannels(),
            rate=wf.getframerate(),
            output=True
        )

        # Play audio
        data = wf.readframes(1024)
        while len(data) > 0:
            stream.write(data)
            data = wf.readframes(1024)

        # Cleanup
        stream.stop_stream()
        stream.close()
        p.terminate()
        wf.close()

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
    print("  1. You will hear a beep (silence)")
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

        if not record_audio(user_audio_file, duration=5):
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
            os.remove(user_audio_file)
            continue

        user_text = stt_result.get("text", "").strip()
        print(f"[YOU SAID] {user_text}")

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
                play_audio(goodbye_file)
                os.remove(goodbye_file)

            os.remove(user_audio_file)
            break

        # Generate AGI response (simple echo for now)
        # In real use, this would call LLM
        agi_response = generate_agi_response(user_text)
        print(f"[AGI RESPONDS] {agi_response}")

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
            os.remove(user_audio_file)
            continue

        # Play AGI response
        play_audio(agi_audio_file)

        # Cleanup
        os.remove(user_audio_file)
        os.remove(agi_audio_file)

        print("\n[TURN COMPLETE]")
        time.sleep(0.5)

    print("\n" + "=" * 60)
    print("Voice Chat Session Ended")
    print("=" * 60)

def generate_agi_response(user_text):
    """Generate AGI response (placeholder - would use LLM in production)"""

    # Simple response logic for demo
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

    else:
        return f"I heard you say: {user_text}. That's interesting! Tell me more."

def main():
    print("\n" + "=" * 60)
    print("FDO-AGI Voice Chat System")
    print("Real-time Microphone Conversation")
    print("=" * 60 + "\n")

    # Check dependencies
    if not check_dependencies():
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
