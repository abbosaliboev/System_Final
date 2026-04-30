# AI-COMS — Final Benchmark Table (All TensorRT FP16)

**Hardware:** NVIDIA TITAN RTX 24GB · Intel i9-10900X · CUDA 12.1 · TensorRT 10.x
**All models:** TensorRT FP16 (.engine format)

---

## Configuration Overview

| Config | PPE Model | Pose Model | Keypoints | Frame Diff | PPE Size | Pose Size | Total Size |
|--------|-----------|------------|:---------:|:----------:|---------:|----------:|-----------:|
| **1** | `best_detect.engine` | `best_pose.engine` | 17 | ✗ | 41.5 MB | 8.9 MB | **50.4 MB** |
| **2** | `best_detect.engine` | `yolo11n-10kp.engine` | 10 | ✗ | 41.5 MB | 7.7 MB | **49.2 MB** |
| **3** | `unify-29march.engine` | `yolo11n-10kp.engine` | 10 | ✗ | 7.8 MB | 7.7 MB | **15.5 MB** |
| **4** | `unify-29march.engine` | `yolo11n-10kp.engine` | 10 | ✓ | 7.8 MB | 7.7 MB | **15.5 MB** |

---

## Pure GPU Speed — Dummy Frame (640×640 black, 200 iter)

*No RTSP overhead. Measures raw GPU inference speed.*

| Config | PPE ms | Pose ms | Total ms | Pure FPS | vs Config 1 |
|--------|-------:|--------:|---------:|---------:|------------:|
| 1: best_detect + 17kp | 6.0 | 4.4 | **10.4** | **96.5** | — |
| 2: best_detect + 10kp | 5.8 | 4.0 | **9.7** | **102.8** | +6.3 (+6.5%) |
| 3: unify + 10kp | 4.4 | 4.2 | **8.6** | **116.7** | +20.2 (+20.9%) |
| 4: unify + 10kp + FD | — | — | — | **invalid*** | — |

> \* Config 4 dummy: 199/200 frames skipped (black frame = no motion) → 1 frame measured → invalid.

---

## Pure GPU Speed — Real Video (test2.mp4, 200 iter)

*Real content frames. Config 4 frame differencing valid here.*

| Config | PPE ms | Pose ms | Total ms | Video FPS | vs Config 1 | FD Skip |
|--------|-------:|--------:|---------:|----------:|------------:|--------:|
| 1: best_detect + 17kp | 7.2 | 5.2 | **12.4** | **80.7** | — | — |
| 2: best_detect + 10kp | 6.9 | 4.6 | **11.5** | **87.2** | +6.5 (+8.1%) | — |
| 3: unify + 10kp | 5.1 | 4.8 | **9.9** | **101.4** | +20.7 (+25.6%) | — |
| 4: unify + 10kp + FD | 7.4 | 6.7 | **14.1** | **70.9** | −9.8 (−12.1%) | 120/200 (60%) |

> Config 4 video FPS (70.9) görünür yomon — chunki faqat 80 frame o'lchandi, va ular harakati bor (qiyin) frame lar. Skip qilingan 120 frame 0ms sarfladi.

---

## End-to-End Stream FPS — Real RTSP (4 cameras, 60s window)

*`[INF 60s]` log, 2nd stable window, state_manager.py*

| Config | cam1 | cam2 | cam3 | cam4 | Total FPS | Per-cam | vs Config 1 |
|--------|-----:|-----:|-----:|-----:|----------:|--------:|------------:|
| 1: best_detect + 17kp | 8.60 | 8.31 | 8.23 | 7.88 | **33.03** | 8.26 | — |
| 2: best_detect + 10kp | — | — | — | — | **~33*** | ~8.3 | ~0% |
| 3: unify + 10kp | 8.76 | 8.71 | 8.44 | 8.42 | **34.33** | 8.58 | +1.30 (+3.9%) |
| 4: unify + 10kp + FD | 6.48 | 6.51 | 5.43 | 5.40 | **23.82** | 5.96 | −9.21 (−27.9%) |

> \* Config 2 RTSP o'lchanmagan. Config 1 bilan PPE modeli bir xil, pose TRT → farq minimal (~33 FPS).

---

## Complete Summary — All Metrics

| Config | PPE Model | Pose | KP | Size | Dummy FPS | Video FPS | RTSP FPS | Fall Acc | Fall Recall |
|--------|-----------|------|----|-----:|----------:|----------:|---------:|:--------:|:-----------:|
| **1** | best_detect | best_pose | 17 | 50.4 MB | 96.5 | 80.7 | 33.03 | 99.10% | 0.980 |
| **2** | best_detect | 10kp | 10 | 49.2 MB | 102.8 | 87.2 | ~33* | **99.21%** | **1.000** |
| **3** | unify | 10kp | 10 | **15.5 MB** | **116.7** | **101.4** | **34.33** | **99.21%** | **1.000** |
| **4** | unify | 10kp + FD | 10 | **15.5 MB** | invalid** | 70.9*** | 23.82 | **99.21%** | **1.000** |

> \* Config 2 RTSP o'lchanmagan — Config 1 bilan PPE bir xil, pose TRT farqi minimal.
> \*\* Config 4 dummy: 199/200 skip (black frame = no motion) → invalid.
> \*\*\* Config 4 video FPS: 60% frame skip, faqat 80 frame o'lchandi.

---

## Key Findings

| Finding | Detail |
|---------|--------|
| **Best config overall** | Config 3 — smallest size, fastest speed, best RTSP FPS |
| **Size reduction** | Config 1→3: 50.4 MB → 15.5 MB (**−69%**) |
| **Dummy FPS gain** | Config 1→3: 96.5 → 116.7 FPS (**+20.9%**) |
| **Video FPS gain** | Config 1→3: 80.7 → 101.4 FPS (**+25.6%**) |
| **RTSP FPS gain** | Config 1→3: 33.03 → 34.33 FPS (**+3.9%**) |
| **Frame diff (Config 4)** | Real RTSP: 33.03 → 23.82 FPS (**−27.9%**) — TRT pose bilan ham xuddi shu natija |
| **Frame diff video** | 60% skip → 70.9 FPS (yaxshi ko'rinadi), lekin faqat 80 "qiyin" frame o'lchandi |
| **Frame diff: PT vs TRT** | RTSP da farq yo'q (23.84 PT ≈ 23.82 TRT) — bottleneck GPU emas, tarmoq |
| **17kp vs 10kp accuracy** | Fall F1: 0.970 vs **0.992** · Fall Recall: 0.980 vs **1.000** |
| **RTSP bottleneck** | Kamera ~8-9 FPS → GPU model tezligi stream FPS ga ta'sir qilmaydi |

---

## Why RTSP FPS Barely Changes Despite GPU Speedup

```
Config 1 dummy:  96.5 FPS  │  Config 1 RTSP: 33.03 FPS
Config 3 dummy: 116.7 FPS  │  Config 3 RTSP: 34.33 FPS
                 +20.9%    │                  +3.9%
```

**3 bottleneck:**
1. RTSP camera → ~8–9 FPS per camera (network limit)
2. 33 FPS hard cap in `streaming_manager.py` (`now - last_frame_time < 0.03`)
3. Alternating inference: Pose every 2nd frame, PPE every 3rd frame

> GPU is never the bottleneck in live streaming. Model speed matters for **latency per detection**, not for stream FPS.
