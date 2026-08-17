from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re

app = Flask(__name__)
CORS(app)

# Rotating list of reliable public Invidious instances
INVIDIOUS_INSTANCES = [
    "https://inv.tux.pizza",
    "https://invidious.nerdvpn.de",
    "https://vid.priv.au",
    "https://invidious.projectsegfau.lt"
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

    # Query Invidious instances sequentially until one resolves the stream
    for instance in INVIDIOUS_INSTANCES:
        try:
            api_endpoint = f"{instance}/api/v1/videos/{video_id}"
            res = requests.get(api_endpoint, timeout=8)
            
            if res.status_code == 200:
                data = res.json()
                
                # If audio requested
                if format_type == 'mp3':
                    audio_streams = data.get('adaptiveFormats', [])
                    for stream in audio_streams:
                        if stream.get('type', '').startswith('audio'):
                            return jsonify({'success': True, 'downloadUrl': stream['url']})
                
                # Check combined (progressive) video formats first
                combined_streams = data.get('formatStreams', [])
                for stream in reversed(combined_streams):
                    quality_label = stream.get('qualityLabel', '')
                    if format_type in quality_label:
                        return jsonify({'success': True, 'downloadUrl': stream['url']})
                
                # Fallback to highest available combined stream
                if combined_streams:
                    return jsonify({'success': True, 'downloadUrl': combined_streams[-1]['url']})
                    
        except Exception:
            continue

    return jsonify({'success': False, 'error': 'All instances busy. Please try again in a few seconds.'}), 502

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
