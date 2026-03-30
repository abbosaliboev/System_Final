"""
YOLO Inference Utilities - Model loading, PPE/Pose inference, Frame grabbing.
~120 lines
"""
import os
import cv2
import time
from queue import Queue
from ultralytics import YOLO

from .helpers import _to_numpy, _bbox_to_int_list

# ─────────────────────────────────────────────────────────────
# Model Loading
# ─────────────────────────────────────────────────────────────
def load_models():
    """
    Load PPE detection and Pose models.

    PPE model priority:
      1. unify-29march.pt  — shared-backbone unified model (pose-aware backbone, detect head)
      2. best_detect.engine — TensorRT fallback

    Pose model priority:
      1. yolo11n-10kp.pt   — 10 keypoint model (.pt)
      2. best_pose.engine  — 17 keypoint TensorRT fallback
    """
    # ── PPE model ──────────────────────────────────────────────
    ppe_model_paths = [
        ("monitor/YOLO/models/unify-29march.engine", 'detect'),  # unified TensorRT FP16 (fastest)
        ("monitor/YOLO/models/unify-29march.pt",     'detect'),  # unified PT fallback
        ("monitor/YOLO/models/best_detect.engine",   'detect'),  # old TensorRT fallback
    ]
    ppe_model = None
    for path, task in ppe_model_paths:
        try:
            ppe_model = YOLO(path, task=task)
            print(f"[Models] PPE model loaded: {path}")
            break
        except Exception as e:
            print(f"[Models] Failed to load PPE model {path}: {e}")

    if ppe_model is None:
        raise RuntimeError("[Models] No valid PPE model found!")

    # ── Pose model ─────────────────────────────────────────────
    pose_model_paths = [
        ("monitor/YOLO/models/yolo11n-10kp.pt",  'pose'),   # 10 keypoint model
        ("monitor/YOLO/models/best_pose.engine", 'pose'),   # 17 keypoint TensorRT fallback
    ]
    pose_model = None
    for path, task in pose_model_paths:
        try:
            pose_model = YOLO(path, task=task)
            print(f"[Models] Pose model loaded: {path}")
            break
        except Exception as e:
            print(f"[Models] Failed to load pose model {path}: {e}")

    if pose_model is None:
        raise RuntimeError("[Models] No valid pose model found!")

    return ppe_model, pose_model

# ─────────────────────────────────────────────────────────────
# PPE Inference
# ─────────────────────────────────────────────────────────────
def ppe_infer(ppe_model, frame):
    """Detect PPE: helmet (0), vest (1), head (2)"""
    detections = []
    r = ppe_model.predict(source=frame, imgsz=640, conf=0.30, verbose=False)[0]
    if getattr(r, "boxes", None) is not None:
        xyxy = _to_numpy(r.boxes.xyxy)
        conf = _to_numpy(r.boxes.conf)
        cls = _to_numpy(r.boxes.cls)
        names = r.names
        for i in range(len(xyxy)):
            detections.append({
                "label": names[int(cls[i])],
                "confidence": float(conf[i]),
                "bbox": _bbox_to_int_list(xyxy[i]),
            })
    return detections

# ─────────────────────────────────────────────────────────────
# Pose Inference
# ─────────────────────────────────────────────────────────────
def pose_infer(pose_model, frame):
    """
    Detect human poses (supports both 10 and 17 keypoints).
    Returns keypoints in consistent format.
    """
    poses = []
    r = pose_model.predict(source=frame, imgsz=640, conf=0.25, verbose=False)[0]
    kp_obj = getattr(r, "keypoints", None)
    if kp_obj is None:
        return poses
    kps = getattr(kp_obj, "xy", None)
    if kps is None:
        return poses
    kps = _to_numpy(kps)
    
    # Get confidence scores if available
    kp_conf = getattr(kp_obj, "conf", None)
    if kp_conf is not None:
        kp_conf = _to_numpy(kp_conf)
    
    for idx, kp in enumerate(kps):
        conf = kp_conf[idx] if kp_conf is not None else None
        poses.append({
            "keypoints": kp.tolist(),
            "conf": conf.tolist() if conf is not None else None
        })
    return poses

# ─────────────────────────────────────────────────────────────
# Frame Grabber Thread
# ─────────────────────────────────────────────────────────────
#2 ─────────────────────────────────────────────────────────────
def frame_grabber(cam_id, url, frame_queue):
    """Background thread to continuously grab frames from RTSP stream"""
    print(f"[{cam_id}] Starting frame grabber thread for {url}")
    
    retry_delay = 2.0
    max_retry_delay = 10.0
    
    while True:
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY)
        
        if not cap.isOpened():
            print(f"[{cam_id}] Failed to open stream. Retrying in {retry_delay}s...")
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 1.5, max_retry_delay)
            continue
        
        retry_delay = 2.0
        print(f"[{cam_id}] Stream connected successfully")
        
        consecutive_failures = 0
        max_consecutive_failures = 10
        
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                consecutive_failures += 1
                if consecutive_failures >= max_consecutive_failures:
                    print(f"[{cam_id}] Too many consecutive failures. Reopening...")
                    cap.release()
                    time.sleep(1.0)
                    break
                continue
            
            consecutive_failures = 0
            
            # Keep only latest frame
            while not frame_queue.empty():
                try:
                    frame_queue.get_nowait()
                except Exception:
                    pass
            
            try:
                frame_queue.put(frame, block=False)
            except:
                pass
                
        cap.release()

# ─────────────────────────────────────────────────────────────
# Database Helpers (for danger zone)
# ─────────────────────────────────────────────────────────────
def extract_camera_num(cam_id):
    """Extract numeric camera ID from string like 'cam3' -> 3"""
    import re
    if isinstance(cam_id, int):
        return cam_id
    if isinstance(cam_id, str):
        match = re.search(r'\d+', cam_id)
        if match:
            return int(match.group())
    return None

def fetch_danger_zones(cam_id):
    """Fetch danger zones for a camera from Django database"""
    try:
        import django
        django.setup()
        from monitor.models import DangerZone
        cam_num = extract_camera_num(cam_id)
        if cam_num is None:
            return []
        zones = DangerZone.objects.filter(camera_id=cam_num)
        return [{"zone_name": z.zone_name, "points": z.points} for z in zones]
    except Exception as e:
        print(f"[DangerZone] Error fetching zones for cam {cam_id}: {e}")
        return []

def save_danger_zone_alert(cam_id, zone_name, frame=None):
    """Save danger zone alert to database"""
    try:
        import django
        import cv2
        django.setup()
        from monitor.models import Alert
        from django.utils.timezone import now
        from datetime import timedelta
        from django.core.files.base import ContentFile
        
        cam_num = extract_camera_num(cam_id)
        if cam_num is None:
            return False
        
        recent_time = now() - timedelta(seconds=50)
        exists = Alert.objects.filter(
            camera_id=cam_num,
            alert_type='danger_zone',
            timestamp__gte=recent_time
        ).exists()
        
        if not exists:
            alert = Alert.objects.create(camera_id=cam_num, alert_type='danger_zone', timestamp=now())
            if frame is not None:
                _, buffer = cv2.imencode('.jpg', frame)
                image_file = ContentFile(buffer.tobytes(), name=f'alert_{alert.id}_dangerzone.jpg')
                alert.frame_image.save(f'alert_{alert.id}_dangerzone.jpg', image_file)
                alert.save()
            print(f"[DangerZone] Alert saved for cam {cam_id}, zone: {zone_name}")
            return True
    except Exception as e:
        print(f"[DangerZone] Error saving alert for cam {cam_id}: {e}")
    return False
