"""
System FPS benchmark — 4 kamera, 60s window, auto-stop.
Run: python run_fps_bench.py [config_label]
"""
import os, sys, time, threading

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_factory.settings')
sys.path.insert(0, '.')

MAX_WAIT = 360   # hard limit
FLUSH_INTERVAL = 0.5

def main():
    import django
    django.setup()

    label = sys.argv[1] if len(sys.argv) > 1 else "?"
    from monitor.camera_loader import start_all

    print(f"[BENCH] Config {label} — starting cameras...", flush=True)
    start_all()
    print(f"[BENCH] Waiting up to {MAX_WAIT}s for [INF 60s] window...", flush=True)

    # monitor output — wait until we see the 60s log from BOTH processes
    # Since child-process stdout goes to same console, we patch print in state_manager
    # Instead: just wait MAX_WAIT — child processes will print their 60s logs to console
    time.sleep(MAX_WAIT)
    print(f"[BENCH] Time limit reached.", flush=True)

if __name__ == '__main__':
    main()
