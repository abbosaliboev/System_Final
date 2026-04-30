# AI-COMS — Final Benchmark Table

**Hardware:** NVIDIA TITAN RTX 24GB · Intel i9-10900X · 64GB RAM · CUDA 12.1 · TensorRT 10.x
**Date:** 2026-04-30

---

## 1. Model Configuration Overview

| Config | PPE Model | PPE Size | PPE Format | Pose Model | Pose Format | Keypoints | Frame Diff |
|--------|-----------|:--------:|:----------:|------------|:-----------:|:---------:|:----------:|
| **A** | `best_detect.engine` | 42 MB | TRT FP16 | `best_pose.engine` | TRT FP16 | 17 | ✗ |
| **B** | `best_detect.engine` | 42 MB | TRT FP16 | `yolo11n-10kp.pt` | PyTorch | 10 | ✗ |
| **C** | `unify-29march.engine` | 7.9 MB | TRT FP16 | `yolo11n-10kp.pt` | PyTorch | 10 | ✗ |
| **D** | `unify-29march.engine` | 7.9 MB | TRT FP16 | `yolo11n-10kp.pt` | PyTorch | 10 | ✓ |
| **E** | `unify-29march.engine` | 7.9 MB | TRT FP16 | `yolo11n-10kp.engine` | TRT FP16 | 10 | ✗ |

---

## 2. Model Speed Benchmark — Dummy Frame

**Source:** 640×640 black frame · 200 iterations · single-thread · no RTSP overhead

| Config | PPE ms | Pose ms | Total ms | Model FPS | vs A |
|--------|-------:|--------:|---------:|----------:|-----:|
| A | 6.4 | 5.0 | **11.4** | **87.9** | — |
| B | 6.7 | 9.2 | **15.8** | **63.2** | −24.7 |
| C | 4.9 | 9.5 | **14.5** | **69.1** | −18.8 |
| D | — | — | — | **invalid*** | — |
| **E** | **5.0** | **4.8** | **9.8** | **102.4** | **+14.5** |

> \* Config D: 199/200 frames skipped (dummy = no motion) → 1 frame only → statistically invalid.

---

## 3. Model Speed Benchmark — Real Video

**Source:** `test2.mp4` · 200 iterations · single-thread

| Config | PPE ms | Pose ms | Total ms | Model FPS | vs A | FD Skipped |
|--------|-------:|--------:|---------:|----------:|-----:|-----------:|
| A | 7.0 | 5.1 | **12.1** | **82.8** | — | — |
| B | 7.0 | 7.7 | **14.7** | **68.0** | −14.8 | — |
| C | 6.1 | 9.1 | **15.2** | **65.8** | −17.0 | — |
| D | 6.2 | 8.2 | **14.5** | **69.2** | −13.6 | 120/200 (60%) |
| **E** | **5.4** | **5.1** | **10.5** | **95.0** | **+12.2** | — |

> Config D with real video: 60% static scenes skipped → faster than C. But live RTSP has much less static content.

---

## 4. End-to-End Stream FPS — Real RTSP

**Source:** 4 real RTSP cameras · `[INF 60s]` log · 2nd stable window · `state_manager.py`

| Config | cam1 | cam2 | cam3 | cam4 | Total FPS | Per-cam avg | vs A |
|--------|-----:|-----:|-----:|-----:|----------:|------------:|-----:|
| A | 8.60 | 8.31 | 8.23 | 7.88 | **33.03** | 8.26 | — |
| B | 8.56 | 8.21 | 8.22 | 7.80 | **32.79** | 8.20 | −0.7% |
| C | 8.81 | 8.40 | 8.09 | 7.79 | **33.09** | 8.27 | +0.2% |
| D | 6.30 | 6.30 | 5.65 | 5.60 | **23.84** | 5.96 | −27.8% |
| **E** | **8.76** | **8.71** | **8.44** | **8.42** | **34.33** | **8.58** | **+3.9%** |

---

## 5. Fall Detection Accuracy — 10kp vs 17kp

**Dataset:** UPFall (Subject1) · 5 fall types + walking, sitting, bending, jumping
**Model:** TCN-Attention · 30-frame sequence input · 2-class output (fall / no_fall)
**Evaluation:** `evaluate_yolo10kp.py` · `evaluate_full_kp.py`

| Metric | 10kp Model | 17kp Model | Winner |
|--------|:----------:|:----------:|:------:|
| Overall Accuracy | **99.21%** | 99.10% | **10kp** |
| Normal — Precision | **1.000** | 1.000 | = |
| Normal — Recall | 0.985 | 0.990 | 17kp |
| Normal — F1 | **0.992** | 0.990 | **10kp** |
| Fall — Precision | **0.984** | 0.950 | **10kp** |
| Fall — Recall | **1.000** | 0.980 | **10kp** |
| Fall — F1 | **0.992** | 0.970 | **10kp** |
| Test samples | 2,163 | 7,591 | — |
| Pose model FPS (TRT) | **209** | 200 | **10kp** |

> **Fall Recall = 1.000** (10kp): zero missed falls. Critical for safety systems.

---

## 6. Complete Summary — All Metrics Side by Side

| Config | PPE ms* | Pose ms* | Total ms* | Model FPS* | Stream FPS | Fall F1 | Fall Recall |
|--------|--------:|---------:|----------:|-----------:|-----------:|--------:|------------:|
| A | 7.0 | 5.1 | 12.1 | 82.8 | 33.03 | 0.970** | 0.980** |
| B | 7.0 | 7.7 | 14.7 | 68.0 | 32.79 | **0.992** | **1.000** |
| C | 6.1 | 9.1 | 15.2 | 65.8 | 33.09 | **0.992** | **1.000** |
| D | 6.2 | 8.2 | 14.5 | 69.2 | 23.84 | **0.992** | **1.000** |
| **E** | **5.4** | **5.1** | **10.5** | **95.0** | **34.33** | **0.992** | **1.000** |

> \* Real video benchmark (test2.mp4)
> \*\* 17kp accuracy — measured with correct keypoint remapping (bug fixed)

---

## 7. Key Findings

### Finding 1 — TensorRT Format > Keypoint Count

| Pose model | Format | Pose ms (real video) |
|------------|:------:|---------------------:|
| best_pose.engine (17kp) | TRT FP16 | 5.1 ms |
| yolo11n-10kp.pt (10kp) | PyTorch | 7.7–9.1 ms |
| **yolo11n-10kp.engine (10kp)** | **TRT FP16** | **5.1 ms** |

> 17kp TRT ≈ 10kp TRT in speed. 10kp PT is ~1.7× slower despite fewer keypoints.

### Finding 2 — Stream FPS Is Network-Bounded, Not GPU-Bounded

| Factor | Effect |
|--------|--------|
| 33 FPS hard cap in `streaming_manager.py` | GPU cannot exceed ~33 FPS regardless of speed |
| Alternating inference (pose every 2nd frame) | Not every frame hits GPU |
| RTSP camera rate ~8–9 FPS per cam | GPU waits for frames |

> Config E: model FPS +14.7% → stream FPS only +3.9%. GPU is not the bottleneck.

### Finding 3 — Frame Differencing Hurts Live RTSP

| Source | FD Skip % | Result vs C |
|--------|----------:|------------:|
| Dummy black frame | 99.5% | invalid (1 frame) |
| Real video (test2.mp4) | 60% | +3.4 FPS (better) |
| **Real RTSP cameras** | **~10%** | **−9.25 FPS (−27.8%)** |

> Frame differencing only helps when scenes are mostly static. Industrial safety cameras always have motion → adds CPU overhead with minimal skipping.

### Finding 4 — 10kp Is Better for Fall Detection

| | 10kp | 17kp |
|--|:----:|:----:|
| Trained on | UPFall custom 10kp dataset | COCO-style 17kp |
| Relevant keypoints | All 10 used for fall | 17 includes eyes, ears, knees, ankles (noise) |
| Fall F1 | **0.992** | 0.970 |
| Fall Recall | **1.000** | 0.980 |
| Pose FPS (TRT) | **209** | 200 |

### Finding 5 — Bug Fixed: 17kp Keypoint Mapping

```
BEFORE (wrong):  keypoints_xy[:10]
→ extracts: nose, left_eye, right_eye, left_ear, right_ear, ...
→ TCN receives face keypoints instead of body keypoints

AFTER (correct): explicit COCO→custom10kp remap
→ nose, l_shoulder, r_shoulder, l_elbow, r_elbow,
   l_wrist, r_wrist, l_hip, r_hip, neck(midpoint)
```

---

## 8. Final Recommendation

**Config E** — optimal for real-time industrial safety monitoring:

| | Value |
|--|------:|
| PPE model | `unify-29march.engine` (TRT FP16, 7.9 MB) |
| Pose model | `yolo11n-10kp.engine` (TRT FP16, ~7 MB) |
| Model FPS | **95.0 FPS** (real video) / **102.4 FPS** (dummy) |
| Stream FPS (4 cam) | **34.33 FPS** |
| Fall Accuracy | **99.21%** |
| Fall Recall | **1.000** (zero missed falls) |
