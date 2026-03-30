"""
Visualization Module - Person drawing and status display.
Handles: bracket drawing, status computation, frame updates
~120 lines
"""
import cv2
from collections import Counter

from .helpers import (
    draw_corner_brackets, draw_status_panel,
    get_person_bbox_from_keypoints, draw_danger_zones_overlay
)


def smooth_ppe_detections(ppe, ppe_history, cam_id):
    """
    Apply temporal smoothing to PPE detections to reduce flicker.
    Returns smoothed PPE list.
    """
    try:
        labels = [d.get("label", "").lower() for d in ppe]
        ppe_history[cam_id].append(labels)
    except Exception:
        pass
    
    smoothed_ppe = ppe
    try:
        flat = [lbl for hist in ppe_history[cam_id] for lbl in hist]
        counts = Counter(flat)
        if counts.get("helmet", 0) >= counts.get("head", 0):
            smoothed_ppe = [d for d in ppe if d.get("label", "").lower() != "head"]
    except Exception:
        smoothed_ppe = ppe
    
    return smoothed_ppe


def match_ppe_to_person(bbox, smoothed_ppe):
    """
    Match PPE detections to a person bounding box.
    Returns (has_helmet, has_vest, has_no_helmet).
    """
    x1, y1, x2, y2 = bbox
    has_helmet = False
    has_vest = False
    has_no_helmet = False
    
    for det in smoothed_ppe:
        det_bbox = det.get("bbox", [0, 0, 0, 0])
        det_label = det.get("label", "").lower()
        dx1, dy1, dx2, dy2 = det_bbox
        
        # Check if detection overlaps with person bbox
        if (dx1 < x2 and dx2 > x1 and dy1 < y2 and dy2 > y1):
            if det_label == "helmet":
                has_helmet = True
            elif det_label == "vest":
                has_vest = True
            elif det_label == "head":
                has_no_helmet = True
    
    return has_helmet, has_vest, has_no_helmet


def draw_person_visualization(frame, poses, smoothed_ppe, danger_zone_cache, cam_id):
    """
    Draw unified person visualization with brackets, status panels, and danger zones.
    """
    if not poses:
        # Just draw danger zone overlay if no people
        draw_danger_zones_overlay(frame, danger_zone_cache.get(cam_id, []))
        return
    
    for idx, pose in enumerate(poses):
        kps = pose.get("keypoints", [])
        bbox = get_person_bbox_from_keypoints(kps)
        if not bbox:
            continue
        
        x1, y1, x2, y2 = bbox
        
        # Determine person status
        is_fall = pose.get("fall") is not None
        is_danger_zone = pose.get("danger_zone") is not None
        
        # Match PPE to this person
        has_helmet, has_vest, has_no_helmet = match_ppe_to_person(bbox, smoothed_ppe)
        
        # Determine bracket color and status text
        # Note: No helmet status is shown via icon panel only, no orange bracket or text
        if is_fall:
            bracket_color = (0, 0, 255)  # Red
            status_text = "FALL!"
        elif is_danger_zone:
            bracket_color = (0, 0, 255)  # Red
            status_text = "DANGER"
        else:
            bracket_color = (0, 255, 0)  # Green (no helmet uses icon instead of orange bracket)
            status_text = "OK"
        
        # Draw corner brackets
        draw_corner_brackets(frame, x1, y1, x2, y2, bracket_color, thickness=2, corner_len=25)
        
        # Draw status panel on the left
        draw_status_panel(frame, x1, y1, has_helmet, has_vest, is_fall, is_danger_zone)
        
        # Draw status text above brackets (only for FALL and DANGER)
        if status_text != "OK":
            cv2.putText(frame, status_text, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, bracket_color, 2)
        
        # Draw danger zone alert marker
        if is_danger_zone:
            dz = pose.get("danger_zone")
            if dz and dz.get("hip_center"):
                hx, hy = int(dz["hip_center"][0]), int(dz["hip_center"][1])
                cv2.circle(frame, (hx, hy), 8, (0, 0, 255), -1)
    
    # Draw danger zones overlay
    draw_danger_zones_overlay(frame, danger_zone_cache.get(cam_id, []))


def compute_status(cam_id, state, smoothed_ppe, poses=None):
    """
    Compute real-time status for frontend status bar.
    Returns: "Danger", "Warning", or "Safe"

    poses: current detected poses — if empty, person-dependent statuses are suppressed.
    """
    try:
        no_person = not poses  # True when room is empty / no detection

        # Fall and danger zone alerts only make sense when a person is present.
        # If poses is empty, these states are being reset in the main loop already,
        # but we also suppress them here to avoid a 1-frame flicker.
        if not no_person:
            has_danger_zone_alert = any(state.danger_zone_alerted.get(cam_id, {}).values())

            if state.fall_alerted.get(cam_id) or has_danger_zone_alert:
                return "Danger"
            elif state.fall_start_time.get(cam_id) is not None:
                return "Warning"
            elif any(state.danger_zone_start_time.get(cam_id, {}).values()):
                return "Warning"

        # No-helmet check: only relevant when a person is detected
        if not no_person:
            has_no_helmet = any(d.get("label", "").lower() == "head" for d in smoothed_ppe)
            if has_no_helmet:
                return "Warning"

        return "Safe"
    except Exception:
        return "Safe"


def send_frame_to_queue(frame, frame_queues, cam_id):
    """Send frame to frontend queue (non-blocking)."""
    if frame_queues and cam_id in frame_queues:
        fq = frame_queues[cam_id]
        # Clear old frames for smooth streaming
        while not fq.empty():
            try:
                fq.get_nowait()
            except Exception:
                pass
        try:
            fq.put(frame.copy(), block=False)
        except:
            pass  # Queue full, skip
