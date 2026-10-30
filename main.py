import sys
import yt_dlp
from yt_dlp.utils import DownloadError, ExtractorError

# (substring in the error message, friendly explanation)
KNOWN_ERRORS = [
    ("private video", "Private video. You need to be logged in with an account that has access (try cookies)."),
    ("members-only", "Members-only video. Needs cookies from an account that is a member."),
    ("join this channel", "Members-only video. Needs cookies from an account that is a member."),
    ("confirm your age", "Age-restricted video. Try cookies from a logged-in browser."),
    ("age-restricted", "Age-restricted video. Try cookies from a logged-in browser."),
    ("not a bot", "YouTube bot check. Try cookies from a logged-in browser or a different IP."),
    ("in your country", "Region-locked video. It's not available where you are."),
    ("not available in your", "Region-locked video. It's not available where you are."),
    ("premieres in", "Premiere hasn't started yet. Try again after it begins."),
    ("will begin in", "Live event hasn't started yet. Try again after it begins."),
    ("drm", "DRM-protected content (paid/rented). Can't be downloaded."),
    ("video unavailable", "Video unavailable. It may have been deleted or made private."),
    ("requested format is not available", "Requested format isn't available. Try a looser format string."),
]


def explain(error: Exception) -> str:
    msg = str(error).lower()
    for needle, explanation in KNOWN_ERRORS:
        if needle in msg:
            return explanation
    return f"Unknown download error: {error}"


def progress_hook(d: dict) -> None:
    if d["status"] == "downloading":
        percent = d.get("_percent_str", "?").strip()
        speed = d.get("_speed_str", "?").strip()
        eta = d.get("_eta_str", "?").strip()
        print(f"\r{percent} at {speed}, ETA {eta}   ", end="", flush=True)
    elif d["status"] == "finished":
        print("\nDownload finished, merging video + audio with ffmpeg...")


def download(url: str, max_height: int = 1080) -> bool:
    opts = {
        # best video (capped) + best audio, fall back to best single file
        "format": f"bv*[height<={max_height}]+ba/b[height<={max_height}]/b",
        "merge_output_format": "mp4",
        "outtmpl": "%(title)s.%(ext)s",
        "progress_hooks": [progress_hook],
        "noplaylist": True,   # single video even if the URL has a playlist id
        "quiet": True,
        "no_warnings": True,
        # Comment it if you don't need login (private/age-restricted/bot check):
        "cookiesfrombrowser": ("chrome",),
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        print("Done!")
        return True
    except (DownloadError, ExtractorError) as e:
        print(f"\nFailed: {explain(e)}")
    except KeyboardInterrupt:
        print("\nCancelled.")
    except Exception as e:  # e.g. ffmpeg missing, disk full, no network
        print(f"\nUnexpected error: {e}")
    return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python yt_download.py <youtube_url> [max_height]")
        sys.exit(1)

    url = sys.argv[1]
    height = int(sys.argv[2]) if len(sys.argv) > 2 else 1080
    sys.exit(0 if download(url, height) else 1)