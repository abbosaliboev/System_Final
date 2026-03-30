# Unified Shared-Backbone Model — Integratsiya

Sana: 2026-03-29

---

## Model arxitekturasi (inspect natijalari)

```
fayl   : monitor/YOLO/models/unify-29march.pt
hajm   : 5.2 MB
task   : detect
nc     : 3  (0=helmet, 1=vest, 2=head)
head   : Detect  (faqat detection head)
kpt    : yo'q  (keypoint head mavjud emas)
```

### "Shared backbone" nima degani?

Trening jarayoni (multitask_training_info.yaml asosida):

```
1. pose_pretrain  [SKIPPED — tayyor model ishlatildi]
      ↓  yolo11n-10kp.pt ning backbone weightlari olingan
2. detection_finetuning  [50 epoch, backbone frozen=True]
      ↓  PPE detection head qo'shildi va trein qilindi
      ↓  backbone esa muzlatilgan holda saqlandi
      =  unify-29march.pt
```

Backbone `yolo11n-10kp.pt` pose modelidan initialize qilingan.
Bu degani backbone inson vujudini, qo'l-oyoqlarni, bosh holatini tushunadigan
feature'larni allaqachon biladi. Shu feature'lar PPE (helmet/vest/head) ni
tanishda ham ishlaydi — helmet boshga, vest vujudga nisbatan aniqlanadi.

**Ammo**: Final modelda Pose head yo'q. Faqat Detect head bor.
Model bitta `.predict()` chaqiruvida faqat PPE box'larini qaytaradi.

---

## Qaysi model nima uchun ishlatiladi (integratsiyadan keyin)

| Vazifa | Model | Format | Hajm |
|--------|-------|--------|------|
| PPE detection (helmet/vest/head) | `unify-29march.pt` | PyTorch `.pt` | 5.2 MB |
| Pose estimation (10 keypoint) | `yolo11n-10kp.pt` | PyTorch `.pt` | 5.1 MB |
| Fall detection | `fall_detection_v4.pth` | TCN-Attention | 1.5 MB |

Eski `best_detect.engine` (TensorRT, 42 MB) o'rnini `unify-29march.pt` egallaydi.

---

## O'zgartirilgan fayl

### `monitor/YOLO/inference_utils.py` — `load_models()`

**Oldin:**
```python
ppe_model = YOLO("monitor/YOLO/models/best_detect.engine", task='detect')
```

**Keyin:**
```python
# Priority 1: unified shared-backbone model
# Priority 2: best_detect.engine (TensorRT fallback)
ppe_model_paths = [
    ("monitor/YOLO/models/unify-29march.pt",   'detect'),
    ("monitor/YOLO/models/best_detect.engine", 'detect'),
]
```

Fallback mexanizmi qoldi — agar `unify-29march.pt` yuklanmasa, eski TensorRT model ishlatiladi.

---

## Haqiqiy benchmark natijalari (TITAN RTX, dummy 640×640, 200 frame)

| Model | Format | Hajm | PPE ms | Total ms | **FPS** |
|-------|--------|------|--------|----------|---------|
| `unify-29march.engine` | TensorRT FP16 | **7.8 MB** | **4.6 ms** | **12.8 ms** | **🏆 78.0** |
| `best_detect.engine` | TensorRT FP16 | 42 MB | 5.9 ms | 14.0 ms | 71.5 |
| `unify-29march.pt` | PyTorch | 5.2 MB | 9.9 ms | 18.2 ms | 54.9 |

**Natija**: `unify-29march.engine` eng tezkor — `best_detect.engine`'dan 1.3 ms (9%) tezroq.
Model kichik (7.8 MB) bo'lgani uchun memory bandwidth kamroq sarflanadi.

### 4 kameradagi taxminiy FPS (hozirgi 13.8 FPS asosida)

| Model | Taxminiy 4-cam FPS | O'zgarish |
|-------|--------------------|-----------|
| `best_detect.engine` (hozirgi) | 13.8 FPS | — |
| `unify-29march.engine` | ~**15.1 FPS** | +~9% |
| `unify-29march.pt` | ~10.6 FPS | −23% |

---

## Tezlikni o'lchash

### Dummy frame bilan (RTSP yo'q holda):
```bash
cd backend/ai_factory
python -m monitor.YOLO.benchmark_models
```

### Video fayl bilan:
```bash
python -m monitor.YOLO.benchmark_models --video monitor/videos/test1.mp4
```

### Haqiqiy RTSP stream bilan:
```bash
python -m monitor.YOLO.benchmark_models --rtsp "rtsp://admin:dalab%24123@10.198.137.226:554/stream1"
```

### Natija ko'rinishi:
```
============================================================
  AI-COMS Model Benchmark
  Source  : RTSP: rtsp://...
  Frames  : 200
  Device  : CUDA
============================================================

  ┌── unify-29march.pt  (shared-backbone, PT)
  │  PPE  inference:   14.2 ms avg  (min 12.1  max 28.3  p95 19.5)  → 70.4 FPS
  │  Pose inference:   11.8 ms avg  ...                             → 84.7 FPS
  │  TOTAL/frame   :   26.0 ms avg  → 38.5 FPS
  └── frames measured: 200

  ┌── best_detect.engine (TensorRT)
  │  PPE  inference:    7.3 ms avg  ...                             → 136.9 FPS
  │  Pose inference:   11.8 ms avg  ...                             → 84.7 FPS
  │  TOTAL/frame   :   19.1 ms avg  → 52.4 FPS
  └── frames measured: 200

COMPARISON SUMMARY
  PPE  latency diff : +6.9 ms  (engine faster)
  Total latency diff: +6.9 ms  (engine faster)
```
*(Yuqoridagi raqamlar taxminiy — haqiqiy natija hardwaredan farq qiladi)*

---

## unify-29march.pt ni TensorRT'ga export qilish (ixtiyoriy)

Agar `unify-29march.pt` ning tezligini oshirish kerak bo'lsa:

```bash
cd backend/ai_factory

# FP16 TensorRT export (tavsiya etilgan)
python -c "
from ultralytics import YOLO
model = YOLO('monitor/YOLO/models/unify-29march.pt')
model.export(format='engine', half=True, imgsz=640, device=0)
# Natija: monitor/YOLO/models/unify-29march.engine
"
```

Export tugagach `inference_utils.py` da path ni yangilash:
```python
("monitor/YOLO/models/unify-29march.engine", 'detect'),  # TensorRT
("monitor/YOLO/models/unify-29march.pt",     'detect'),  # PT fallback
```

> Export ~5-10 daqiqa ketadi. Har safar GPU o'zgarganda qayta export qilish kerak.

---

## Kelajakda: haqiqiy multi-task output

Agar kelajakda modelni shu tarzda train qilsangiz, bitta `.predict()` da ham box ham keypoint chiqarishi mumkin:

```yaml
# Ultralytics multi-task (Detect + Pose bir vaqtda)
nc: 3
kpt_shape: [10, 3]
head:
  - ...
  - [[16, 19, 22], 1, Pose, [nc, kpt_shape]]   # PPE box + 10kp bir headda
```

Bu holda `r.boxes` (helmet/vest/head) va `r.keypoints` (10kp) bir vaqtda keladi,
ikkita model o'rniga bitta model ishlaydi — inference ~2x tezlashadi.

---

## Qaysi fayllar o'zgartirildi

| Fayl | O'zgarish |
|------|-----------|
| `monitor/YOLO/inference_utils.py` | `load_models()` — unify model priority 1 |
| `monitor/YOLO/benchmark_models.py` | **YANGI** — tezlik benchmark script |
