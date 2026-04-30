"""
Pose Configuration Benchmark — 4 config comparison
Measures: PPE ms, Pose ms, Total ms, Model FPS (single-thread, no stream overhead)

Configs:
  A: best_detect.engine  + best_pose.engine  (17kp)
  B: best_detect.engine  + yolo11n-10kp.pt   (10kp)
  C: unify-29march.engine + yolo11n-10kp.pt  (10kp, shared backbone)
  D: unify-29march.engine + yolo11n-10kp.pt  (10kp) + frame differencing

Run from backend/ai_factory/:
    python -m monitor.YOLO.benchmark_pose_configs
    python -m monitor.YOLO.benchmark_pose_configs --video monitor/videos/test.mp4
    python -m monitor.YOLO.benchmark_pose_configs --frames 300
"""
import time
import argparse
import numpy as np
import cv2
import torch
from ultralytics import YOLO

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from monitor.frame_differencing import frame_differencing

# ─────────────────────────────────────────────────────────────
CONFIGS = [
    {
        "label":      "1: best_detect.engine + Pose 17kp TRT (best_pose.engine)",
        "ppe_paths":  ["monitor/YOLO/models/best_detect.engine"],
        "pose_paths": ["monitor/YOLO/models/best_pose.engine"],
        "frame_diff": False,
        "kp_count":   17,
    },
    {
        "label":      "2: best_detect.engine + Pose 10kp TRT (yolo11n-10kp.engine)",
        "ppe_paths":  ["monitor/YOLO/models/best_detect.engine"],
        "pose_paths": ["monitor/YOLO/models/yolo11n-10kp.engine"],
        "frame_diff": False,
        "kp_count":   10,
    },
    {
        "label":      "3: unify-29march.engine + Pose 10kp TRT (yolo11n-10kp.engine)",
        "ppe_paths":  ["monitor/YOLO/models/unify-29march.engine"],
        "pose_paths": ["monitor/YOLO/models/yolo11n-10kp.engine"],
        "frame_diff": False,
        "kp_count":   10,
    },
    {
        "label":      "4: unify-29march.engine + Pose 10kp TRT + Frame Differencing",
        "ppe_paths":  ["monitor/YOLO/models/unify-29march.engine"],
        "pose_paths": ["monitor/YOLO/models/yolo11n-10kp.engine"],
        "frame_diff": True,
        "kp_count":   10,
    },
    {
        "label":      "E: unify-29march.engine + Pose 10kp (yolo11n-10kp.engine TRT)",
        "ppe_paths":  ["monitor/YOLO/models/unify-29march.engine",
                       "monitor/YOLO/models/unify-29march.pt"],
        "pose_paths": ["monitor/YOLO/models/yolo11n-10kp.engine"],
        "frame_diff": False,
        "kp_count":   10,
    },
]

WARMUP_FRAMES  = 10
MEASURE_FRAMES = 200
IMG_SIZE       = 640
PPE_CONF       = 0.30
POSE_CONF      = 0.25
# ─────────────────────────────────────────────────────────────


def load_first(paths, task):
    """Try paths in order, return first that loads."""
    for p in paths:
        try:
            m = YOLO(p, task=task)
            print(f"    Loaded: {p}")
            return m, p
        except Exception as e:
            print(f"    Failed {p}: {e}")
    return None, None


def bench_config(cfg, source, n_frames):
    print(f"\n{'─'*60}")
    print(f"  Config: {cfg['label']}")
    print(f"{'─'*60}")

    ppe_model, ppe_path = load_first(cfg["ppe_paths"], "detect")
    if ppe_model is None:
        print("  ✗ PPE model could not be loaded. Skipping.")
        return None

    pose_model, pose_path = load_first(cfg["pose_paths"], "pose")
    if pose_model is None:
        print("  ✗ Pose model could not be loaded. Skipping.")
        return None

    use_frame_diff = cfg["frame_diff"]

    # Build frame list
    if isinstance(source, np.ndarray):
        all_frames = [source] * (n_frames + WARMUP_FRAMES)
        use_cap = False
        cap = None
    else:
        cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            print(f"  ✗ Cannot open source: {source}")
            return None
        use_cap = True
        all_frames = None

    def get_frame(idx):
        if not use_cap:
            return True, all_frames[idx].copy()
        ret, f = cap.read()
        return ret, f

    # Warmup
    print(f"  Warming up ({WARMUP_FRAMES} frames)...", end="", flush=True)
    for i in range(WARMUP_FRAMES):
        ok, f = get_frame(i)
        if not ok:
            break
        ppe_model.predict(source=f, imgsz=IMG_SIZE, conf=PPE_CONF, verbose=False)
        pose_model.predict(source=f, imgsz=IMG_SIZE, conf=POSE_CONF, verbose=False)
    print(" done")

    # Measure
    ppe_times, pose_times, total_times = [], [], []
    fd_skipped = 0
    prev_frame = None

    print(f"  Measuring ({n_frames} frames)...", end="", flush=True)
    for i in range(n_frames):
        ok, frame = get_frame(i + WARMUP_FRAMES)
        if not ok:
            break

        # Frame differencing check
        if use_frame_diff and prev_frame is not None:
            has_motion = frame_differencing("bench", frame, prev_frame)
            if not has_motion:
                fd_skipped += 1
                prev_frame = frame
                continue  # skip inference this frame

        prev_frame = frame

        t0 = time.perf_counter()
        ppe_model.predict(source=frame, imgsz=IMG_SIZE, conf=PPE_CONF, verbose=False)
        t1 = time.perf_counter()
        pose_model.predict(source=frame, imgsz=IMG_SIZE, conf=POSE_CONF, verbose=False)
        t2 = time.perf_counter()

        ppe_times.append((t1 - t0) * 1000)
        pose_times.append((t2 - t1) * 1000)
        total_times.append((t2 - t0) * 1000)

    if cap:
        cap.release()

    print(" done")

    if not ppe_times:
        print("  ✗ No frames measured.")
        return None

    def stats(arr):
        a = np.array(arr)
        return {
            "mean": float(np.mean(a)),
            "min":  float(np.min(a)),
            "max":  float(np.max(a)),
            "p95":  float(np.percentile(a, 95)),
            "fps":  1000.0 / float(np.mean(a)),
        }

    return {
        "label":      cfg["label"],
        "kp_count":   cfg["kp_count"],
        "frame_diff": use_frame_diff,
        "ppe_path":   ppe_path,
        "pose_path":  pose_path,
        "frames":     len(ppe_times),
        "fd_skipped": fd_skipped,
        "ppe":        stats(ppe_times),
        "pose":       stats(pose_times),
        "total":      stats(total_times),
    }


def print_result(r):
    if r is None:
        return
    fd_note = f"  (frame_diff: {r['fd_skipped']} frames skipped)" if r["frame_diff"] else ""
    print(f"\n  ┌── {r['label']}")
    print(f"  │  Keypoints : {r['kp_count']}kp")
    print(f"  │  PPE model : {r['ppe_path']}")
    print(f"  │  Pose model: {r['pose_path']}")
    if r["frame_diff"]:
        total_f = r["frames"] + r["fd_skipped"]
        skip_pct = r["fd_skipped"] / total_f * 100 if total_f else 0
        print(f"  │  Frame diff: {r['fd_skipped']}/{total_f} skipped ({skip_pct:.1f}%)")
    print(f"  │")
    print(f"  │  PPE  inference: {r['ppe']['mean']:6.1f} ms avg  "
          f"(p95 {r['ppe']['p95']:.1f} ms)  → {r['ppe']['fps']:.1f} FPS")
    print(f"  │  Pose inference: {r['pose']['mean']:6.1f} ms avg  "
          f"(p95 {r['pose']['p95']:.1f} ms)  → {r['pose']['fps']:.1f} FPS")
    print(f"  │  TOTAL/frame  : {r['total']['mean']:6.1f} ms avg  "
          f"(p95 {r['total']['p95']:.1f} ms)  → {r['total']['fps']:.1f} FPS")
    print(f"  └── frames measured: {r['frames']}{fd_note}")


def print_summary(results):
    valid = [r for r in results if r is not None]
    if not valid:
        return

    print(f"\n{'='*70}")
    print("  SUMMARY TABLE")
    print(f"{'='*70}")
    print(f"  {'Config':<45} {'PPE ms':>7} {'Pose ms':>8} {'Total ms':>9} {'FPS':>7}")
    print(f"  {'-'*45} {'-'*7} {'-'*8} {'-'*9} {'-'*7}")
    for r in valid:
        fd = " +FD" if r["frame_diff"] else ""
        label = r["label"].split(":")[0] + fd
        print(f"  {label:<45} {r['ppe']['mean']:>7.1f} {r['pose']['mean']:>8.1f} "
              f"{r['total']['mean']:>9.1f} {r['total']['fps']:>7.1f}")
    print(f"{'='*70}")

    # vs baseline (Config A)
    baseline = valid[0]
    if len(valid) > 1:
        print(f"\n  vs {baseline['label'].split(':')[0]} (baseline):")
        for r in valid[1:]:
            diff_ms  = r["total"]["mean"] - baseline["total"]["mean"]
            diff_fps = r["total"]["fps"]  - baseline["total"]["fps"]
            print(f"    {r['label'].split(':')[0]}: {diff_ms:+.1f} ms  {diff_fps:+.1f} FPS")
    print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video",  type=str, default=None)
    parser.add_argument("--rtsp",   type=str, default=None)
    parser.add_argument("--frames", type=int, default=MEASURE_FRAMES)
    args = parser.parse_args()

    if args.rtsp:
        source = args.rtsp
        src_label = f"RTSP: {args.rtsp}"
    elif args.video:
        source = args.video
        src_label = f"Video: {args.video}"
    else:
        source = np.zeros((640, 640, 3), dtype=np.uint8)
        src_label = "Dummy 640×640 black frame"

    print(f"\n{'='*70}")
    print(f"  AI-COMS Pose Config Benchmark")
    print(f"  Source : {src_label}")
    print(f"  Frames : {args.frames}")
    print(f"  Device : {'CUDA ' + torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
    print(f"{'='*70}")

    results = []
    for cfg in CONFIGS:
        r = bench_config(cfg, source, args.frames)
        results.append(r)
        print_result(r)

        # Free GPU memory between configs
        torch.cuda.empty_cache()

    print_summary(results)


if __name__ == "__main__":
    main()
