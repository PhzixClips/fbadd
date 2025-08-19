"""
Facebook video extraction using yt-dlp.
"""
import json
import subprocess
from pathlib import Path
from typing import Optional, Dict

from config import YT_DLP_PATH
from utils.logging import log_upgrade


def is_facebook_url(url: str) -> bool:
    """Check if the URL is a Facebook URL."""
    return "facebook.com" in url.lower() or "fb.watch" in url.lower()

def normalize_facebook_url(url: str) -> str:
    """
    Basic normalization for a Facebook URL.
    - Trims whitespace.
    - More complex normalization (like removing tracking params) can be added later.
    """
    return url.strip()

def extract_facebook_metadata(url: str, cookies_path: Optional[str]) -> Dict:
    """
    Extract metadata from a Facebook URL using yt-dlp.
    """
    command = [
        YT_DLP_PATH,
        '--dump-json',
        '--no-warnings',
        '--no-call-home',
        '--concurrent-fragments', '4',
        url
    ]

    if cookies_path:
        command.extend(['--cookies', cookies_path])

    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'
        )
        return json.loads(process.stdout)
    except subprocess.CalledProcessError as e:
        # This often happens for private videos without cookies
        error_message = e.stderr.strip()
        if "private" in error_message.lower():
            return {"error": "private_video", "message": error_message}
        elif "unavailable" in error_message.lower():
            return {"error": "unavailable_video", "message": error_message}
        else:
            return {"error": "extraction_failed", "message": error_message}
    except json.JSONDecodeError:
        return {"error": "json_decode_error", "message": "Failed to parse yt-dlp output."}
    except Exception as e:
        return {"error": "unknown_error", "message": str(e)}


def download_facebook_video(url: str, cookies_path: Optional[str], output_path: Path) -> bool:
    """
    Download a video from Facebook using yt-dlp.
    """
    try:
        output_template = str(output_path / '%(title)s.%(ext)s')
        command = [
            YT_DLP_PATH,
            '-f', 'bestvideo*+bestaudio/best',
            '--merge-output-format', 'mp4',
            '--no-mtime',
            '-o', output_template,
            url
        ]

        if cookies_path:
            command.extend(['--cookies', cookies_path])

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )

        stdout, stderr = process.communicate()

        if process.returncode == 0:
            log_upgrade(f"Successfully downloaded Facebook video: {url}")
            return True
        else:
            log_upgrade(f"Facebook download failed for {url}: {stderr}")
            return False

    except Exception as e:
        log_upgrade(f"Facebook download error for {url}: {e}")
        return False
