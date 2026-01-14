import os, time, threading
import yt_dlp
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

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

# 🔍 Search
@app.route("/api/search")
def search():
    q = request.args.get("q")
    if not q:
        return jsonify({"error": "query required"}), 400

    with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
        info = ydl.extract_info(f"ytsearch1:{q}", download=False)
        v = info["entries"][0]

    return jsonify({
        "id": v["id"],
        "title": v["title"],
        "artist": v.get("artist") or v.get("uploader"),
        "thumbnail": v["thumbnail"],
        "duration": v["duration"],
        "description": v.get("description", "")
    })

# 🎧 Stream
@app.route("/api/stream/<vid>")
def stream(vid):
    with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
        info = ydl.extract_info(vid, download=False)

    for f in info["formats"]:
        if f.get("acodec") != "none":
            return jsonify({
                "stream_url": f["url"],
                "title": info["title"],
                "artist": info.get("artist") or info.get("uploader"),
                "thumbnail": info["thumbnail"]
            })

    return jsonify({"error": "audio not found"}), 404

# ⬇️ Download with Quality
@app.route("/api/download/<vid>")
def download(vid):
    quality = request.args.get("quality", "medium")
    bitrate = QUALITY_MAP.get(quality, "128")

    file_path = f"{DOWNLOAD_DIR}/{vid}_{bitrate}.mp3"

    ydl_opts = {
        "format": "bestaudio",
        "outtmpl": file_path,
        "quiet": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": bitrate
        }]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([vid])

    threading.Thread(target=auto_delete, args=(file_path,)).start()
    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
