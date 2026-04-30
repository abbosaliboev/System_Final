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

**Qilingan ishlar:**

| Fix | Muammo | Yechim |
|-----|--------|--------|
| P1 | `torch.cuda.synchronize()` har frame da → 1–10ms isrof | O'chirildi (YOLO o'zi sync qiladi) |
| P2 | Har frame uchun yangi `Thread()` yaratilardi | `ThreadPoolExecutor` — bir marta yaratib qayta ishlatish |
| P3 | `time.sleep(0.001)` unconditional | Faqat barcha queue bo'sh bo'lsa yield |
| P4 | `chunk_size=1` → 4 ta alohida process | `chunk_size=2` → 2 process, har biri 2 kamera |
| P5 | Frame queue o'lchamlari to'g'ri emas | Max-size-1 queue, faqat oxirgi frame saqlanadi |
| P6 | Har frame uchun danger zone DB so'rovi | 30 soniyada bir cache yangilanadi |
| P7 | `list.pop(0)` → O(N) TCN buffer | `deque(maxlen=30)` → O(1) |

**Natija:** 24.93 FPS → 34.55 FPS (+38.5%) — faqat kod, model o'zgarishsiz.

---

### Bosqich 2 — Unified Model Integratsiyasi

**Muammo:** `best_detect.engine` (42 MB) katta va sekin.

**Yangi model:** `unify-29march.engine` — pose-aware backbone bilan train qilingan, detect head. Faqat 7.9 MB (5x kichik).

**Natija:**

| Model | Size | PPE ms | Stream FPS (4 cam) |
|-------|------|--------|---------------------|
| `best_detect.engine` | 42 MB | 6.2 ms | 34.55 |
| `unify-29march.engine` | 7.9 MB | 4.7 ms | **49.12** |

**Umumiy taraqqiyot (Bosqich 1 + 2):** 24.93 → 49.12 FPS = **+97% (~2x)**

> ⚠️ Keyingi benchmarklarda 49.12 FPS qayta o'lchanmadi (RTSP sharoiti o'zgargan). Bu qiymat birinchi sessiyada olingan.

---

### Bosqich 3 — Pose Model Taqqoslash (5 Config)

**Savol:** Qaysi pose model kombinatsiyasi eng yaxshi?

| Config | PPE model | Pose model | Format |
|--------|-----------|------------|--------|
| A | best_detect.engine | best_pose.engine (17kp) | TRT+TRT |
| B | best_detect.engine | yolo11n-10kp.pt (10kp) | TRT+PT |
| C | unify-29march.engine | yolo11n-10kp.pt (10kp) | TRT+PT |
| D | unify-29march.engine | yolo11n-10kp.pt (10kp) + Frame Diff | TRT+PT |
| **E** | unify-29march.engine | **yolo11n-10kp.engine (10kp)** | **TRT+TRT** |

**Model Tezligi (dummy 640×640, 200 iter):**

| Config | PPE ms | Pose ms | Total ms | FPS | vs A |
|--------|--------|---------|----------|-----|------|
| A | 6.4 | 5.0 | 11.4 | 87.9 | — |
| B | 6.7 | 9.2 | 15.8 | 63.2 | -24.6 |
| C | 4.9 | 9.5 | 14.5 | 69.1 | -18.8 |
| D* | 4.8 | 8.0 | 12.8 | 78.4 | -9.5 |
| **E** | **5.0** | **4.8** | **9.8** | **102.4** | **+14.5** |

> \* Config D — dummy frame da 99.5% skip (harakatsiz), faqat 1 frame o'lchandi → bekor.

**Stream FPS (4 RTSP kamera, 60s window):**

| Config | cam1 | cam2 | cam3 | cam4 | Total | vs A |
|--------|------|------|------|------|-------|------|
| A | 8.60 | 8.31 | 8.23 | 7.88 | 33.03 | — |
| B | 8.56 | 8.21 | 8.22 | 7.80 | 32.79 | -0.7% |
| C | 8.81 | 8.40 | 8.09 | 7.79 | 33.09 | +0.2% |
| D | 6.30 | 6.30 | 5.65 | 5.60 | 23.84 | -27.8% |
| **E** | **8.76** | **8.71** | **8.44** | **8.42** | **34.33** | **+3.9%** |

**Asosiy kashfiyot:** Format (TRT vs PT) keypoint sonidan ko'ra muhimroq.

| Pose model | Format | Pose ms |
|------------|--------|---------|
| best_pose.engine (17kp) | TRT FP16 | 5.0 ms |
| yolo11n-10kp.pt (10kp) | PyTorch | 9.2–9.5 ms |
| yolo11n-10kp.engine (10kp) | TRT FP16 | **4.8 ms** |

**Nima uchun stream FPS farqi kichik (+3.9%)?**
3 ta sabab: (1) 33 FPS hard cap (`if now - last_frame_time < 0.03`), (2) Alternating inference (pose har 2-frame), (3) RTSP o'zi ~8-9 FPS beradi → GPU bottleneck emas, tarmoq bottleneck.

**Frame Differencing nima uchun zarar qiladi?**
Real RTSP da harakat (odam, yorug'lik o'zgarishi) doim bor → skip kamdan-kam → faqat CPU overhead qo'shadi → -27.8% FPS.

---

### Bosqich 4 — Fall Detection Accuracy (10kp vs 17kp)

**Bug topildi:** `tcn_fall.py` da 17kp keypoint lar noto'g'ri mapping qilingan edi.

```python
# XATO (avvalgi kod):
keypoints_xy = keypoints_xy[:10]  # COCO [:10] = nose+eyes+ears+shoulders+elbows → noto'g'ri!

# TO'G'RI (tuzatilgan):
# COCO 17kp → Custom 10kp to'g'ri remap:
# nose(0), l_sho(5), r_sho(6), l_elb(7), r_elb(8),
# l_wri(9), r_wri(10), l_hip(11), r_hip(12), neck((5+6)/2)
```

**Accuracy natijalari** (UPFall dataset, offline evaluation):

| Metric | 10kp model | 17kp (full_kp) model |
|--------|-----------|---------------------|
| **Accuracy** | **99.21%** | 99.10% |
| Normal — F1 | **0.992** | 0.990 |
| Fall — F1 | **0.992** | 0.970 |
| Fall — Precision | 0.984 | 0.950 |
| Fall — Recall | **1.000** | 0.980 |
| Test samples | 2,163 | 7,591 |
| Model FPS (TRT) | **209 FPS** | 200 FPS |

**Xulosa:** 10kp — ham tezroq (209 vs 200 FPS), ham aniqroq (F1: 0.992 vs 0.970).

**Nima uchun?**
- TCN modeli aynan 10kp uchun train qilingan (UPFall dataset, custom keypoints)
- 17kp da knees/ankles — fall detection uchun keraksiz "shovqin"
- 10kp da faqat kerakli keypoint'lar: shoulders, elbows, wrists, hips, neck

---

## Yakuniy Tanlov — Config E

**Hozirgi tizim (default):** `unify-29march.engine` + `yolo11n-10kp.engine`

```python
# backend/ai_factory/monitor/YOLO/inference_utils.py
ppe_model_paths = [
    ("monitor/YOLO/models/unify-29march.engine", 'detect'),   # ← ishlatiladi
    ("monitor/YOLO/models/unify-29march.pt",     'detect'),   # fallback
    ("monitor/YOLO/models/best_detect.engine",   'detect'),   # eski fallback
]
pose_model_paths = [
    ("monitor/YOLO/models/yolo11n-10kp.engine",  'pose'),     # ← ishlatiladi
    ("monitor/YOLO/models/yolo11n-10kp.pt",      'pose'),     # fallback
    ("monitor/YOLO/models/best_pose.engine",     'pose'),     # eski fallback
]
```

---

## Hamma Natijalarni Birgalikda

| Holat | Total FPS (4 cam) | vs Baseline |
|-------|-------------------|-------------|
| Baseline (eski kod + best_detect) | 24.93 | — |
| Optimized kod + best_detect | 34.55 | +38.5% |
| Optimized kod + unify.engine | ~49.12 | +97.0% |
| **Config E (unify + 10kp.engine)** | **34.33** | +37.7%* |

> \* 49.12 va 34.33 o'rtasidagi farq RTSP sharoiti o'zgarganidan — bu ikki o'lchov har xil kunda olingan. Model tezligi benchmark da Config E (102.4 FPS) Config A (87.9 FPS) dan +14.5 FPS yuqori.

---

## Fayllar Xaritasi

| Fayl | Vazifa |
|------|--------|
| `backend/ai_factory/monitor/YOLO/inference_utils.py` | Model yuklash (priority list) |
| `backend/ai_factory/monitor/YOLO/streaming_manager.py` | Asosiy inference loop |
| `backend/ai_factory/monitor/YOLO/tcn_fall.py` | Fall detection (17kp bug fix shu yerda) |
| `backend/ai_factory/monitor/YOLO/benchmark_pose_configs.py` | 5-config model benchmark |
| `backend/ai_factory/run_fps_bench.py` | Stream FPS benchmark |
| `backend/ai_factory/export_10kp_engine.py` | 10kp TRT export script |
| `C:/Users/dalab/Desktop/ali/2026_Fall_research/scripts/evaluate_yolo10kp.py` | 10kp accuracy evaluation |
| `C:/Users/dalab/Desktop/ali/2026_Fall_research/scripts/evaluate_full_kp.py` | 17kp accuracy evaluation |

---

## Keyingi Qadamlar (Agar Kerak Bo'lsa)

- [ ] Stream FPS ni bir necha kun qayta o'lchab o'rtacha olish (RTSP o'zgaruvchan)
- [ ] 17kp keypoint bug fix dan keyin 17kp accuracy ni qayta o'lchash
- [ ] Config D (frame differencing) ni real video bilan o'lchash (dummy bilan invalid)
- [ ] Multi-subject dataset bilan accuracy tekshirish (hozir faqat Subject1)
