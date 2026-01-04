#!/usr/bin/env python3
"""
Video Compression Script using FFmpeg

Compress videos with various quality presets and options.
Supports multiple output formats and compression levels.

Usage:
    python scripts/compress_video.py input.mp4 -o output.mp4 -q medium
    python scripts/compress_video.py input.mov --preset high --format mp4
"""

import argparse
import subprocess
import os
import sys
from pathlib import Path


def get_video_info(input_file):
    """Get video information using ffprobe"""
    try:
        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            input_file,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Parse basic info from output
        import json

        data = json.loads(result.stdout)

        if "format" in data:
            size_mb = int(data["format"].get("size", 0)) / (1024 * 1024)
            duration = float(data["format"].get("duration", 0))
            bitrate = int(data["format"].get("bit_rate", 0)) / 1000  # kbps

            print(f"\n📹 Input Video Info:")
            print(f"   Size: {size_mb:.2f} MB")
            print(f"   Duration: {duration:.2f} seconds")
            print(f"   Bitrate: {bitrate:.0f} kbps")

            for stream in data.get("streams", []):
                if stream["codec_type"] == "video":
                    print(
                        f"   Resolution: {stream.get('width')}x{stream.get('height')}"
                    )
                    print(f"   Codec: {stream.get('codec_name')}")
                    print(f"   FPS: {eval(stream.get('r_frame_rate', '0/1')):.2f}")
            print()

            return size_mb
    except FileNotFoundError:
        print("❌ Error: ffprobe not found. Please install FFmpeg:")
        print("   macOS: brew install ffmpeg")
        print("   Linux: sudo apt-get install ffmpeg")
        sys.exit(1)
    except Exception as e:
        print(f"⚠️  Warning: Could not get video info: {e}")
        return None


def compress_video(
    input_file,
    output_file,
    preset="medium",
    crf=23,
    scale=None,
    audio_bitrate="128k",
    format=None,
    two_pass=False,
):
    """
    Compress video using FFmpeg with H.264 codec

    Args:
        input_file: Path to input video
        output_file: Path to output video
        preset: FFmpeg preset (ultrafast, fast, medium, slow, veryslow)
        crf: Constant Rate Factor (0-51, lower = better quality, 23 is default)
        scale: Target resolution (e.g., '1280:720', '1920:1080', or '-1:720' to maintain aspect ratio)
        audio_bitrate: Audio bitrate (e.g., '128k', '192k', '256k')
        format: Output format (mp4, webm, mkv)
        two_pass: Use two-pass encoding for better quality
    """

    if not os.path.exists(input_file):
        print(f"❌ Error: Input file '{input_file}' not found!")
        return False

    # Auto-detect format from extension if not specified
    if format is None:
        format = Path(output_file).suffix.lstrip(".")

    # Build FFmpeg command
    cmd = ["ffmpeg", "-i", input_file]

    # Video codec and settings
    if format == "webm":
        # WebM uses VP9 codec
        cmd.extend(["-c:v", "libvpx-vp9", "-crf", str(crf), "-b:v", "0"])
    else:
        # MP4/MKV use H.264
        cmd.extend(["-c:v", "libx264", "-preset", preset, "-crf", str(crf)])

    # Resolution scaling
    if scale:
        cmd.extend(["-vf", f"scale={scale}"])

    # Audio settings
    cmd.extend(["-c:a", "aac", "-b:a", audio_bitrate])

    # Output file
    cmd.extend(["-y", output_file])  # -y to overwrite

    print(f"\n🎬 Compressing video...")
    print(f"   Preset: {preset}")
    print(f"   CRF: {crf} (lower = better quality)")
    print(f"   Scale: {scale or 'original'}")
    print(f"   Audio bitrate: {audio_bitrate}")
    if two_pass:
        print(f"   Mode: Two-pass encoding")
    print()

    try:
        if two_pass and format != "webm":
            # Two-pass encoding for better quality
            print("📊 Pass 1/2...")
            pass1_cmd = cmd[:-1] + [
                "-pass",
                "1",
                "-f",
                format,
                "/dev/null" if os.name != "nt" else "NUL",
            ]
            subprocess.run(pass1_cmd, check=True, capture_output=True)

            print("📊 Pass 2/2...")
            pass2_cmd = cmd[:-1] + ["-pass", "2", output_file]
            result = subprocess.run(pass2_cmd, check=True, capture_output=False)

            # Clean up log files
            for f in ["ffmpeg2pass-0.log", "ffmpeg2pass-0.log.mbtree"]:
                if os.path.exists(f):
                    os.remove(f)
        else:
            # Single-pass encoding
            result = subprocess.run(cmd, check=True, capture_output=False)

        if os.path.exists(output_file):
            output_size = os.path.getsize(output_file) / (1024 * 1024)
            print(f"\n✅ Compression complete!")
            print(f"   Output: {output_file}")
            print(f"   Size: {output_size:.2f} MB")

            return True
        else:
            print(f"\n❌ Error: Output file was not created")
            return False

    except subprocess.CalledProcessError as e:
        print(f"\n❌ FFmpeg error: {e}")
        return False
    except FileNotFoundError:
        print("\n❌ Error: ffmpeg not found. Please install FFmpeg:")
        print("   macOS: brew install ffmpeg")
        print("   Linux: sudo apt-get install ffmpeg")
        print("   Windows: Download from https://ffmpeg.org/download.html")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Compress videos using FFmpeg",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Quality Presets:
  low       - Smaller file, lower quality (CRF 28)
  medium    - Balanced quality/size (CRF 23) - DEFAULT
  high      - Better quality, larger file (CRF 20)
  veryhigh  - Excellent quality (CRF 18)
  
Resolution Presets:
  720p      - 1280x720
  1080p     - 1920x1080
  original  - Keep original resolution
  
Examples:
  # Basic compression (default medium quality)
  python scripts/compress_video.py video.mov -o compressed.mp4
  
  # High quality compression
  python scripts/compress_video.py video.mov -o output.mp4 -q high
  
  # Compress to 720p
  python scripts/compress_video.py video.mov -o output.mp4 -r 720p
  
  # Maximum compression (smallest file)
  python scripts/compress_video.py video.mov -o output.mp4 -q low -r 720p
  
  # Two-pass encoding for best quality/size ratio
  python scripts/compress_video.py video.mov -o output.mp4 --two-pass
        """,
    )

    parser.add_argument("input", help="Input video file")
    parser.add_argument(
        "-o", "--output", help="Output video file (default: input_compressed.mp4)"
    )
    parser.add_argument(
        "-q",
        "--quality",
        choices=["low", "medium", "high", "veryhigh"],
        default="medium",
        help="Quality preset (default: medium)",
    )
    parser.add_argument(
        "-r",
        "--resolution",
        choices=["720p", "1080p", "original"],
        default="original",
        help="Target resolution (default: original)",
    )
    parser.add_argument(
        "--crf", type=int, help="Custom CRF value (0-51, overrides quality preset)"
    )
    parser.add_argument(
        "--preset",
        choices=["ultrafast", "fast", "medium", "slow", "veryslow"],
        default="medium",
        help="FFmpeg encoding preset (default: medium)",
    )
    parser.add_argument(
        "--audio-bitrate", default="128k", help="Audio bitrate (default: 128k)"
    )
    parser.add_argument(
        "--format",
        choices=["mp4", "webm", "mkv"],
        help="Output format (default: auto-detect from extension)",
    )
    parser.add_argument(
        "--two-pass",
        action="store_true",
        help="Use two-pass encoding for better quality",
    )
    parser.add_argument(
        "--no-info", action="store_true", help="Skip video info display"
    )

    args = parser.parse_args()

    # Generate output filename if not provided
    if not args.output:
        input_path = Path(args.input)
        args.output = str(
            input_path.parent / f"{input_path.stem}_compressed{input_path.suffix}"
        )

    # Quality to CRF mapping
    quality_map = {"low": 28, "medium": 23, "high": 20, "veryhigh": 18}

    crf = args.crf if args.crf is not None else quality_map[args.quality]

    # Resolution to scale mapping
    scale_map = {
        "720p": "-1:720",  # Keep aspect ratio, height 720
        "1080p": "-1:1080",  # Keep aspect ratio, height 1080
        "original": None,
    }

    scale = scale_map[args.resolution]

    print("=" * 60)
    print("     VIDEO COMPRESSION TOOL")
    print("=" * 60)

    # Show input video info
    if not args.no_info:
        original_size = get_video_info(args.input)

    # Compress the video
    success = compress_video(
        input_file=args.input,
        output_file=args.output,
        preset=args.preset,
        crf=crf,
        scale=scale,
        audio_bitrate=args.audio_bitrate,
        format=args.format,
        two_pass=args.two_pass,
    )

    # Show comparison
    if success and not args.no_info and original_size:
        output_size = os.path.getsize(args.output) / (1024 * 1024)
        reduction = ((original_size - output_size) / original_size) * 100
        print(f"\n📊 Compression Results:")
        print(f"   Original: {original_size:.2f} MB")
        print(f"   Compressed: {output_size:.2f} MB")
        print(f"   Reduction: {reduction:.1f}%")

    print("\n" + "=" * 60)
    if success:
        print("     ✅ Compression completed successfully!")
    else:
        print("     ❌ Compression failed")
    print("=" * 60)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
