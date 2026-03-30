# AI-COMS System FPS Benchmark

**Maqsad:** 4 ta RTSP kamera bilan real tizim FPS ni turli model va kod konfiguratsiyalarida o'lchash.

---

## Natijalar jadvali

### Single-Model Benchmark (dummy frames, 200 iter, TITAN RTX)

| # | Model | Format | Size | PPE ms | FPS |
|---|-------|--------|------|--------|-----|
| 1 | `best_detect.engine` | TensorRT FP16 | 42 MB | 6.2 ms | 69.3 |
| 2 | `best_detect.engine` | TensorRT FP16 | 42 MB | 6.2 ms | 69.3 |
| 3 | `unify-29march.engine` | TensorRT FP16 | 7.9 MB | 4.7 ms | 77.0 |
| 4 | `unify-29march.pt` | PyTorch | 5.2 MB | 9.6 ms | 56.6 |

### Real System Benchmark (4 RTSP cameras, 60s stable window)

| # | Model | Code state | cam1 | cam2 | cam3 | cam4 | Total FPS | Per-cam avg | vs Config 1 |
|---|-------|-----------|------|------|------|------|-----------|-------------|-------------|
| 1 | `best_detect.engine` | **Before** optimization | 6.23 | 6.23 | 6.23 | 6.23 | **24.93** | 6.23 | — |
| 2 | `best_detect.engine` | **After** optimization | 8.70 (+39.6%) | 8.80 (+41.3%) | 8.50 (+36.4%) | 8.55 (+37.2%) | **34.55** | 8.64 | **+38.5%** |
| 3 | `unify-29march.engine` | **After** optimization | 12.19 (+95.7%) | 12.23 (+96.3%) | 12.18 (+95.5%) | 12.52 (+100.9%) | **49.12** | 12.28 | **+97.0%** |
| 4 | `unify-29march.pt` | **After** optimization | 8.82 (+41.6%) | 8.62 (+38.4%) | 8.60 (+38.0%) | 8.72 (+39.9%) | **34.76** | 8.69 | **+39.4%** |

> Config 1 per-cam qiymatlari: 24.93 / 4 = 6.23 FPS (teng taqsimlangan)

### Xulosa

| Solishtirish | Delta |
|---|---|
| Optimization only — same model (Config 2 vs 1) | +38.5% |
| New engine model — same optimized code (Config 3 vs 2) | +42.2% |
| **Full improvement: optimization + new model (Config 3 vs 1)** | **+97.0% (~2x)** |
| PT vs engine — same optimized code (Config 4 vs 2) | +0.6% (minimal farq) |

---

## Konfiguratsiyalar tafsiloti

### Config 1 — Before (baseline)
- **Model:** `best_detect.engine` (eski PPE model, TensorRT FP16, 42 MB)
- **Code:** optimizatsiyasiz (per-frame Thread, cuda.synchronize, sleep, busy-wait)
- **chunk_size:** 1 (4 process)
- **Natija:** 24.93 FPS total (real o'lchov, avval mavjud edi)

### Config 2 — After optimization, old model
- **Model:** `best_detect.engine`
- **Code:** to'liq optimizatsiya (P1–P7 barcha fix)
- **chunk_size:** 2 (2 process)
- **Natija:** 34.55 FPS total

### Config 3 — After optimization, new engine model
- **Model:** `unify-29march.engine` (yangi unified model, TensorRT FP16, 7.9 MB)
- **Code:** to'liq optimizatsiya
- **chunk_size:** 2 (2 process)
- **Natija:** 49.12 FPS total

### Config 4 — After optimization, PT format
- **Model:** `unify-29march.pt` (PyTorch format, 5.2 MB)
- **Code:** to'liq optimizatsiya
- **chunk_size:** 2 (2 process)
- **Natija:** 34.76 FPS total

---

## Qanday o'lchandi

### Metod

`[INF 60s]` log liniyasi — `state_manager.py` da har 60 soniyada bir chiqadi:

```
***** [INF 60s] Process-3 *****
  cam3:total=510  cam4:total=513
  cam3:fps=8.50  cam4:fps=8.55  |  ALL:total=1023 ALL:fps=17.04  |  elapsed=60.0s
```

- `cam3:fps` = 60 soniya ichida cam3 uchun inference qilingan frame soni / 60
- `ALL:fps` = ikki kamera yig'indisi (process darajasida)
- **System total FPS** = Process-2 ALL + Process-3 ALL (ikkinchi, barqaror window)
- Birinchi window ko'pincha kameralar ulanish bosqichida bo'ladi → ikkinchi window ishlatiladi

### Benchmark script

**Fayl:** `backend/ai_factory/run_fps_bench.py`

```bash
cd backend/ai_factory
python run_fps_bench.py
```

Script `start_all()` ni ishga tushiradi va 360 soniya kutadi.
Console outputida `[INF 60s]` liniyalarini qidiring.

> **Muhim:** Windows'da multiprocessing uchun `if __name__ == '__main__'` guard majburiy.
> Script to'g'ri yozilgan — to'g'ridan-to'g'ri `python run_fps_bench.py` ishlatsa bo'ladi.

### Model almashtirish

`inference_utils.py` dagi `load_models()` — priority list tartibida birinchi topilganni yuklaydi:

```python
# backend/ai_factory/monitor/YOLO/inference_utils.py
ppe_model_paths = [
    ("monitor/YOLO/models/unify-29march.engine", 'detect'),  # 1-chi
    ("monitor/YOLO/models/unify-29march.pt",     'detect'),  # 2-chi (fallback)
    ("monitor/YOLO/models/best_detect.engine",   'detect'),  # 3-chi (eski fallback)
]
```

Config 2 yoki 4 ni qayta o'lchash uchun:
1. `unify-29march.engine` va `unify-29march.pt` ni models/ papkasidan vaqtincha olib qo'ying
2. `run_fps_bench.py` ni ishga tushiring
3. Tugagach fayllarni qaytaring

### chunk_size o'zgartirish

```python
# backend/ai_factory/monitor/camera_loader.py
chunk_size = 2   # 2 kamera → 1 process (hozirgi)
# chunk_size = 1 → har kamera alohida process (Config 1 holat)
```

---

## Hardware

| Komponent | Ma'lumot |
|-----------|----------|
| GPU | NVIDIA TITAN RTX (24 GB VRAM) |
| CPU | Intel Core i9-10900X @ 3.70 GHz (20 thread) |
| RAM | 64 GB |
| OS | Windows 10 Pro |
| CUDA | 12.1 |
| TensorRT | 10.x |

---

## Fayl joylashuvi

| Fayl | Vazifa |
|------|--------|
| `backend/ai_factory/run_fps_bench.py` | System FPS benchmark script |
| `backend/ai_factory/monitor/YOLO/benchmark_models.py` | Single-model dummy benchmark |
| `backend/ai_factory/monitor/YOLO/inference_utils.py` | `load_models()` — model priority list |
| `backend/ai_factory/monitor/camera_loader.py` | `chunk_size`, `CAMERA_SOURCES` |
| `backend/ai_factory/monitor/YOLO/state_manager.py` | `[INF 60s]` log chiqaradi |
| `backend/ai_factory/monitor/YOLO/models/` | Model fayllari (.engine, .pt) |
