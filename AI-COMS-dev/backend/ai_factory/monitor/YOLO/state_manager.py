
"""
State Manager - Camera state tracking and initialization.
Handles: state variables, fall tracking, danger zone tracking, frame grabbers
~120 lines
"""
import time
from queue import Queue
from threading import Thread
from collections import deque

from .inference_utils import frame_grabber


class CameraStateManager:
    """
    Manages all state tracking for camera inference.
    Centralizes state initialization and management.
    """
    
    # Constants
    FALL_DURATION_THRESHOLD = 1.0      # Fall must persist for 1.0 sec
    FALL_COOLDOWN_DURATION = 3.0       # Keep fall alert active for 3 sec
    DANGER_ZONE_REFRESH_INTERVAL = 10.0  # Refresh zones from DB every 10 sec
    DANGER_ZONE_DURATION_THRESHOLD = 1.5  # Person must be in zone for 1.5 sec
    
    def __init__(self, cam_list):
        """Initialize state for all cameras in the list."""
        self.cam_list = cam_list
        self.cam_ids = [cam["id"] for cam in cam_list]
        
        # Frame timing
        self.last_frame_time = {cam_id: 0.0 for cam_id in self.cam_ids}
        self.toggle = {cam_id: 0 for cam_id in self.cam_ids}
        
        # Detection caches
        self.last_pose = {cam_id: [] for cam_id in self.cam_ids}
        self.last_ppe = {cam_id: [] for cam_id in self.cam_ids}
        
        # PPE history for temporal smoothing
        self.ppe_history = {cam_id: deque(maxlen=5) for cam_id in self.cam_ids}
        
        # Fall detection tracking
        self.fall_start_time = {cam_id: None for cam_id in self.cam_ids}
        self.fall_alerted = {cam_id: False for cam_id in self.cam_ids}
        self.fall_cooldown_until = {cam_id: 0.0 for cam_id in self.cam_ids}
        
        # Danger zone tracking
        self.danger_zone_cache = {cam_id: [] for cam_id in self.cam_ids}
        self.danger_zone_last_fetch = {cam_id: 0.0 for cam_id in self.cam_ids}
        self.danger_zone_alerted = {cam_id: {} for cam_id in self.cam_ids}
        self.danger_zone_start_time = {cam_id: {} for cam_id in self.cam_ids}
        
        # Frame grabbers
        self.grabber_threads = {}
        self.input_queues = {}
        
        # FPS tracking
        self.fps_window_start = time.monotonic()
        self.cam_counts = {cam_id: 0 for cam_id in self.cam_ids}

        # ✅ (추가) 60초 처리 프레임수 용
        self.min_window_start = time.monotonic()
        self.min_counts = {cam_id: 0 for cam_id in self.cam_ids}
    
    def start_frame_grabbers(self):
        """Start frame grabber threads for all cameras."""
        for cam in self.cam_list:
            cam_id = cam["id"]
            url = cam["url"]
            q = Queue(maxsize=1)
            self.input_queues[cam_id] = q
            t = Thread(target=frame_grabber, args=(cam_id, url, q), daemon=True)
            t.start()
            self.grabber_threads[cam_id] = t
            print(f"[{cam_id}] Frame grabber thread started")
    
    def reset_fall_state(self, cam_id):
        """Reset fall detection state for a camera."""
        self.fall_start_time[cam_id] = None
        self.fall_alerted[cam_id] = False
    
    def update_fall_state(self, cam_id, is_fall, confidence, now):
        """
        Update fall state with duration tracking and cooldown.
        Returns True if fall should be visualized.
        """
        if is_fall:
            # Start or continue fall tracking
            if self.fall_start_time[cam_id] is None:
                self.fall_start_time[cam_id] = now
            
            fall_duration = now - self.fall_start_time[cam_id]
            
            if fall_duration >= self.FALL_DURATION_THRESHOLD:
                self.fall_alerted[cam_id] = True
                # High confidence -> extend cooldown
                if confidence >= 0.7:
                    self.fall_cooldown_until[cam_id] = now + self.FALL_COOLDOWN_DURATION
                return True
        else:
            # Check if still in cooldown
            if now < self.fall_cooldown_until[cam_id]:
                return True  # Keep showing fall during cooldown
            else:
                self.reset_fall_state(cam_id)
        
        return False
    
    def log_fps(self):
        """Log FPS statistics and reset counters."""
        now_m = time.monotonic()
        elapsed = now_m - self.fps_window_start
        
        if elapsed >= 1.0:
            per_cam_fps = {}
            active_counts = 0
            fps_sum = 0.0
            
            for cid, cnt in self.cam_counts.items():
                fps_val = cnt / elapsed if elapsed > 0 else 0
                per_cam_fps[cid] = fps_val
                fps_sum += fps_val
                if cnt > 0:
                    active_counts += 1
            
            avg_fps = (fps_sum / active_counts) if active_counts > 0 else 0.0
            cams_str = "  ".join([f"{cid}={per_cam_fps[cid]:.1f}" for cid in sorted(per_cam_fps)])
            
            from multiprocessing import current_process
            print(f"[INF FPS] {current_process().name}  {cams_str}", end="")
            if active_counts > 1:
                print(f"  |  AVG={avg_fps:.1f}")
            else:
                print()
            
            # Reset counters
            self.fps_window_start = now_m
            for cid in self.cam_counts:
                self.cam_counts[cid] = 0

    def log_minute_counts(self):
        now_m = time.monotonic()
        elapsed = now_m - self.min_window_start

        if elapsed >= 60.0:
            from multiprocessing import current_process

            # 1) per-cam: total frames in 60s window
            totals_str = "  ".join([
                f"{cid}:total={self.min_counts[cid]}"
                for cid in sorted(self.min_counts)
            ])

            # 2) per-cam: avg FPS over the 60s window
            fps_str = "  ".join([
                f"{cid}:fps={self.min_counts[cid] / elapsed:.2f}"
                for cid in sorted(self.min_counts)
            ])

            # 3) overall totals (all cams)
            total_all = sum(self.min_counts.values())
            fps_all = total_all / elapsed if elapsed > 0 else 0.0

            print(f"***** [INF 60s] {current_process().name} *****")
            print("  " + totals_str)
            print("  " + fps_str + f"  |  ALL:total={total_all} ALL:fps={fps_all:.2f}  |  elapsed={elapsed:.1f}s")

            # reset window
            self.min_window_start = now_m
            for cid in self.min_counts:
                self.min_counts[cid] = 0
