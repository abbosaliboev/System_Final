"""
Streaming Manager - Main camera process for multi-camera inference.
Imports from: helpers.py, inference_utils.py, state_manager.py, visualization.py
~210 lines (down from 750+)
"""
import os
import time
from multiprocessing import current_process
from concurrent.futures import ThreadPoolExecutor  # P2: reusable thread pool
import numpy as np
import torch

# Import from helper modules
from .helpers import get_hip_center, check_danger_zone
from .inference_utils import (
    load_models, ppe_infer, pose_infer,
    fetch_danger_zones, save_danger_zone_alert
)
from .state_manager import CameraStateManager
from .visualization import (
    smooth_ppe_detections, draw_person_visualization,
    compute_status, send_frame_to_queue
)

os.environ.pop("OPENCV_FFMPEG_CAPTURE_OPTIONS", None)


def camera_process(cam_list, camera_results, frame_queues=None):
    """
    Main worker process for multi-camera PPE and fall detection.
    """
    print(f"Starting process: {current_process().name} for cameras: "
          f"{[c['id'] for c in cam_list]}")

    # 1) Initialize state manager
    state = CameraStateManager(cam_list)

    # 2) Load models (PPE + Pose)
    ppe_model, pose_model = load_models()
    print("[Models] PPE and Pose models loaded (TensorRT .engine)")

    # 3) Warm-up
    dummy = np.zeros((512, 512, 3), dtype=np.uint8)
    ppe_names = None
    print("[Warm-up] Warming up models...")
    for i in range(3):
        ppe_r = ppe_model.predict(source=dummy, imgsz=640, conf=0.30, verbose=False)[0]
        pose_model.predict(source=dummy, imgsz=640, conf=0.25, verbose=False)
        if ppe_names is None:
            ppe_names = getattr(ppe_r, 'names', None)
    print("[Warm-up] Models ready for real-time inference")

    # 4) CUDA streams for parallel inference
    detect_stream = torch.cuda.Stream()
    pose_stream = torch.cuda.Stream()

    # 5) Fall Detector
    try:
        from monitor.YOLO.tcn_fall import FallDetector
        fall_detector = FallDetector()
        print("[FallDetector] Loaded successfully")
    except Exception as e:
        print(f"[FallDetector] Failed to load: {e}")
        fall_detector = None

    # 6) Start frame grabber threads
    state.start_frame_grabbers()

    # P2: Single thread pool created once — reused every frame, no per-frame Thread()
    executor = ThreadPoolExecutor(max_workers=2)

    # Parallel inference helpers (closures capture CUDA streams from above)
    def _run_ppe(out_box, model, frame_):
        with torch.cuda.stream(detect_stream):
            out_box["ppe"] = ppe_infer(model, frame_)

    def _run_pose(out_box, model, frame_):
        with torch.cuda.stream(pose_stream):
            out_box["poses"] = pose_infer(model, frame_)

    # P3: Main inference loop — no unconditional sleeps
    while True:
        any_frame = False  # P3: track whether any camera had a frame

        for cam in cam_list:
            cam_id = cam["id"]
            q = state.input_queues.get(cam_id)
            if q is None or q.empty():
                continue  # P3: removed sleep(0.001) here

            try:
                frame = q.get_nowait()
            except Exception:
                continue

            any_frame = True

            # Frame rate control
            now = time.time()
            if now - state.last_frame_time[cam_id] < 0.03:  # ~33 FPS max
                continue
            state.last_frame_time[cam_id] = now
            state.toggle[cam_id] += 1

            # Alternating inference strategy
            run_ppe = (state.toggle[cam_id] % 3 == 0)
            run_pose = (state.toggle[cam_id] % 2 == 0)

            ppe = state.last_ppe[cam_id]
            poses = state.last_pose[cam_id]

            # Run inference
            if run_ppe and run_pose:
                ppe, poses = _run_parallel_inference(
                    ppe_model, pose_model, frame, ppe, poses,
                    _run_ppe, _run_pose, fall_detector, cam_id, state, now,
                    executor  # P2: pass pool
                )
            elif run_ppe:
                ppe = _run_ppe_only(ppe_model, frame, ppe, _run_ppe)
            elif run_pose:
                poses = _run_pose_only(
                    pose_model, frame, poses, _run_pose,
                    fall_detector, cam_id, state, now
                )

            state.last_ppe[cam_id] = ppe
            state.last_pose[cam_id] = poses

            # If no person in frame → reset fall state so status bar returns to Safe
            if not poses:
                state.update_fall_state(cam_id, False, 0.0, now)
                # Clear TCN buffer so stale data doesn't cause false fall when person reappears
                if fall_detector and cam_id in fall_detector.buffer:
                    fall_detector.buffer[cam_id].clear()

            # Danger Zone Detection
            _process_danger_zones(cam_id, poses, frame, state, now)

            # PPE smoothing
            smoothed_ppe = smooth_ppe_detections(ppe, state.ppe_history, cam_id)

            # Draw visualization
            draw_person_visualization(frame, poses, smoothed_ppe, state.danger_zone_cache, cam_id)

            # Compute status (pass poses so status can ignore fall when no person present)
            status_val = compute_status(cam_id, state, smoothed_ppe, poses)

            # Update shared results
            camera_results[cam_id] = {
                "timestamp": now,
                "detections": smoothed_ppe,
                "poses": poses,
                "status": status_val,
            }

            # Send frame to frontend
            send_frame_to_queue(frame, frame_queues, cam_id)
            state.cam_counts[cam_id] += 1
            state.min_counts[cam_id] += 1

        # P3: only yield CPU when all queues are empty (no useful work this iteration)
        if not any_frame:
            time.sleep(0.001)

        state.log_fps()
        state.log_minute_counts()


def _run_parallel_inference(ppe_model, pose_model, frame, ppe, poses,
                            _run_ppe, _run_pose, fall_detector, cam_id, state, now,
                            executor):
    """
    Run PPE and Pose inference concurrently via thread pool.
    P1: No torch.cuda.synchronize() — YOLO handles sync internally.
    P2: executor.submit() reuses existing threads instead of creating new ones.
    """
    ppe_box, pose_box = {}, {}
    f_ppe = executor.submit(_run_ppe, ppe_box, ppe_model, frame)
    f_pose = executor.submit(_run_pose, pose_box, pose_model, frame)
    f_ppe.result()   # wait for PPE to finish
    f_pose.result()  # wait for Pose to finish
    # P1: torch.cuda.synchronize() removed — was blocking 1-10ms per frame

    ppe = ppe_box.get("ppe", ppe)
    poses = pose_box.get("poses", poses)

    # Fall detection
    _process_fall_detection(fall_detector, poses, cam_id, state, now)

    return ppe, poses


def _run_ppe_only(ppe_model, frame, ppe, _run_ppe):
    """
    Run only PPE inference.
    P2: called directly — no thread overhead for single inference.
    P1: torch.cuda.synchronize() removed.
    """
    ppe_box = {}
    _run_ppe(ppe_box, ppe_model, frame)
    return ppe_box.get("ppe", ppe)


def _run_pose_only(pose_model, frame, poses, _run_pose, fall_detector, cam_id, state, now):
    """
    Run only Pose inference.
    P2: called directly — no thread overhead for single inference.
    P1: torch.cuda.synchronize() removed.
    """
    pose_box = {}
    _run_pose(pose_box, pose_model, frame)
    poses = pose_box.get("poses", poses)

    # Fall detection
    _process_fall_detection(fall_detector, poses, cam_id, state, now)

    return poses


def _process_fall_detection(fall_detector, poses, cam_id, state, now):
    """Process fall detection for all poses (supports 10 or 17 keypoints)."""
    if not fall_detector or not poses:
        return

    for pose in poses:
        kps = np.array(pose["keypoints"])

        # Get confidence scores from pose data
        confs = pose.get("conf")
        if confs is not None:
            confs = np.array(confs)
        else:
            # Fallback: assume all keypoints have confidence 1.0
            confs = np.ones(len(kps))

        # Skip low-confidence detections (dark room noise, partial artifacts)
        # Average keypoint confidence < 0.15 → not a real person
        if confs.mean() < 0.15:
            continue

        label, conf, draw_info = fall_detector.predict(cam_id, kps, confs)

        is_fall = (label == "fall")
        should_show = state.update_fall_state(cam_id, is_fall, conf, now)

        if should_show and draw_info:
            pose["fall"] = draw_info


def _process_danger_zones(cam_id, poses, frame, state, now):
    """Process danger zone detection for all poses."""
    if not poses:
        return

    # Refresh danger zones periodically
    if now - state.danger_zone_last_fetch[cam_id] > state.DANGER_ZONE_REFRESH_INTERVAL:
        state.danger_zone_cache[cam_id] = fetch_danger_zones(cam_id)
        state.danger_zone_last_fetch[cam_id] = now
        print(f"[DangerZone] Fetched {len(state.danger_zone_cache[cam_id])} zones for {cam_id}")

    zones = state.danger_zone_cache[cam_id]
    if not zones:
        return

    frame_h, frame_w = frame.shape[:2]

    for idx, pose in enumerate(poses):
        kps = pose.get("keypoints", [])
        if len(kps) < 13:
            continue

        hip_center = get_hip_center(kps)
        if not hip_center:
            continue

        zone_name = check_danger_zone(hip_center, zones, frame_w, frame_h)
        person_key = f"person_{idx}"

        if zone_name:
            # Person is in danger zone
            if person_key not in state.danger_zone_start_time[cam_id]:
                state.danger_zone_start_time[cam_id][person_key] = now
                print(f"[DangerZone] {cam_id} {person_key} entered zone '{zone_name}'")

            duration_in_zone = now - state.danger_zone_start_time[cam_id][person_key]

            if duration_in_zone >= state.DANGER_ZONE_DURATION_THRESHOLD:
                if not state.danger_zone_alerted[cam_id].get(person_key, False):
                    state.danger_zone_alerted[cam_id][person_key] = True
                    print(f"[DangerZone] ⚠️ ALERT! {cam_id} {person_key} in '{zone_name}'")
                    save_danger_zone_alert(cam_id, zone_name, frame)

                pose["danger_zone"] = {
                    "zone_name": zone_name,
                    "hip_center": hip_center,
                    "duration": duration_in_zone,
                }
        else:
            # Person left danger zone
            if person_key in state.danger_zone_start_time[cam_id]:
                del state.danger_zone_start_time[cam_id][person_key]
            if person_key in state.danger_zone_alerted[cam_id]:
                del state.danger_zone_alerted[cam_id][person_key]
