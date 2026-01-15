import os
import time
import threading
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

# ======================
# CONFIG
# ======================
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

YTDL_BASE = {
    "quiet": True,
    "cookiefile": "cookies.txt",
    "nocheckcertificate": True,
    "ignoreerrors": True,
    "extractor_args": {
        "youtube": {
            "player_client": ["android"]
        }
    }
}

QUALITY_MAP = {
    "low": "64",
    "medium": "128",
    "high": "192",
    "veryhigh": "320"
}

# ======================
# UTILS
# ======================
def auto_delete(path, delay=1200):
    time.sleep(delay)
    if os.path.exists(path):
        os.remove(path)

# ======================
# ROUTES
# ======================

@app.route("/")
def home():
    return "YouTube Music Backend Running"

# ---------- SEARCH ----------
@app.route("/api/search")
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])

    search_url = f"https://music.youtube.com/search?q={q.replace(' ', '+')}"

    opts = {
        **YTDL_BASE,
        "extract_flat": True,
        "skip_download": True,
    }

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(search_url, download=False)

    results = []

    for v in info.get("entries", []):
        if not v:
            continue
        if v.get("_type") != "url":
            continue

        url = v.get("url", "")
        if "watch?v=" not in url:
            continue

        vid = url.split("watch?v=")[-1]

        results.append({
            "id": vid,
            "title": v.get("title", "Unknown title")
        })

    return jsonify(results[:10])

# ---------- STREAM ----------
@app.route("/api/stream/<vid>")
def stream(vid):
    if len(vid) < 8:
        return jsonify({"error": "invalid id"}), 400

    try:
        with yt_dlp.YoutubeDL(YTDL_BASE) as ydl:
            info = ydl.extract_info(
                f"https://www.youtube.com/watch?v={vid}",
                download=False
            )

        if not info:
            return jsonify({"error": "video info not available"}), 404

        audio_url = None
        for f in info.get("formats", []):
            if f.get("acodec") != "none" and f.get("vcodec") == "none":
                audio_url = f.get("url")
                break

        if not audio_url:
            return jsonify({"error": "audio not found"}), 404

        return jsonify({
            "stream_url": audio_url,
            "title": info.get("title", "Unknown"),
            "artist": info.get("uploader", "Unknown"),
            "thumbnail": info.get("thumbnail")
        })

    except Exception as e:
        print("STREAM ERROR:", e)
        return jsonify({"error": "internal server error"}), 500

# ---------- DOWNLOAD ----------
@app.route("/api/download/<vid>")
def download(vid):
    quality = request.args.get("quality", "medium")
    bitrate = QUALITY_MAP.get(quality, "128")

    path = f"{DOWNLOAD_DIR}/{vid}_{bitrate}.mp3"

    opts = {
        **YTDL_BASE,
        "format": "bestaudio",
        "outtmpl": path,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": bitrate
        }]
    }

    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([vid])

    threading.Thread(target=auto_delete, args=(path,)).start()
    return send_file(path, as_attachment=True)

# ======================
# MAIN (RENDER SAFE)
# ======================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
