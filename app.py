from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import re

app = Flask(__name__)
CORS(app)

def clean_youtube_url(raw_url):
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

    # Use the iOS/TV embedded client rotation to bypass the datacenter bot check
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'android', 'mweb'],
                'player_skip': ['webpage', 'configs', 'js']
            }
        },
        'http_headers': {
            'User-Agent': 'com.google.ios.youtube/19.29.1 (iPhone14,3; U; CPU iOS 17_5_1 like Mac OS X; en_US)'
        }
    }

    if format_type == 'mp3':
        ydl_opts['format'] = 'ba/b'
    else:
        ydl_opts['format'] = f'b[height<={format_type}]/bv*[height<={format_type}]+ba/b'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=False)
            
            download_url = None
            if 'url' in info:
                download_url = info['url']
            elif 'formats' in info and len(info['formats']) > 0:
                # Find the direct progressive/combined stream URL
                for f in reversed(info['formats']):
                    if f.get('url') and (f.get('vcodec') != 'none' or format_type == 'mp3'):
                        download_url = f['url']
                        break

            if download_url:
                return jsonify({'success': True, 'downloadUrl': download_url})
            else:
                return jsonify({'success': False, 'error': 'Could not extract direct stream URL.'}), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
