# Presentation: Pose Model Selection Research
# AI-COMS — 10kp vs 17kp Benchmark & Fall Detection Accuracy

---

## Slide 1 — Title

**Title:**
> Pose Estimation Model Selection for Real-Time Fall Detection:
> 10-Keypoint vs 17-Keypoint Comparative Study

**Subtitle:**
> Speed Benchmark · Stream FPS · Fall Detection Accuracy

**Info:**
> Chungbuk National University — Data Analytics Lab
> NVIDIA TITAN RTX · CUDA 12.1 · TensorRT 10.x · 2026

---

## Slide 2 — Starting Point: What We Had

**Title:** Available Models & Research Question

**Available models at the start:**

| Category | Model | Format | Size |
|----------|-------|--------|------|
| PPE Detection | `best_detect.engine` | TensorRT FP16 | 42 MB |
| PPE Detection | `unify-29march.engine` | TensorRT FP16 | 7.9 MB |
| Pose (17kp) | `best_pose.engine` | TensorRT FP16 | 8 MB |
| Pose (10kp) | `yolo11n-10kp.pt` | PyTorch | — |
| Frame Diff | `frame_differencing.py` | CPU function | — |

**Research question:**
> Which PPE + Pose combination gives the best speed and accuracy for fall detection?

**Two metrics needed:**
1. **Model speed** — inference time per frame (GPU only, no RTSP overhead)
2. **End-to-end stream FPS** — real 4 RTSP cameras, 60-second window

---

## Slide 3 — Experimental Design: 4 Configurations

**Title:** 4 Configurations to Compare

| Config | PPE Model | Pose Model | Keypoints | Frame Diff |
|--------|-----------|------------|-----------|:----------:|
| **A** | `best_detect.engine` (42 MB) | `best_pose.engine` | 17 | ✗ |
| **B** | `best_detect.engine` (42 MB) | `yolo11n-10kp.pt` | 10 | ✗ |
| **C** | `unify-29march.engine` (7.9 MB) | `yolo11n-10kp.pt` | 10 | ✗ |
| **D** | `unify-29march.engine` (7.9 MB) | `yolo11n-10kp.pt` | 10 | ✓ |

**What changes between configs:**
- A → B: same PPE, pose model changes (17kp TRT → 10kp PT)
- B → C: same pose, PPE model changes (42MB → 7.9MB)
- C → D: same models, frame differencing added

**Frame differencing:** Skip inference on static frames (no motion detected)
→ Already implemented in `frame_differencing.py`, needed to integrate into streaming pipeline

---

## Slide 4 — Model Speed Benchmark Results

**Title:** Model Speed: Pure GPU Inference (No RTSP Overhead)

**Method:** Dummy 640×640 black frame, 200 iterations, TITAN RTX
**Script:** `benchmark_pose_configs.py` — custom written for this experiment

**Results:**

| Config | PPE ms | Pose ms | Total ms | FPS | vs A |
|--------|-------:|--------:|---------:|----:|-----:|
| A: best_detect + 17kp engine | 6.4 | 5.0 | **11.4** | **87.9** | — |
| B: best_detect + 10kp pt | 6.7 | 9.2 | **15.8** | **63.2** | −24.6 |
| C: unify + 10kp pt | 4.9 | 9.5 | **14.5** | **69.1** | −18.8 |
| D: unify + 10kp pt + FD | — | — | — | — | invalid* |

> \* Config D: dummy black frame → 99.5% frames skipped (no motion) → only 1 frame measured → statistically invalid for dummy source.

**Key observation from this table:**

| | 17kp (best_pose.engine) | 10kp (yolo11n-10kp.pt) |
|--|:-----------------------:|:----------------------:|
| Format | TensorRT FP16 | PyTorch (.pt) |
| Pose ms | **5.0 ms** | 9.2–9.5 ms |
| Ratio | — | ~2× slower |

> **Finding:** Model format (TRT vs PT) determines speed more than keypoint count.
> 17kp TRT is faster than 10kp PT — despite having more keypoints.

---

## Slide 5 — Stream FPS Results (Configs A–D)

**Title:** End-to-End Stream FPS: Real 4 RTSP Cameras

**Method:** `[INF 60s]` log — state_manager.py emits per-camera FPS every 60 seconds.
Second stable window used (first window = camera connect phase).

**Results:**

| Config | cam1 | cam2 | cam3 | cam4 | Total FPS | vs A |
|--------|-----:|-----:|-----:|-----:|----------:|-----:|
| A: best_detect + 17kp | 8.60 | 8.31 | 8.23 | 7.88 | **33.03** | — |
| B: best_detect + 10kp pt | 8.56 | 8.21 | 8.22 | 7.80 | **32.79** | −0.7% |
| C: unify + 10kp pt | 8.81 | 8.40 | 8.09 | 7.79 | **33.09** | +0.2% |
| D: unify + 10kp pt + FD | 6.30 | 6.30 | 5.65 | 5.60 | **23.84** | **−27.8%** |

**Why is Config D the worst?**

> Frame differencing was designed to skip static frames and save GPU time.
> But real RTSP cameras always have motion (people moving, lighting changes).
> Result: almost no frames are skipped → only CPU overhead is added → **−27.8% FPS**.

**Why is the gap between A, B, C so small?**

Three reasons why stream FPS doesn't reflect model speed differences:
1. **33 FPS hard cap** in `streaming_manager.py` (`if now − last_frame_time < 0.03`)
2. **Alternating inference**: Pose runs every 2nd frame, PPE every 3rd frame
3. **RTSP bottleneck**: cameras send only ~8–9 FPS → GPU waits for frames, not vice versa

---

## Slide 6 — New Idea: Export 10kp Model to TensorRT

**Title:** Insight → Config E: What If 10kp Was Also TensorRT?

**Problem identified:**

| Pose model | Format | Pose ms | Why slow? |
|------------|--------|--------:|-----------|
| best_pose.engine (17kp) | TRT FP16 | 5.0 ms | ✓ Optimized |
| yolo11n-10kp.pt (10kp) | PyTorch | 9.2 ms | ✗ Not compiled |

> 10kp PyTorch is 2× slower than 17kp TensorRT — not because of keypoints, but **format**.

**Action taken:**
```bash
python export_10kp_engine.py
# Exports yolo11n-10kp.pt → yolo11n-10kp.engine (TRT FP16)
```

**Config E added:**

| Config | PPE Model | Pose Model | Format |
|--------|-----------|------------|--------|
| **E** | `unify-29march.engine` | `yolo11n-10kp.engine` | **TRT + TRT** |

---

## Slide 7 — Config E Results: Full 5-Config Comparison

**Title:** Config E — Best of Both Worlds

**Model speed benchmark (all 5 configs):**

| Config | PPE ms | Pose ms | Total ms | FPS | vs A |
|--------|-------:|--------:|---------:|----:|-----:|
| A: best_detect + 17kp TRT | 6.4 | 5.0 | 11.4 | 87.9 | — |
| B: best_detect + 10kp PT | 6.7 | 9.2 | 15.8 | 63.2 | −24.6 |
| C: unify + 10kp PT | 4.9 | 9.5 | 14.5 | 69.1 | −18.8 |
| D: unify + 10kp PT + FD | — | — | — | — | invalid |
| **E: unify + 10kp TRT** | **5.0** | **4.8** | **9.8** | **102.4** | **+14.5** |

**Stream FPS (4 RTSP cameras):**

| Config | Total FPS | vs A |
|--------|----------:|-----:|
| A | 33.03 | — |
| B | 32.79 | −0.7% |
| C | 33.09 | +0.2% |
| D | 23.84 | −27.8% |
| **E** | **34.33** | **+3.9%** |

**Why stream FPS gain is small (+3.9%) despite model gain (+16.5%)?**
> Same bottleneck: RTSP network limits to ~8–9 FPS per camera regardless of GPU speed.
> Model benchmark shows real GPU capability; stream FPS shows real deployment constraint.

---

## Slide 8 — Fall Detection Accuracy: 10kp vs 17kp

**Title:** Does Keypoint Count Affect Fall Detection Accuracy?

**Evaluation setup:**
- Dataset: UPFall (Subject1) — 5 fall types + 4 normal activities (walking, sitting, bending, jumping)
- Model: TCN-Attention (30-frame sequence → fall / no_fall)
- Evaluated offline using `evaluate_yolo10kp.py` and `evaluate_full_kp.py`

**Results:**

| Metric | 10kp Model | 17kp Model | Winner |
|--------|:----------:|:----------:|:------:|
| Overall Accuracy | **99.21%** | 99.10% | 10kp |
| Normal — F1 | **0.992** | 0.990 | 10kp |
| Fall — F1 | **0.992** | 0.970 | **10kp** |
| Fall — Precision | 0.984 | 0.950 | **10kp** |
| **Fall — Recall** | **1.000** | 0.980 | **10kp** |
| Pose FPS (TRT) | **209** | 200 | 10kp |

**Fall Recall = 1.000 for 10kp:**
> Zero missed falls. In a safety system, this is the most critical metric.
> A missed fall = undetected emergency.

**Why 10kp outperforms 17kp on accuracy?**

| 10kp keypoints (all relevant) | 17kp extra keypoints (noise for fall) |
|-------------------------------|--------------------------------------|
| nose, neck | **eyes, ears** → face tracking, not fall-related |
| shoulders, elbows, wrists | **knees, ankles** → lower body detail not needed |
| hips (root of fall motion) | — |

> 10kp TCN model was trained specifically on UPFall custom annotations.
> 17kp model feeds irrelevant joint data → degrades fall classification.

---

## Slide 9 — Bug Found & Fixed: 17kp Keypoint Mapping

**Title:** Critical Bug Discovered in 17kp Fall Detection Pipeline

**Bug location:** `tcn_fall.py`

**Wrong code (before fix):**
```python
if len(keypoints_xy) == 17:
    keypoints_xy = keypoints_xy[:10]   # ← WRONG
```

**What this actually extracts from COCO 17kp:**

| Index | COCO 17kp joint | Intended (Custom 10kp) |
|:-----:|-----------------|------------------------|
| 0 | nose ✓ | nose |
| 1 | **left_eye ✗** | left_shoulder |
| 2 | **right_eye ✗** | right_shoulder |
| 3 | **left_ear ✗** | left_elbow |
| 4 | **right_ear ✗** | right_elbow |
| 5 | **left_shoulder ✗** | left_wrist |
| ... | ... | ... |

> TCN was receiving **eye and ear coordinates** instead of **shoulder and hip coordinates**.
> Fall detection with 17kp was producing incorrect results.

**Fixed code (after):**
```python
if len(keypoints_xy) == 17:
    neck = (kp17[5] + kp17[6]) / 2.0          # shoulder midpoint
    keypoints_xy = np.array([
        kp17[0],   # nose       kp17[5],   # left_shoulder
        kp17[6],   # right_shoulder         kp17[7],   # left_elbow
        kp17[8],   # right_elbow            kp17[9],   # left_wrist
        kp17[10],  # right_wrist            kp17[11],  # left_hip
        kp17[12],  # right_hip              neck,      # neck
    ])
```

**Impact:** 17kp fall detection now correctly maps to the same joint space as 10kp TCN input.

---

## Slide 10 — Conclusions & Final System

**Title:** Conclusions

**Research question answers:**

| Question | Finding |
|----------|---------|
| Does more keypoints = better speed? | **No** — TRT format dominates over keypoint count |
| Does more keypoints = better accuracy? | **No** — 10kp outperforms 17kp (F1: 0.992 vs 0.970) |
| Does frame differencing help stream FPS? | **No** — real cameras always have motion (−27.8%) |
| What is the optimal configuration? | **Config E: unify.engine + 10kp.engine (both TRT)** |

**Final system (Config E):**

| Component | Model | Speed |
|-----------|-------|------:|
| PPE Detection | unify-29march.engine (TRT FP16, 7.9 MB) | 5.0 ms |
| Pose Estimation | yolo11n-10kp.engine (TRT FP16) | 4.8 ms |
| **Combined** | **Both TensorRT** | **9.8 ms → 102.4 FPS** |
| Fall Detection | TCN-Attention (10kp, 30-frame) | Recall = **1.000** |

**Summary of contributions:**

1. Designed and executed 5-configuration benchmark (model speed + stream FPS)
2. Discovered: **TensorRT format > keypoint count** for inference speed
3. Exported 10kp model to TensorRT → **2× faster** (9.2 ms → 4.8 ms)
4. Proved 10kp model is superior for fall detection in **both speed and accuracy**
5. Found and fixed critical **17kp keypoint mapping bug** in fall detection pipeline

**Future work:**
- Multi-subject dataset evaluation (currently Subject1 only)
- Adaptive FPS cap based on real-time GPU utilization
- Config D evaluation with real-motion video (dummy benchmark was invalid)
