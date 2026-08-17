from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess

app = Flask(__name__)
CORS(app)

@app.route('/download', methods=['GET'])
def get_download():
    url = request.args.get('url')
    format_type = request.args.get('format', '720')

    if not url:
        return jsonify({'success': False, 'error': 'No URL provided'}), 400

    if format_type == 'mp3':
        ydl_opts = '--extract-audio --audio-format mp3 --get-url'
    else:
        ydl_opts = f'-f "bestvideo[height<={format_type}]+bestaudio/best[height<={format_type}]/best" --get-url'

    try:
        command = f'yt-dlp {ydl_opts} "{url}"'
        output = subprocess.check_output(command, shell=True, text=True).strip()
        urls = output.split('\n')
        return jsonify({'success': True, 'downloadUrl': urls[0]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
