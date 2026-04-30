# AI-COMS Research Overview

**Loyiha:** Real-time Multi-Camera Industrial Safety Monitoring
**Universitet:** Chungbuk National University — Data Analytics Lab
**Hardware:** NVIDIA TITAN RTX (24 GB) · Intel i9-10900X · 64 GB RAM · CUDA 12.1 · TensorRT 10.x

---

## Nima qildik — Qisqacha

Bu research ikki asosiy savolga javob beradi:

1. **Tizim tezligi qanday oshiriladi?** → Kod optimizatsiyasi + TensorRT model formati
2. **10kp vs 17kp pose model: qaysi biri yaxshi?** → Tezlik ham, aniqlik ham 10kp

---

## Research Bosqichlari

### Bosqich 1 — Kod Optimizatsiyasi (P1–P7)

**Muammo:** Tizim 4 RTSP kamera bilan atigi ~25 FPS berardi.

| Fix | Muammo | Yechim |
|-----|--------|--------|
| P1 | `torch.cuda.synchronize()` har frame da | O'chirildi |
| P2 | Har frame uchun yangi `Thread()` | `ThreadPoolExecutor` — bir marta |
| P3 | `time.sleep(0.001)` unconditional | Faqat queue bo'sh bo'lsa |
| P4 | `chunk_size=1` → 4 process | `chunk_size=2` → 2 process |
| P5 | Frame queue to'lib ketadi | Max-size-1 queue |
| P6 | Har frame DB so'rovi | 30s cache |
| P7 | `list.pop(0)` O(N) | `deque(maxlen=30)` O(1) |

**Natija:** 24.93 → 34.55 FPS (+38.5%) — faqat kod, model o'zgarishsiz.

---

### Bosqich 2 — Unified Model Integratsiyasi

**Muammo:** `best_detect.engine` (42 MB) katta va sekin.

| Model | Size | PPE ms | Stream FPS |
|-------|-----:|-------:|-----------:|
| `best_detect.engine` | 42 MB | 6.2 ms | 34.55 |
| `unify-29march.engine` | 7.9 MB | 4.7 ms | **~49.12** |

**Umumiy (Bosqich 1 + 2):** 24.93 → ~49.12 FPS = **+97% (~2x)**

> ⚠️ 49.12 FPS birinchi sessiyada o'lchangan. RTSP sharoiti kun sayin farq qiladi.

---

### Bosqich 3 — Pose Model Benchmark (4 Config, hammasi TRT)

**Savol:** Qaysi PPE + Pose kombinatsiyasi eng tez va aniq?

**Boshlang'ich holat:** 10kp pose model faqat `.pt` (PyTorch) formatida bor edi.
**Qilingan ish:** `yolo11n-10kp.pt` → `yolo11n-10kp.engine` (TRT FP16) ga export qilindi.

#### 4 Konfiguratsiya

| Config | PPE | Pose | KP | Size | Frame Diff |
|--------|-----|------|----|-----:|:----------:|
| 1 | best_detect.engine | best_pose.engine | 17 | 50.4 MB | ✗ |
| 2 | best_detect.engine | yolo11n-10kp.engine | 10 | 49.2 MB | ✗ |
| **3** | unify-29march.engine | yolo11n-10kp.engine | 10 | **15.5 MB** | ✗ |
| 4 | unify-29march.engine | yolo11n-10kp.engine | 10 | **15.5 MB** | ✓ |

#### Dummy FPS (640×640 black frame, 200 iter)

| Config | PPE ms | Pose ms | Total ms | FPS | vs 1 |
|--------|-------:|--------:|---------:|----:|-----:|
| 1 | 6.0 | 4.4 | 10.4 | 96.5 | — |
| 2 | 5.8 | 4.0 | 9.7 | 102.8 | +6.5% |
| **3** | **4.4** | **4.2** | **8.6** | **116.7** | **+20.9%** |
| 4 | — | — | — | invalid* | — |

> \* Config 4 dummy: 199/200 skip → bekor.

#### Video FPS (test2.mp4, 200 iter)

| Config | PPE ms | Pose ms | Total ms | FPS | vs 1 | FD Skip |
|--------|-------:|--------:|---------:|----:|-----:|--------:|
| 1 | 7.2 | 5.2 | 12.4 | 80.7 | — | — |
| 2 | 6.9 | 4.6 | 11.5 | 87.2 | +8.1% | — |
| **3** | **5.1** | **4.8** | **9.9** | **101.4** | **+25.6%** | — |
| 4 | 7.4 | 6.7 | 14.1 | 70.9 | −12.1% | 60% |

#### RTSP FPS (4 real kamera, 60s window)

| Config | cam1 | cam2 | cam3 | cam4 | Total | vs 1 |
|--------|-----:|-----:|-----:|-----:|------:|-----:|
| 1 | 8.60 | 8.31 | 8.23 | 7.88 | 33.03 | — |
| 2 | — | — | — | — | ~33 | ~0% |
| **3** | **8.76** | **8.71** | **8.44** | **8.42** | **34.33** | **+3.9%** |
| 4 | 6.48 | 6.51 | 5.43 | 5.40 | 23.82 | −27.9% |

#### Asosiy Kashfiyotlar

**1. Format > Keypoint soni:**
- 10kp TRT (4.6 ms) ≈ 17kp TRT (5.2 ms) — format hal qiladi, keypoint soni emas
- PT formatdagi 10kp 9.2 ms — TRT formatidagi 17kp dan **2x sekin**

**2. Frame Differencing RTSP da zarar qiladi:**
- Real video: 60% skip → yaxshi ko'rinadi
- Real RTSP: ~10% skip → faqat CPU overhead → −27.9% FPS
- PT vs TRT pose bilan farq yo'q: 23.84 (PT) ≈ 23.82 (TRT) — bottleneck GPU emas

**3. RTSP FPS nega model FPS dan farq qiladi:**
- 33 FPS hard cap, alternating inference, RTSP ~8–9 FPS tarmoq limiti

---

### Bosqich 4 — Fall Detection Accuracy (10kp vs 17kp)

**Bug topildi va tuzatildi:** `tcn_fall.py` da 17kp → `[:10]` noto'g'ri edi (ko'z/quloq koordinatalari).
**To'g'ri remap:** COCO indekslaridan custom 10kp ga explicit mapping qilindi.

**Natijalar (UPFall dataset, Subject1):**

| Metric | 10kp | 17kp | Winner |
|--------|:----:|:----:|:------:|
| Accuracy | **99.21%** | 99.10% | 10kp |
| Fall F1 | **0.992** | 0.970 | **10kp** |
| Fall Recall | **1.000** | 0.980 | **10kp** |
| Pose FPS (TRT) | **209** | 200 | **10kp** |

10kp — ham tezroq, ham aniqroq. Sabab: TCN modeli aynan 10kp custom dataset bilan train qilingan.

---

## Yakuniy Natijalar — Config 3 (Optimal)

| Metric | Config 1 (baseline) | Config 3 (optimal) | Delta |
|--------|--------------------:|-------------------:|------:|
| Model size | 50.4 MB | **15.5 MB** | **−69%** |
| Dummy FPS | 96.5 | **116.7** | **+20.9%** |
| Video FPS | 80.7 | **101.4** | **+25.6%** |
| RTSP FPS | 33.03 | **34.33** | **+3.9%** |
| Fall Recall | 0.980 | **1.000** | **+2.0%** |

---

## Fayllar Xaritasi

| Fayl | Vazifa |
|------|--------|
| `monitor/YOLO/inference_utils.py` | Model yuklash priority list |
| `monitor/YOLO/streaming_manager.py` | `USE_FRAME_DIFFERENCING` toggle |
| `monitor/YOLO/tcn_fall.py` | 17kp bug fix (remap) |
| `monitor/YOLO/benchmark_pose_configs.py` | 4-config benchmark script |
| `run_fps_bench.py` | RTSP stream FPS benchmark |
| `export_10kp_engine.py` | 10kp TRT export |
| `docs/benchmark-pose-configs.md` | Barcha benchmark natijalari |
| `docs/fall-detection-accuracy.md` | Accuracy tahlili |
| `docs/final-benchmark-table.md` | Yakuniy jadval |
| `docs/model-comparison-table.md` | Model size/speed taqqos |

---

## Keyingi Qadamlar

- [ ] RTSP FPS ni bir necha kun qayta o'lchab o'rtacha olish (tarmoq o'zgaruvchan)
- [ ] Multi-subject accuracy evaluation (hozir faqat Subject1)
- [ ] Config 4 video FPS ni harakatsiz video bilan to'g'ri o'lchash
