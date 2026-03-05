import subprocess
import os
from pathlib import Path

def generate_lumen_video(audio_path, image_paths, output_path):
    """
    Combines images and audio into a cinematic video using FFmpeg.
    Applies a slow zoom effect (Ken Burns) to each image.
    """
    print(f"🎬 [ENGINE] Generating video for: {audio_path}")
    
    # Validation
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio not found: {audio_path}")
    for p in image_paths:
        if not os.path.exists(p):
            raise FileNotFoundError(f"Image not found: {p}")

    # Get audio duration
    try:
        cmd_duration = [
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', audio_path
        ]
        duration = float(subprocess.check_output(cmd_duration).decode().strip())
    except Exception as e:
        print(f"❌ Error getting duration: {e}. Defaulting to 180s.")
        duration = 180.0
    
    # Calculate duration per image
    per_image_duration = duration / len(image_paths)
    
    # Build FFmpeg command (Complex Filter for Ken Burns Effect)
    # This filter takes each image, scales it, and applies a slow zoom-in.
    filter_complex = ""
    inputs = ""
    for i, img in enumerate(image_paths):
        inputs += f"-loop 1 -t {per_image_duration} -i \"{img}\" "
        # Simple zoom-in effect: zoompan filter
        # s=1920x1080: output size
        # d=duration in frames (assumed 24fps)
        frames = int(per_image_duration * 24)
        # Using a safer zoompan syntax for Windows compatibility
        filter_complex += f"[{i}:v]scale=8000:-1,zoompan=z='zoom+0.0005':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080[v{i}];"
    
    # Concatenate clips
    filter_complex += "".join([f"[v{i}]" for i in range(len(image_paths))])
    filter_complex += f"concat=n={len(image_paths)}:v=1:a=0[outv]"

    # Final Command
    cmd = [
        'ffmpeg', '-y'
    ]
    # Splitting inputs
    for i, img in enumerate(image_paths):
        cmd += ['-loop', '1', '-t', str(per_image_duration), '-i', img]
    cmd += ['-i', audio_path]
    cmd += ['-filter_complex', filter_complex]
    cmd += ['-map', '[outv]', '-map', f'{len(image_paths)}:a']
    cmd += ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-r', '24', '-b:v', '5M', '-shortest', output_path]
    
    print(f"🚀 [EXEC] Running FFmpeg assembly...")
    subprocess.run(cmd, check=True)
    print(f"✅ [SUCCESS] Video created: {output_path}")

if __name__ == "__main__":
    # Test path resolution
    AUD = r"D:\ARCHIVE_WORKSPACE\agi\music\Resonance of Lumen.wav"
    IMGS = [
        r"C:\Users\kuirv\.gemini\antigravity\brain\353fbbae-c45e-495b-97f2-3a66c2e7b4ff\lumen_phase_1_void_mu_1772333669972.png",
        r"C:\Users\kuirv\.gemini\antigravity\brain\353fbbae-c45e-495b-97f2-3a66c2e7b4ff\lumen_phase_2_awakening_proton_1772333686546.png",
        r"C:\Users\kuirv\.gemini\antigravity\brain\353fbbae-c45e-495b-97f2-3a66c2e7b4ff\resonance_lumen_visual_bridge_1772333510386.png",
        r"C:\Users\kuirv\.gemini\antigravity\brain\353fbbae-c45e-495b-97f2-3a66c2e7b4ff\lumen_phase_3_unified_resonance_1772333712261.png"
    ]
    OUT = r"C:\workspace\agi\lumen_factory\Resonance_of_Lumen_PV.mp4"
    
    try:
        generate_lumen_video(AUD, IMGS, OUT)
    except Exception as e:
        print(f"❌ Assembly failed: {e}")
