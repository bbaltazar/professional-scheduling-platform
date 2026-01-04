# 🎬 Video Compression Guide

Simple Python script to compress videos using FFmpeg.

## Quick Start

```bash
# Install FFmpeg first (if not already installed)
brew install ffmpeg  # macOS
# sudo apt-get install ffmpeg  # Linux

# Basic compression (default settings)
python scripts/compress_video.py your_video.mov -o compressed.mp4

# High quality compression
python scripts/compress_video.py your_video.mov -o output.mp4 -q high

# Compress to 720p (smaller file)
python scripts/compress_video.py your_video.mov -o output.mp4 -r 720p

# Maximum compression
python scripts/compress_video.py your_video.mov -o output.mp4 -q low -r 720p
```

## Quality Presets

| Preset     | CRF | File Size | Quality | Use Case |
|------------|-----|-----------|---------|----------|
| `low`      | 28  | Smallest  | Acceptable | Sharing on chat apps |
| `medium`   | 23  | Balanced  | Good | **Default - recommended** |
| `high`     | 20  | Larger    | Excellent | Archiving, YouTube |
| `veryhigh` | 18  | Largest   | Near lossless | Professional use |

**Lower CRF = Better quality, Larger file**

## Resolution Presets

- `original` - Keep original resolution (default)
- `720p` - Compress to 1280x720 (HD)
- `1080p` - Compress to 1920x1080 (Full HD)

## Common Use Cases

### 1. Compress for Email/Messaging
```bash
python scripts/compress_video.py large_video.mov -o small.mp4 -q low -r 720p
```
**Result**: Very small file, suitable for email attachments

### 2. Balanced Quality (Recommended)
```bash
python scripts/compress_video.py video.mov -o compressed.mp4
```
**Result**: Good quality, reasonable file size (default settings)

### 3. High Quality Archive
```bash
python scripts/compress_video.py video.mov -o archive.mp4 -q veryhigh --two-pass
```
**Result**: Excellent quality with optimal compression

### 4. Convert Format
```bash
python scripts/compress_video.py video.avi -o video.mp4 -q medium
```
**Result**: Converts AVI to MP4 while compressing

### 5. Compress for Web/Streaming
```bash
python scripts/compress_video.py video.mov -o web.mp4 -q high -r 1080p --two-pass
```
**Result**: Optimized for web playback

## Advanced Options

```bash
# Custom CRF value
python scripts/compress_video.py video.mov -o output.mp4 --crf 25

# Adjust audio quality
python scripts/compress_video.py video.mov -o output.mp4 --audio-bitrate 192k

# Different encoding speed (slower = better compression)
python scripts/compress_video.py video.mov -o output.mp4 --preset slow

# Two-pass encoding (better quality/size ratio, takes longer)
python scripts/compress_video.py video.mov -o output.mp4 --two-pass

# WebM format (better for web, not all players support it)
python scripts/compress_video.py video.mov -o output.webm --format webm
```

## Understanding Output

The script shows:
- **Original size** - Your input video size
- **Compressed size** - Final output size
- **Reduction %** - How much smaller it is
- **Video info** - Resolution, codec, bitrate, duration

Example output:
```
📹 Input Video Info:
   Size: 450.23 MB
   Duration: 120.45 seconds
   Bitrate: 30000 kbps
   Resolution: 1920x1080
   Codec: h264
   FPS: 30.00

✅ Compression complete!
   Output: compressed.mp4
   Size: 85.67 MB

📊 Compression Results:
   Original: 450.23 MB
   Compressed: 85.67 MB
   Reduction: 81.0%
```

## Tips

1. **Start with defaults** - The medium preset works well for most cases
2. **Test small sections** - Use `--crf` to test different values on a short clip first
3. **Two-pass for best results** - Slower but better quality/size ratio
4. **720p for social media** - Most platforms compress anyway
5. **Keep originals** - Never overwrite your source files

## CRF Quick Reference

| CRF | Quality | When to Use |
|-----|---------|-------------|
| 18  | Visually lossless | Professional archiving |
| 20  | Excellent | High-quality sharing |
| 23  | Good (default) | General purpose |
| 28  | Acceptable | Space-constrained sharing |
| 32+ | Poor | Only if desperate for space |

## Batch Processing

To compress multiple videos:

```bash
# In scripts directory
for file in *.mov; do
    python compress_video.py "$file" -o "${file%.mov}_compressed.mp4" -q medium
done
```

## Troubleshooting

### "ffmpeg not found"
```bash
# Install FFmpeg
brew install ffmpeg  # macOS
sudo apt-get install ffmpeg  # Linux
```

### Output is too large
- Lower quality: `-q low`
- Reduce resolution: `-r 720p`
- Lower CRF: `--crf 28` (higher number = smaller file)

### Output quality is poor
- Higher quality: `-q high` or `-q veryhigh`
- Use two-pass: `--two-pass`
- Higher CRF: `--crf 18` (lower number = better quality)

### Slow processing
- Use faster preset: `--preset fast` or `--preset ultrafast`
- Skip two-pass encoding
- Use original resolution (don't scale)

---

**Made a mistake?** Just delete the output file and run again with different settings!
