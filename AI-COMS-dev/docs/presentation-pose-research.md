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
|----------|-------|:------:|-----:|
| PPE Detection | `best_detect.engine` | TRT FP16 | 41.5 MB |
| PPE Detection | `unify-29march.engine` | TRT FP16 | 7.8 MB |
| Pose (17kp) | `best_pose.engine` | TRT FP16 | 8.9 MB |
| Pose (10kp) | `yolo11n-10kp.pt` | **PyTorch** | 5.1 MB |
| Frame Diff | `frame_differencing.py` | CPU function | — |

**Problem:** 10kp pose model only existed in PyTorch format → slow inference.

**Research question:**
> Which PPE + Pose combination gives the best speed and accuracy for fall detection?

**Action taken:** Export `yolo11n-10kp.pt` → `yolo11n-10kp.engine` (TRT FP16)

**Two metrics measured:**
1. **Model speed** — pure GPU inference (dummy + real video)
2. **Stream FPS** — 4 real RTSP cameras, 60-second stable window

---

## Slide 3 — Experimental Design: 4 Configurations (All TRT)

**Title:** 4 Configurations — All TensorRT FP16

| Config | PPE Model | Pose Model | KP | Total Size | Frame Diff |
|--------|-----------|------------|:--:|-----------:|:----------:|
| **1** | `best_detect.engine` | `best_pose.engine` | 17 | 50.4 MB | ✗ |
| **2** | `best_detect.engine` | `yolo11n-10kp.engine` | 10 | 49.2 MB | ✗ |
| **3** | `unify-29march.engine` | `yolo11n-10kp.engine` | 10 | **15.5 MB** | ✗ |
| **4** | `unify-29march.engine` | `yolo11n-10kp.engine` | 10 | **15.5 MB** | ✓ |

**What changes between configs:**
- 1 → 2: PPE same, pose changes (17kp → 10kp), both TRT
- 2 → 3: pose same, PPE changes (42MB → 7.8MB unified)
- 3 → 4: models same, frame differencing added

**Frame differencing:** Skip inference when no motion detected between frames.
Implemented in `frame_differencing.py`, toggle via `USE_FRAME_DIFFERENCING` in `streaming_manager.py`.

---

## Slide 4 — Pure GPU Speed Benchmark

**Title:** Model Speed: Raw GPU Inference (No RTSP Overhead)

**Dummy frame (640×640 black) — Config 4 invalid:**

| Config | PPE ms | Pose ms | Total ms | FPS | vs 1 |
|--------|-------:|--------:|---------:|----:|-----:|
| 1: best_detect + 17kp | 6.0 | 4.4 | 10.4 | **96.5** | — |
| 2: best_detect + 10kp | 5.8 | 4.0 | 9.7 | **102.8** | +6.5% |
| 3: unify + 10kp | 4.4 | 4.2 | 8.6 | **116.7** | +20.9% |
| 4: unify + 10kp + FD | — | — | — | **invalid*** | — |

> \* Dummy = no motion → 199/200 frames skipped → 1 frame measured → invalid.

**Real video (test2.mp4) — Config 4 valid:**

| Config | PPE ms | Pose ms | Total ms | FPS | vs 1 | FD Skip |
|--------|-------:|--------:|---------:|----:|-----:|--------:|
| 1 | 7.2 | 5.2 | 12.4 | **80.7** | — | — |
| 2 | 6.9 | 4.6 | 11.5 | **87.2** | +8.1% | — |
| **3** | **5.1** | **4.8** | **9.9** | **101.4** | **+25.6%** | — |
| 4 | 7.4 | 6.7 | 14.1 | 70.9 | −12.1% | 60% |

> Config 4: 60% frames skipped → only 80 "hard" frames measured → ms yaxshi ko'rinmaydi.

**Key finding:**
> **10kp TRT (4.8 ms) ≈ 17kp TRT (5.2 ms)** — format hal qiladi, keypoint soni emas.
> Config 3 = smallest model (15.5 MB) + fastest inference (101.4 FPS video).

---

## Slide 5 — End-to-End Stream FPS (4 RTSP Cameras)

**Title:** Real Deployment: Stream FPS vs Pure GPU Speed

**Method:** `[INF 60s]` log from `state_manager.py`, 2nd stable 60-second window.

| Config | cam1 | cam2 | cam3 | cam4 | Total FPS | vs 1 |
|--------|-----:|-----:|-----:|-----:|----------:|-----:|
| 1: best_detect + 17kp | 8.60 | 8.31 | 8.23 | 7.88 | **33.03** | — |
| 2: best_detect + 10kp | — | — | — | — | **~33*** | ~0% |
| **3: unify + 10kp** | **8.76** | **8.71** | **8.44** | **8.42** | **34.33** | **+3.9%** |
| 4: unify + 10kp + FD | 6.48 | 6.51 | 5.43 | 5.40 | **23.82** | −27.9% |

> \* Config 2 not measured in RTSP — PPE identical to Config 1, pose TRT → difference minimal.

**Why is Config 4 (Frame Diff) the worst?**

| Source | FD Skip % | FPS |
|--------|----------:|----:|
| Dummy black frame | 99.5% | invalid |
| Real video (test2.mp4) | 60% | 70.9 (good) |
| **Real RTSP (live cameras)** | **~10%** | **23.82 (bad)** |

> Real cameras always have motion (people, lighting) → few frames skipped → only CPU overhead added → −27.9%.

**PT vs TRT pose makes no difference for Config 4:**
> Old PT pose: 23.84 FPS · New TRT pose: 23.82 FPS → identical.
> Bottleneck is the CPU frame differencing overhead, not GPU.

**Why does Config 3 gain only +3.9% despite +25.6% model speedup?**

Three bottlenecks in live streaming:
1. **33 FPS hard cap** — `if now - last_frame_time < 0.03` in `streaming_manager.py`
2. **Alternating inference** — Pose every 2nd frame, PPE every 3rd frame
3. **RTSP network** — cameras send ~8–9 FPS → GPU waits for frames

---

## Slide 6 — Fall Detection Accuracy: 10kp vs 17kp

**Title:** Does Keypoint Count Affect Fall Detection Accuracy?

**Dataset:** UPFall (Subject1) — 5 fall types + walking, sitting, bending, jumping
**Model:** TCN-Attention — 30-frame sequence → fall / no_fall
**Evaluation:** `evaluate_yolo10kp.py` · `evaluate_full_kp.py`

| Metric | 10kp Model | 17kp Model | Winner |
|--------|:----------:|:----------:|:------:|
| Overall Accuracy | **99.21%** | 99.10% | **10kp** |
| Normal — F1 | **0.992** | 0.990 | 10kp |
| Fall — F1 | **0.992** | 0.970 | **10kp** |
| Fall — Precision | **0.984** | 0.950 | **10kp** |
| **Fall — Recall** | **1.000** | 0.980 | **10kp** |
| Pose FPS (TRT) | **209** | 200 | **10kp** |

**Fall Recall = 1.000 (10kp):** Zero missed falls.
> In a safety system: missed fall = undetected emergency. This is the most critical metric.

**Why 10kp is more accurate:**

| 10kp keypoints (all relevant) | 17kp extra keypoints (noise) |
|-------------------------------|------------------------------|
| shoulders, elbows, wrists | **eyes, ears** — face only |
| hips — root of fall motion | **knees, ankles** — lower body detail |
| nose, neck | — |

> 10kp TCN model trained specifically on UPFall custom 10kp annotations.
> 17kp feeds irrelevant joint data → degrades classification boundary.

---

## Slide 7 — Bug Found & Fixed: 17kp Keypoint Mapping

**Title:** Critical Bug in 17kp Fall Detection Pipeline

**Bug location:** `tcn_fall.py` — keypoint extraction when using 17kp pose model

**Wrong code (before):**
```python
if len(keypoints_xy) == 17:
    keypoints_xy = keypoints_xy[:10]   # WRONG
```

**What `[:10]` actually extracts from COCO 17kp:**

| Index | COCO 17kp joint | Should be (custom 10kp) |
|:-----:|:---------------:|:-----------------------:|
| 0 | nose ✓ | nose |
| 1 | **left_eye ✗** | left_shoulder |
| 2 | **right_eye ✗** | right_shoulder |
| 3 | **left_ear ✗** | left_elbow |
| 4 | **right_ear ✗** | right_elbow |

> TCN received eye/ear coordinates instead of shoulder/hip → incorrect fall detection.

**Fixed code (after):**
```python
if len(keypoints_xy) == 17:
    neck = (kp17[5] + kp17[6]) / 2.0   # shoulder midpoint = neck
    keypoints_xy = np.array([
        kp17[0],   # nose          kp17[5],   # left_shoulder
        kp17[6],   # right_shoulder  kp17[7],   # left_elbow
        kp17[8],   # right_elbow   kp17[9],   # left_wrist
        kp17[10],  # right_wrist   kp17[11],  # left_hip
        kp17[12],  # right_hip     neck,      # neck
    ])
```

---

## Slide 8 — Summary & Conclusions

**Title:** Summary and Conclusions

**Research question answers:**

| Question | Answer |
|----------|--------|
| More keypoints = faster? | **No** — TRT format dominates (10kp TRT ≈ 17kp TRT) |
| More keypoints = more accurate? | **No** — 10kp wins (Fall F1: 0.992 vs 0.970) |
| Frame differencing helps? | **No** — real cameras always moving → −27.9% RTSP FPS |
| Best configuration? | **Config 3: unify.engine + 10kp.engine (both TRT)** |

**Final system — Config 3:**

| Component | Model | Size | Speed |
|-----------|-------|-----:|------:|
| PPE | unify-29march.engine | 7.8 MB | 5.1 ms |
| Pose | yolo11n-10kp.engine | 7.7 MB | 4.8 ms |
| **Combined** | **Both TRT FP16** | **15.5 MB** | **101.4 FPS (video)** |
| Fall | TCN-Attention 10kp | 1.5 MB | Recall = **1.000** |

**vs Config 1 (baseline):**

| Metric | Config 1 | Config 3 | Delta |
|--------|:--------:|:--------:|:-----:|
| Model size | 50.4 MB | **15.5 MB** | **−69%** |
| Video FPS | 80.7 | **101.4** | **+25.6%** |
| RTSP FPS | 33.03 | **34.33** | **+3.9%** |
| Fall Recall | 0.980 | **1.000** | **+2%** |

**Key contributions:**

1. Exported 10kp pose model to TensorRT → **~2× faster** than PyTorch format
2. Designed 4-config benchmark with 3 metrics (dummy / video / RTSP FPS)
3. Proved: **TensorRT format > keypoint count** for inference speed
4. Proved: **10kp > 17kp** for fall detection accuracy
5. Fixed critical **17kp keypoint mapping bug** in TCN fall detector
6. Showed: **Frame differencing hurts** live RTSP (real cameras always have motion)

**Future work:**
- Multi-subject accuracy evaluation (currently Subject1 only)
- Adaptive FPS cap based on GPU utilization
- RTSP FPS statistical averaging across multiple days
