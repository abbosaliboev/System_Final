# backend/ai_factory/monitor/stream_views.py
from datetime import timedelta
import cv2
import time
from django.http import StreamingHttpResponse, HttpResponse
from .camera_loader import frame_queues, camera_results
from .pose_utils import draw_poses
from .models import DangerZone
from monitor.models import Alert
from django.utils.timezone import now
from django.core.files.base import ContentFile

# 🎨 Draw bounding boxes for FIRE only (PPE handled by unified visualization)

def draw_detections(frame, detections, camera_id):
    camera_num = int(str(camera_id).replace("cam", ""))
    annotated_frame = frame.copy()  # Create copy for annotations

    for det in detections:
        label = det.get("label", "unknown").lower()
        conf = det.get("confidence", 0)
        x1, y1, x2, y2 = det.get("bbox", [0, 0, 0, 0])

        # Only draw box for FIRE detection (PPE is handled by unified person visualization)
        if label == "fire":
            color = (0, 0, 255)  # Red for fire
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 3)
            cv2.putText(annotated_frame, f"FIRE! {int(conf * 100)}%",
                        (x1, max(20, y1 - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

            save_alert(
                camera_id=camera_num,
                alert_type="fire",
                frame=frame,
                annotated_frame=annotated_frame
            )

        # Save no_helmet alerts (but don't draw box - unified visualization handles it)
        elif label == "head":
            save_alert(
                camera_id=camera_num,
                alert_type="no_helmet",
                frame=frame,
                annotated_frame=annotated_frame
            )

    return annotated_frame


# P4: Module-level danger zone cache — avoids DB query on every frame
_zone_cache = {}
_zone_cache_ts = {}
_ZONE_CACHE_TTL = 30.0  # seconds

# 📍 Load polygon zones from DB (with 30-second cache)
def get_camera_zones(cam_id):
    now_ts = time.monotonic()
    if cam_id in _zone_cache and now_ts - _zone_cache_ts.get(cam_id, 0) < _ZONE_CACHE_TTL:
        return _zone_cache[cam_id]  # P4: return cached value, skip DB

    try:
        cam_num = int(str(cam_id).replace("cam", ""))
    except Exception:
        cam_num = int(cam_id)

    zones = DangerZone.objects.filter(camera_id=cam_num)
    result = [zone.points for zone in zones]
    _zone_cache[cam_id] = result
    _zone_cache_ts[cam_id] = now_ts
    return result


# 💾 Save alert to DB
def save_alert(camera_id, alert_type, frame=None, annotated_frame=None, worker_id=None):
    # Check if similar alert exists in last 30 minutes
    recent_time = now() - timedelta(seconds=1800)
    exists = Alert.objects.filter(
        camera_id=camera_id,
        alert_type=alert_type,
        timestamp__gte=recent_time
    ).exists()

    if not exists:
        alert = Alert.objects.create(
            camera_id=camera_id,
            alert_type=alert_type,
            worker_id=worker_id,
            timestamp=now()
        )

        # Save the annotated frame (with bounding boxes) if provided
        if annotated_frame is not None:
            _, buffer = cv2.imencode('.jpg', annotated_frame)
            image_file = ContentFile(buffer.tobytes(), name=f'alert_{alert.id}_annotated.jpg')
            alert.frame_image.save(f'alert_{alert.id}_annotated.jpg', image_file)
            alert.save()


# 🔁 MJPEG generator: gets pre-inferred detections & current frame
def generate_stream(cam_id):
    while True:
        if cam_id not in frame_queues or cam_id not in camera_results:
            time.sleep(0.1)
            continue

        # P5: blocking get() instead of busy-wait empty() + sleep(0.01)
        try:
            frame = frame_queues[cam_id].get(timeout=0.033)
        except Exception:
            continue

        # 🧠 Get detections and poses from shared memory
        cam_data = camera_results.get(cam_id, {})
        detections = cam_data.get("detections", [])
        poses = cam_data.get("poses", [])

        # 🎯 Load danger zones for this camera (P4: cached, no DB hit per frame)
        danger_zones = get_camera_zones(cam_id)

        # 🖼️ Draw detection boxes and save fire/no_helmet alerts
        frame = draw_detections(frame, detections, cam_id)

        # 🧍 Draw skeletons + red center if inside danger zone
        frame, alerts = draw_poses(frame, poses, danger_zones=danger_zones)

        # 🔔 FALL alerts: check per-pose 'fall' annotation produced by worker
        if poses:
            for pose in poses:
                fall_info = pose.get("fall")
                if fall_info and isinstance(fall_info, dict):
                    txt = str(fall_info.get("text", "")).upper()
                    if txt.startswith("FALL"):
                        camera_num = int(str(cam_id).replace("cam", ""))
                        print(f"⚠️ FALL ALERT [{cam_id}] detected - saving to DB")
                        save_alert(camera_id=camera_num, alert_type="fall", frame=frame, annotated_frame=frame)

        if alerts:
            print(f"⚠️ ALERT [{cam_id}]: {len(alerts)} person(s) inside danger zone.")
            for alert in alerts:
                camera_num = int(str(cam_id).replace("cam", ""))
                save_alert(camera_id=camera_num, alert_type="danger_zone")

        # 📦 Encode as JPEG
        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')


# 🔗 Django view
def video_feed(request, cam_id):
    if cam_id not in frame_queues:
        return HttpResponse("Camera not found", status=404)

    return StreamingHttpResponse(
        generate_stream(cam_id),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )
