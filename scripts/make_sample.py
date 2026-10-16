"""Generate synthetic vertical talking-head test video with TTS audio and vertical video."""
import subprocess
import sys
from pathlib import Path


def generate_synthetic_video(output_path="samples/synthetic.mp4"):
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    audio_file = out_file.parent / "temp_speech.mp3"
    
    # Realistic speech text incorporating phrases from reference screenshots
    text = (
        "Making money is basically a skills problem rather than a luck problem. "
        "Everything that is a skill can be learnt. "
        "Number one, stop planning and take action to monetise your ideas."
    )

    print(f"Generating TTS audio with edge-tts...")
    # Generate audio
    cmd_tts = [
        sys.executable,
        "-m",
        "edge_tts",
        "--text",
        text,
        "--write-media",
        str(audio_file),
        "--voice",
        "en-US-ChristopherNeural",
    ]
    subprocess.run(cmd_tts, check=True)

    # Get duration of audio with ffprobe
    probe_cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(audio_file)
    ]
    res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
    duration = float(res.stdout.strip())
    # Add a slight tail margin so the last word isn't clipped
    total_duration = duration + 0.5
    print(f"Audio duration: {duration:.2f}s, target video: {total_duration:.2f}s")

    # Generate 1080x1920 video at 30 fps with smooth subtle dark gradient background
    # using ffmpeg lavfi testsrc2 or color/gradients
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i", f"color=c=0x1a1e24:s=1080x1920:r=30:d={total_duration}",
        "-i", str(audio_file),
        "-vf", "drawbox=x=100:y=200:w=880:h=600:color=0x262c36@0.4:t=fill,drawbox=x=340:y=1100:w=400:h=500:color=0x2d3748@0.5:t=fill",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(out_file)
    ]
    print("Muxing video and audio with ffmpeg...")
    subprocess.run(ffmpeg_cmd, check=True)

    if audio_file.exists():
        audio_file.unlink()

    print(f"Successfully generated {out_file} ({out_file.stat().st_size} bytes)")


if __name__ == "__main__":
    generate_synthetic_video()
