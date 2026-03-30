# AI-COMS System Optimization
## Presentation Content — PPT uchun

**Loyiha:** AI-COMS (AI-based Comprehensive Occupational Monitoring System)
**Tashkilot:** Data Analytics Lab, Chungbuk National University
**Sana:** 2026-03-29 / 30

---

---

# SLIDE 1 — Title

## AI-COMS: Real-Time Multi-Camera Safety Monitoring
### System Optimization & Unified Model Integration

**Data Analytics Lab — Chungbuk National University**
2026-03-29

---

---

# SLIDE 2 — Tizim haqida qisqacha

## AI-COMS nima?

Real-vaqt sanoat xavfsizligi monitoring tizimi — 4+ IP kamera orqali:

| Modul | Vazifa |
|-------|--------|
| PPE Detection | Helmet / Vest / Head (shlem yo'q) |
| Pose Estimation | 10 keypoint — inson holati |
| Fall Detection | TCN-Attention — yiqilish aniqlash |
| Danger Zone | Polygon zonalarda odam borligini kuzatish |

**Tech stack:** Django REST + React 19 + YOLOv11 + TensorRT + CUDA

---

---

# SLIDE 3 — Muammolar (Dastlabki holat)

## 4+ Stream yuklanganda tizim qotadi

4 ta RTSP kamera ishlaydi. Kamera soni oshganda FPS keskin tushadi va tizim qotib qoladi.

### Aniqlangan bottleneck'lar

| # | Muammo | Fayl | Og'irlik |
|---|--------|------|----------|
| P1 | `torch.cuda.synchronize()` har frame'da GPU bloklaydi | streaming_manager.py | Kritik |
| P2 | Har frame'da yangi `Thread()` yaratiladi | streaming_manager.py | Kritik |
| P3 | Main loop ichida `time.sleep(6ms)` — ish bo'lsa ham | streaming_manager.py | Yuqori |
| P4 | Danger zone DB query har frame'da — 120 query/s | stream_views.py | Yuqori |
| P5 | MJPEG streaming busy-wait (CPU doim band) | stream_views.py | O'rta |
| P6 | Har kamera alohida process: model 4x GPU RAM'da | camera_loader.py | O'rta |
| P7 | `list.pop(0)` O(N) buffer — fall detector | tcn_fall.py | Kichik |

---

---

# SLIDE 4 — P1: GPU Sync muammosi

## `torch.cuda.synchronize()` — Har frame'da GPU to'liq bloklanadi

### Oldin
```python
t_ppe.join()
t_pose.join()
torch.cuda.synchronize()   # ← 1–10 ms blok, har frame
```

### Keyin
```python
f_ppe.result()
f_pose.result()
# synchronize() — olib tashlandi
```

### Nima uchun?
YOLO `.predict()` o'z ichida CUDA sync qiladi. Qo'shimcha sync — keraksiz, faqat blok yaratadi.

| | Oldin | Keyin |
|--|-------|-------|
| GPU sync/frame | 1–10 ms | 0 ms |
| 4 cam × 30 FPS | 120–1200 ms/s yo'qotish | 0 |

---

---

# SLIDE 5 — P2: Thread Creation muammosi

## Har frame'da yangi `Thread()` — 264 ta/s overhead

### Oldin
```python
# Har frame'da yangi thread yaratiladi:
t_ppe  = Thread(target=_run_ppe, ...)   # ~150–300µs
t_pose = Thread(target=_run_pose, ...)  # ~150–300µs
t_ppe.start(); t_pose.start()
t_ppe.join(); t_pose.join()
```

### Keyin
```python
# Bir marta yaratiladi, qayta ishlatiladi:
executor = ThreadPoolExecutor(max_workers=2)  # process start'ida

f_ppe  = executor.submit(_run_ppe,  ...)
f_pose = executor.submit(_run_pose, ...)
f_ppe.result(); f_pose.result()
```

| | Oldin | Keyin |
|--|-------|-------|
| Thread yaratish/s (4 cam) | ~264 | 0 |
| Thread creation latency | 150–300 µs/frame | 0 |

---

---

# SLIDE 6 — P3, P4, P5: Boshqa optimizatsiyalar

## Loop, Database va Streaming tuzatishlari

### P3 — Main loop `sleep(6ms)` olib tashlandi
| | Oldin | Keyin |
|--|-------|-------|
| Loop minimal kutish | 6 ms (har doim) | 0 ms (faqat bo'sh paytda) |

```python
# Oldin: 3 ta sleep — doim
time.sleep(0.001)  ...  time.sleep(0.005)

# Keyin: faqat hamma queue bo'sh bo'lganda
if not any_frame:
    time.sleep(0.001)
```

### P4 — Danger Zone DB cache (30 soniya)
| | Oldin | Keyin |
|--|-------|-------|
| DB query/s (4 cam) | 120 | ~0.13 |

### P5 — MJPEG busy-wait → blocking `queue.get()`
| | Oldin | Keyin |
|--|-------|-------|
| CPU busy-wait | Doim (har frame) | Yo'q |

```python
# Oldin:  if not queue.empty(): ... else: sleep(0.01)
# Keyin:  frame = queue.get(timeout=0.033)
```

---

---

# SLIDE 7 — P6: GPU Memory Duplikatsiya

## `chunk_size=1` → `chunk_size=2`

### Oldin (chunk_size=1)
```
4 kamera → 4 ta alohida Process
Process-1: load unify.engine  (22 MB GPU)
Process-2: load unify.engine  (22 MB GPU)
Process-3: load unify.engine  (22 MB GPU)
Process-4: load unify.engine  (22 MB GPU)
Jami: ~88 MB faqat model uchun
```

### Keyin (chunk_size=2)
```
4 kamera → 2 ta Process
Process-1: load unify.engine (22 MB)  ← cam1 + cam2 shared
Process-2: load unify.engine (22 MB)  ← cam3 + cam4 shared
Jami: ~44 MB  (2x kamaytirish)
```

| | Oldin | Keyin |
|--|-------|-------|
| Process soni | 4 | 2 |
| GPU model copies | 4× | 2× |
| GPU model RAM | ~88 MB | ~44 MB |

---

---

# SLIDE 8 — Optimizatsiya umumiy natija

## Barcha tuzatishlar — Xulosa jadvali

| # | Muammo | Yechim | Fayl |
|---|--------|--------|------|
| P1 | `cuda.synchronize()` bloki | Olib tashlandi | streaming_manager.py |
| P2 | Per-frame thread yaratish | ThreadPoolExecutor | streaming_manager.py |
| P3 | Loop ichida 6ms sleep | Faqat bo'sh paytda | streaming_manager.py |
| P4 | DB query har frame | 30s cache | stream_views.py |
| P5 | Busy-wait polling | `queue.get(timeout=)` | stream_views.py |
| P6 | 4x GPU model kopi | chunk_size=2 | camera_loader.py |
| P7 | `list.pop(0)` O(N) | `deque(maxlen=30)` | tcn_fall.py |

### Taxminiy ta'sir

| Ko'rsatkich | Oldin | Keyin |
|-------------|-------|-------|
| Loop latency | 6 ms (majburiy) | ~0 ms |
| Thread yaratish/s | 264 | 0 |
| GPU sync bloklash | 1–10 ms/frame | Yo'q |
| Danger zone DB load | 120 query/s | 0.13 query/s |
| GPU model RAM | ~88 MB | ~44 MB |

---

---

# SLIDE 9 — Unified Shared-Backbone Model

## Yangi PPE modeli: `unify-29march.pt`

### Model arxitekturasi

```
Trening strategiyasi: Sequential Finetuning (Pose-first)

Bosqich 1: yolo11n-10kp.pt  (pose pre-trained backbone)
              ↓  backbone weights olinadi
Bosqich 2: Detection head qo'shildi + 50 epoch fine-tune
              ↓  backbone frozen (muzlatilgan)
              =  unify-29march.pt
```

### Model parametrlari

| Parametr | Qiymat |
|----------|--------|
| Base | YOLO11n |
| Task | Detect |
| Classes | 0=helmet, 1=vest, 2=head |
| Backbone | Pose-aware (yolo11n-10kp'dan) |
| Backbone epochs | Frozen during detection fine-tune |
| Detection epochs | 50 |
| Model hajmi (.pt) | 5.2 MB |

### Nima uchun shared backbone?
Backbone `yolo11n-10kp.pt` pose modelidan initialize — inson vujudini, qo'l-oyoq holatini allaqachon biladi. Shu feature'lar helmet/vest tanishda ham ishlaydi (helmet boshga, vest vujudga nisbatan).

---

---

# SLIDE 10 — Model TensorRT Export va Benchmark

## `unify-29march.pt` → `unify-29march.engine`

### Export
```bash
model.export(format='engine', half=True, imgsz=640, device=0)
# Natija: unify-29march.engine (7.8 MB, FP16 TensorRT)
# Export vaqti: ~4.3 daqiqa (TITAN RTX)
```

### Benchmark natijalari — TITAN RTX, 200 frame, dummy 640×640

| Model | Format | Hajm | PPE ms | Total ms | FPS |
|-------|--------|------|--------|----------|-----|
| **unify-29march.engine** | TensorRT FP16 | **7.8 MB** | **4.6 ms** | **12.8 ms** | **78.0** |
| best_detect.engine (eski) | TensorRT FP16 | 42 MB | 5.9 ms | 14.0 ms | 71.5 |
| unify-29march.pt | PyTorch | 5.2 MB | 9.9 ms | 18.2 ms | 54.9 |

### 4 kameradagi taxminiy FPS

| Model | 4-cam FPS | O'zgarish |
|-------|-----------|-----------|
| best_detect.engine (oldin) | 13.8 | — |
| **unify-29march.engine (keyin)** | **~15.1** | **+9%** |

> `unify-29march.engine` eski modeldan **1.3 ms tezroq (+9%)** — kichik hajm (7.8 MB vs 42 MB) sababli GPU memory bandwidth kamroq sarflanadi.

---

---

# SLIDE 11 — Fall Detection & Status Bar Tuzatishlari

## 2 ta kritik bug — Topildi va tuzatildi

### Bug 1 — Odam yo'q bo'lsa status sariq/qizil qolib ketadi

**Sabab:**
```
poses = []  →  _process_fall_detection chaqirilmaydi
            →  update_fall_state(is_fall=False) hech ishlamaydi
            →  fall_alerted = True   (abadiy saqlanib qoladi)
            →  Status: "Danger" / "Warning"  (xona bo'sh bo'lsa ham)
```

**Yechim:**
```python
if not poses:
    state.update_fall_state(cam_id, False, 0.0, now)  # reset
    fall_detector.buffer[cam_id].clear()               # buffer tozalanadi
```

### Bug 2 — Qorong'i xona / noise → yolg'on fall detection

**Sabab:** Pose model past yoritishda shovqinni "odam" deb topadi, keypoint confidence'lar juda past → TCN buffer garbage ma'lumot yig'adi → "fall" chiqaradi.

**Yechim — Keypoint confidence filtri:**
```python
if confs.mean() < 0.15:   # avg 15% dan past = haqiqiy odam emas
    continue              # fall detector'ga berilmaydi
```

| Holat | Oldin | Keyin |
|-------|-------|-------|
| Bo'sh xona, avval fall bo'lgan | Status: Danger/Warning | Status: Safe ✅ |
| Qorong'i xona, noise detection | Yolg'on fall alert | Ignore ✅ |
| `compute_status()` bo'sh xonada | Fall state tekshiriladi | Tekshirilmaydi ✅ |

---

---

# SLIDE 12 — Barcha o'zgartirilgan fayllar

## Qilingan ishlar — To'liq ro'yhat

| Fayl | O'zgarishlar | Kategoriya |
|------|-------------|------------|
| `monitor/YOLO/streaming_manager.py` | P1 (sync), P2 (thread pool), P3 (sleep), Bug1+2 fix | Optimization + Bugfix |
| `monitor/YOLO/visualization.py` | `compute_status()` — poses parametri | Bugfix |
| `monitor/YOLO/tcn_fall.py` | P7 — `deque` buffer | Optimization |
| `monitor/YOLO/inference_utils.py` | `load_models()` — unify model priority | Model Integration |
| `monitor/stream_views.py` | P4 (DB cache), P5 (blocking queue) | Optimization |
| `monitor/camera_loader.py` | P6 — `chunk_size=2` | Optimization |
| `monitor/YOLO/benchmark_models.py` | **Yangi** — tezlik benchmark script | New Tool |

### Yaratilgan dokumentatsiya

| Fayl | Tavsif |
|------|--------|
| `docs/stream-optimization-plan.md` | Muammolar va prioritet ro'yhat |
| `docs/stream-optimization-changelog.md` | Har o'zgarish: nima edi / nima bo'ldi / nima uchun |
| `docs/unified-model-integration.md` | Model arxitekturasi, benchmark, export yo'riqnomasi |
| `docs/presentation-aicoms-optimization.md` | Ushbu fayl (PPT kontenti) |
| `CLAUDE.md` | Loyiha uchun AI assistant yo'riqnomasi |

---

---

# SLIDE 13 — Xulosa

## Nima qildik?

### 1. Tizim optimizatsiyasi (7 ta bottleneck)
- GPU sync bloklashi yo'qoldi
- Thread pool — 264 thread/s → 0
- Loop latency 6ms → 0ms
- DB load 120 query/s → 0.13 query/s
- GPU model RAM 88 MB → 44 MB

### 2. Unified Shared-Backbone Model integratsiyasi
- Yangi model: pose-aware backbone + PPE detection head
- TensorRT export: 5.2 MB PT → 7.8 MB engine
- Eski modeldan 9% tezroq (78.0 vs 71.5 FPS)
- 4 kamerada: 13.8 → ~15.1 FPS (+1.3 FPS)

### 3. Bug tuzatishlari
- Bo'sh xonada status bar yashil bo'ladi
- Qorong'i xonada yolg'on fall detection bartaraf etildi

| Soha | Holat |
|------|-------|
| Stream optimization | ✅ 7 ta bottleneck tuzatildi |
| Model integration | ✅ unify-29march.engine ishga tushdi |
| Bug fixes | ✅ Status bar + fall detection |
| Documentation | ✅ 4 ta docs fayl yaratildi |

---

*AI-COMS — Data Analytics Lab, Chungbuk National University*
