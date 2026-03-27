import subprocess
import requests
from flask import Flask, Response, request, render_template_string, abort

app = Flask(__name__)

# --- CONFIGURATION ---
SECRET_KEY = "tesla123" 
TARGET_FPS = "15"
RESOLUTION = "854:480" # Aiming for ~1GB per hour

# Public Invidious API instances to bypass 429 errors
INSTANCES = [
    "https://yewtu.be",
    "https://invidious.nerdvpn.de",
    "https://inv.vern.cc",
    "https://invidious.no-logs.com"
]

def get_direct_url(video_id):
    """Bypasses YouTube blocks by asking Invidious for the direct MP4 link."""
    for instance in INSTANCES:
        try:
            api_url = f"{instance}/api/v1/videos/{video_id}"
            data = requests.get(api_url, timeout=5).json()
            
            # Find the best 480p or 360p MP4 stream
            formats = data.get('formatStreams', [])
            for f in formats:
                if "480p" in f.get('qualityLabel', '') or "360p" in f.get('qualityLabel', ''):
                    return f['url']
            
            # Fallback to any adaptive format if direct MP4 isn't found
            adaptive = data.get('adaptiveFormats', [])
            for a in adaptive:
                if "video" in a.get('type', '') and "480p" in a.get('qualityLabel', ''):
                    return a['url']
        except:
            continue
    return None

def generate_frames(video_id):
    raw_url = get_direct_url(video_id)
    if not raw_url:
        return

    # FFmpeg tuned for Intel Atom (MCU2) stability
    ffmpeg_cmd = [
        'ffmpeg', '-re', '-i', raw_url, 
        '-vf', f'scale={RESOLUTION},fps={TARGET_FPS}', 
        '-f', 'image2pipe', '-vcodec', 'mjpeg', '-q:v', '10', 
        '-threads', '1', 'pipe:1'
    ]
    
    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    try:
        while True:
            # Buffer size optimized for 480p frames
            frame = process.stdout.read(1024*64) 
            if not frame: break
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b"\r\n")
    finally:
        process.kill()

@app.route('/stream/<v_id>')
def stream(v_id):
    if request.args.get('key') != SECRET_KEY:
        abort(403)
    return Response(generate_frames(v_id), mimetype='multipart/x-mixed-replace; boundary=frame')

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
        body { background-color: var(--yt-black); color: var(--yt-white); font-family: 'Roboto', sans-serif; margin: 0; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
        main { flex: 1; display: flex; flex-direction: column; padding: 25px 40px; overflow-y: auto; background: radial-gradient(circle at top center, #1e1e1e 0%, #0f0f0f 100%); padding-bottom: calc(var(--nav-height) + 20px); }
        .header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
        .logo-group { display: flex; align-items: center; gap: 10px; cursor: pointer; }
        .yt-play-icon { width: 36px; height: 26px; background: var(--yt-red); border-radius: 7px; display: flex; align-items: center; justify-content: center; }
        .yt-play-icon::after { content: ''; border-style: solid; border-width: 5px 0 5px 9px; border-color: transparent transparent transparent white; }
        .yt-text { font-size: 22px; font-weight: 700; color: white; }
        .search-pill { background: var(--glass); border: 1px solid var(--glass-border); padding: 12px 25px; border-radius: 40px; width: 380px; display: flex; align-items: center; }
        .search-pill input { background: transparent; border: none; color: white; font-size: 18px; width: 100%; outline: none; margin-left: 12px; }
        #player-container { width: 100%; display: none; margin-bottom: 30px; text-align: center; }
        #player-container img { width: 100%; max-width: 900px; border-radius: 12px; border: 1px solid var(--glass-border); }
        .video-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 24px; }
        .tv-card { cursor: pointer; transition: 0.2s; }
        .thumb-wrap { border-radius: 12px; overflow: hidden; aspect-ratio: 16/9; background: #222; }
        .thumb-wrap img { width: 100%; height: 100%; object-fit: cover; }
        .meta { margin-top: 12px; }
        #status { text-align: center; padding: 20px; color: #888; font-size: 18px; }
        nav.bottom-rail { position: fixed; bottom: 0; left: 0; right: 0; height: var(--nav-height); background: rgba(15, 15, 15, 0.98); display: flex; justify-content: center; align-items: center; gap: 90px; border-top: 1px solid var(--glass-border); }
        .nav-item { display: flex; flex-direction: column; align-items: center; color: white; opacity: 0.6; cursor: pointer; }
        .nav-item.active { opacity: 1; }
    </style>
</head>
<body>
    <main>
        <div class="header-row">
            <div class="logo-group" onclick="location.reload()"><div class="yt-play-icon"></div><div class="yt-text">YouTube</div></div>
            <div class="search-pill"><input type="text" id="search-box" placeholder="Search"></div>
        </div>
        <div id="player-container"><div id="video-wrapper"></div><p id="sync-note" style="color:#666; font-size:12px; margin-top:10px;">Use Bluetooth for Audio</p></div>
        <div id="status">Loading...</div>
        <div class="video-grid" id="video-grid"></div>
    </main>

    <nav class="bottom-rail">
        <div class="nav-item active" onclick="location.reload()"><span>Home</span></div>
        <div class="nav-item"><span>Shorts</span></div>
        <div class="nav-item"><span>Library</span></div>
    </nav>

    <script>
        const API_KEY = "AIzaSyCmzrNRJa7YA5fhln-1gB9tq8Ac9HeaJoc";
        const SECRET = "tesla123";

        async function fetchVideos(query = "") {
            const status = document.getElementById('status');
            status.style.display = "block";
            let url = query ? `https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=20&q=${encodeURIComponent(query)}&type=video&key=${API_KEY}`
                            : `https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&chart=mostPopular&regionCode=US&maxResults=20&key=${API_KEY}`;
            try {
                const res = await fetch(url);
                const data = await res.json();
                render(data.items, !!query);
                status.style.display = "none";
            } catch (e) { status.innerText = "Error: " + e.message; }
        }

        function playVideo(videoId) {
            document.getElementById('player-container').style.display = "block";
            document.getElementById('video-wrapper').innerHTML = `<img src="/stream/${videoId}?key=${SECRET}">`;
            window.scrollTo({top: 0, behavior: 'smooth'});
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
