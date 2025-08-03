"""
YouTube Playlist to MP3 Music Archiver
A comprehensive tool to download YouTube playlists as high-quality MP3s with metadata and cover art.
"""

import os
import sys
import re
import json
import time
import shutil
import logging
import requests
import subprocess
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from typing import Dict, List, Optional, Tuple

try:
    import yt_dlp, lyricsgenius
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON, APIC, USLT
    from mutagen.id3._util import ID3NoHeaderError
except ImportError as e:
    print(f"Missing required package: {e}")
    print("Install with: pip install yt-dlp mutagen lyricsgenius requests")
    sys.exit(1)

class YouTubeMP3Archiver:
    def __init__(self, output_dir: str = "Downloaded_Playlists", quality: str = "320"):
        """
        Initialize the YouTube MP3 Archiver
        
        Args:
            output_dir: Directory to save downloaded music
            quality: MP3 quality in kbps (320, 256, 192, 128)
        """
        self.output_dir = Path(output_dir)
        self.quality = quality
        self.setup_logging()
        self.setup_directories()
        
        # API configurations
        self.genius_token = None  # Set this if you have a Genius API token
        self.genius = None
        
        # iTunes API endpoint
        self.itunes_api = "https://itunes.apple.com/search"
        
        self.temp_dir = self.output_dir / "temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)


        # yt-dlp configuration
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(self.temp_dir / '%(title).100s.%(ext)s'),
            'noplaylist': False,
            'quiet': True,
            'no_warnings': True,
            'writeinfojson': True,
            'writethumbnail': True,
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': self.quality,  # like "320"
                },
                {
                    'key': 'EmbedThumbnail',
                },
                {
                    'key': 'FFmpegMetadata',
                }
            ],
        }


    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('youtube_archiver.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_directories(self):
        """Create necessary directories"""
        self.output_dir.mkdir(exist_ok=True)
        self.temp_dir = self.output_dir / "temp"
        self.temp_dir.mkdir(exist_ok=True)

    def setup_genius_api(self, token: str):
        """Setup Genius API for lyrics fetching"""
        self.genius_token = token
        try:
            self.genius = lyricsgenius.Genius(token)
            self.genius.verbose = False
            self.genius.remove_section_headers = True
            self.logger.info("Genius API initialized successfully")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Genius API: {e}")

    def clean_filename(self, filename: str) -> str:
        """Clean filename for filesystem compatibility"""
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Remove extra spaces and dots
        filename = re.sub(r'\s+', ' ', filename).strip()
        filename = filename.strip('.')
        # Limit length
        if len(filename) > 200:
            filename = filename[:200]
        return filename

    def extract_playlist_info(self, playlist_url: str) -> Tuple[str, List[Dict]]:
        """Extract playlist information and video list"""
        self.logger.info(f"Extracting playlist info from: {playlist_url}")
        
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                playlist_info = ydl.extract_info(playlist_url, download=False)
                
                playlist_title = self.clean_filename(playlist_info.get('title', 'Unknown Playlist'))
                videos = playlist_info.get('entries', [])
                
                self.logger.info(f"Found playlist: {playlist_title} with {len(videos)} videos")
                return playlist_title, videos
                
        except Exception as e:
            self.logger.error(f"Failed to extract playlist info: {e}")
            raise

    def download_audio(self, video_info: Dict, output_path: Path) -> Optional[Path]:
        """Download audio from a single video"""
        try:
            video_url = video_info.get('webpage_url') or f"https://youtube.com/watch?v={video_info['id']}"
            title = video_info.get('title', 'Unknown')
            
            self.logger.info(f"Downloading: {title}")
            
            # Configure output template
            ydl_opts = self.ydl_opts.copy()
            ydl_opts['outtmpl'] = str(output_path / '%(title)s.%(ext)s')
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
                
            # Find the downloaded file
            for file in output_path.glob("*.mp3"):
                if title.lower() in file.stem.lower():
                    return file
                    
            # Fallback: return the most recent mp3 file
            mp3_files = list(output_path.glob("*.mp3"))
            if mp3_files:
                return max(mp3_files, key=os.path.getctime)
                
        except Exception as e:
            self.logger.error(f"Failed to download {title}: {e}")
            return None

    def search_itunes_metadata(self, title: str, artist: str = "") -> Optional[Dict]:
        """Search iTunes API for track metadata"""
        try:
            # Clean up search terms
            search_term = f"{artist} {title}".strip()
            search_term = re.sub(r'[^\w\s]', ' ', search_term)
            search_term = re.sub(r'\s+', ' ', search_term).strip()
            
            params = {
                'term': search_term,
                'media': 'music',
                'entity': 'song',
                'limit': 5
            }
            
            response = requests.get(self.itunes_api, params=params, timeout=10)
            data = response.json()
            
            if data.get('results'):
                # Return the first result (usually most relevant)
                result = data['results'][0]
                return {
                    'title': result.get('trackName', title),
                    'artist': result.get('artistName', artist),
                    'album': result.get('collectionName', ''),
                    'genre': result.get('primaryGenreName', ''),
                    'year': result.get('releaseDate', '')[:4] if result.get('releaseDate') else '',
                    'artwork_url': result.get('artworkUrl100', '').replace('100x100', '600x600')
                }
        except Exception as e:
            self.logger.warning(f"iTunes API search failed for '{title}': {e}")
            
        return None

    def download_cover_art(self, artwork_url: str) -> Optional[bytes]:
        """Download cover art from URL"""
        if not artwork_url:
            return None
            
        try:
            response = requests.get(artwork_url, timeout=15)
            if response.status_code == 200:
                return response.content
        except Exception as e:
            self.logger.warning(f"Failed to download cover art: {e}")
            
        return None

    def get_lyrics(self, title: str, artist: str) -> Optional[str]:
        """Fetch lyrics using Genius API"""
        if not self.genius:
            return None
            
        try:
            song = self.genius.search_song(title, artist)
            if song:
                return song.lyrics
        except Exception as e:
            self.logger.warning(f"Failed to fetch lyrics for '{title}' by {artist}: {e}")
            
        return None

    def extract_artist_title(self, video_title: str) -> Tuple[str, str]:
        """Extract artist and title from video title"""
        # Common patterns for "Artist - Title" or "Artist: Title"
        patterns = [
            r'^(.+?)\s*[-–—]\s*(.+)$',
            r'^(.+?)\s*:\s*(.+)$',
            r'^(.+?)\s*\|\s*(.+)$',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, video_title.strip())
            if match:
                artist = match.group(1).strip()
                title = match.group(2).strip()
                
                # Remove common suffixes
                title = re.sub(r'\s*\(.*?\)\s*$', '', title)
                title = re.sub(r'\s*\[.*?\]\s*$', '', title)
                
                return artist, title
                
        # If no pattern matches, return empty artist and full title
        return "", video_title.strip()

    def add_metadata_to_mp3(self, mp3_path: Path, video_info: Dict, metadata: Optional[Dict] = None):
        """Add metadata to MP3 file"""
        try:
            # Load or create ID3 tags
            try:
                audio_file = MP3(str(mp3_path), ID3=ID3)
                audio_file.add_tags()
            except ID3NoHeaderError:
                audio_file = MP3(str(mp3_path))
                audio_file.add_tags()

            # Extract basic info
            video_title = video_info.get('title', 'Unknown')
            artist, title = self.extract_artist_title(video_title)
            
            # Use iTunes metadata if available
            if metadata:
                title = metadata.get('title', title)
                artist = metadata.get('artist', artist)
                album = metadata.get('album', '')
                genre = metadata.get('genre', '')
                year = metadata.get('year', '')
                artwork_url = metadata.get('artwork_url', '')
            else:
                album = ''
                genre = ''
                year = ''
                artwork_url = ''

            # Set basic tags
            audio_file.tags.add(TIT2(encoding=3, text=title))
            if artist:
                audio_file.tags.add(TPE1(encoding=3, text=artist))
            if album:
                audio_file.tags.add(TALB(encoding=3, text=album))
            if genre:
                audio_file.tags.add(TCON(encoding=3, text=genre))
            if year:
                audio_file.tags.add(TDRC(encoding=3, text=year))

            # Add cover art
            if artwork_url:
                cover_data = self.download_cover_art(artwork_url)
                if cover_data:
                    audio_file.tags.add(APIC(
                        encoding=3,
                        mime='image/jpeg',
                        type=3,  # Cover (front)
                        desc='Cover',
                        data=cover_data
                    ))

            # Add lyrics if available
            if self.genius and artist and title:
                lyrics = self.get_lyrics(title, artist)
                if lyrics:
                    audio_file.tags.add(USLT(encoding=3, lang='eng', desc='Lyrics', text=lyrics))

            # Save changes
            audio_file.save()
            self.logger.info(f"Added metadata to: {mp3_path.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to add metadata to {mp3_path.name}: {e}")

    def process_playlist(self, playlist_url: str, custom_name: str = "") -> Path:
        """Process entire playlist"""
        try:
            # Extract playlist info
            playlist_title, videos = self.extract_playlist_info(playlist_url)
            
            # Use custom name if provided
            if custom_name:
                playlist_title = self.clean_filename(custom_name)
            
            # Create playlist directory
            playlist_dir = self.output_dir / playlist_title
            playlist_dir.mkdir(exist_ok=True)
            
            self.logger.info(f"Processing {len(videos)} videos into: {playlist_dir}")
            
            successful_downloads = 0
            failed_downloads = []
            
            for i, video in enumerate(videos, 1):
                if not video:  # Skip unavailable videos
                    continue
                    
                video_title = video.get('title', f'Unknown Video {i}')
                self.logger.info(f"[{i}/{len(videos)}] Processing: {video_title}")
                
                try:
                    # Download audio
                    temp_path = self.temp_dir
                    audio_file = self.download_audio(video, temp_path)
                    
                    if not audio_file or not audio_file.exists():
                        failed_downloads.append(video_title)
                        continue
                    
                    # Search for metadata
                    artist, title = self.extract_artist_title(video_title)
                    metadata = self.search_itunes_metadata(title, artist)
                    
                    # Add metadata
                    self.add_metadata_to_mp3(audio_file, video, metadata)
                    
                    # Create final filename
                    if metadata:
                        final_artist = metadata.get('artist', artist)
                        final_title = metadata.get('title', title)
                    else:
                        final_artist = artist
                        final_title = title
                    
                    if final_artist:
                        final_name = f"{final_artist} - {final_title}.mp3"
                    else:
                        final_name = f"{final_title}.mp3"
                    
                    final_name = self.clean_filename(final_name)
                    final_path = playlist_dir / final_name
                    
                    # Move file to final location
                    shutil.move(str(audio_file), str(final_path))
                    successful_downloads += 1
                    
                    self.logger.info(f"✅ Completed: {final_name}")
                    
                    # Small delay to be respectful to APIs
                    time.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f"❌ Failed to process {video_title}: {e}")
                    failed_downloads.append(video_title)
                    continue
            
            # Cleanup temp files
            for temp_file in self.temp_dir.glob("*"):
                try:
                    temp_file.unlink()
                except:
                    pass
            
            # Summary
            self.logger.info(f"\n🎵 PLAYLIST DOWNLOAD COMPLETE 🎵")
            self.logger.info(f"Playlist: {playlist_title}")
            self.logger.info(f"Location: {playlist_dir}")
            self.logger.info(f"Successfully downloaded: {successful_downloads}/{len(videos)} tracks")
            
            if failed_downloads:
                self.logger.warning(f"Failed downloads: {len(failed_downloads)}")
                for failed in failed_downloads[:5]:  # Show first 5 failures
                    self.logger.warning(f"  - {failed}")
                if len(failed_downloads) > 5:
                    self.logger.warning(f"  ... and {len(failed_downloads) - 5} more")
            
            return playlist_dir
            
        except Exception as e:
            self.logger.error(f"Failed to process playlist: {e}")
            raise

def main():
    """Main function with CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="YouTube Playlist to MP3 Music Archiver",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python youtube_archiver.py "https://youtube.com/playlist?list=..." 
  python youtube_archiver.py "https://youtube.com/playlist?list=..." --name "My Awesome Playlist"
  python youtube_archiver.py "https://youtube.com/playlist?list=..." --quality 256 --genius-token "your_token"
        """
    )
    
    parser.add_argument("playlist_url", help="YouTube playlist URL")
    parser.add_argument("--name", help="Custom name for the playlist folder")
    parser.add_argument("--output", default="Downloaded_Playlists", help="Output directory (default: Downloaded_Playlists)")
    parser.add_argument("--quality", choices=["128", "192", "256", "320"], default="320", help="MP3 quality in kbps (default: 320)")
    parser.add_argument("--genius-token", help="Genius API token for lyrics (optional)")
    
    args = parser.parse_args()
    
    # Validate playlist URL
    if "playlist" not in args.playlist_url and "list=" not in args.playlist_url:
        print("❌ Error: Please provide a valid YouTube playlist URL")
        sys.exit(1)
    
    # Initialize archiver
    archiver = YouTubeMP3Archiver(output_dir=args.output, quality=args.quality)
    
    # Setup Genius API if token provided
    if args.genius_token:
        archiver.setup_genius_api(args.genius_token)
    
    try:
        # Process playlist
        output_dir = archiver.process_playlist(args.playlist_url, args.name or "")
        print(f"\n🎉 Success! Your music is ready at: {output_dir}")
        print(f"📱 Ready to transfer to SD card, phone, or music player!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Download cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()