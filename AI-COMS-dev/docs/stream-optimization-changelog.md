# Stream Optimization — O'zgarishlar tarixi

Sana: 2026-03-29
Muhandis: Claude Code (Sonnet 4.6)
Maqsad: 4+ RTSP stream yuklanganda tizim qotishini bartaraf etish.

---

## P1 — `torch.cuda.synchronize()` olib tashlandi

### Fayl
`backend/ai_factory/monitor/YOLO/streaming_manager.py`

### Qanday edi
```python
# _run_parallel_inference (164-qator)
t_ppe.join()
t_pose.join()
torch.cuda.synchronize()   # ← har frame'da GPU to'liq bloklandi

# _run_ppe_only (181-qator)
t_ppe.join()
torch.cuda.synchronize()   # ← xuddi shunday

# _run_pose_only (191-qator)
t_pose.join()
torch.cuda.synchronize()   # ← xuddi shunday
```

### Nimaga o'zgartirildi
```python
f_ppe.result()   # wait for completion
f_pose.result()
# torch.cuda.synchronize() — OLIB TASHLANDI
```

### Nima uchun bunday
`torch.cuda.synchronize()` barcha GPU operatsiyalari tugaguncha CPU-ni to'liq bloklab turadi.
YOLO `.predict()` methodi o'z ichida CUDA sync qiladi — tashqaridan qo'shimcha sync keraksiz.
Natija: har frame'da 1–10 ms ortiqcha kutish yo'qoldi.

---

## P2 — Per-frame `Thread()` o'rniga `ThreadPoolExecutor`

### Fayl
`backend/ai_factory/monitor/YOLO/streaming_manager.py`

### Qanday edi
```python
# Har frame'da YANGI thread yaratilardi:
t_ppe = Thread(target=_run_ppe, args=(ppe_box, ppe_model, frame))
t_pose = Thread(target=_run_pose, args=(pose_box, pose_model, frame))
t_ppe.start()
t_pose.start()
t_ppe.join()
t_pose.join()
```

### Nimaga o'zgartirildi
```python
# Bir marta yaratiladi, har frame'da QAYTA ISHLATILADI:
executor = ThreadPoolExecutor(max_workers=2)   # camera_process() ichida bir marta

# Parallel inference:
f_ppe = executor.submit(_run_ppe, ppe_box, ppe_model, frame)
f_pose = executor.submit(_run_pose, pose_box, pose_model, frame)
f_ppe.result()
f_pose.result()

# Yagona inference (thread kerak emas — to'g'ridan-to'g'ri chaqiriladi):
_run_ppe_only:  _run_ppe(ppe_box, ppe_model, frame)   # thread yo'q
_run_pose_only: _run_pose(pose_box, pose_model, frame) # thread yo'q
```

### Nima uchun bunday
Python'da `Thread()` yaratish ~100–300 µs sarflaydi (OS-darajada resource allocatsiya).
4 kamera × 33 FPS = 264 ta thread yaratish/yo'q qilish har soniyada.
`ThreadPoolExecutor` threadlarni oldindan yaratib, qayta ishlatadi — creation overhead nolga tushadi.
Yagona inference (PPE yoki Pose alohida) uchun thread umuman kerak emas — bevosita chaqiruv tezroq.

---

## P3 — Main inference loop ichidagi `time.sleep()` olib tashlandi

### Fayl
`backend/ai_factory/monitor/YOLO/streaming_manager.py`

### Qanday edi
```python
while True:
    for cam in cam_list:
        if q is None or q.empty():
            time.sleep(0.001)   # ← har bo'sh queue uchun 1ms
            continue
        ...

    time.sleep(0.001)           # ← loop oxirida har doim
    state.log_fps()
    state.log_minute_counts()
    time.sleep(0.005)           # ← yana 5ms
```
Jami: loop har iteratsiyada **kamida 6 ms** uxlardi — ish bo'lsa ham, bo'lmasa ham.

### Nimaga o'zgartirildi
```python
while True:
    any_frame = False
    for cam in cam_list:
        if q is None or q.empty():
            continue            # sleep yo'q
        ...
        any_frame = True
        ...

    if not any_frame:
        time.sleep(0.001)       # faqat hamma queue bo'sh bo'lganda
    state.log_fps()
    state.log_minute_counts()
```

### Nima uchun bunday
Agar kamida bitta kamerada frame bor bo'lsa, loop hech kutmasdan ishlashi kerak.
Faqat haqiqatdan hamma queue bo'sh bo'lganda (kameralar ulanmagan yoki lag qilgan payt) CPU-ni bo'shatish uchun `sleep(0.001)` qoldirildi.
Natija: ish yuklanganda `6 ms` artifisial latency to'liq yo'qoldi.

---

## P4 — Danger zone DB query har 30 soniyada bir marta

### Fayl
`backend/ai_factory/monitor/stream_views.py`

### Qanday edi
```python
def generate_stream(cam_id):
    while True:
        ...
        danger_zones = get_camera_zones(cam_id)   # ← har frame'da DB ga so'rov!
        ...

def get_camera_zones(cam_id):
    zones = DangerZone.objects.filter(camera_id=cam_num)   # har safar SQL
    return [zone.points for zone in zones]
```
4 kamera × 30 FPS = **120 ta SQL query/s** faqat danger zone uchun.

### Nimaga o'zgartirildi
```python
# Modul darajasida kesh:
_zone_cache = {}
_zone_cache_ts = {}
_ZONE_CACHE_TTL = 30.0  # soniya

def get_camera_zones(cam_id):
    now_ts = time.monotonic()
    if cam_id in _zone_cache and now_ts - _zone_cache_ts.get(cam_id, 0) < _ZONE_CACHE_TTL:
        return _zone_cache[cam_id]   # DB ga bormaydi
    # ... DB dan o'qiydi va keshga saqlaydi
```

### Nima uchun bunday
Danger zone'lar tez-tez o'zgarmaydi — foydalanuvchi qo'lda qo'shadi/o'chiradi.
30 soniyalik kesh ma'lumotni doimo yangi saqlaydi, lekin SQL query sonini
**120/s → 0.13/s** ga tushiradi (har 30s da 4 ta query).

---

## P5 — MJPEG streaming busy-wait bartaraf etildi

### Fayl
`backend/ai_factory/monitor/stream_views.py`

### Qanday edi
```python
def generate_stream(cam_id):
    while True:
        if not frame_queues[cam_id].empty():     # ← bo'sh tekshiruv
            frame = frame_queues[cam_id].get()   # ← so'ng get
            ...
        else:
            time.sleep(0.01)                     # ← 10ms kutish, CPU band
```
Bu **busy-wait** pattern — frame yo'q paytda CPU doimo `empty()` tekshirib turadi.

### Nimaga o'zgartirildi
```python
def generate_stream(cam_id):
    while True:
        try:
            frame = frame_queues[cam_id].get(timeout=0.033)   # ← bloklovchi get
            ...
        except Exception:
            continue
```

### Nima uchun bunday
`queue.get(timeout=N)` — frame kelguncha thread bloklanadi, CPU bo'sh qoladi.
`empty()` + `sleep()` kombinatsiyasi esa CPU-ni keraksiz band qilardi.
`timeout=0.033` (33 ms ≈ 30 FPS) — agar frame kelmasa, loop davom etadi.
Race condition ham yo'qoldi: eski kodda `empty()` True qaytarib, `get()` ga yetmasdan
boshqa thread frame-ni olib ketishi mumkin edi (TOCTOU muammo).

---

## P6 — `chunk_size` 1 dan 2 ga o'zgartirildi

### Fayl
`backend/ai_factory/monitor/camera_loader.py`

### Qanday edi
```python
chunk_size = 1   # 4 kamera = 4 process = modellar 4x GPU RAM'da
```
Har process `best_detect.engine` (42 MB) + `best_pose.engine` (9 MB) yuklardi.
4 process × 51 MB = ~**204 MB** faqat model duplikatsiyasi.

### Nimaga o'zgartirildi
```python
chunk_size = 2   # 4 kamera = 2 process = modellar 2x GPU RAM'da
```

### Nima uchun bunday
Modellar bir process ichida bir marta yuklanadi va shu process ichidagi barcha
kameralarda qayta ishlatiladi. `chunk_size=2` bilan:
- GPU model memory: 204 MB → **~102 MB** (2x kamaytirish)
- OS process soni: 4 → 2 (IPC overhead kamaytirish)
- Har process 2 ta kamerani bir xil model bilan boshqaradi — qo'shimcha overhead yo'q.

> **Eslatma:** Agar 8+ kamera bo'lsa, `chunk_size=3` yoki `chunk_size=4` ham ko'rib chiqilishi mumkin.

---

## P7 — `tcn_fall.py` buffer: `list.pop(0)` → `deque(maxlen=30)`

### Fayl
`backend/ai_factory/monitor/YOLO/tcn_fall.py`

### Qanday edi
```python
self.buffer = {}   # cam_id -> list

# Har frame'da:
self.buffer[cam_id].append(flat)
if len(self.buffer[cam_id]) > self.sequence_length:
    self.buffer[cam_id].pop(0)   # ← O(N) — 30 ta elementni siljitadi
```

### Nimaga o'zgartirildi
```python
from collections import deque

self.buffer = {}   # cam_id -> deque(maxlen=30)

# Har frame'da:
if cam_id not in self.buffer:
    self.buffer[cam_id] = deque(maxlen=self.sequence_length)
self.buffer[cam_id].append(flat)   # O(1) — deque avtomatik eski elementni o'chiradi
# pop(0) KERAK EMAS
```

### Nima uchun bunday
`list.pop(0)` — listning barcha elementlarini bir o'rincha siljitadi (O(N) = 30 operatsiya).
`collections.deque(maxlen=N)` — maxsize to'lganda yangi element qo'shilsa, eng eski avtomatik o'chadi (O(1)).
Har frame'da fall detector chaqiriladi, ya'ni bu optimallashtirish ham har frame'da ishlaydi.

---

## Umumiy natija

| Ko'rsatkich | Oldin | Keyin |
|-------------|-------|-------|
| Main loop minimal latency | 6 ms (har doim) | ~0 ms (faqat ish vaqti) |
| Thread yaratish/s (4 cam) | ~264 | 0 |
| GPU sync blocking/frame | 1–10 ms | Yo'q |
| Danger zone SQL query/s | 120 | ~0.13 |
| GPU model copies | 4× | 2× |
| MJPEG CPU busy-wait | Doim | Yo'q (bloklovchi get) |
| tcn_fall buffer pop | O(N)=30 ops | O(1) |

### Qaysi fayllar o'zgardi
| Fayl | O'zgarishlar |
|------|-------------|
| `monitor/YOLO/streaming_manager.py` | P1, P2, P3 |
| `monitor/stream_views.py` | P4, P5 |
| `monitor/camera_loader.py` | P6 |
| `monitor/YOLO/tcn_fall.py` | P7 |
