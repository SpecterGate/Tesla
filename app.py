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
            v_url = next(f['url'] for f in data.get('formatStreams', []) if "360p" in f.get('qualityLabel', ''))
            adaptive = data.get('adaptiveFormats', [])
            a_url = next(f['url'] for f in adaptive if "audio" in f.get('type', ''))
            return v_url, a_url
        except: continue
    return None, None

@app.route('/video_stream/<v_id>')
def video_stream(v_id):
    if request.args.get('key') != SECRET_KEY: abort(403)
    v_url, _ = get_stream_urls(v_id)
    if not v_url: return ""
    
    cmd = ['ffmpeg', '-re', '-i', v_url, '-vf', 'scale=640:360,fps=12', '-f', 'image2pipe', '-vcodec', 'mjpeg', '-q:v', '12', 'pipe:1']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    def generate():
        try:
            while True:
                frame = p.stdout.read(1024*64)
                if not frame: break
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        finally: p.kill()
        
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/audio_stream/<v_id>')
def audio_stream(v_id):
    if request.args.get('key') != SECRET_KEY: abort(403)
    _, a_url = get_stream_urls(v_id)
    if not a_url: return ""
    
    cmd = ['ffmpeg', '-re', '-i', a_url, '-c:a', 'aac', '-b:a', '96k', '-f', 'adts', 'pipe:1']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return Response(p.stdout, mimetype='audio/aac')

@app.route('/')
def index():
    if request.args.get('key') != SECRET_KEY: return "Access Denied", 403
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Tesla Tube</title>
    <style>
        body { background: #0f0f0f; color: #fff; font-family: sans-serif; margin: 0; padding: 10px; }
        .search-container { padding: 10px; text-align: center; }
        input { width: 90%; padding: 12px; border-radius: 20px; border: none; background: #222; color: #fff; font-size: 16px; margin-bottom: 15px; }
        #player { display: none; width: 100%; text-align: center; margin-bottom: 20px; }
        #v-frame { width: 100%; border-radius: 12px; border: 1px solid #333; }
        .close-btn { background: #cc0000; color: white; border: none; padding: 10px; width: 100%; border-radius: 8px; margin-top: 10px; font-weight: bold; cursor: pointer; }
        .video-grid { display: flex; flex-wrap: wrap; gap: 10px; justify-content: space-between; }
        .video-card { width: 48%; background: #1a1a1a; border-radius: 10px; overflow: hidden; margin-bottom: 10px; cursor: pointer; }
        .video-card img { width: 100%; aspect-ratio: 16/9; object-fit: cover; }
        .video-card h4 { font-size: 12px; margin: 8px; color: #efefef; height: 32px; overflow: hidden; line-height: 1.3; }
    </style>
</head>
<body>
    <div class="search-container">
        <input type="text" id="q" placeholder="Search...">
    </div>
    <div id="player">
        <img id="v-frame" src="">
        <audio id="a-track" autoplay></audio>
        <button class="close-btn" onclick="stopPlayer()">✕ Close Video</button>
    </div>
    <div class="video-grid" id="g"></div>
    <script>
        const KEY = "tesla123";
        const Y_KEY = "AIzaSyCmzrNRJa7YA5fhln-1gB9tq8Ac9HeaJoc";
        async function search(q="") {
            const url = q ? `https://www.googleapis.com/youtube/v3/search?q=${q}&type=video&part=snippet&maxResults=20&key=${Y_KEY}` 
                          : `https://www.googleapis.com/youtube/v3/videos?chart=mostPopular&regionCode=US&part=snippet&maxResults=20&key=${Y_KEY}`;
            const res = await fetch(url);
            const data = await res.json();
            document.getElementById('g').innerHTML = data.items.map(i => {
                const id = i.id.videoId || i.id;
                return `
                <div class="video-card" onclick="play('${id}')">
                    <img src="${i.snippet.thumbnails.medium.url}">
                    <h4>${i.snippet.title}</h4>
                </div>`;
            }).join('');
        }
        function play(id) {
            document.getElementById('player').style.display = "block";
            document.getElementById('g').style.display = "none";
            document.getElementById('v-frame').src = `/video_stream/${id}?key=${KEY}`;
            document.getElementById('a-track').src = `/audio_stream/${id}?key=${KEY}`;
            window.scrollTo(0,0);
        }
        function stopPlayer() {
            document.getElementById('v-frame').src = "";
            document.getElementById('a-track').src = "";
            document.getElementById('player').style.display = "none";
            document.getElementById('g').style.display = "flex";
        }
        document.getElementById('q').onkeypress = (e) => { if(e.key==='Enter') search(e.target.value); };
        search();
    </script>
</body>
</html>
    """)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
