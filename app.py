from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re

app = Flask(__name__)
CORS(app)

# Rotating list of public high-speed Cobalt processing nodes
COBALT_INSTANCES = [
    "https://cobalt-api.kwiatekm.com",
    "https://api.cobalt.tools",
    "https://cobalt.hyonsu.com"
]

def clean_youtube_url(raw_url):
    match = re.search(r'(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|shorts\/))([\w-]{11})', raw_url)
    if match:
        return f"https://www.youtube.com/watch?v={match.group(1)}"
    return raw_url

@app.route('/download', methods=['GET'])
def get_download():
    raw_url = request.args.get('url')
    format_type = request.args.get('format', '720')

    if not raw_url:
        return jsonify({'success': False, 'error': 'No URL provided'}), 400

    clean_url = clean_youtube_url(raw_url)

    payload = {
        "url": clean_url,
        "videoQuality": format_type if format_type != 'mp3' else '720',
        "downloadMode": "audio" if format_type == 'mp3' else "auto",
        "youtubeVideoCodec": "h264"
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    for instance in COBALT_INSTANCES:
        try:
            res = requests.post(instance, json=payload, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if 'url' in data:
                    return jsonify({'success': True, 'downloadUrl': data['url']})
                if 'stream' in data:
                    return jsonify({'success': True, 'downloadUrl': data['stream']})
        except Exception:
            continue

    return jsonify({'success': False, 'error': 'Upstream nodes busy. Please try again.'}), 502

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
