from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import time

app = Flask(__name__)
CORS(app)

DOWNLOAD_DIR = "downloads"
COOKIES_FILE = "cookies.txt" # Ensure this exists if needed

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://www.youtube.com/"
}

# ---------------- MEMORY STORAGE ----------------
download_progress = {}
download_history = []

# ---------------- HELPERS ----------------
def format_size(bytes):
    """Converts raw bytes into a human-readable format (MB, GB, etc.)"""
    if not bytes: return "Unknown"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024: return f"{bytes:.1f} {unit}"
        bytes /= 1024
    return f"{bytes:.1f} TB"

# ---------------- PROGRESS HOOK ----------------
def progress_hook(d):
    video_id = d.get('info_dict', {}).get('id')
    if not video_id: return
    
    if d['status'] == 'downloading':
        # Enhanced real-time data for the frontend
        download_progress[video_id] = {
            "status": "downloading",
            "percent": d.get('_percent_str', '0%').replace('%','').strip(),
            "speed": d.get('_speed_str', 'N/A'),
            "eta": d.get('_eta_str', 'N/A'),
            "bytes_downloaded": format_size(d.get('downloaded_bytes', 0)),
            "total_bytes": format_size(d.get('total_bytes') or d.get('total_bytes_estimate', 0))
        }

    if d['status'] == 'finished':
        download_progress[video_id] = {
            "status": "finished",
            "percent": "100"
        }

# ---------------- VIDEO INFO ----------------
@app.route("/info", methods=["POST"])
def info():
    url = request.json.get("url")

    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "cookies": COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
        "http_headers": COMMON_HEADERS
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)

        # Get raw size and format it for the UI
        raw_size = info_dict.get("filesize") or info_dict.get("filesize_approx") or 0
        
        return jsonify({
            "id": info_dict.get("id"),
            "title": info_dict.get("title"),
            "thumbnail": info_dict.get("thumbnail"),
            "duration": info_dict.get("duration"),
            "filesize": format_size(raw_size),
            "raw_size": raw_size
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ---------------- DOWNLOAD ----------------
@app.route("/download", methods=["POST"])
def download():
    data = request.json
    url = data.get("url")
    mode = data.get("mode")    # audio / video
    quality = int(data.get("quality", 720))

    ydl_opts = {
        "outtmpl": os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
        "cookies": COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
        "http_headers": COMMON_HEADERS,
        "progress_hooks": [progress_hook],
        "quiet": False
    }

    # -------- AUDIO CONFIG --------
    if mode == "audio":
        ydl_opts.update({
            "format": "bestaudio",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }]
        })
        ext = "mp3"

    # -------- VIDEO CONFIG --------
    else:
        if quality > 1080:
            return jsonify({"error": "Max 1080p allowed"}), 403

        ydl_opts.update({
            "format": f"bestvideo[ext=mp4][height<={quality}]+bestaudio[ext=m4a]/best",
            "merge_output_format": "mp4"
        })
        ext = "mp4"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)

        # Determine the final filename path
        filename = ydl.prepare_filename(info_dict)
        base, _ = os.path.splitext(filename)
        final_path = f"{base}.{ext}"

        # SAVE TO HISTORY
        download_history.insert(0, {
            "title": info_dict.get("title"),
            "mode": mode,
            "quality": f"{quality}p" if mode == "video" else "192kbps",
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "size": format_size(info_dict.get("filesize") or info_dict.get("filesize_approx", 0))
        })

        return send_file(
            final_path,
            as_attachment=True,
            download_name=os.path.basename(final_path)
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- PROGRESS API ----------------
@app.route("/progress/<video_id>")
def get_progress(video_id):
    return jsonify(download_progress.get(video_id, {"status": "waiting"}))


# ---------------- HISTORY API ----------------
@app.route("/history")
def get_history():
    return jsonify(download_history[:10])


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import time

app = Flask(__name__)
CORS(app)

DOWNLOAD_DIR = "downloads"
COOKIES_FILE = "cookies.txt" # Ensure this exists if needed

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://www.youtube.com/"
}

# ---------------- MEMORY STORAGE ----------------
download_progress = {}
download_history = []

# ---------------- HELPERS ----------------
def format_size(bytes):
    """Converts raw bytes into a human-readable format (MB, GB, etc.)"""
    if not bytes: return "Unknown"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024: return f"{bytes:.1f} {unit}"
        bytes /= 1024
    return f"{bytes:.1f} TB"

# ---------------- PROGRESS HOOK ----------------
def progress_hook(d):
    video_id = d.get('info_dict', {}).get('id')
    if not video_id: return
    
    if d['status'] == 'downloading':
        # Enhanced real-time data for the frontend
        download_progress[video_id] = {
            "status": "downloading",
            "percent": d.get('_percent_str', '0%').replace('%','').strip(),
            "speed": d.get('_speed_str', 'N/A'),
            "eta": d.get('_eta_str', 'N/A'),
            "bytes_downloaded": format_size(d.get('downloaded_bytes', 0)),
            "total_bytes": format_size(d.get('total_bytes') or d.get('total_bytes_estimate', 0))
        }

    if d['status'] == 'finished':
        download_progress[video_id] = {
            "status": "finished",
            "percent": "100"
        }

# ---------------- VIDEO INFO ----------------
@app.route("/info", methods=["POST"])
def info():
    url = request.json.get("url")

    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "cookies": COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
        "http_headers": COMMON_HEADERS
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)

        # Get raw size and format it for the UI
        raw_size = info_dict.get("filesize") or info_dict.get("filesize_approx") or 0
        
        return jsonify({
            "id": info_dict.get("id"),
            "title": info_dict.get("title"),
            "thumbnail": info_dict.get("thumbnail"),
            "duration": info_dict.get("duration"),
            "filesize": format_size(raw_size),
            "raw_size": raw_size
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ---------------- DOWNLOAD ----------------
@app.route("/download", methods=["POST"])
def download():
    data = request.json
    url = data.get("url")
    mode = data.get("mode")    # audio / video
    quality = int(data.get("quality", 720))

    ydl_opts = {
        "outtmpl": os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
        "cookies": COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
        "http_headers": COMMON_HEADERS,
        "progress_hooks": [progress_hook],
        "quiet": False
    }

    # -------- AUDIO CONFIG --------
    if mode == "audio":
        ydl_opts.update({
            "format": "bestaudio",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }]
        })
        ext = "mp3"

    # -------- VIDEO CONFIG --------
    else:
        if quality > 1080:
            return jsonify({"error": "Max 1080p allowed"}), 403

        ydl_opts.update({
            "format": f"bestvideo[ext=mp4][height<={quality}]+bestaudio[ext=m4a]/best",
            "merge_output_format": "mp4"
        })
        ext = "mp4"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)

        # Determine the final filename path
        filename = ydl.prepare_filename(info_dict)
        base, _ = os.path.splitext(filename)
        final_path = f"{base}.{ext}"

        # SAVE TO HISTORY
        download_history.insert(0, {
            "title": info_dict.get("title"),
            "mode": mode,
            "quality": f"{quality}p" if mode == "video" else "192kbps",
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "size": format_size(info_dict.get("filesize") or info_dict.get("filesize_approx", 0))
        })

        return send_file(
            final_path,
            as_attachment=True,
            download_name=os.path.basename(final_path)
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- PROGRESS API ----------------
@app.route("/progress/<video_id>")
def get_progress(video_id):
    return jsonify(download_progress.get(video_id, {"status": "waiting"}))


# ---------------- HISTORY API ----------------
@app.route("/history")
def get_history():
    return jsonify(download_history[:10])


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)