"""
YOLO Streaming Helpers - Visualization and Danger Zone detection.
~150 lines - Icon loading, drawing, danger zone checking.
"""
import os
import cv2
import numpy as np

# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────
KP_LEFT_HIP = 11
KP_RIGHT_HIP = 12
ICONS_DIR = os.path.join(os.path.dirname(__file__), "icons")
ICON_SIZE = 24

# ─────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────
def _to_numpy(x):
    try:
        import torch
        if hasattr(x, "detach"):
            return x.detach().cpu().numpy()
    except Exception:
        pass
    return x

def _bbox_to_int_list(xyxy_row):
    return [int(v) for v in list(xyxy_row)]

# ─────────────────────────────────────────────────────────────
# Icon Loading
# ─────────────────────────────────────────────────────────────
def load_icon(filename):
    """Load and resize icon with alpha channel"""
    path = os.path.join(ICONS_DIR, filename)
    if os.path.exists(path):
        icon = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if icon is not None:
            return cv2.resize(icon, (ICON_SIZE, ICON_SIZE))
    return None

# Pre-load icons
ICON_HELMET_OK = load_icon("helmet_ok.png")
ICON_HELMET_NO = load_icon("helmet_no.png")
ICON_VEST_OK = load_icon("vest_ok.png")
ICON_VEST_NO = load_icon("vest_no.png")

def overlay_icon(frame, icon, x, y):
    """Overlay PNG icon with alpha transparency onto frame"""
    if icon is None:
        return
    h, w = icon.shape[:2]
    if x < 0 or y < 0 or x + w > frame.shape[1] or y + h > frame.shape[0]:
        return
    if icon.shape[2] == 4:
        alpha = icon[:, :, 3] / 255.0
        for c in range(3):
            frame[y:y+h, x:x+w, c] = alpha * icon[:, :, c] + (1 - alpha) * frame[y:y+h, x:x+w, c]
    else:
        frame[y:y+h, x:x+w] = icon[:, :, :3]

# ─────────────────────────────────────────────────────────────
# Visualization Functions
# ─────────────────────────────────────────────────────────────
def draw_corner_brackets(frame, x1, y1, x2, y2, color, thickness=2, corner_len=20):
    """Draw corner brackets instead of full rectangle"""
    cv2.line(frame, (x1, y1), (x1 + corner_len, y1), color, thickness)
    cv2.line(frame, (x1, y1), (x1, y1 + corner_len), color, thickness)
    cv2.line(frame, (x2, y1), (x2 - corner_len, y1), color, thickness)
    cv2.line(frame, (x2, y1), (x2, y1 + corner_len), color, thickness)
    cv2.line(frame, (x1, y2), (x1 + corner_len, y2), color, thickness)
    cv2.line(frame, (x1, y2), (x1, y2 - corner_len), color, thickness)
    cv2.line(frame, (x2, y2), (x2 - corner_len, y2), color, thickness)
    cv2.line(frame, (x2, y2), (x2, y2 - corner_len), color, thickness)

def draw_status_panel(frame, x, y, has_helmet, has_vest, is_fall, is_danger_zone):
    """Draw vertical status panel with PNG icons"""
    panel_x = x - 35
    panel_y = y + 5
    spacing = ICON_SIZE + 4
    overlay_icon(frame, ICON_HELMET_OK if has_helmet else ICON_HELMET_NO, panel_x, panel_y)
    overlay_icon(frame, ICON_VEST_OK if has_vest else ICON_VEST_NO, panel_x, panel_y + spacing)

def get_person_bbox_from_keypoints(keypoints):
    """Calculate bounding box from pose keypoints"""
    valid_points = [(kp[0], kp[1]) for kp in keypoints if len(kp) >= 2 and kp[0] > 0 and kp[1] > 0]
    if len(valid_points) < 3:
        return None
    xs = [p[0] for p in valid_points]
    ys = [p[1] for p in valid_points]
    return (int(min(xs) - 30), int(min(ys) - 20), int(max(xs) + 30), int(max(ys) + 20))

# ─────────────────────────────────────────────────────────────
# Danger Zone Functions
# ─────────────────────────────────────────────────────────────
def get_hip_center(keypoints):
    """Calculate hip center from pose keypoints"""
    try:
        left_hip = keypoints[KP_LEFT_HIP]
        right_hip = keypoints[KP_RIGHT_HIP]
        if left_hip[0] > 0 and left_hip[1] > 0 and right_hip[0] > 0 and right_hip[1] > 0:
            return ((left_hip[0] + right_hip[0]) / 2, (left_hip[1] + right_hip[1]) / 2)
        if left_hip[0] > 0 and left_hip[1] > 0:
            return (left_hip[0], left_hip[1])
        if right_hip[0] > 0 and right_hip[1] > 0:
            return (right_hip[0], right_hip[1])
    except (IndexError, TypeError):
        pass
    return None

def point_in_polygon(point, polygon):
    """Ray casting algorithm to check if point is inside polygon"""
    x, y = point
    n = len(polygon)
    inside = False
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def check_danger_zone(hip_center, danger_zones, frame_width=640, frame_height=480):
    """Check if hip center is inside any danger zone"""
    if hip_center is None or not danger_zones:
        return None
    for zone in danger_zones:
        points = zone.get("points", [])
        if len(points) >= 3:
            scaled_points = [[p[0] * frame_width, p[1] * frame_height] for p in points]
            if point_in_polygon(hip_center, scaled_points):
                return zone.get("zone_name", "Danger Zone")
    return None

def draw_danger_zones_overlay(frame, zones):
    """Draw semi-transparent danger zone polygons"""
    if not zones:
        return
    frame_h, frame_w = frame.shape[:2]
    overlay = frame.copy()
    for zone in zones:
        pts = zone.get("points", [])
        if len(pts) >= 3:
            scaled_pts = [[int(p[0] * frame_w), int(p[1] * frame_h)] for p in pts]
            pts_array = np.array(scaled_pts, dtype=np.int32)
            cv2.fillPoly(overlay, [pts_array], (0, 0, 180))
            cv2.polylines(frame, [pts_array], True, (0, 0, 255), 2)
            if len(scaled_pts) > 0:
                cv2.putText(frame, zone.get("zone_name", "Zone"), 
                           (scaled_pts[0][0], scaled_pts[0][1] - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
