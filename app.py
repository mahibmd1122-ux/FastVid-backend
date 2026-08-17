from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import re

app = Flask(__name__)
CORS(app)

def clean_youtube_url(raw_url):
    # Extract only the valid video ID (strips out ?si= and other tracking queries)
    match = re.search(r'(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|shorts\/))([\w-]{11})', raw_url)
    if match:
        return f"https://www.youtube.com/watch?v={match.group(1)}"
    return raw_url

@app.route('/download', methods=['GET'])
def get_download():
    url = request.args.get('url')
    format_type = request.args.get('format', '720')

    if not url:
        return jsonify({'success': False, 'error': 'No URL provided'}), 400

    clean_url = clean_youtube_url(url)

    # yt-dlp configuration using native Python API
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        # Mimic Android client to bypass cloud server datacenter blocks
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        }
    }

    if format_type == 'mp3':
        ydl_opts['format'] = 'bestaudio/best'
    else:
        ydl_opts['format'] = f'bestvideo[height<={format_type}]+bestaudio/best[height<={format_type}]/best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=False)
            
            # Extract direct URL from formats
            download_url = None
            if 'url' in info:
                download_url = info['url']
            elif 'formats' in info and len(info['formats']) > 0:
                download_url = info['formats'][-1]['url']

            if download_url:
                return jsonify({'success': True, 'downloadUrl': download_url})
            else:
                return jsonify({'success': False, 'error': 'Could not extract direct stream URL.'}), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
