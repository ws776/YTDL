from flask import Flask, request, jsonify, send_from_directory
import subprocess
import os
import urllib.parse
import time

app = Flask(__name__)

DOWNLOAD_FOLDER = "/tmp/downloads"
SECRET_KEY = "124816"  # 固定鍵（例：年月日曜日→hex化）

# 一時ディレクトリ作成（Renderでは重要）
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def is_authorized(key: str) -> bool:
    return key == SECRET_KEY

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get("url")
    ext = data.get("ext", "mp4")
    key = data.get("key")

    if not is_authorized(key):
        return jsonify({"error": "認証失敗"}), 403

    if not url:
        return jsonify({"error": "URLがありません"}), 400

    unique_id = str(int(time.time() * 1000))
    filename_template = f"%(title)s-[{unique_id}].%(ext)s"
    output_path = os.path.join(DOWNLOAD_FOLDER, filename_template)

    if ext == "mp3":
        cmd = [
            "yt-dlp",
            "-x",
            "--audio-format", "mp3",
            "-o", output_path,
            url
        ]
    else:
        cmd = [
            "yt-dlp",
            "-f", "best",
            "-o", output_path,
            url
        ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        return jsonify({"error": "ダウンロード失敗"}), 500

    files = [f for f in os.listdir(DOWNLOAD_FOLDER) if f.endswith(f".{ext}")]
    matched_files = [f for f in files if f"[{unique_id}]" in f]

    if not matched_files:
        return jsonify({"error": "ファイルが見つかりません"}), 500

    saved_file = matched_files[0]
    encoded_file = urllib.parse.quote(saved_file)
    download_url = f"https://{request.host}/downloads/{encoded_file}"
    return jsonify({"message": "ダウンロード成功", "url": download_url})

@app.route('/downloads/<path:filename>')
def serve_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

# Renderではapp.run()を呼ばない
