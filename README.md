# 🎵 PyTunes-CLI

A comprehensive Python CLI tool to download YouTube playlists as high-quality MP3s with automatic metadata enrichment, cover art, and lyrics support.

## ✨ Features

- **High-Quality Audio**: Download playlists in 320 kbps MP3 format
- **Smart Metadata**: Automatic artist/title extraction and iTunes API metadata enrichment
- **Cover Art**: Automatically downloads and embeds album artwork
- **Lyrics Support**: Optional Genius API integration for lyrics embedding
- **Batch Processing**: Download entire playlists efficiently
- **Clean Organization**: Automatically organizes files with proper naming
- **Resume Support**: Handles interruptions gracefully
- **Comprehensive Logging**: Detailed logs for troubleshooting

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- FFmpeg (for audio processing)

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/Priyanshu10Anand/PyTunes-CLI.git
   cd PyTunes-CLI
   ```

2. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Install FFmpeg**

   **Windows:**

   - Download from [FFmpeg official site](https://ffmpeg.org/download.html)
   - Add to PATH environment variable

   **macOS:**

   ```bash
   brew install ffmpeg
   ```

   **Ubuntu/Debian:**

   ```bash
   sudo apt update
   sudo apt install ffmpeg
   ```

### Basic Usage

```bash
# Download a playlist with default settings (320 kbps)
python song.py "https://youtube.com/playlist?list=PLxxxxxxxxxxxxxx"

# Custom playlist name and quality
python song.py "https://youtube.com/playlist?list=PLxxxxxxxxxxxxxx" --name "My Awesome Playlist" --quality 256

# With lyrics support (requires Genius API token)
python song.py "https://youtube.com/playlist?list=PLxxxxxxxxxxxxxx" --genius-token "your_genius_token_here"
```

## 📖 Detailed Usage

### Command Line Options

```
python song.py <playlist_url> [options]

Required:
  playlist_url          YouTube playlist URL

Optional:
  --name NAME          Custom name for the playlist folder
  --output DIR         Output directory (default: Downloaded_Playlists)
  --quality QUALITY    MP3 quality: 128, 192, 256, 320 (default: 320)
  --genius-token TOKEN Genius API token for lyrics (optional)
```

### Examples

```bash
# Basic download
python song.py "https://www.youtube.com/playlist?list=PLFgquLnL59alCl_2TQvOiD5Vgm1hCaGSI"

# High-quality with custom name
python song.py "https://www.youtube.com/playlist?list=PLFgquLnL59alCl_2TQvOiD5Vgm1hCaGSI" \
  --name "Chill Vibes 2024" \
  --quality 320

# Complete setup with lyrics
python song.py "https://www.youtube.com/playlist?list=PLFgquLnL59alCl_2TQvOiD5Vgm1hCaGSI" \
  --name "Complete Collection" \
  --output "/path/to/music" \
  --genius-token "your_token_here"
```

## 🔧 Configuration

### Genius API Setup (Optional)

For lyrics support, you'll need a Genius API token:

1. Visit [Genius API](https://genius.com/api-clients)
2. Create a new API client
3. Copy the "Client Access Token"
4. Use it with the `--genius-token` parameter

### Output Structure

```
Downloaded_Playlists/
├── My Awesome Playlist/
│   ├── Artist - Song Title.mp3
│   ├── Another Artist - Another Song.mp3
│   └── ...
├── Another Playlist/
│   └── ...
└── temp/ (temporary files, auto-cleaned)
```

## 🎯 How It Works

1. **Playlist Analysis**: Extracts all video URLs from the YouTube playlist
2. **Audio Download**: Downloads highest quality audio using yt-dlp
3. **Metadata Enrichment**:
   - Parses artist/title from video titles
   - Searches iTunes API for accurate metadata
   - Downloads high-resolution cover art
4. **File Processing**:
   - Converts to MP3 with specified quality
   - Embeds metadata and cover art
   - Optionally adds lyrics from Genius
5. **Organization**: Creates clean, organized file structure

## 📊 Metadata Features

### Automatic Metadata Detection

The tool intelligently extracts artist and title information from video titles using common patterns:

- `Artist - Title`
- `Artist: Title`
- `Artist | Title`

### iTunes API Integration

Automatically searches iTunes for:

- ✅ Accurate track titles
- ✅ Artist names
- ✅ Album information
- ✅ Genre classification
- ✅ Release year
- ✅ High-resolution artwork (600x600px)

### ID3 Tags

Embeds comprehensive metadata:

- **TIT2**: Track title
- **TPE1**: Artist name
- **TALB**: Album name
- **TDRC**: Release year
- **TCON**: Genre
- **APIC**: Cover artwork
- **USLT**: Lyrics (with Genius API)

## ⚙️ Advanced Configuration

### Custom Quality Settings

| Quality | Bitrate  | File Size | Use Case               |
| ------- | -------- | --------- | ---------------------- |
| 128     | 128 kbps | Small     | Mobile/Storage limited |
| 192     | 192 kbps | Medium    | Good balance           |
| 256     | 256 kbps | Large     | High quality           |
| 320     | 320 kbps | Largest   | Audiophile/Archive     |

### Logging

The tool creates detailed logs in `youtube_archiver.log` for:

- Download progress
- Metadata search results
- Error tracking
- API responses

## 🛠️ Troubleshooting

### Common Issues

**"Missing required package" error:**

```bash
pip install yt-dlp mutagen lyricsgenius requests
```

**FFmpeg not found:**

- Ensure FFmpeg is installed and in your system PATH
- Test with: `ffmpeg -version`

**Playlist not found:**

- Verify the playlist URL is correct and public
- Check if the playlist exists and is accessible

**Slow downloads:**

- Large playlists take time due to respectful API rate limiting
- Consider using lower quality for faster processing

### Debug Mode

For detailed debugging, check the log file:

```bash
tail -f youtube_archiver.log
```

## 📝 File Naming

The tool uses intelligent file naming:

1. **With metadata**: `Artist - Title.mp3`
2. **Without artist**: `Title.mp3`
3. **Fallback**: Original video title (cleaned)

Special characters are automatically removed for filesystem compatibility.

## 🚫 Limitations

- **YouTube Terms**: Respect YouTube's Terms of Service
- **Copyright**: Only download content you have rights to use
- **Rate Limits**: APIs have rate limits; large playlists may take time
- **Quality**: Output quality depends on source material
- **Availability**: Some videos may become unavailable during processing

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚖️ Legal Notice

This tool is for personal use only. Users are responsible for complying with:

- YouTube's Terms of Service
- Copyright laws in their jurisdiction
- Fair use guidelines

Only download content you have the right to access and use.

## 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube download functionality
- [Mutagen](https://mutagen.readthedocs.io/) - Audio metadata handling
- [Genius](https://genius.com/) - Lyrics API
- [iTunes Search API](https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/) - Metadata enrichment

## 📞 Support

If you encounter issues:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review the log file for detailed error information
3. Search existing [Issues](https://github.com/yourusername/youtube-playlist-archiver/issues)
4. Create a new issue with:
   - Error message
   - Operating system
   - Python version
   - Example playlist URL (if public)

---

**Made with ❤️ for music lovers who want to preserve their favorite playlists**
