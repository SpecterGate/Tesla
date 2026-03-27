import subprocess
import requests
from flask import Flask, Response, request, render_template_string, abort

app = Flask(__name__)

SECRET_KEY = "tesla123" 
INSTANCES = ["https://yewtu.be", "https://inv.vern.cc", "https://invidious.nerdvpn.de"]

def get_stream_urls(video_id):
    for instance in INSTANCES:
        try:
            data = requests.get(f"{instance}/api/v1/videos/{video_id}", timeout=5).json()
            # Get video link
            v_url = next(f['url'] for f in data.get('formatStreams', []) if "360p" in f.get('qualityLabel', ''))
            # Get separate audio link (usually in adaptiveFormats)
            a_url = next(f['url'] for f in data.get('adaptiveFormats', []) if "audio" in f.get('type', ''))
            return v_url, a_url
        except: continue
    return None, None

@app.route('/video_stream/<v_id>')
def video_stream(v_id):
    if request.args.get('key') != SECRET_KEY: abort(403)
    v_url, _ = get_stream_urls(v_id)
    if not v_url: return ""
    
    # VIDEO ONLY: MJPEG "Flipbook" (Bypasses Drive Lockout)
    cmd = ['ffmpeg', '-re', '-i', v_url, '-vf', 'scale=640:360,fps=12', '-f', 'image2pipe', '-vcodec', 'mjpeg', '-q:v', '15', 'pipe:1']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return Response((b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + p.stdout.read(1024*64) + b'\r\n' for _ in iter(int, 1)), 
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/audio_stream/<v_id>')
def audio_stream(v_id):
    if request.args.get('key') != SECRET_KEY: abort(403)
    _, a_url = get_stream_urls(v_id)
    if not a_url: return ""
    
    # AUDIO ONLY: Constant AAC stream
    cmd = ['ffmpeg', '-re', '-i', a_url, '-c:a', 'aac', '-b:a', '64k', '-f', 'adts', 'pipe:1']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return Response(p.stdout, mimetype='audio/aac')

@app.route('/')
def index():
    if request.args.get('key') != SECRET_KEY: return "Denied", 403
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background: #000; color: #fff; font-family: sans-serif; margin: 0; text-align: center; }
        #v-frame { width: 100%; max-width: 800px; border-radius: 8px; margin-top: 10px; }
        .card { padding: 10px; background: #111; margin: 5px; border-radius: 5px; display: inline-block; width: 40%; vertical-align: top; }
        img.thumb { width: 100%; border-radius: 4px; }
    </style>
</head>
<body>
    <div id="player" style="display:none;">
        <img id="v-frame" src="">
        <audio id="a-track" autoplay></audio>
        <button onclick="location.reload()" style="display:block; width:100%; padding:10px;">Close Player</button>
    </div>
    <div id="results"></div>
    <script>
        const KEY = "tesla123";
        async function load() {
            const res = await fetch(`https://www.googleapis.com/youtube/v3/videos?chart=mostPopular&regionCode=US&part=snippet&maxResults=10&key=AIzaSyCmzrNRJa7YA5fhln-1gB9tq8Ac9HeaJoc`);
            const data = await res.json();
            document.getElementById('results').innerHTML = data.items.map(i => `
                <div class="card" onclick="play('${i.id}')">
                    <img class="thumb" src="${i.snippet.thumbnails.medium.url}">
                    <p style="font-size:10px">${i.snippet.title}</p>
                </div>`).join('');
        }
        function play(id) {
            document.getElementById('player').style.display = "block";
            document.getElementById('results').style.display = "none";
            // Set Video Source (MJPEG)
            document.getElementById('v-frame').src = `/video_stream/${id}?key=${KEY}`;
            // Set Audio Source (AAC)
            document.getElementById('a-track').src = `/audio_stream/${id}?key=${KEY}`;
            document.getElementById('a-track').play();
        }
        load();
    </script>
</body>
</html>
    """)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
