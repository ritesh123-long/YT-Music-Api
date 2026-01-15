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
@app.route("/api/search")
def search():
    q = request.args.get("q")
    if not q:
        return jsonify([])

    search_url = f"https://music.youtube.com/search?q={q.replace(' ', '+')}"

    ydl_opts = {
        **YTDL_BASE,
        "extract_flat": True,
        "skip_download": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_url, download=False)

    results = []

    for v in info.get("entries", []):
        if not v:
            continue
        if v.get("_type") != "url":
            continue
        if "watch?v=" not in v.get("url", ""):
            continue

        vid = v["url"].split("watch?v=")[-1]

        results.append({
            "id": vid,
            "title": v.get("title"),
            "artist": v.get("uploader"),
            "thumbnail": v.get("thumbnails", [{}])[-1].get("url"),
        })

    return jsonify(results[:10])

# 🎧 STREAM (FAST – NO DOWNLOAD)
@app.route("/api/search")
def search():
    q = request.args.get("q")
    if not q:
        return jsonify([])

    search_url = f"https://music.youtube.com/search?q={q.replace(' ', '+')}"

    ydl_opts = {
        **YTDL_BASE,
        "extract_flat": True,
        "skip_download": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_url, download=False)

    results = []

    for v in info.get("entries", []):
        if not v:
            continue
        if v.get("_type") != "url":
            continue
        if "watch?v=" not in v.get("url", ""):
            continue

        vid = v["url"].split("watch?v=")[-1]

        results.append({
            "id": vid,
            "title": v.get("title"),
            "artist": v.get("uploader"),
            "thumbnail": v.get("thumbnails", [{}])[-1].get("url"),
        })

    return jsonify(results[:10])

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
