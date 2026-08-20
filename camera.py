#!/usr/bin/env python3
import os
import time
import threading
import signal
import sys
import socket
from datetime import datetime
from flask import Flask, Response, send_file
from io import BytesIO
from PIL import Image
import subprocess
import glob

try:
    from picamera2 import Picamera2
    CAMERA_AVAILABLE = True
except:
    CAMERA_AVAILABLE = False

class Timelapse:
    def __init__(self):
        self.photo_dir = os.path.expanduser("~/timelapse/photos")
        self.video_dir = os.path.expanduser("~/timelapse/videos")
        os.makedirs(self.photo_dir, exist_ok=True)
        os.makedirs(self.video_dir, exist_ok=True)
        
        self.count = 0
        self.running = True
        self.camera = None
        self.stream_img = None
        self.lock = threading.Lock()
        self.start = time.time()
        self.camera_working = False
        
        self.app = Flask(__name__)
        self.setup_routes()
        
        signal.signal(signal.SIGINT, self.stop)
    
    def setup_routes(self):
        @self.app.route('/')
        def home():
            total_photos = len(glob.glob(os.path.join(self.photo_dir, 'tl_*.jpg')))
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>✦ TIMELAPSE ✦</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <meta http-equiv="refresh" content="10">
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');
                    
                    * { margin: 0; padding: 0; box-sizing: border-box; }
                    
                    body {
                        font-family: 'VT323', 'Courier New', monospace;
                        background: #7d8c6e;
                        background-image: 
                            radial-gradient(circle at 20% 50%, #8b9b7e 1px, transparent 1px),
                            radial-gradient(circle at 80% 20%, #8b9b7e 1px, transparent 1px);
                        background-size: 50px 50px;
                        min-height: 100vh;
                        padding: 20px;
                        color: #2c3a1f;
                    }
                    
                    .crt {
                        max-width: 800px;
                        margin: 0 auto;
                        background: #c5d0b0;
                        border: 8px solid #4a5a3a;
                        border-radius: 15px;
                        box-shadow: 
                            0 0 0 4px #2c3a1f,
                            0 0 0 8px #4a5a3a,
                            0 0 20px rgba(0,0,0,0.5),
                            inset 0 0 60px rgba(44,58,31,0.1);
                        padding: 20px;
                        position: relative;
                        overflow: hidden;
                    }
                    
                    .crt::before {
                        content: '';
                        position: absolute;
                        top: 0; left: 0; right: 0; bottom: 0;
                        background: repeating-linear-gradient(
                            0deg,
                            transparent,
                            transparent 2px,
                            rgba(44,58,31,0.03) 2px,
                            rgba(44,58,31,0.03) 4px
                        );
                        pointer-events: none;
                    }
                    
                    .header {
                        text-align: center;
                        border-bottom: 3px double #4a5a3a;
                        padding-bottom: 15px;
                        margin-bottom: 15px;
                    }
                    
                    .header h1 {
                        font-size: 48px;
                        text-transform: uppercase;
                        letter-spacing: 4px;
                        color: #2c3a1f;
                        text-shadow: 2px 2px #8b9b7e;
                        margin: 0;
                    }
                    
                    .header .subtitle {
                        font-size: 18px;
                        color: #4a5a3a;
                        letter-spacing: 2px;
                    }
                    
                    .stream-box {
                        border: 4px solid #4a5a3a;
                        border-radius: 8px;
                        overflow: hidden;
                        margin: 15px 0;
                        background: #2c3a1f;
                        box-shadow: inset 0 0 20px rgba(0,0,0,0.3);
                        position: relative;
                    }
                    
                    .stream-box img {
                        width: 100%;
                        display: block;
                        filter: sepia(0.2) brightness(0.95);
                    }
                    
                    .stream-label {
                        position: absolute;
                        top: 10px;
                        left: 10px;
                        background: #2c3a1f;
                        color: #c5d0b0;
                        padding: 3px 8px;
                        font-size: 14px;
                        letter-spacing: 1px;
                        border: 1px solid #4a5a3a;
                        z-index: 10;
                    }
                    
                    .status-panel {
                        display: grid;
                        grid-template-columns: repeat(2, 1fr);
                        gap: 10px;
                        margin: 15px 0;
                    }
                    
                    .stat {
                        background: #b8c5a4;
                        border: 2px solid #4a5a3a;
                        padding: 10px;
                        text-align: center;
                    }
                    
                    .stat .label {
                        font-size: 14px;
                        text-transform: uppercase;
                        letter-spacing: 2px;
                        color: #4a5a3a;
                        margin-bottom: 5px;
                    }
                    
                    .stat .value {
                        font-size: 36px;
                        color: #2c3a1f;
                        text-shadow: 1px 1px #8b9b7e;
                    }
                    
                    .controls {
                        text-align: center;
                        margin-top: 15px;
                    }
                    
                    .btn {
                        display: inline-block;
                        padding: 10px 20px;
                        margin: 5px;
                        font-family: 'VT323', monospace;
                        font-size: 20px;
                        text-transform: uppercase;
                        letter-spacing: 2px;
                        text-decoration: none;
                        background: #8b9b7e;
                        color: #2c3a1f;
                        border: 3px solid #4a5a3a;
                        cursor: pointer;
                        transition: all 0.1s;
                    }
                    
                    .btn:hover {
                        background: #7d8c6e;
                        border-color: #2c3a1f;
                        transform: translateY(-2px);
                        box-shadow: 0 4px 0 #4a5a3a;
                    }
                    
                    .btn:active {
                        transform: translateY(0);
                        box-shadow: none;
                    }
                    
                    .blink {
                        animation: blink 1s infinite;
                    }
                    
                    @keyframes blink {
                        0%, 100% { opacity: 1; }
                        50% { opacity: 0; }
                    }
                    
                    .footer {
                        text-align: center;
                        margin-top: 20px;
                        font-size: 14px;
                        color: #4a5a3a;
                        letter-spacing: 2px;
                    }
                    
                    .scanlines {
                        position: absolute;
                        top: 0; left: 0; right: 0; bottom: 0;
                        background: repeating-linear-gradient(
                            0deg,
                            transparent,
                            transparent 2px,
                            rgba(0,0,0,0.02) 2px,
                            rgba(0,0,0,0.02) 4px
                        );
                        pointer-events: none;
                    }
                </style>
            </head>
            <body>
                <div class="crt">
                    <div class="scanlines"></div>
                    <div class="header">
                        <h1>◈ TIMELAPSE ◈</h1>
                        <div class="subtitle">retro surveillance system v1.0</div>
                    </div>
                    
                    <div class="stream-box">
                        <div class="stream-label">● LIVE FEED</div>
                        <img src="/stream" alt="Camera Stream">
                    </div>
                    
                    <div class="status-panel">
                        <div class="stat">
                            <div class="label">[ CAPTURES ]</div>
                            <div class="value">''' + str(total_photos) + '''</div>
                        </div>
                        <div class="stat">
                            <div class="label">[ RUNTIME ]</div>
                            <div class="value">''' + self.runtime() + '''</div>
                        </div>
                        <div class="stat">
                            <div class="label">[ INTERVAL ]</div>
                            <div class="value">5s</div>
                        </div>
                        <div class="stat">
                            <div class="label">[ STORAGE ]</div>
                            <div class="value">''' + self.free_space() + '''</div>
                        </div>
                    </div>
                    
                    <div class="controls">
                        <a href="/stream" class="btn">▶ STREAM</a>
                        <a href="/video" class="btn">⬇ VIDEO</a>
                    </div>
                    
                    <div class="footer">
                        <span class="blink">⬤</span> SYSTEM ACTIVE - ALL PHOTOS SAVED <span class="blink">⬤</span>
                    </div>
                </div>
            </body>
            </html>'''
        
        @self.app.route('/stream')
        def stream():
            return Response(
                self.gen_stream(),
                mimetype='multipart/x-mixed-replace; boundary=frame'
            )
        
        @self.app.route('/video')
        def video():
            v = self.make_video()
            return send_file(v, as_attachment=True) if v else ("NOT READY", 404)
    
    def runtime(self):
        t = int(time.time() - self.start)
        h, m, s = t//3600, (t%3600)//60, t%60
        return f"{h:02d}:{m:02d}:{s:02d}"
    
    def free_space(self):
        try:
            s = os.statvfs('/')
            free = (s.f_frsize * s.f_bavail) / (1024**3)
            return f"{free:.1f}G"
        except:
            return "N/A"
    
    def gen_stream(self):
        while self.running:
            with self.lock:
                if self.stream_img:
                    io = BytesIO()
                    self.stream_img.save(io, 'JPEG', quality=70)
                    frame = io.getvalue()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n'
                           b'Content-Length: ' + str(len(frame)).encode() + b'\r\n\r\n' + 
                           frame + b'\r\n')
            time.sleep(0.033)
    
    def init_camera(self):
        print("📸 Initializing camera...")
        try:
            if not CAMERA_AVAILABLE:
                raise Exception("Picamera2 not installed")
            
            self.camera = Picamera2()
            config = self.camera.create_video_configuration(
                main={"size": (1280, 720)},
                controls={"FrameDurationLimits": (33333, 33333)}
            )
            self.camera.configure(config)
            self.camera.start()
            time.sleep(2)
            
            test_path = os.path.join(self.photo_dir, "test_init.jpg")
            self.camera.capture_file(test_path)
            if os.path.exists(test_path):
                os.remove(test_path)
                print("✅ Camera working!")
                self.camera_working = True
                return True
        except Exception as e:
            print(f"❌ Camera init error: {e}")
            self.camera_working = False
            return False
    
    def capture(self):
        if not self.camera_working:
            return False
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            fname = f"tl_{timestamp}_{self.count:06d}.jpg"
            fpath = os.path.join(self.photo_dir, fname)
            
            self.camera.capture_file(fpath)
            
            if not os.path.exists(fpath) or os.path.getsize(fpath) == 0:
                print("❌ Failed to save photo")
                return False
            
            img = Image.open(fpath)
            img.save(fpath, 'JPEG', quality=85, optimize=True)
            
            self.count += 1
            
            if self.count % 100 == 0:
                total_photos = len(glob.glob(os.path.join(self.photo_dir, 'tl_*.jpg')))
                photo_size = sum(os.path.getsize(f) for f in glob.glob(os.path.join(self.photo_dir, 'tl_*.jpg')))
                size_mb = photo_size / (1024*1024)
                print(f"📷 {total_photos} photos total | {size_mb:.1f}MB used | ALL PHOTOS SAVED")
                
                if size_mb > 2000:
                    print("⚠️  WARNING: Photos using over 2GB! Consider manual cleanup.")
            
            if self.count % 12 == 0:
                print(f"📸 {self.count} new captures | Next in 5s")
            
            return True
        except Exception as e:
            print(f"❌ Capture failed: {e}")
            return False
    
    def update_stream(self):
        while self.running:
            try:
                if self.camera_working:
                    io = BytesIO()
                    self.camera.capture_file(io, format='jpeg')
                    io.seek(0)
                    with self.lock:
                        self.stream_img = Image.open(io)
                time.sleep(0.033)
            except Exception as e:
                print(f"Stream error: {e}")
                time.sleep(1)
    
    def make_video(self):
        try:
            photos = sorted(glob.glob(os.path.join(self.photo_dir, 'tl_*.jpg')))
            if len(photos) < 10:
                return None
            
            all_photos = photos
            
            lst = os.path.join(self.video_dir, "list.txt")
            with open(lst, 'w') as f:
                for p in all_photos:
                    f.write(f"file '{p}'\n")
            
            out = os.path.join(self.video_dir, "timelapse_all.mp4")
            subprocess.run([
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', lst,
                '-framerate', '30', '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                '-preset', 'ultrafast', '-crf', '23',
                out
            ], capture_output=True, timeout=120)
            
            if os.path.exists(lst):
                os.remove(lst)
            
            if os.path.exists(out):
                size_mb = os.path.getsize(out) / (1024*1024)
                total = len(all_photos)
                print(f"🎬 Video ready: {size_mb:.1f}MB | {total} photos | {total/30:.0f} seconds")
            return out
        except Exception as e:
            print(f"Video error: {e}")
            return None
    
    def capture_loop(self):
        print("⏱️  Capture loop starting (every 5 seconds) - ALL PHOTOS SAVED")
        next_capture = time.time() + 5
        
        while self.running:
            now = time.time()
            if now >= next_capture:
                self.capture()
                next_capture = now + 5.0
            else:
                time.sleep(0.1)
    
    def video_loop(self):
        while self.running:
            time.sleep(120)
            self.make_video()
    
    def stop(self, *args):
        total = len(glob.glob(os.path.join(self.photo_dir, 'tl_*.jpg')))
        print(f"\n🛑 Shutdown. {total} total photos saved")
        self.running = False
        if self.camera:
            self.camera.stop()
        sys.exit(0)
    
    def run(self):
        print("""
╔══════════════════════════════════════╗
║   RETRO TIMELAPSE SYSTEM v2.0       ║
║   Sage Green - ALL PHOTOS SAVED     ║
╚══════════════════════════════════════╝
        """)
        
        if not self.init_camera():
            print("⚠️  Camera not working! Check connection.")
        
        self.start = time.time()
        
        threading.Thread(target=self.update_stream, daemon=True).start()
        threading.Thread(target=self.capture_loop, daemon=True).start()
        threading.Thread(target=self.video_loop, daemon=True).start()
        
        ip = socket.gethostbyname(socket.gethostname())
        print(f"""
┌──────────────────────────────────────┐
│  ◈ RETRO TIMELAPSE ONLINE ◈        │
├──────────────────────────────────────┤
│  Web:  http://{ip}:8080/  │
│  VLC:  http://{ip}:8080/stream │
│  Vid:  http://{ip}:8080/video │
│  Interval: 5 seconds                │
│  Storage: ALL PHOTOS SAVED          │
│  Theme: Sage Green Retro            │
└──────────────────────────────────────┘
        """)
        
        self.app.run(host='0.0.0.0', port=8080, threaded=True)

if __name__ == "__main__":
    Timelapse().run()
