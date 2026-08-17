from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re

app = Flask(__name__)
CORS(app)

# Rotating Piped API instances that handle YouTube stream extraction
PIPED_INSTANCES = [
    "https://pipedapi.kavin.rocks",
    "https://api.piped.privacydev.net",
    "https://piped-api.garudalinux.org",
    "https://pipedapi.tokhmi.xyz"
]

def extract_video_id(url):
    match = re.search(r'(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|shorts\/))([\w-]{11})', url)
    return match.group(1) if match else None

@app.route('/download', methods=['GET'])
def get_download():
    raw_url = request.args.get('url')
    format_type = request.args.get('format', '720')

    if not raw_url:
        return jsonify({'success': False, 'error': 'No URL provided'}), 400

    video_id = extract_video_id(raw_url)
    if not video_id:
        return jsonify({'success': False, 'error': 'Invalid YouTube link'}), 400

    # Query public piped instances
    for instance in PIPED_INSTANCES:
        try:
            res = requests.get(f"{instance}/streams/{video_id}", timeout=6)
            if res.status_code == 200:
                data = res.json()

                # If audio requested
                if format_type == 'mp3':
                    audio_streams = data.get('audioStreams', [])
                    if audio_streams:
                        # Grab the highest bitrate audio stream
                        return jsonify({'success': True, 'downloadUrl': audio_streams[0]['url']})

                # Check video streams (progressive / combined)
                video_streams = data.get('videoStreams', [])
                
                # First pass: try matching exact quality resolution
                for s in video_streams:
                    if format_type in str(s.get('quality', '')) and s.get('videoOnly') is False:
                        return jsonify({'success': True, 'downloadUrl': s['url']})

                # Second pass: pick the first combined stream with both audio and video
                for s in video_streams:
                    if s.get('videoOnly') is False:
                        return jsonify({'success': True, 'downloadUrl': s['url']})

                # Fallback: pick any top stream URL
                if video_streams:
                    return jsonify({'success': True, 'downloadUrl': video_streams[0]['url']})

        except Exception:
            continue

    return jsonify({'success': False, 'error': 'Failed to resolve stream link. Please try again.'}), 502

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
