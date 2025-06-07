"""
Download all your YouTube-based assets—gameplay backgrounds and lofi tracks—
as best-available single files.  Saves everything as .mp4.
"""

import json
from pathlib import Path
import yt_dlp

# output folders
VIDEO_DIR = Path("videos")
MUSIC_DIR = Path("music")
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
MUSIC_DIR.mkdir(parents=True, exist_ok=True)

def load_metadata(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("__")}

def download_one(uri: str, filename: str, out_dir: Path):
    target_stem = Path(filename).stem
    outtmpl = str(out_dir / f"{target_stem}.%(ext)s")
    # skip if already downloaded
    existing = list(out_dir.glob(f"{target_stem}.*"))
    if existing:
        print(f"[SKIP] {filename} (already have {existing[0].name})")
        return

    print(f"[DL] {uri} → {filename}")
    ydl_opts = {
        "format": "best",               # grab best muxed stream
        "outtmpl": outtmpl,
        "nocheckcertificate": True,
        "geo_bypass": True,
        "retries": 3,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept-Language": "en-US,en;q=0.9",
        },
        "extractor_args": {
            "youtube": {"player_client": ["android", "android_exo"]}
        },
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(uri, download=True)
        ext = info.get("ext", "mp4")
    final = out_dir / f"{target_stem}.{ext}"
    if final.exists():
        print(f"[OK] saved {final.name}")
    else:
        print(f"[ERR] failed {filename}")

def main():
    bg_meta = load_metadata(Path("backgrounds.json"))
    for key, (uri, filename, *_ ) in bg_meta.items():
        download_one(uri, filename, VIDEO_DIR)

    lofi_meta = load_metadata(Path("lofi.json"))
    for key, (uri, filename, *_ ) in lofi_meta.items():
        download_one(uri, filename, MUSIC_DIR)

if __name__ == "__main__":
    main()
