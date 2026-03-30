"""
Model Speed Benchmark — PPE detection model comparison
Run from backend/ai_factory/:

    python -m monitor.YOLO.benchmark_models
    python -m monitor.YOLO.benchmark_models --rtsp rtsp://admin:pass@192.168.x.x/stream1
    python -m monitor.YOLO.benchmark_models --video monitor/videos/test1.mp4
"""
import time
import argparse
import numpy as np
import cv2
import torch
from ultralytics import YOLO

# ─────────────────────────────────────────────────────────────
MODELS_TO_TEST = [
    {
        "name":  "unify-29march.engine (TensorRT FP16)",
        "path":  "monitor/YOLO/models/unify-29march.engine",
        "task":  "detect",
    },
    {
        "name":  "best_detect.engine  (TensorRT FP16)",
        "path":  "monitor/YOLO/models/best_detect.engine",
        "task":  "detect",
    },
    {
        "name":  "unify-29march.pt    (PyTorch, baseline)",
        "path":  "monitor/YOLO/models/unify-29march.pt",
        "task":  "detect",
    },
]

POSE_MODEL = {
    "name": "yolo11n-10kp.pt (pose, always loaded)",
    "path": "monitor/YOLO/models/yolo11n-10kp.pt",
    "task": "pose",
}

WARMUP_FRAMES  = 10
MEASURE_FRAMES = 200   # frames per model
IMG_SIZE       = 640
CONF           = 0.30
# ─────────────────────────────────────────────────────────────


def bench_model(model, pose_model, source, n_frames, label):
    """
    Run n_frames of PPE + Pose inference and report timing.
    Returns dict with timing stats.
    """
    ppe_times  = []
    pose_times = []
    total_times = []

    frame_count = 0
    cap = None

    if isinstance(source, np.ndarray):
        # dummy frame repeated
        frames = [source] * (n_frames + WARMUP_FRAMES)
        use_cap = False
    else:
        cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            print(f"  ⚠  Could not open source: {source}")
            return None
        use_cap = True
        frames = None

    def get_frame(idx):
        if not use_cap:
            return True, frames[idx]
        ret, f = cap.read()
        return ret, f

    # Warmup
    print(f"  Warming up ({WARMUP_FRAMES} frames)...", end="", flush=True)
    for i in range(WARMUP_FRAMES):
        ok, f = get_frame(i)
        if not ok:
            break
        model.predict(source=f, imgsz=IMG_SIZE, conf=CONF, verbose=False)
        pose_model.predict(source=f, imgsz=IMG_SIZE, conf=0.25, verbose=False)
    print(" done")

    # Measure
    print(f"  Measuring ({n_frames} frames)...", end="", flush=True)
    for i in range(n_frames):
        ok, f = get_frame(i + WARMUP_FRAMES)
        if not ok:
            break

        t0 = time.perf_counter()
        model.predict(source=f, imgsz=IMG_SIZE, conf=CONF, verbose=False)
        t1 = time.perf_counter()
        pose_model.predict(source=f, imgsz=IMG_SIZE, conf=0.25, verbose=False)
        t2 = time.perf_counter()

        ppe_ms   = (t1 - t0) * 1000
        pose_ms  = (t2 - t1) * 1000
        total_ms = (t2 - t0) * 1000

        ppe_times.append(ppe_ms)
        pose_times.append(pose_ms)
        total_times.append(total_ms)
        frame_count += 1

    if cap:
        cap.release()

    print(" done")

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
        "label":      label,
        "frames":     frame_count,
        "ppe":        stats(ppe_times),
        "pose":       stats(pose_times),
        "total":      stats(total_times),
    }


def print_result(r):
    if r is None:
        return
    print(f"\n  ┌── {r['label']}")
    print(f"  │  PPE  inference: {r['ppe']['mean']:6.1f} ms avg  "
          f"(min {r['ppe']['min']:.1f}  max {r['ppe']['max']:.1f}  p95 {r['ppe']['p95']:.1f}) "
          f"→ {r['ppe']['fps']:.1f} FPS")
    print(f"  │  Pose inference: {r['pose']['mean']:6.1f} ms avg  "
          f"(min {r['pose']['min']:.1f}  max {r['pose']['max']:.1f}  p95 {r['pose']['p95']:.1f}) "
          f"→ {r['pose']['fps']:.1f} FPS")
    print(f"  │  TOTAL/frame   : {r['total']['mean']:6.1f} ms avg  → {r['total']['fps']:.1f} FPS")
    print(f"  └── frames measured: {r['frames']}")


def main():
    parser = argparse.ArgumentParser(description="Model speed benchmark")
    parser.add_argument("--rtsp",  type=str, default=None, help="RTSP URL to use as source")
    parser.add_argument("--video", type=str, default=None, help="Video file path")
    parser.add_argument("--frames", type=int, default=MEASURE_FRAMES)
    args = parser.parse_args()

    # Determine source
    if args.rtsp:
        source = args.rtsp
        src_label = f"RTSP: {args.rtsp}"
    elif args.video:
        source = args.video
        src_label = f"Video: {args.video}"
    else:
        source = np.zeros((640, 640, 3), dtype=np.uint8)
        src_label = "Dummy 640×640 black frame"

    print(f"\n{'='*60}")
    print(f"  AI-COMS Model Benchmark")
    print(f"  Source  : {src_label}")
    print(f"  Frames  : {args.frames}")
    print(f"  Device  : {'CUDA' if torch.cuda.is_available() else 'CPU'}")
    print(f"{'='*60}\n")

    # Load pose model once (shared across all tests)
    print(f"Loading pose model: {POSE_MODEL['path']}")
    pose_model = YOLO(POSE_MODEL["path"], task=POSE_MODEL["task"])

    results = []
    for cfg in MODELS_TO_TEST:
        print(f"\nLoading: {cfg['path']}")
        try:
            model = YOLO(cfg["path"], task=cfg["task"])
        except Exception as e:
            print(f"  ⚠  Failed to load: {e}")
            continue

        r = bench_model(model, pose_model, source, args.frames, cfg["name"])
        results.append(r)
        print_result(r)

        # free GPU memory before next model
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    # ── Summary comparison ─────────────────────────────────────
    if len(results) >= 2 and all(r is not None for r in results):
        print(f"\n{'='*60}")
        print("  COMPARISON SUMMARY")
        print(f"{'='*60}")
        r0, r1 = results[0], results[1]
        diff_ppe   = r0["ppe"]["mean"]   - r1["ppe"]["mean"]
        diff_total = r0["total"]["mean"] - r1["total"]["mean"]
        print(f"  PPE  latency diff : {diff_ppe:+.1f} ms  "
              f"({'unify faster' if diff_ppe < 0 else 'engine faster'})")
        print(f"  Total latency diff: {diff_total:+.1f} ms  "
              f"({'unify faster' if diff_total < 0 else 'engine faster'})")
        print(f"  unify  total FPS  : {r0['total']['fps']:.1f}")
        print(f"  engine total FPS  : {r1['total']['fps']:.1f}")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
