# AI-COMS — Full Model Comparison Table

**Hardware:** NVIDIA TITAN RTX 24GB · CUDA 12.1 · TensorRT 10.x
**Benchmark:** real video (test2.mp4), 200 iterations, single inference (no alternating)

---

## PPE Detection Models

| Model | Format | Size | Inference ms | FPS | Task | Notes |
|-------|:------:|-----:|-------------:|----:|------|-------|
| `best_detect.engine` | TRT FP16 | **41.5 MB** | 6.4–7.0 ms | 143–157 | detect | Old model, large |
| `best_detect.pt` | PyTorch | 4.2 MB | ~12–15 ms | ~70 | detect | PT version of above |
| `unify-29march.engine` | TRT FP16 | **7.8 MB** | 4.9–6.1 ms | 164–204 | detect | Unified, pose-aware backbone |
| `unify-29march.pt` | PyTorch | 5.2 MB | ~9.6 ms | ~56–70 | detect | PT version of above |

> `unify-29march.engine` — **5× kichik**, 10–15% tezroq `best_detect.engine` dan.
> PT format TRT dan ~1.5–2× sekin, lekin GPU bo'lmagan holda fallback sifatida ishlatiladi.

---

## Pose Estimation Models

| Model | Format | Size | Keypoints | Inference ms | FPS | Training data | Notes |
|-------|:------:|-----:|:---------:|-------------:|----:|---------------|-------|
| `best_pose.engine` | TRT FP16 | **8.9 MB** | 17 | 5.0–5.1 ms | 197–200 | COCO standard | Old TRT model |
| `best_pose.pt` | PyTorch | 5.2 MB | 17 | ~10–12 ms | ~85 | COCO standard | PT version |
| `yolo11n-pose.pt` | PyTorch | 6.0 MB | 17 | ~10–12 ms | ~85 | COCO standard | Standard YOLO11n pose |
| `yolo11n-10kp.pt` | PyTorch | **5.1 MB** | 10 | 7.7–9.5 ms | 105–130 | UPFall custom | Fall detection optimized |
| `yolo11n-10kp.engine` | TRT FP16 | **7.7 MB** | 10 | 4.8–5.1 ms | 195–209 | UPFall custom | **Current default** |

> `yolo11n-10kp.engine` — same speed as `best_pose.engine` (17kp TRT), but only 10kp → better for fall detection.
> `.pt` → `.engine` export: **~1.7–2× speedup** (9.2 ms → 4.8 ms).

---

## Fall Detection Model

| Model | Format | Size | Input | Architecture | Accuracy | Fall Recall |
|-------|:------:|-----:|-------|--------------|:--------:|:-----------:|
| `fall_detection_v4.pth` | PyTorch | 1.5 MB | 30 frames × 10kp | TCN-Attention | **99.21%** | **1.000** |
| `fall_detection_full_kp.pth` | PyTorch | — | 30 frames × 17kp | TCN-Attention | 99.10% | 0.980 |

---

## Format Comparison: TRT FP16 vs PyTorch

| Format | Pose ms (10kp) | Pose FPS | PPE ms (unify) | PPE FPS |
|--------|---------------:|---------:|---------------:|--------:|
| PyTorch (.pt) | 7.7–9.5 ms | 105–130 | 9.6 ms | ~56–70 |
| **TensorRT FP16 (.engine)** | **4.8–5.1 ms** | **195–209** | **4.9–6.1 ms** | **164–204** |
| **Speedup** | **~1.7–2×** | | **~1.5–1.7×** | |

---

## All Models — Size & Speed Overview

| Model | Size | Format | ms | FPS | Role |
|-------|-----:|:------:|---:|----:|------|
| `unify-29march.engine` | **7.8 MB** | TRT | 4.9–6.1 | 164–204 | PPE ✓ active |
| `unify-29march.pt` | 5.2 MB | PT | ~9.6 | ~70 | PPE fallback |
| `best_detect.engine` | 41.5 MB | TRT | 6.4–7.0 | 143–157 | PPE old fallback |
| `best_detect.pt` | 4.2 MB | PT | ~13 | ~77 | PPE old fallback |
| `yolo11n-10kp.engine` | **7.7 MB** | TRT | 4.8–5.1 | 195–209 | Pose ✓ active |
| `yolo11n-10kp.pt` | 5.1 MB | PT | 7.7–9.5 | 105–130 | Pose fallback |
| `best_pose.engine` | 8.9 MB | TRT | 5.0–5.1 | 197–200 | Pose old (17kp) |
| `best_pose.pt` | 5.2 MB | PT | ~11 | ~90 | Pose old fallback |
| `yolo11n-pose.pt` | 6.0 MB | PT | ~11 | ~90 | Pose old (17kp) |
| `fall_detection_v4.pth` | 1.5 MB | PT | — | — | Fall ✓ active |
| `fire.engine` | 47.7 MB | TRT | — | — | Fire detection |
| `ppe.engine` | 52.6 MB | TRT | — | — | Old PPE (unused) |
| `fd_best.pt` | 3.2 MB | PT | — | — | Old fall model |

---

## Current Active Pipeline (Config E)

```
unify-29march.engine  (7.8 MB, TRT FP16)  →  PPE:  4.9–6.1 ms
yolo11n-10kp.engine   (7.7 MB, TRT FP16)  →  Pose: 4.8–5.1 ms
fall_detection_v4.pth (1.5 MB, PyTorch)   →  Fall: 99.21% acc
─────────────────────────────────────────────────────────────
Combined model size:  ~17 MB  (vs old: best_detect + best_pose = 50+ MB)
Combined inference:   ~10.5 ms/frame  →  95 FPS (real video)
Stream FPS (4 cam):   34.33 FPS
```
