# AI-COMS Pose Configuration Benchmark

**Maqsad:** 4 ta model konfiguratsiyasini ikki jihatdan solishtirish:
1. **Model tezligi** — bitta frame uchun inference ms (benchmark script)
2. **End-to-end stream FPS** — real 4 RTSP kamera, 60s window (`[INF 60s]` log)

---

## 5 ta Konfiguratsiya

| Config | PPE model | Pose model | Keypoints | Frame Diff |
|--------|-----------|------------|-----------|------------|
| **A** | `best_detect.engine` (42 MB, TRT FP16) | `best_pose.engine` (17kp) | 17 | ✗ |
| **B** | `best_detect.engine` (42 MB, TRT FP16) | `yolo11n-10kp.pt` (10kp) | 10 | ✗ |
| **C** | `unify-29march.engine` (7.9 MB, TRT FP16) | `yolo11n-10kp.pt` (10kp) | 10 | ✗ |
| **D** | `unify-29march.engine` (7.9 MB, TRT FP16) | `yolo11n-10kp.pt` (10kp) | 10 | ✓ |
| **E** | `unify-29march.engine` (7.9 MB, TRT FP16) | `yolo11n-10kp.engine` (10kp, TRT) | 10 | ✗ |

---

## Model Tezligi Benchmark Natijalari

Ikki xil source bilan o'lchandi:

### A) Dummy frame (640×640 qora frame, 200 iter)

| Config | PPE ms | Pose ms | Total ms | FPS | vs A |
|--------|--------|---------|----------|-----|------|
| **A** | 6.4 ms | 5.0 ms | **11.4 ms** | **87.9** | — |
| **B** | 6.7 ms | 9.2 ms | **15.8 ms** | **63.2** | -24.6 |
| **C** | 4.9 ms | 9.5 ms | **14.5 ms** | **69.1** | -18.8 |
| **D** +FD | — | — | — | invalid* | — |
| **E** | 5.0 ms | 4.8 ms | **9.8 ms** | **102.4** | **+14.5** ✓ |

> \* Config D dummy da: 199/200 frame skip (99.5%) → faqat 1 frame o'lchandi → bekor.

### B) Real video (test2.mp4, 200 iter) — Config D uchun valid

| Config | PPE ms | Pose ms | Total ms | FPS | vs A | Skip |
|--------|--------|---------|----------|-----|------|------|
| **A** | 7.0 ms | 5.1 ms | **12.1 ms** | **82.8** | — | — |
| **B** | 7.0 ms | 7.7 ms | **14.7 ms** | **68.0** | -14.8 | — |
| **C** | 6.1 ms | 9.1 ms | **15.2 ms** | **65.8** | -17.0 | — |
| **D** +FD | 6.2 ms | 8.2 ms | **14.5 ms** | **69.2** | -13.6 | 120/200 (60%) |
| **E** | 5.4 ms | 5.1 ms | **10.5 ms** | **95.0** | **+12.2** ✓ | — |

> Config D real video da 60% frame skip → C dan tezroq (69.2 > 65.8 FPS).
> Lekin real RTSP da skip atigi 10–20% → stream FPS da -27.8% (pastga qarang).

### Asosiy Xulosa — Model Format > Keypoint Soni

| | best_pose.engine (17kp, TRT) | yolo11n-10kp.pt (10kp, PT) | yolo11n-10kp.engine (10kp, TRT) |
|--|--|--|--|
| Pose ms (real video) | 5.1 ms | 7.7–9.1 ms | **5.1 ms** |
| Format | TensorRT FP16 | PyTorch (PT) | TensorRT FP16 |

**Config E (unify + 10kp TRT) — eng tezkor**: 95.0 FPS (real video), 102.4 FPS (dummy). Ikkala model ham TensorRT → maksimal GPU samaradorligi.

---

## End-to-End Stream FPS (4 RTSP kamera, 60s window)

*(TO'LDIRILADI)*

| Config | cam1 | cam2 | cam3 | cam4 | Total FPS | Per-cam avg | vs A |
|--------|------|------|------|------|-----------|-------------|------|
| A: best_detect + 17kp engine | 8.60 | 8.31 | 8.23 | 7.88 | **33.03** | 8.26 | — |
| B: best_detect + 10kp pt | 8.56 | 8.21 | 8.22 | 7.80 | **32.79** | 8.20 | -0.7% |
| C: unify + 10kp pt | 8.81 | 8.40 | 8.09 | 7.79 | **33.09** | 8.27 | +0.2% |
| D: unify + 10kp pt + FD | 6.30 | 6.30 | 5.65 | 5.60 | **23.84** | 5.96 | -27.8% |
| E: unify + 10kp engine (TRT) | 8.76 | 8.71 | 8.44 | 8.42 | **34.33** | 8.58 | **+3.9%** |

> `[INF 60s]` 2nd (stable) window, real 4 RTSP kamera, TITAN RTX

### ⚠️ Config D — Frame Differencing real RTSP da zarar qiladi

Real kameralarda harakat (odam, yorug'lik) doim bor → skip kam → frame diff faqat CPU overhead qo'shadi → FPS -27.8%.

---

## 10kp vs 17kp Taqqoslash

### FPS farqi

| | 17kp (best_pose.engine, TRT) | 10kp (yolo11n-10kp.pt, PT) | Farq |
|--|------------------------------|----------------------------|------|
| Pose ms | **4.6 ms** | 8.6–9.2 ms | ~2x sekin |
| Pose FPS | **215 FPS** | 109–116 FPS | ~2x sekin |
| **Sabab** | TensorRT FP16 | PyTorch format | Format hal qiladi |

### Accuracy farqi (UPFall dataset, offline evaluation)

| Metric | 10kp model | 17kp model | Farq |
|--------|-----------|------------|------|
| **Accuracy** | **99.21%** | 99.10% | +0.11% |
| Fall F1-score | **0.992** | 0.970 | **+0.022** |
| Fall Precision | 0.984 | 0.950 | +0.034 |
| Fall Recall | **1.000** | 0.980 | **+0.020** |
| Normal F1-score | **0.992** | 0.990 | +0.002 |

> To'liq natijalar: `docs/fall-detection-accuracy.md`

### Xulosa
- **10kp ham tezroq, ham aniqroq** — fall F1: 0.992 vs 0.970
- **Fall Recall = 1.000** (10kp) — birorta yiqilish o'tkazib yuborilmagan
- **10kp training dataset mos** — UPFall custom keypoints bilan train qilingan
- **17kp da keraksiz keypoint'lar** — eyes/ears/knees fall detection uchun "shovqin"
- **17kp universalroq** — boshqa pose task lar uchun (yugurish, o'tirish tahlili)

---

## Frame Differencing Ta'siri

Frame differencing harakatsiz (static) frame larni aniqlaydi va inference ni skip qiladi.

| Holat | Inference | FPS ta'siri |
|-------|-----------|-------------|
| Harakat bor | To'liq PPE + Pose | Normal |
| Harakat yo'q (static scene) | Skip — cached natija qaytariladi | +X% (skip % ga bog'liq) |

**Muhim:** Frame differencing dummy (qora) frame bilan sinovda ko'p skip qiladi (o'zgarish yo'q). Real RTSP da skip % kamroq bo'ladi.

---

## Benchmark Ishga Tushirish

### Model tezligi (bitta frame)

```bash
cd backend/ai_factory

# Dummy frame bilan (tez, GPU tezligini o'lchaydi)
python -m monitor.YOLO.benchmark_pose_configs

# Video fayl bilan (real frame)
python -m monitor.YOLO.benchmark_pose_configs --video monitor/videos/test.mp4

# Frame soni o'zgartirish
python -m monitor.YOLO.benchmark_pose_configs --frames 300
```

### End-to-end stream FPS

Model almashtirish uchun `inference_utils.py` dagi priority list tartibini o'zgartiring:

**Config A — best_detect + 17kp:**
```python
# inference_utils.py
ppe_model_paths = [
    ("monitor/YOLO/models/best_detect.engine", 'detect'),
    ...
]
pose_model_paths = [
    ("monitor/YOLO/models/best_pose.engine", 'pose'),
    ("monitor/YOLO/models/yolo11n-pose.pt",  'pose'),
    ...
]
```

**Config B — best_detect + 10kp:**
```python
ppe_model_paths = [
    ("monitor/YOLO/models/best_detect.engine", 'detect'),
    ...
]
pose_model_paths = [
    ("monitor/YOLO/models/yolo11n-10kp.pt", 'pose'),
    ...
]
```

**Config C — unify + 10kp (default/hozirgi):**
```python
ppe_model_paths = [
    ("monitor/YOLO/models/unify-29march.engine", 'detect'),
    ...
]
pose_model_paths = [
    ("monitor/YOLO/models/yolo11n-10kp.pt", 'pose'),
    ...
]
```

**Config D — unify + 10kp + frame diff:**
```python
# streaming_manager.py da frame differencing integratsiya qilinadi
# (hozircha streaming_manager.py ga qo'lda qo'shiladi)
```

Stream FPS o'lchash:
```bash
cd backend/ai_factory
python run_fps_bench.py
# Console da [INF 60s] liniyalarini kuting (60–180 soniya)
```

---

## Fayl joylashuvi

| Fayl | Vazifa |
|------|--------|
| `backend/ai_factory/monitor/YOLO/benchmark_pose_configs.py` | Model tezligi benchmark (4 config) |
| `backend/ai_factory/monitor/frame_differencing.py` | Frame diff funksiyasi |
| `backend/ai_factory/monitor/YOLO/inference_utils.py` | `load_models()` — model priority list |
| `backend/ai_factory/run_fps_bench.py` | Stream FPS benchmark |
| `backend/ai_factory/monitor/YOLO/state_manager.py` | `[INF 60s]` log chiqaradi |

---

## Hardware

| Komponent | Ma'lumot |
|-----------|----------|
| GPU | NVIDIA TITAN RTX (24 GB VRAM) |
| CPU | Intel Core i9-10900X @ 3.70 GHz (20 thread) |
| RAM | 64 GB |
| CUDA | 12.1 |
| TensorRT | 10.x |
