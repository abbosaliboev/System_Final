# AI-COMS Pose Configuration Benchmark

**Maqsad:** 4 ta konfiguratsiyani uchta metrikada solishtirish (hammasi TensorRT FP16):
1. **Pure FPS** — dummy frame, GPU tezligi
2. **Video FPS** — real video (test2.mp4), frame diff valid
3. **RTSP FPS** — 4 real RTSP kamera, 60s window

**Hardware:** NVIDIA TITAN RTX 24GB · CUDA 12.1 · TensorRT 10.x

---

## 4 ta Konfiguratsiya (hammasi TRT)

| Config | PPE Model | Pose Model | KP | PPE Size | Pose Size | Frame Diff |
|--------|-----------|------------|:--:|---------:|----------:|:----------:|
| **1** | `best_detect.engine` | `best_pose.engine` | 17 | 41.5 MB | 8.9 MB | ✗ |
| **2** | `best_detect.engine` | `yolo11n-10kp.engine` | 10 | 41.5 MB | 7.7 MB | ✗ |
| **3** | `unify-29march.engine` | `yolo11n-10kp.engine` | 10 | 7.8 MB | 7.7 MB | ✗ |
| **4** | `unify-29march.engine` | `yolo11n-10kp.engine` | 10 | 7.8 MB | 7.7 MB | ✓ |

---

## 1. Pure GPU Speed — Dummy Frame

**Source:** 640×640 black frame · 200 iterations · single-thread

| Config | PPE ms | Pose ms | Total ms | Pure FPS | vs 1 |
|--------|-------:|--------:|---------:|---------:|-----:|
| 1: best_detect + 17kp | 6.0 | 4.4 | **10.4** | **96.5** | — |
| 2: best_detect + 10kp | 5.8 | 4.0 | **9.7** | **102.8** | +6.3 (+6.5%) |
| 3: unify + 10kp | 4.4 | 4.2 | **8.6** | **116.7** | +20.2 (+20.9%) |
| 4: unify + 10kp + FD | — | — | — | **invalid*** | — |

> \* Config 4 dummy: 199/200 frame skip (qora frame = harakat yo'q) → 1 frame → bekor.

---

## 2. Pure GPU Speed — Real Video

**Source:** `test2.mp4` · 200 iterations · Config 4 uchun valid

| Config | PPE ms | Pose ms | Total ms | Video FPS | vs 1 | FD Skip |
|--------|-------:|--------:|---------:|----------:|-----:|--------:|
| 1: best_detect + 17kp | 7.2 | 5.2 | **12.4** | **80.7** | — | — |
| 2: best_detect + 10kp | 6.9 | 4.6 | **11.5** | **87.2** | +6.5 (+8.1%) | — |
| 3: unify + 10kp | 5.1 | 4.8 | **9.9** | **101.4** | +20.7 (+25.6%) | — |
| 4: unify + 10kp + FD | 7.4 | 6.7 | **14.1** | **70.9** | −9.8 (−12.1%) | 120/200 (60%) |

> Config 4 video da 60% frame skip → faqat 80 "harakatli" frame o'lchandi → ms yuqori ko'rinadi.

---

## 3. End-to-End Stream FPS — Real RTSP

**Source:** 4 real RTSP kamera · `[INF 60s]` log · 2nd stable window

| Config | cam1 | cam2 | cam3 | cam4 | Total FPS | Per-cam | vs 1 |
|--------|-----:|-----:|-----:|-----:|----------:|--------:|-----:|
| 1: best_detect + 17kp | 8.60 | 8.31 | 8.23 | 7.88 | **33.03** | 8.26 | — |
| 2: best_detect + 10kp | — | — | — | — | **~33*** | ~8.3 | ~0% |
| 3: unify + 10kp | 8.76 | 8.71 | 8.44 | 8.42 | **34.33** | 8.58 | +1.30 (+3.9%) |
| 4: unify + 10kp + FD | 6.48 | 6.51 | 5.43 | 5.40 | **23.82** | 5.96 | −9.21 (−27.9%) |

> \* Config 2 RTSP o'lchanmagan. PPE modeli Config 1 bilan bir xil, pose TRT → farq minimal.

---

## 4. To'liq Solishtirma

| Config | Size | Dummy FPS | Video FPS | RTSP FPS | Fall Acc | Fall Recall |
|--------|-----:|----------:|----------:|---------:|:--------:|:-----------:|
| 1 | 50.4 MB | 96.5 | 80.7 | 33.03 | 99.10% | 0.980 |
| 2 | 49.2 MB | 102.8 | 87.2 | ~33 | **99.21%** | **1.000** |
| **3** | **15.5 MB** | **116.7** | **101.4** | **34.33** | **99.21%** | **1.000** |
| 4 | **15.5 MB** | invalid | 70.9* | 23.82 | **99.21%** | **1.000** |

> \* Config 4 video: 60% skip, faqat 80 frame o'lchandi.

---

## 5. Asosiy Xulosalar

### Format > Keypoint soni

| Pose model | Format | Pose ms (real video) | Pose FPS |
|------------|:------:|---------------------:|---------:|
| best_pose.engine (17kp) | TRT FP16 | 5.2 ms | 193 |
| yolo11n-10kp.engine (10kp) | TRT FP16 | **4.6–4.8 ms** | **209–217** |

> 10kp TRT ≈ 17kp TRT tezlikda. Farq keypoint soni emas, format hal qiladi.

### Frame Differencing — Real RTSP da zarar

| Holat | FD Skip % | RTSP FPS | Xulosa |
|-------|----------:|---------:|--------|
| Dummy frame | 99.5% | invalid | — |
| Real video (test2.mp4) | 60% | 70.9* | Static sahna ko'p → skip yordam beradi |
| **Real RTSP (live)** | **~10%** | **23.82** | **Harakat doim bor → −27.9%** |

> PT vs TRT pose bilan frame diff RTSP farq yo'q: PT=23.84, TRT=23.82.
> Bottleneck GPU emas — tarmoq va CPU overhead.

### RTSP FPS nega model tezligidan farq qiladi

```
Config 3 dummy:  116.7 FPS  →  Config 3 RTSP: 34.33 FPS
                 +20.9% vs 1       +3.9% vs 1
```

3 ta sabab:
1. **33 FPS hard cap** — `streaming_manager.py`: `if now - last_frame_time < 0.03`
2. **Alternating inference** — Pose har 2-frame, PPE har 3-frame
3. **RTSP tarmoq** — har kamera ~8–9 FPS yuboradi → GPU frame kutib turadi

### 10kp vs 17kp Accuracy

| Metric | 10kp | 17kp |
|--------|:----:|:----:|
| Accuracy | **99.21%** | 99.10% |
| Fall F1 | **0.992** | 0.970 |
| Fall Recall | **1.000** | 0.980 |

---

## 6. Hozirgi Tizim (Config 3 — default)

```python
# backend/ai_factory/monitor/YOLO/inference_utils.py
ppe_model_paths = [
    ("monitor/YOLO/models/unify-29march.engine", 'detect'),  # ← aktiv
    ("monitor/YOLO/models/unify-29march.pt",     'detect'),  # fallback
    ("monitor/YOLO/models/best_detect.engine",   'detect'),  # eski fallback
]
pose_model_paths = [
    ("monitor/YOLO/models/yolo11n-10kp.engine",  'pose'),   # ← aktiv
    ("monitor/YOLO/models/yolo11n-10kp.pt",      'pose'),   # fallback
    ("monitor/YOLO/models/best_pose.engine",     'pose'),   # eski fallback
]

# backend/ai_factory/monitor/YOLO/streaming_manager.py
USE_FRAME_DIFFERENCING = False  # Config 4 uchun True
```

---

## 7. Benchmark Ishga Tushirish

```bash
cd backend/ai_factory

# Dummy frame
python -m monitor.YOLO.benchmark_pose_configs

# Real video
python -m monitor.YOLO.benchmark_pose_configs --video monitor/videos/test2.mp4

# Stream FPS (60–120 soniya kuting)
python run_fps_bench.py
```

---

## Hardware

| Komponent | Ma'lumot |
|-----------|----------|
| GPU | NVIDIA TITAN RTX (24 GB VRAM) |
| CPU | Intel Core i9-10900X @ 3.70 GHz (20 thread) |
| RAM | 64 GB |
| CUDA | 12.1 |
| TensorRT | 10.x |
