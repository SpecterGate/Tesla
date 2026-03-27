<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Tesla YouTube TV</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500&display=swap" rel="stylesheet">
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

        /* Fixed Logo SVG */
        .logo-group svg {
            height: 32px;
            cursor: pointer;
        }

        .search-pill {
            background: var(--glass);
            border: 1px solid var(--glass-border);
            padding: 12px 25px;
            border-radius: 40px;
            width: 380px;
            display: flex;
            align-items: center;
            transition: all 0.2s ease;
        }

        .search-pill:focus-within {
            border-color: #3ea6ff;
            background: rgba(255,255,255,0.12);
            width: 420px;
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

        nav.bottom-rail {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            height: var(--nav-height);
            background: rgba(15, 15, 15, 0.98);
            backdrop-filter: blur(25px);
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 70px;
            border-top: 1px solid var(--glass-border);
            z-index: 1000;
        }

        .nav-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            cursor: pointer;
            color: white;
            opacity: 0.6;
            transition: all 0.2s;
            text-decoration: none;
            min-width: 80px;
        }

        .nav-item.active { opacity: 1; }
        .nav-item svg { width: 26px; height: 26px; margin-bottom: 6px; }
        .nav-item span { font-size: 12px; font-weight: 400; }

        .video-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 24px;
        }

        .tv-card { cursor: pointer; transition: transform 0.2s cubic-bezier(0.33, 1, 0.68, 1); }
        .tv-card:hover { transform: translateY(-5px); }

        .thumb-wrap {
            position: relative;
            border-radius: 14px;
            overflow: hidden;
            aspect-ratio: 16/9;
            background: #222;
        }

        .thumb-wrap img { width: 100%; height: 100%; object-fit: cover; }

        .duration {
            position: absolute;
            bottom: 10px;
            right: 10px;
            background: rgba(0,0,0,0.85);
            padding: 4px 7px;
            font-size: 12px;
            font-weight: 500;
            border-radius: 4px;
        }

        .meta { margin-top: 14px; display: flex; gap: 14px; }
        .channel-art { width: 40px; height: 40px; border-radius: 50%; background: #333; flex-shrink: 0; overflow: hidden; }
        .meta-text h3 { font-size: 17px; font-weight: 500; margin: 0 0 6px 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.4; color: #fff; }
        .meta-text p { color: #aaa; font-size: 14px; margin: 0; }

        #status-msg { width: 100%; text-align: center; padding: 40px; font-size: 18px; color: #888; }
    </style>
</head>
<body>

    <main>
        <div class="header-row">
            <div class="logo-group" onclick="location.reload()">
                <svg viewBox="0 0 100 24" xmlns="http://www.w3.org/2000/svg">
                    <path d="M23.5 4.6c-.3-1.1-1.1-1.9-2.2-2.2C19.3 2 12 2 12 2s-7.3 0-9.3.5C1.6 2.8.8 3.6.5 4.6 0 6.6 0 10.8 0 10.8s0 4.2.5 6.2c.3 1.1 1.1 1.9 2.2 2.2 2 1 9.3 1 9.3 1s7.3 0 9.3-.5c1.1-.3 1.9-1.1 2.2-2.2.5-2 .5-6.2.5-6.2s0-4.2-.5-6.2z" fill="#f00"/>
                    <path d="M9.6 15.4l6.3-3.6-6.3-3.6v7.2z" fill="#fff"/>
                    <path d="M32.5 17.5l-2.6-9.1h-2.1l-1.3 6.3c-.3 1.4-.6 2.8-.8 4.2h-.1c-.2-1.4-.5-2.8-.8-4.2l-1.4-6.3h-2.1l-2.6 9.1h1.9l.4-2.5c.2-1.1.4-2.2.6-3.4h.1c.2 1.2.4 2.3.6 3.4l.4 2.5h1.9l1.4-6.3c.3-1.4.6-2.8.8-4.2h.1c.2 1.4.5 2.8.8 4.2l1.4 6.3h1.9z" fill="#fff" transform="translate(10, 1) scale(0.8)"/>
                </svg>
            </div>
            <div class="search-pill">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="white"><path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"></path></svg>
                <input type="text" id="search-box" placeholder="Search videos...">
            </div>
        </div>

        <div id="status-msg">Fetching the latest videos...</div>
        <div class="video-grid" id="video-grid"></div>
    </main>

    <nav class="bottom-rail">
        <div class="nav-item active">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M4 10V21H9V15H15V21H20V10L12 3L4 10Z"></path></svg>
            <span>Home</span>
        </div>
        <div class="nav-item">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M10 14.65V10.5L14 12.58L10 14.65ZM17.77 10.32C17.33 8.31 15.57 7 13.5 7H13.22L14.73 5.3C15.41 4.54 15.34 3.37 14.58 2.69C13.82 2.01 12.65 2.08 11.97 2.84L8.33 6.91C7.3 8.06 7.31 9.77 8.35 10.91L8.68 11.27L7.23 12.87C6.55 13.63 6.62 14.8 7.38 15.48C8.14 16.16 9.31 16.09 9.99 15.33L13.63 11.26C14.66 10.11 14.65 8.4 13.61 7.26L13.28 6.9L14.73 5.3C14.73 5.3 14.74 5.29 14.74 5.29C14.88 5.14 15.02 5.3 14.73 5.3H13.5C14.88 5.3 16.04 6.13 16.5 7.35C16.96 8.57 16.64 9.94 15.71 10.84L12.07 14.91C11.66 15.37 11.02 15.6 10.4 15.53C9.77 15.46 9.24 15.1 8.92 14.58L8.35 13.63L6.23 15.97C5.07 17.26 5.16 19.24 6.45 20.41C7.74 21.58 9.72 21.49 10.89 20.2L14.53 16.13C16.48 13.96 16.27 10.65 14.07 8.74L13.74 8.45L15.19 6.85C16.56 5.32 18.73 5.15 20.31 6.45C21.89 7.75 22.15 10.03 20.9 11.63L17.77 15.14V10.32Z"></path></svg>
            <span>Shorts</span>
        </div>
        <div class="nav-item">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M10 18V7L15 12.5L10 18ZM20 3H4V1H20V3ZM22 6H2V4H22V6ZM22 19V8H2V19H22ZM12 21H2V23H22V21H12Z"></path></svg>
            <span>Subscriptions</span>
        </div>
    </nav>

    <script>
        // Use a more reliable public instance list
        const INSTANCES = [
            "https://pipedapi.leptons.xyz", 
            "https://api-piped.mha.fi",
            "https://pipedapi.kavin.rocks"
        ];
        let currentInstanceIdx = 0;

        async function fetchVideos(query = "") {
            const status = document.getElementById('status-msg');
            status.style.display = "block";
            status.innerText = "Loading...";

            try {
                const baseUrl = INSTANCES[currentInstanceIdx];
                const endpoint = query 
                    ? `${baseUrl}/search?q=${encodeURIComponent(query)}&filter=videos`
                    : `${baseUrl}/trending?region=US`;

                const response = await fetch(endpoint);
                if (!response.ok) throw new Error("API Limit Reached");
                
                const data = await response.json();
                renderVideos(query ? data.items : data);
                status.style.display = "none";
            } catch (err) {
                console.warn(`Instance ${INSTANCES[currentInstanceIdx]} failed, trying next...`);
                if (currentInstanceIdx < INSTANCES.length - 1) {
                    currentInstanceIdx++;
                    fetchVideos(query);
                } else {
                    status.innerText = "All instances busy. Try again in a minute.";
                }
            }
        }

        function renderVideos(videos) {
            const grid = document.getElementById('video-grid');
            grid.innerHTML = '';
            
            if (!videos || videos.length === 0) {
                document.getElementById('status-msg').innerText = "No videos found.";
                document.getElementById('status-msg').style.display = "block";
                return;
            }

            videos.forEach(v => {
                const card = document.createElement('div');
                card.className = 'tv-card';
                // Direct YouTube link for reliability
                const videoId = v.url.split('=')[1];
                card.onclick = () => window.open(`https://www.youtube.com/watch?v=${videoId}`, '_blank');
                
                card.innerHTML = `
                    <div class="thumb-wrap">
                        <img src="${v.thumbnail}" onerror="this.src='https://images.unsplash.com/photo-1611162617474-5b21e879e113?auto=format&fit=crop&w=800&q=60'">
                        <div class="duration">${v.duration > 0 ? formatTime(v.duration) : 'LIVE'}</div>
                    </div>
                    <div class="meta">
                        <div class="channel-art"><img src="https://ui-avatars.com/api/?name=${encodeURIComponent(v.uploaderName)}&background=random" style="width:100%"></div>
                        <div class="meta-text">
                            <h3>${v.title}</h3>
                            <p>${v.uploaderName} • ${v.shortViews || 'Live'}</p>
                        </div>
                    </div>
                `;
                grid.appendChild(card);
            });
        }

        function formatTime(s) {
            if (isNaN(s)) return s;
            const hrs = Math.floor(s / 3600);
            const mins = Math.floor((s % 3600) / 60);
            const secs = Math.floor(s % 60);
            return (hrs > 0 ? hrs + ":" : "") + (mins < 10 && hrs > 0 ? "0" : "") + mins + ":" + (secs < 10 ? "0" : "") + secs;
        }

        document.getElementById('search-box').onkeypress = (e) => {
            if(e.key === 'Enter') {
                currentInstanceIdx = 0; // Reset to first instance for new search
                fetchVideos(e.target.value);
            }
        };

        fetchVideos();
    </script>
</body>
</html>
