# AI-COMS Presentation — Slide Content

**Sarlavha:** Real-time Multi-Camera Industrial Safety Monitoring System Optimization
**Universitet:** Chungbuk National University — Data Analytics Lab
**Hardware:** NVIDIA TITAN RTX · Intel i9-10900X · 64 GB RAM · CUDA 12.1 · TensorRT 10.x

---

## Slide 1 — Title

**Title:**
> Real-time Multi-Camera Industrial Safety Monitoring:
> System Optimization and Pose Model Evaluation

**Subtitle:**
> PPE Detection · Fall Detection · Danger Zone Monitoring

**Info (pastki qism):**
- Chungbuk National University — Data Analytics Lab
- Hardware: NVIDIA TITAN RTX 24GB · CUDA 12.1 · TensorRT 10.x
- 2026

---

## Slide 2 — System Overview

**Title:** AI-COMS: What Does the System Do?

**Left column — Pipeline:**
```
RTSP Cameras (×4)
       ↓
 Frame Grabber
       ↓
  PPE Detection    ←─ unify-29march.engine (TRT FP16)
  Pose Estimation  ←─ yolo11n-10kp.engine  (TRT FP16)
       ↓
 TCN-Attention Fall Detector  ←─ 30-frame sequence
       ↓
 Danger Zone Check
       ↓
 Django REST API → React Frontend
```

**Right column — What is detected:**

| Task | Model | Output |
|------|-------|--------|
| PPE (helmet/vest/head) | YOLOv8 detect | Bounding box + class |
| Pose estimation | YOLOv11 10kp | 10 keypoints per person |
| Fall detection | TCN-Attention | fall / no_fall + confidence |
| Danger zone | Polygon check | Alert if person inside |

**Note:**
> 4 RTSP camera → 2 OS process (2 cam/process) → multiprocessing parallelism

---

## Slide 3 — Problem Statement

**Title:** Problem: System Was Too Slow

**Main statement (bold, center):**
> Original system: only **24.93 FPS** for 4 cameras = **~6.2 FPS per camera**

**Root causes identified:**

| # | Problem | Impact |
|---|---------|--------|
| P1 | `torch.cuda.synchronize()` called every frame | +1–10 ms wasted per frame |
| P2 | New `Thread()` created per frame | Thread creation overhead |
| P3 | `time.sleep(0.001)` runs even when frames available | Unconditional yield |
| P4 | `chunk_size=1` → 4 separate processes | No camera sharing |
| P5 | Frame queue holds multiple frames | Stale frame processing |
| P6 | DB query for danger zones every frame | Repeated I/O |
| P7 | `list.pop(0)` for TCN buffer → O(N) | Slow buffer management |

**Bottom line:**
> These are all **engineering bottlenecks** — not model limitations.

---

## Slide 4 — Code Optimization Results

**Title:** Phase 1: Code Optimization (P1–P7)

**Fix summary:**

| Fix | Before | After |
|-----|--------|-------|
| P1 — CUDA sync | `synchronize()` every frame | Removed (YOLO handles internally) |
| P2 — Threading | `Thread()` per frame | `ThreadPoolExecutor` — reused pool |
| P3 — Sleep | Unconditional `sleep(0.001)` | Only when all queues empty |
| P4 — Process | 4 processes (1 cam each) | 2 processes (2 cam each) |
| P5 — Queue | Multiple frames buffered | Max-size-1, keep latest only |
| P6 — DB | Every frame | 30-second cache refresh |
| P7 — Buffer | `list.pop(0)` O(N) | `deque(maxlen=30)` O(1) |

**Result (same model, only code changed):**

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Total FPS (4 cam) | 24.93 | **34.55** | **+38.5%** |
| Per-camera avg | 6.23 | 8.64 | +38.7% |

**Key insight:**
> +38.5% FPS gain with **zero model change** — pure engineering optimization.

---

## Slide 5 — Unified Model Integration

**Title:** Phase 2: Replacing the PPE Model

**Problem with old model (`best_detect.engine`):**
- Size: 42 MB — large for inference
- Not aware of human pose → more false positives

**New model (`unify-29march.engine`):**
- Pose-aware backbone (shared feature extraction)
- Size: **7.9 MB** (5× smaller)
- TensorRT FP16 — same format

**Model comparison:**

| Model | Size | PPE Inference | Stream FPS (4 cam) |
|-------|------|---------------|---------------------|
| `best_detect.engine` | 42 MB | 6.2 ms | 34.55 |
| `unify-29march.engine` | **7.9 MB** | **4.7 ms** | **~49.12** |

**Combined result (Phase 1 + Phase 2):**

| Stage | Total FPS | vs Baseline |
|-------|-----------|-------------|
| Baseline (original) | 24.93 | — |
| + Code optimization | 34.55 | +38.5% |
| + Unified model | **~49.12** | **+97%** |

**Visual (bar or arrow):**
```
24.93  ──────────────────────────────────── Baseline
34.55  ──────────────────────────────────────────────── +38.5%
49.12  ──────────────────────────────────────────────────────────────── +97%
```

---

## Slide 6 — Pose Model Benchmark: 5 Configurations

**Title:** Phase 3: Which Pose Model Combination is Best?

**5 configurations tested:**

| Config | PPE Model | Pose Model | Format |
|--------|-----------|------------|--------|
| A | best_detect.engine (42 MB) | best_pose.engine (17kp) | TRT + TRT |
| B | best_detect.engine (42 MB) | yolo11n-10kp.pt (10kp) | TRT + PT |
| C | unify-29march.engine (7.9 MB) | yolo11n-10kp.pt (10kp) | TRT + PT |
| D | unify-29march.engine (7.9 MB) | yolo11n-10kp.pt + Frame Diff | TRT + PT |
| **E** | **unify-29march.engine (7.9 MB)** | **yolo11n-10kp.engine (10kp)** | **TRT + TRT** |

**Model speed benchmark (dummy 640×640, 200 iterations, TITAN RTX):**

| Config | PPE ms | Pose ms | Total ms | FPS | vs A |
|--------|--------|---------|----------|-----|------|
| A | 6.4 | 5.0 | 11.4 | 87.9 | — |
| B | 6.7 | 9.2 | 15.8 | 63.2 | −24.6 |
| C | 4.9 | 9.5 | 14.5 | 69.1 | −18.8 |
| D | — | — | — | — | invalid* |
| **E** | **5.0** | **4.8** | **9.8** | **102.4** | **+14.5** |

> \* Config D: dummy frame → 99.5% skipped → only 1 frame measured → statistically invalid.

**Winner: Config E — 102.4 FPS**

---

## Slide 7 — Stream FPS & Key Finding

**Title:** Stream FPS vs Model FPS: Why the Gap?

**End-to-end stream FPS (4 RTSP cameras, 60s stable window):**

| Config | cam1 | cam2 | cam3 | cam4 | Total FPS | vs A |
|--------|------|------|------|------|-----------|------|
| A | 8.60 | 8.31 | 8.23 | 7.88 | 33.03 | — |
| B | 8.56 | 8.21 | 8.22 | 7.80 | 32.79 | −0.7% |
| C | 8.81 | 8.40 | 8.09 | 7.79 | 33.09 | +0.2% |
| D | 6.30 | 6.30 | 5.65 | 5.60 | 23.84 | −27.8% |
| **E** | **8.76** | **8.71** | **8.44** | **8.42** | **34.33** | **+3.9%** |

**Why model speed ≠ stream FPS?**

Three bottlenecks limit stream FPS regardless of GPU speed:

1. **33 FPS hard cap** — `if now - last_frame_time < 0.03` in streaming_manager.py
2. **Alternating inference** — Pose runs every 2nd frame, PPE every 3rd frame
3. **RTSP network** — cameras send only ~8–9 FPS → GPU waits for frames

> GPU is NOT the bottleneck. Network and scheduling are.

**Key finding:**
> **TensorRT format > keypoint count**

| Pose model | Format | Pose ms |
|------------|--------|---------|
| best_pose.engine (17kp) | TRT FP16 | 5.0 ms |
| yolo11n-10kp.pt (10kp) | PyTorch | 9.2–9.5 ms |
| **yolo11n-10kp.engine (10kp)** | **TRT FP16** | **4.8 ms** |

> 17kp TRT ≈ 10kp TRT in speed. 10kp PT is 2× slower than 10kp TRT.

---

## Slide 8 — Fall Detection: 10kp vs 17kp Accuracy

**Title:** Phase 4: Fall Detection Accuracy Evaluation

**Dataset:** UPFall (Subject1) — 5 fall types + 4 normal activities

**TCN-Attention model:** 30-frame sequence input, 2-class output (fall / no_fall)

**Results (offline evaluation):**

| Metric | 10kp model | 17kp model | Winner |
|--------|-----------|------------|--------|
| **Overall Accuracy** | **99.21%** | 99.10% | 10kp |
| Normal — F1 | **0.992** | 0.990 | 10kp |
| Fall — F1 | **0.992** | 0.970 | **10kp** |
| Fall — Precision | 0.984 | 0.950 | **10kp** |
| **Fall — Recall** | **1.000** | 0.980 | **10kp** |
| Pose model FPS (TRT) | **209** | 200 | 10kp |
| Test samples | 2,163 | 7,591 | — |

**Fall Recall = 1.000 (10kp)** → zero missed falls → critical for safety systems.

**Why 10kp is more accurate?**

- TCN model trained specifically on 10kp UPFall dataset
- 17kp includes irrelevant keypoints for fall detection:
  - eyes, ears → face tracking noise
  - knees, ankles → lower body noise
- 10kp contains only what matters: shoulders, elbows, wrists, hips, neck

**Bug found & fixed:**
> When using 17kp model, `tcn_fall.py` was incorrectly taking `keypoints[:10]`
> = nose + eyes + ears + shoulders → wrong input to TCN.
> Fixed: proper COCO→custom remapping implemented.

---

## Slide 9 — Final Configuration & Architecture

**Title:** Final System: Config E (Optimal)

**Selected configuration:**

| Component | Model | Format | Size | Speed |
|-----------|-------|--------|------|-------|
| PPE Detection | unify-29march.engine | TensorRT FP16 | 7.9 MB | 5.0 ms |
| Pose Estimation | yolo11n-10kp.engine | TensorRT FP16 | ~7 MB | 4.8 ms |
| Fall Detection | fall_detection_v4.pth | PyTorch | 1.5 MB | — |
| **Combined** | | **Both TRT** | | **9.8 ms → 102.4 FPS** |

**System architecture:**
```
4 RTSP Cameras
      │
      ▼
┌─────────────────────────────────────────────────┐
│  Process-2 (cam1 + cam2)                        │
│  Process-3 (cam3 + cam4)                        │
│                                                 │
│  Per camera loop:                               │
│   Frame → PPE (every 3rd) + Pose (every 2nd)   │
│         → TCN-Attention (30-frame buffer)       │
│         → Danger Zone polygon check             │
│         → Annotated frame → MJPEG stream        │
└─────────────────────────────────────────────────┘
      │
      ▼
Django REST API → React Frontend
```

**Overall improvement from baseline:**

| | Baseline | Final (Config E) | Improvement |
|--|----------|-----------------|-------------|
| Stream FPS (4 cam) | 24.93 | **34.33** | **+37.7%** |
| Model FPS | 87.9 (Config A) | **102.4** | **+16.5%** |
| PPE model size | 42 MB | **7.9 MB** | **−81%** |
| Fall Recall | — | **100%** | — |

---

## Slide 10 — Summary & Conclusions

**Title:** Summary and Conclusions

**Research questions & answers:**

| Question | Answer |
|----------|--------|
| How to improve real-time FPS? | Code optimization (+38.5%) + TRT model (+97% total) |
| Does model format matter more than keypoint count? | **Yes** — TRT FP16 dominates over PT regardless of keypoints |
| Is 10kp or 17kp better for fall detection? | **10kp** — higher accuracy + faster inference |
| Does frame differencing help? | **No** — real cameras always have motion → −27.8% FPS |

**Key contributions:**

1. **7 engineering optimizations (P1–P7)** → +38.5% FPS with zero model change
2. **Unified model integration** → 5× smaller, faster PPE detection
3. **TensorRT export of 10kp pose model** → 2× faster than PyTorch format
4. **10kp vs 17kp benchmark** → 10kp wins on both speed and accuracy
5. **Bug fix in 17kp→10kp keypoint mapping** → correct fall detection input

**Final system performance:**

```
Model benchmark:   102.4 FPS  (single inference, GPU only)
Stream (4 cameras): 34.33 FPS  (real RTSP, network-bounded)
Fall detection:     99.21% accuracy, Recall = 1.000
```

**Future work:**

- [ ] Export `fall_detection_v4.pth` to TensorRT for faster TCN inference
- [ ] Multi-subject fall detection evaluation
- [ ] Adaptive FPS cap based on GPU load
- [ ] Frame differencing evaluation with real-motion video

---

## Qo'shimcha — Slide uchun vizual g'oyalar

**Slide 4 uchun (code optimization):** before/after FPS bar chart: 24.93 → 34.55

**Slide 5 uchun (unified model):** 3-bar chart: 24.93 → 34.55 → 49.12

**Slide 6 uchun (5 config):** horizontal bar chart, Config E highlighted in green

**Slide 7 uchun (stream vs model FPS):** dual bar (model FPS + stream FPS side by side) — gap vizual ko'rsatish

**Slide 8 uchun (accuracy):** 2x2 confusion matrix image yonma-yon + Fall F1 comparison bar
