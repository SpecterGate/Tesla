import subprocess
import requests
from flask import Flask, Response, request, render_template_string, abort

app = Flask(__name__)

# --- CONFIGURATION ---
SECRET_KEY = "tesla123" 
# Public Invidious API instances to bypass YouTube 429 blocks
INSTANCES = ["https://yewtu.be", "https://inv.vern.cc", "https://invidious.nerdvpn.de"]

def get_stream_urls(video_id):
    for instance in INSTANCES:
        try:
            data = requests.get(f"{instance}/api/v1/videos/{video_id}", timeout=5).json()
            # Extract Video-only stream (360p is best for MJPEG stability)
            v_url = next(f['url'] for f in data.get('formatStreams', []) if "360p" in f.get('qualityLabel', ''))
            # Extract Audio-only stream
            a_url = next(f['url'] for f in data.get('adaptiveFormats', []) if "audio" in f.get('type', ''))
            return v_url, a_url
        except: continue
    return None, None

@app.route('/v_stream/<v_id>')
def video_stream(v_id):
    if request.args.get('key') != SECRET_KEY: abort(403)
    v_url, _ = get_stream_urls(v_id)
    if not v_url: return ""
    
    # FFmpeg: Convert video to MJPEG (Image Stream) to bypass Tesla Video Lockout
    cmd = [
        'ffmpeg', '-re', '-i', v_url, 
        '-vf', 'scale=854:480,fps=15', 
        '-f', 'image2pipe', '-vcodec', 'mjpeg', '-q:v', '12', 'pipe:1'
    ]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    def generate():
        try:
            while True:
                frame = p.stdout.read(1024*64)
                if not frame: break
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        finally:
            p.kill()
            
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/a_stream/<v_id>')
def audio_stream(v_id):
    if request.args.get('key') != SECRET_KEY: abort(403)
    _, a_url = get_stream_urls(v_id)
    if not a_url: return ""
    
    # FFmpeg: Pipe audio directly as AAC
    cmd = ['ffmpeg', '-re', '-i', a_url, '-c:a', 'aac', '-b:a', '128k', '-f', 'adts', 'pipe:1']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return Response(p.stdout, mimetype='audio/aac')

@app.route('/')
def index():
    if request.args.get('key') != SECRET_KEY:
        return "Access Denied. Use ?key=tesla123", 403

    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Tesla YouTube</title>
    <style>
        :root {
            --yt-black: #0f0f0f; --yt-red: #ff0000; --yt-white: #f1f1f1;
            --nav-height: 85px; --glass: rgba(255, 255, 255, 0.07); --glass-border: rgba(255, 255, 255, 0.1);
        }
        body { background-color: var(--yt-black); color: var(--yt-white); font-family: sans-serif; margin: 0; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
        main { flex: 1; display: flex; flex-direction: column; padding: 25px 40px; overflow-y: auto; background: radial-gradient(circle at top center, #1e1e1e 0%, #0f0f0f 100%); padding-bottom: calc(var(--nav-height) + 20px); }
        .header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
        .logo-group { display: flex; align-items: center; gap: 10px; cursor: pointer; }
        .yt-play-icon { width: 36px; height: 26px; background: var(--yt-red); border-radius: 7px; display: flex; align-items: center; justify-content: center; }
        .yt-play-icon::after { content: ''; border-style: solid; border-width: 5px 0 5px 9px; border-color: transparent transparent transparent white; }
        .yt-text { font-size: 22px; font-weight: 700; color: white; }
        .search-pill { background: var(--glass); border: 1px solid var(--glass-border); padding: 12px 25px; border-radius: 40px; width: 380px; display: flex; align-items: center; }
        .search-pill input { background: transparent; border: none; color: white; font-size: 18px; width: 100%; outline: none; margin-left: 12px; }
        
        /* Player Overlay */
        #player-overlay { display: none; margin-bottom: 30px; text-align: center; background: #000; border-radius: 12px; padding: 10px; border: 1px solid var(--glass-border); }
        #stream-img { width: 100%; max-width: 854px; border-radius: 8px; }
        
        .video-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 24px; }
        .tv-card { cursor: pointer; transition: 0.2s; }
        .thumb-wrap { border-radius: 12px; overflow: hidden; aspect-ratio: 16/9; background: #222; }
        .thumb-wrap img { width: 100%; height: 100%; object-fit: cover; }
        .meta { margin-top: 12px; }
        .meta h3 { font-size: 16px; margin: 0; color: #fff; }
        .meta p { color: #aaa; font-size: 13px; }

        nav.bottom-rail { position: fixed; bottom: 0; left: 0; right: 0; height: var(--nav-height); background: rgba(15, 15, 15, 0.98); display: flex; justify-content: center; align-items: center; gap: 90px; border-top: 1px solid var(--glass-border); }
        .nav-item { display: flex; flex-direction: column; align-items: center; color: white; opacity: 0.6; cursor: pointer; }
        .nav-item.active { opacity: 1; }
        .nav-item svg { width: 24px; height: 24px; }
    </style>
</head>
<body>

    <main>
        <div class="header-row">
            <div class="logo-group" onclick="location.reload()">
                <div class="yt-play-icon"></div>
                <div class="yt-text">YouTube</div>
            </div>
            <div class="search-pill">
                <input type="text" id="search-box" placeholder="Search">
            </div>
        </div>

        <div id="player-overlay">
            <img id="stream-img" src="">
            <audio id="stream-audio" autoplay></audio>
            <div style="margin-top:10px;"><button onclick="stopPlayer()" style="background:var(--glass); color:white; border:1px solid #444; padding:10px 20px; border-radius:20px; cursor:pointer;">Close Video</button></div>
        </div>

        <div id="status" style="text-align:center; padding:20px;">Loading...</div>
        <div class="video-grid" id="video-grid"></div>
    </main>

    <nav class="bottom-rail">
        <div class="nav-item active" onclick="location.reload()">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M4 10V21H9V15H15V21H20V10L12 3L4 10Z"></path></svg>
            <span>Home</span>
        </div>
        <div class="nav-item">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M10 14.65V10.5L14 12.58L10 14.65ZM17.77 10.32C17.33 8.31 15.57 7 13.5 7H13.22L14.73 5.3C15.41 4.54 15.34 3.37 14.58 2.69C13.82 2.01 12.65 2.08 11.97 2.84L8.33 6.91C7.3 8.06 7.31 9.77 8.35 10.91L8.68 11.27L7.23 12.87C6.55 13.63 6.62 14.8 7.38 15.48C8.14 16.16 9.31 16.09 9.99 15.33L13.63 11.26C14.66 10.11 14.65 8.4 13.61 7.26L13.28 6.9L14.73 5.3C14.73 5.3 14.74 5.29 14.74 5.29C14.88 5.14 15.02 5.3 14.73 5.3H13.5C14.88 5.3 16.04 6.13 16.5 7.35C16.96 8.57 16.64 9.94 15.71 10.84L12.07 14.91C11.66 15.37 11.02 15.6 10.4 15.53C9.77 15.46 9.24 15.1 8.92 14.58L8.35 13.63L6.23 15.97C5.07 17.26 5.16 19.24 6.45 20.41C7.74 21.58 9.72 21.49 10.89 20.2L14.53 16.13C16.48 13.96 16.27 10.65 14.07 8.74L13.74 8.45L15.19 6.85C16.56 5.32 18.73 5.15 20.31 6.45C21.89 7.75 22.15 10.03 20.9 11.63L17.77 15.14V10.32Z"></path></svg>
            <span>Shorts</span>
        </div>
        <div class="nav-item">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14.5v-9l6 4.5-6 4.5z"></path></svg>
            <span>Library</span>
        </div>
    </nav>

    <script>
        const API_KEY = "AIzaSyCmzrNRJa7YA5fhln-1gB9tq8Ac9HeaJoc";
        const SECRET = "tesla123";

        async function fetchVideos(query = "") {
            const status = document.getElementById('status');
            status.style.display = "block";
            let url = query ? `https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=15&q=${encodeURIComponent(query)}&type=video&key=${API_KEY}`
                            : `https://www.googleapis.com/youtube/v3/videos?part=snippet&chart=mostPopular&regionCode=US&maxResults=15&key=${API_KEY}`;
            try {
                const res = await fetch(url);
                const data = await res.json();
                render(data.items, !!query);
                status.style.display = "none";
            } catch (e) { status.innerText = "Error: " + e.message; }
        }

        function playVideo(videoId) {
            document.getElementById('player-overlay').style.display = "block";
            document.getElementById('stream-img').src = `/v_stream/${videoId}?key=${SECRET}`;
            document.getElementById('stream-audio').src = `/a_stream/${videoId}?key=${SECRET}`;
            window.scrollTo({top: 0, behavior: 'smooth'});
        }

        function stopPlayer() {
            document.getElementById('player-overlay').style.display = "none";
            document.getElementById('stream-img').src = "";
            document.getElementById('stream-audio').src = "";
        }

        function render(items, isSearch) {
            const grid = document.getElementById('video-grid');
            grid.innerHTML = '';
            items.forEach(item => {
                const videoId = isSearch ? item.id.videoId : item.id;
                const card = document.createElement('div');
                card.className = 'tv-card';
                card.onclick = () => playVideo(videoId);
                card.innerHTML = `<div class="thumb-wrap"><img src="${item.snippet.thumbnails.high.url}"></div>
                                  <div class="meta"><h3>${item.snippet.title}</h3><p>${item.snippet.channelTitle}</p></div>`;
                grid.appendChild(card);
            });
        }

        document.getElementById('search-box').onkeypress = (e) => { if(e.key === 'Enter') fetchVideos(e.target.value); };
        fetchVideos();
    </script>
</body>
</html>
    """)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
