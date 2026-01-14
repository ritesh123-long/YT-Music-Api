import os, time, threading
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# 🔐 yt-dlp BASE (Cookies + fallback)
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

# 🧹 Auto delete after 20 minutes
def auto_delete(path, delay=1200):
    time.sleep(delay)
    if os.path.exists(path):
        os.remove(path)

@app.route("/")
def home():
    return render_template("index.html")

# 🔍 SEARCH (MULTIPLE RESULTS)
@app.route("/api/search")
def search():
    q = request.args.get("q")
    if not q:
        return jsonify([])

    ydl_opts = {
        **YTDL_BASE,
        "skip_download": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(
            f"ytsearch10:{q}",
            download=False
        )

    results = []

    for v in info.get("entries", []):
        if not v:
            continue

        # ✅ STRICT FILTER (THIS FIXES ERROR)
        if v.get("_type") != "video":
            continue
        if not v.get("id"):
            continue
        if len(v["id"]) < 8:
            continue

        results.append({
            "id": v["id"],
            "title": v.get("title"),
            "artist": v.get("uploader"),
            "thumbnail": v.get("thumbnail"),
            "duration": v.get("duration"),
        })

    return jsonify(results)

# 🎧 STREAM (FAST – NO DOWNLOAD)
@app.route("/api/stream/<vid>")
def stream(vid):
    if len(vid) < 8:
        return jsonify({"error": "invalid video id"}), 400

    with yt_dlp.YoutubeDL(YTDL_BASE) as ydl:
        info = ydl.extract_info(
            f"https://www.youtube.com/watch?v={vid}",
            download=False
        )

    audio_url = None
    for f in info.get("formats", []):
        if f.get("acodec") != "none" and f.get("vcodec") == "none":
            audio_url = f.get("url")
            break

    if not audio_url:
        return jsonify({"error": "audio not found"}), 404

    return jsonify({
        "stream_url": audio_url,
        "title": info.get("title"),
        "artist": info.get("uploader"),
        "thumbnail": info.get("thumbnail")
    })

# ⬇️ DOWNLOAD WITH QUALITY
@app.route("/api/download/<vid>")
def download(vid):
    quality = request.args.get("quality", "medium")
    bitrate = QUALITY_MAP.get(quality, "128")

    path = f"{DOWNLOAD_DIR}/{vid}_{bitrate}.mp3"

    ydl_opts = {
        **YTDL_BASE,
        "format": "bestaudio",
        "outtmpl": path,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": bitrate
        }]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([vid])

    threading.Thread(target=auto_delete, args=(path,)).start()
    return send_file(path, as_attachment=True)

# 📜 LYRICS (FROM DESCRIPTION)
@app.route("/api/lyrics/<vid>")
def lyrics(vid):
    with yt_dlp.YoutubeDL(YTDL_BASE) as ydl:
        info = ydl.extract_info(vid, download=False)

    return jsonify({
        "title": info["title"],
        "lyrics": info.get("description", "")[:4000]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
