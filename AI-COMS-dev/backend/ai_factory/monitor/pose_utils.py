import cv2
import numpy as np

SKELETON_CONNECTIONS = [
    (0, 1), (0, 2),         # Nose to Eyes
    (1, 3), (2, 4),         # Eyes to Ears
    (5, 6),                 # Shoulders
    (5, 7), (7, 9),         # Left Arm
    (6, 8), (8, 10),        # Right Arm
    (5, 11), (6, 12),       # Shoulder to Hip
    (11, 12),               # Hips
    (11, 13), (13, 15),     # Left Leg
    (12, 14), (14, 16)      # Right Leg
]


def get_pose_center(keypoints):
    """Returns midpoint between left hip (11) and right hip (12)."""
    if len(keypoints) < 13:
        return None
    lh, rh = keypoints[11], keypoints[12]
    if len(lh) >= 2 and len(rh) >= 2:
        if lh[0] > 0 and rh[0] > 0:
            cx = int((lh[0] + rh[0]) / 2)
            cy = int((lh[1] + rh[1]) / 2)
            return [cx, cy]
    return None


def point_in_polygon(point, polygon):
    """Returns True if point is inside polygon (ray casting)"""
    x, y = point
    inside = False
    n = len(polygon)
    px1, py1 = polygon[0]
    for i in range(n + 1):
        px2, py2 = polygon[i % n]
        if y > min(py1, py2):
            if y <= max(py1, py2):
                if x <= max(px1, px2):
                    if py1 != py2:
                        xinters = (y - py1) * (px2 - px1) / (py2 - py1 + 1e-6) + px1
                        if px1 == px2 or x <= xinters:
                            inside = not inside
        px1, py1 = px2, py2
    return inside


def draw_poses(frame, poses, color=(255, 255, 102), min_connections=3, danger_zones=None):
    """
    Minimal pose drawing - only skeleton lines (no boxes, unified visualization handles that)
    """
    alerts = []

    for person in poses:
        keypoints = person.get("keypoints", [])

        # Draw skeleton connections only (no keypoint dots for cleaner look)
        valid_lines = []
        for i, j in SKELETON_CONNECTIONS:
            if i < len(keypoints) and j < len(keypoints):
                kpt1 = keypoints[i]
                kpt2 = keypoints[j]

                if len(kpt1) == 3:
                    x1, y1, v1 = kpt1
                elif len(kpt1) == 2:
                    x1, y1 = kpt1
                    v1 = 1.0
                else:
                    continue

                if len(kpt2) == 3:
                    x2, y2, v2 = kpt2
                elif len(kpt2) == 2:
                    x2, y2 = kpt2
                    v2 = 1.0
                else:
                    continue

                if (
                    v1 > 0.2 and v2 > 0.2 and
                    x1 > 0 and y1 > 0 and
                    x2 > 0 and y2 > 0 and
                    abs(x1 - x2) < 300 and abs(y1 - y2) < 300
                ):
                    pt1 = (int(x1), int(y1))
                    pt2 = (int(x2), int(y2))
                    valid_lines.append((pt1, pt2))

        if len(valid_lines) >= min_connections:
            for pt1, pt2 in valid_lines:
                cv2.line(frame, pt1, pt2, color, 1)

        # Check danger zones (for alerts, but don't draw - unified visualization handles it)
        if danger_zones:
            center = get_pose_center(keypoints)
            if center:
                for polygon in danger_zones:
                    if point_in_polygon(center, polygon):
                        alerts.append({"center": center, "zone": polygon})
                        break

    return frame, alerts
