import subprocess
from flask import Flask, Response, request, render_template_string, abort

app = Flask(__name__)

# CONFIGURATION
SECRET_KEY = "tesla123" 
TARGET_FPS = "15"
RESOLUTION = "854:480" # Targeted for ~1GB per hour

# --- BYPASS ENGINE ---
def generate_frames(video_id):
    # Fetch 480p stream URL using yt-dlp
    cmd_url = [
        "yt-dlp", "-g", 
        "-f", "bestvideo[height<=480][ext=mp4]/best[height<=480]", 
        f"https://www.youtube.com/watch?v={video_id}"
    ]
    try:
        raw_url = subprocess.check_output(cmd_url).decode("utf-8").strip()
    except:
        return

    # FFmpeg tuned for Intel Atom (MCU2) & 1GB/hr data limit
    # -q:v 9 provides the quality balance you requested
    ffmpeg_cmd = [
        'ffmpeg', '-re', '-i', raw_url, 
        '-vf', f'scale={RESOLUTION},fps={TARGET_FPS}', 
        '-f', 'image2pipe', '-vcodec', 'mjpeg', '-q:v', '9', 
        '-threads', '1', 'pipe:1'
    ]
    
    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    try:
        while True:
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

# --- FULL UI INTEGRATION ---
@app.route('/')
def index():
    if request.args.get('key') != SECRET_KEY:
        return "Access Denied. Please use your secret key in the URL.", 403

    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Tesla YouTube</title>
    <style>
        :root {
            --yt-black: #0f0f0f;
            --yt-red: #ff0000;
            --yt-white: #f1f1f1;
            --nav-height: 85px;
            --glass: rgba(255, 255, 255, 0.07);
            --glass-border: rgba(255, 255, 255, 0.1);
        }

        body {
            background-color: var(--yt-black);
            color: var(--yt-white);
            font-family: 'Roboto', sans-serif;
            margin: 0;
            display: flex;
            flex-direction: column;
            height: 100vh;
            overflow: hidden;
        }

        main {
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 25px 40px;
            overflow-y: auto;
            background: radial-gradient(circle at top center, #1e1e1e 0%, #0f0f0f 100%);
            padding-bottom: calc(var(--nav-height) + 20px);
        }

        .header-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
        }

        .logo-group {
            display: flex;
            align-items: center;
            gap: 10px;
            cursor: pointer;
        }

        .yt-play-icon { 
            width: 36px; height: 26px; 
            background: var(--yt-red); 
            border-radius: 7px; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
        }

        .yt-play-icon::after { 
            content: ''; 
            border-style: solid; 
            border-width: 5px 0 5px 9px; 
            border-color: transparent transparent transparent white; 
        }

        .yt-text { 
            font-size: 22px; 
            font-weight: 700; 
            letter-spacing: -0.8px; 
            color: white; 
        }

        .search-pill {
            background: var(--glass);
            border: 1px solid var(--glass-border);
            padding: 12px 25px;
            border-radius: 40px;
            width: 380px;
            display: flex;
            align-items: center;
        }

        .search-pill input {
            background: transparent;
            border: none;
            color: white;
            font-size: 18px;
            width: 100%;
            outline: none;
            margin-left: 12px;
        }

        /* Video Player Styling */
        #player-container {
            width: 100%;
            display: none;
            margin-bottom: 30px;
            text-align: center;
        }
        #player-container img {
            width: 100%;
            max-width: 960px;
            border-radius: 12px;
            border: 2px solid var(--glass-border);
            box-shadow: 0 10px 40px rgba(0,0,0,0.8);
        }
        .sync-controls {
            margin-top: 15px;
            display: flex;
            justify-content: center;
            gap: 20px;
            align-items: center;
        }
        .sync-btn {
            background: var(--glass);
            border: 1px solid var(--glass-border);
            color: white;
            padding: 8px 20px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 14px;
        }

        .video-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 24px;
        }

        .tv-card { cursor: pointer; transition: 0.2s; }
        .tv-card:hover { transform: scale(1.02); }

        .thumb-wrap {
            position: relative;
            border-radius: 12px;
            overflow: hidden;
            aspect-ratio: 16/9;
            background: #222;
        }
        .thumb-wrap img { width: 100%; height: 100%; object-fit: cover; }
        
        .meta { margin-top: 12px; display: flex; gap: 12px; }
        .meta-text h3 { font-size: 16px; margin: 0 0 4px 0; color: #fff; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
        .meta-text p { color: #aaa; font-size: 13px; margin: 0; }

        #status { text-align: center; padding: 20px; color: #888; font-size: 18px; }

        nav.bottom-rail {
            position: fixed;
            bottom: 0; left: 0; right: 0;
            height: var(--nav-height);
            background: rgba(15, 15, 15, 0.98);
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 90px;
            border-top: 1px solid var(--glass-border);
            z-index: 100;
        }

        .nav-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            color: white;
            opacity: 0.6;
            cursor: pointer;
        }

        .nav-item.active { opacity: 1; }
        .nav-item svg { width: 24px; height: 24px; margin-bottom: 5px; }
        .nav-item span { font-size: 11px; }

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

        <div id="player-container">
            <div id="video-wrapper"></div>
            <div class="sync-controls">
                <div class="sync-btn" onclick="adjustSync()">Reset Video Buffer (Sync)</div>
            </div>
        </div>

        <div id="status">Loading...</div>
        <div class="video-grid" id="video-grid"></div>
    </main>

    <nav class="bottom-rail">
        <div class="nav-item active" onclick="location.reload()">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M4 10V21H9V15H15V21H20V10L12 3L4 10Z"></path></svg>
            <span>Home</span>
        </div>
        <div class="nav-item" onclick="fetchVideos('shorts')">
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
            status.innerText = "Connecting to YouTube...";

            let url;
            if (query) {
                url = `https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=20&q=${encodeURIComponent(query)}&type=video&key=${API_KEY}`;
            } else {
                url = `https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&chart=mostPopular&regionCode=US&maxResults=20&key=${API_KEY}`;
            }

            try {
                const res = await fetch(url);
                const data = await res.json();
                if (data.error) throw new Error(data.error.message);
                render(data.items, !!query);
                status.style.display = "none";
            } catch (e) {
                status.innerText = "Error: " + e.message;
            }
        }

        function playBypass(videoId) {
            const playerContainer = document.getElementById('player-container');
            const videoWrapper = document.getElementById('video-wrapper');
            
            playerContainer.style.display = "block";
            
            // Generate the MJPEG stream URL
            const streamUrl = `/stream/${videoId}?key=${SECRET}`;
            
            // Inject the bypass image
            videoWrapper.innerHTML = `<img id="bypass-img" src="${streamUrl}">`;
            
            // Scroll to player
            window.scrollTo({top: 0, behavior: 'smooth'});
        }

        function adjustSync() {
            const img = document.getElementById('bypass-img');
            if (!img) return;
            const currentSrc = img.src;
            img.src = "";
            setTimeout(() => { img.src = currentSrc; }, 100);
        }

        function render(items, isSearch) {
            const grid = document.getElementById('video-grid');
            grid.innerHTML = '';
            
            items.forEach(item => {
                const videoId = isSearch ? item.id.videoId : item.id;
                const snippet = item.snippet;
                
                const card = document.createElement('div');
                card.className = 'tv-card';
                
                // CLICK HANDLER UPDATED TO BYPASS
                card.onclick = () => playBypass(videoId);
                
                card.innerHTML = `
                    <div class="thumb-wrap">
                        <img src="${snippet.thumbnails.high.url}" loading="lazy">
                    </div>
                    <div class="meta">
                        <div class="meta-text">
                            <h3>${snippet.title}</h3>
                            <p>${snippet.channelTitle}</p>
                        </div>
                    </div>
                `;
                grid.appendChild(card);
            });
        }

        document.getElementById('search-box').onkeypress = (e) => {
            if(e.key === 'Enter') fetchVideos(e.target.value);
        };

        fetchVideos();
    </script>
</body>
</html>
    """)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
