# 🎓 FFmpeg Parameters & Flags Explained

Complete breakdown of every parameter used in the video compression script.

---

## Basic FFmpeg Command Structure

```bash
ffmpeg -i input.mov [video options] [audio options] output.mp4
```

---

## 📥 Input Options

### `-i input_file`
**What it does**: Specifies the input video file  
**Example**: `-i video.mov`  
**Why we use it**: Required - tells FFmpeg which file to process

---

## 🎬 Video Codec Options

### `-c:v libx264`
**What it does**: Sets the video codec to H.264  
**Alternatives**:
- `libx265` - H.265/HEVC (better compression, slower encoding)
- `libvpx-vp9` - VP9 for WebM (open source, web-friendly)
- `copy` - Copy without re-encoding (fast but no compression)

**Why we use it**: H.264 is universally compatible and offers good compression

### `-c:v libvpx-vp9` (for WebM)
**What it does**: Uses VP9 codec for WebM format  
**Why we use it**: WebM requires VP9 or VP8 codec  
**Trade-off**: Better compression than H.264 but slower encoding

---

## ⚙️ Encoding Speed & Quality

### `-preset [ultrafast|fast|medium|slow|veryslow]`
**What it does**: Controls encoding speed vs compression efficiency  

| Preset | Speed | File Size | Quality | When to Use |
|--------|-------|-----------|---------|-------------|
| `ultrafast` | Fastest | Largest | Lower | Quick previews, real-time |
| `fast` | Fast | Larger | Good | General use, time-constrained |
| `medium` | Balanced | Balanced | Good | **Default - recommended** |
| `slow` | Slow | Smaller | Better | Archiving, final output |
| `veryslow` | Slowest | Smallest | Best | Professional work |

**Example**: `-preset medium`  
**Why we use it**: Balances encoding time and file size  
**Important**: This does NOT affect visual quality, only how efficiently it compresses

---

## 🎯 Quality Control

### `-crf [0-51]`
**What it does**: Constant Rate Factor - controls quality level  
**Full name**: Constant Rate Factor  
**Range**: 0 (lossless) to 51 (worst quality)

| CRF Value | Quality | File Size | Subjective Quality |
|-----------|---------|-----------|-------------------|
| 0 | Lossless | Huge | Perfect |
| 18 | Visually lossless | Very large | Indistinguishable from source |
| 20 | Excellent | Large | Excellent for archiving |
| 23 | Good (default) | Medium | **Recommended default** |
| 28 | Acceptable | Small | Good for web/sharing |
| 32 | Poor | Very small | Noticeable quality loss |
| 51 | Worst | Smallest | Unusable |

**Example**: `-crf 23`  
**Why we use it**: Maintains consistent quality throughout the video  
**Rule of thumb**: Lower CRF = better quality = larger file

### How CRF Works:
- FFmpeg automatically adjusts bitrate to maintain target quality
- Complex scenes get more bits, simple scenes get fewer bits
- Better than fixed bitrate for most use cases

---

## 📐 Resolution Scaling

### `-vf scale=WIDTH:HEIGHT`
**What it does**: Resizes the video  
**Full name**: Video Filter - Scale  
**Examples**:
- `scale=1280:720` - Exact 720p resolution
- `scale=-1:720` - Height 720, width auto (maintains aspect ratio)
- `scale=1920:-1` - Width 1920, height auto
- `scale=iw/2:ih/2` - Half the width and height

**Why we use -1**: 
- `-1` means "calculate automatically"
- `scale=-1:720` = "make height 720px, figure out width to maintain aspect ratio"
- Prevents distortion/stretching

**Common presets**:
```bash
# 720p HD (maintain aspect ratio)
-vf scale=-1:720

# 1080p Full HD (maintain aspect ratio)
-vf scale=-1:1080

# 4K UHD (maintain aspect ratio)
-vf scale=-1:2160

# Force exact size (may distort)
-vf scale=1920:1080
```

---

## 🔊 Audio Options

### `-c:a aac`
**What it does**: Sets audio codec to AAC  
**Why we use it**: AAC is universal and efficient  
**Alternatives**:
- `libmp3lame` - MP3 (widely compatible)
- `libopus` - Opus (better quality than AAC)
- `copy` - Keep original audio codec

### `-b:a 128k`
**What it does**: Sets audio bitrate to 128 kbps  
**Full name**: Audio bitrate

| Bitrate | Quality | Use Case |
|---------|---------|----------|
| 64k | Low | Voice-only, podcasts |
| 128k | Good | **Default - most videos** |
| 192k | Better | Music videos |
| 256k | Excellent | High-quality music |
| 320k | Best | Audiophile quality |

**Example**: `-b:a 192k`  
**Why 128k**: Good balance - most people can't tell difference from higher bitrates

---

## 🎭 Two-Pass Encoding

### `-pass 1` and `-pass 2`
**What it does**: Encodes the video twice for better quality/size ratio  

**How it works**:
1. **First pass** (`-pass 1`): 
   - Analyzes the entire video
   - Creates a log file with statistics
   - Figures out which scenes need more bits
   - Output goes to `/dev/null` (discarded)

2. **Second pass** (`-pass 2`):
   - Reads the log file from pass 1
   - Distributes bitrate optimally
   - Complex scenes get more bits
   - Simple scenes get fewer bits
   - Creates the actual output file

**Command structure**:
```bash
# Pass 1 (analysis)
ffmpeg -i input.mp4 -c:v libx264 -preset medium -b:v 2M -pass 1 -f mp4 /dev/null

# Pass 2 (encoding)
ffmpeg -i input.mp4 -c:v libx264 -preset medium -b:v 2M -pass 2 output.mp4
```

**Trade-offs**:
- ✅ Better quality at same file size
- ✅ OR smaller file at same quality
- ❌ Takes 2x as long (or more)
- ❌ Creates temporary log files

**When to use**:
- Final/archival versions
- Uploading to YouTube/Vimeo
- When file size is critical
- Professional work

**When NOT to use**:
- Quick compressions
- Testing/previewing
- When time is limited

---

## 🎨 Output Options

### `-y`
**What it does**: Automatically overwrite output file if it exists  
**Without it**: FFmpeg will ask "Overwrite? (y/N)"  
**Why we use it**: Automation - no manual confirmation needed

### `-f format`
**What it does**: Forces output format  
**Example**: `-f mp4`, `-f webm`, `-f mkv`  
**Usually optional**: FFmpeg auto-detects from file extension

---

## 📊 Information/Analysis Commands

### `ffprobe` (separate command)
**What it does**: Analyzes video files without encoding  
**Why we use it**: Get video info before compression

**Example command**:
```bash
ffprobe -v quiet -print_format json -show_format -show_streams input.mp4
```

**Flags explained**:
- `-v quiet` - Don't show verbose output
- `-print_format json` - Output as JSON (easy to parse)
- `-show_format` - Show file format info (duration, size, bitrate)
- `-show_streams` - Show stream info (resolution, codec, fps)

---

## 🧮 Calculating Bitrates

### Understanding Video Bitrate

**Formula**: `bitrate (kbps) = file_size (MB) × 8192 / duration (seconds)`

**Example**:
- File: 100 MB
- Duration: 60 seconds
- Bitrate: 100 × 8192 / 60 = ~13,653 kbps

### Recommended Bitrates by Resolution

| Resolution | Low Quality | Medium Quality | High Quality |
|------------|-------------|----------------|--------------|
| 480p | 500 kbps | 1,000 kbps | 2,500 kbps |
| 720p | 1,500 kbps | 2,500 kbps | 5,000 kbps |
| 1080p | 3,000 kbps | 5,000 kbps | 8,000 kbps |
| 4K | 15,000 kbps | 25,000 kbps | 50,000 kbps |

**Note**: With CRF encoding, you don't set bitrate directly - FFmpeg calculates it automatically to maintain quality

---

## 🎯 Complete Command Examples with Explanations

### Example 1: Basic Compression
```bash
ffmpeg -i input.mov -c:v libx264 -preset medium -crf 23 -c:a aac -b:a 128k output.mp4
```
**Breakdown**:
- `-i input.mov` - Input file
- `-c:v libx264` - Use H.264 video codec
- `-preset medium` - Balanced encoding speed
- `-crf 23` - Default quality (good)
- `-c:a aac` - Use AAC audio codec
- `-b:a 128k` - Audio at 128 kbps
- `output.mp4` - Output file

### Example 2: High Quality with Scaling
```bash
ffmpeg -i input.mov -c:v libx264 -preset slow -crf 18 -vf scale=-1:1080 -c:a aac -b:a 192k output.mp4
```
**Breakdown**:
- `-preset slow` - Better compression (takes longer)
- `-crf 18` - Excellent quality
- `-vf scale=-1:1080` - Resize to 1080p height, auto width
- `-b:a 192k` - Higher audio quality

### Example 3: Maximum Compression
```bash
ffmpeg -i input.mov -c:v libx264 -preset veryslow -crf 28 -vf scale=-1:720 -c:a aac -b:a 96k output.mp4
```
**Breakdown**:
- `-preset veryslow` - Best compression efficiency
- `-crf 28` - Lower quality but smaller file
- `-vf scale=-1:720` - Reduce to 720p
- `-b:a 96k` - Lower audio bitrate

### Example 4: Two-Pass for Best Results
```bash
# Pass 1
ffmpeg -i input.mov -c:v libx264 -preset slow -b:v 3M -pass 1 -f mp4 /dev/null

# Pass 2
ffmpeg -i input.mov -c:v libx264 -preset slow -b:v 3M -pass 2 -c:a aac -b:a 192k output.mp4
```
**Breakdown**:
- `-b:v 3M` - Target 3 Mbps video bitrate
- `-pass 1` - First pass (analysis)
- `-f mp4 /dev/null` - Discard pass 1 output
- `-pass 2` - Second pass (encoding)

---

## 🔍 Quick Reference Cheat Sheet

```bash
# QUALITY CONTROL
-crf 18      # Excellent quality
-crf 23      # Good quality (default)
-crf 28      # Lower quality, smaller file

# ENCODING SPEED
-preset ultrafast   # Fastest, largest file
-preset medium      # Balanced (default)
-preset veryslow    # Slowest, smallest file

# RESOLUTION
-vf scale=-1:720    # 720p (maintain aspect ratio)
-vf scale=-1:1080   # 1080p (maintain aspect ratio)

# AUDIO
-c:a aac -b:a 128k  # Standard audio
-c:a aac -b:a 192k  # Better audio
-c:a copy           # Keep original audio

# VIDEO CODEC
-c:v libx264        # H.264 (MP4)
-c:v libvpx-vp9     # VP9 (WebM)

# OTHER
-y                  # Overwrite output
-pass 1 / -pass 2   # Two-pass encoding
```

---

## 💡 Pro Tips

1. **Start with CRF 23** - It's the default for a reason
2. **Lower CRF by 1-2 if quality isn't good enough** - Small changes make big differences
3. **Use -preset slow for final outputs** - Worth the extra time
4. **Don't go below CRF 18** - Diminishing returns, huge files
5. **Scale resolution before adjusting CRF** - Bigger impact on file size
6. **Test on short clips first** - Use `-t 30` to encode only 30 seconds
7. **Audio bitrate matters less than you think** - 128k is fine for most content

---

**Questions?** Try the command with `--help`:
```bash
ffmpeg -h full > ffmpeg_help.txt
```
