# import cv2
# import math

# # ======= Motion- Detection by Frame Differencing =======

# # =======================================================

# def frame_differencing(cam_id, frame, previous_frame, params=None):
#     """Setup parameters for frame differencing."""
#     if (previous_frame is None) or (frame is None):
#         print(f"[{cam_id}] Previous frame or current frame is None, cannot perform frame differencing.")
#         return False

#     params = params or {}
#     scale = float(params.get("scale", 1.0))
#     min_contour_area = params.get("min_contour_area", 800)
#     min_total_motion = params.get("min_total_motion", 1500)
#     use_contours = params.get("use_contours", True)
#     min_motion_pixels = params.get("min_motion_pixels", min_total_motion)
#     blur_ksize = params.get("blur_ksize", 5)
#     use_morph = params.get("use_morph", True)

#     object_distance_m = 1.0
#     object_size_factor = 1.0
#     angle_rad = 20.0
#     diff_thresh = params.get(
#         "diff_thresh",
#         10 * object_size_factor * math.cos(angle_rad) / (object_distance_m ** 2.6) + 0.1,
#     )

#     if scale != 1.0:
#         prev_small = cv2.resize(
#             previous_frame,
#             (int(frame.shape[1] * scale), int(frame.shape[0] * scale)),
#             interpolation=cv2.INTER_AREA,
#         )
#         frame_small = cv2.resize(
#             frame,
#             (int(frame.shape[1] * scale), int(frame.shape[0] * scale)),
#             interpolation=cv2.INTER_AREA,
#         )
#     else:
#         prev_small = previous_frame
#         frame_small = frame

#     prev_gray = cv2.cvtColor(prev_small, cv2.COLOR_BGR2GRAY)
#     gray = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)

#     if blur_ksize and blur_ksize > 1:
#         prev_gray = cv2.GaussianBlur(prev_gray, (blur_ksize, blur_ksize), 0)
#         gray = cv2.GaussianBlur(gray, (blur_ksize, blur_ksize), 0)

#     diff = cv2.absdiff(prev_gray, gray)
#     _, th = cv2.threshold(diff, diff_thresh, 255, cv2.THRESH_BINARY)

#     if use_morph:
#         th = cv2.medianBlur(th, 5)
#         th = cv2.dilate(th, None, iterations=2)

#     if use_contours:
#         contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#         total_motion_area = 0.0
#         for c in contours:
#             area = cv2.contourArea(c)
#             if area < min_contour_area * (scale * scale):
#                 continue
#             total_motion_area += area

#         if total_motion_area >= min_total_motion * (scale * scale):
#             return True
#     else:
#         motion_pixels = cv2.countNonZero(th)
#         if motion_pixels >= min_motion_pixels * (scale * scale):
#             return True

#     return False


import cv2
import math
from concurrent.futures import ThreadPoolExecutor

# ======= Motion- Detection by Frame Differencing =======
# =======================================================


def frame_differencing(cam_id, frame, previous_frame, params=None):
    """Setup parameters for frame differencing."""
    if (previous_frame is None) or (frame is None):
        print(f"[{cam_id}] Previous frame or current frame is None, cannot perform frame differencing.")
        return False

    params = params or {}
    scale = float(params.get("scale", 1.0))
    min_contour_area = params.get("min_contour_area", 800)
    min_total_motion = params.get("min_total_motion", 1500)
    use_contours = params.get("use_contours", True)
    min_motion_pixels = params.get("min_motion_pixels", min_total_motion)
    blur_ksize = params.get("blur_ksize", 5)
    use_morph = params.get("use_morph", True)

    object_distance_m = 1.0
    object_size_factor = 1.0
    angle_rad = 20.0
    diff_thresh = params.get(
        "diff_thresh",
        10 * object_size_factor * math.cos(angle_rad) / (object_distance_m ** 2.6) + 0.1,
    )

    if scale != 1.0:
        prev_small = cv2.resize(
            previous_frame,
            (int(frame.shape[1] * scale), int(frame.shape[0] * scale)),
            interpolation=cv2.INTER_AREA,
        )
        frame_small = cv2.resize(
            frame,
            (int(frame.shape[1] * scale), int(frame.shape[0] * scale)),
            interpolation=cv2.INTER_AREA,
        )
    else:
        prev_small = previous_frame
        frame_small = frame

    prev_gray = cv2.cvtColor(prev_small, cv2.COLOR_BGR2GRAY)
    gray = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)

    if blur_ksize and blur_ksize > 1:
        prev_gray = cv2.GaussianBlur(prev_gray, (blur_ksize, blur_ksize), 0)
        gray = cv2.GaussianBlur(gray, (blur_ksize, blur_ksize), 0)

    diff = cv2.absdiff(prev_gray, gray)
    _, th = cv2.threshold(diff, diff_thresh, 255, cv2.THRESH_BINARY)

    if use_morph:
        th = cv2.medianBlur(th, 5)
        th = cv2.dilate(th, None, iterations=2)

     # ===== 16분할 + 멀티스레드 처리 =====
    h, w = th.shape
    rows, cols = 4, 4
    tiles = []

    for r in range(rows):
        for c in range(cols):
            y1 = h * r // rows
            y2 = h * (r + 1) // rows
            x1 = w * c // cols
            x2 = w * (c + 1) // cols
            tiles.append(th[y1:y2, x1:x2])

    scale_factor = scale * scale

    if use_contours:
        min_area_scaled = min_contour_area * scale_factor

        def _process_tile_contour(th_tile):
            contours, _ = cv2.findContours(th_tile, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            total_motion_area = 0.0
            for c in contours:
                area = cv2.contourArea(c)
                if area >= min_area_scaled:
                    total_motion_area += area
            return total_motion_area

        with ThreadPoolExecutor(max_workers=4) as executor:
            total_motion_area = sum(executor.map(_process_tile_contour, tiles))

        if total_motion_area >= min_total_motion * scale_factor:
            return True

    else:
        with ThreadPoolExecutor(max_workers=4) as executor:
            motion_pixels = sum(executor.map(cv2.countNonZero, tiles))

        if motion_pixels >= min_motion_pixels * scale_factor:
            return True