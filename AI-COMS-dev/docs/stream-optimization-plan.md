# Stream Optimization Plan

Tahlil sanasi: 2026-03-29
Muammo: 4+ RTSP stream yuklanganda tizim qotadi (freeze).

---

## Muammolar ro'yhati (prioritet bo'yicha)

### P1 — `torch.cuda.synchronize()` har frame'da chaqiriladi
- **Fayl:** `backend/ai_factory/monitor/YOLO/streaming_manager.py`
- **Qatorlar:** 164, 181, 191
- **Muammo:** GPU inference tugashini kutib, CPU to'liq bloklanadi (1–10 ms/frame).
  YOLO `.predict()` o'zi ichida CUDA sync qiladi — ortiqcha sync kerak emas.
- **Ta'sir:** Katta. Har frame'da 1–10 ms yo'qoladi.
- **Holat:** ✅ Tuzatildi

---

### P2 — Har frame'da yangi `Thread` ob'ekti yaratiladi
- **Fayl:** `backend/ai_factory/monitor/YOLO/streaming_manager.py`
- **Qatorlar:** 158–163, 178–181, 188–191
- **Muammo:** `_run_parallel_inference`, `_run_ppe_only`, `_run_pose_only` har chaqirilganda
  yangi `Thread()` yaratib, start/join qiladi. Thread yaratish ~100–300 µs.
  4 stream × 33 FPS → ~264 thread/s faqat creation/destruction.
- **Yechim:** Bir marta `ThreadPoolExecutor(max_workers=2)` yaratib, frame'lar uchun qayta ishlatish.
  Parallel bo'lmagan holatlarda (`_run_ppe_only`, `_run_pose_only`) thread ishlatmaslik.
- **Ta'sir:** Katta.
- **Holat:** ✅ Tuzatildi

---

### P3 — Main inference loop ichida `time.sleep()` bor
- **Fayl:** `backend/ai_factory/monitor/YOLO/streaming_manager.py`
- **Qatorlar:** 84, 148, 151
- **Muammo:** Loop har iteratsiyada kamida `0.001 + 0.005 = 6 ms` uxlaydi,
  ish bo'lsa ham bo'lmasa ham. Bundan tashqari har bo'sh queue uchun ham `sleep(0.001)` bor.
- **Yechim:** Sleeplarni olib tashlash; faqat hamma queue bo'sh bo'lganda `sleep(0.001)` qoldirish.
- **Ta'sir:** O'rta-katta.
- **Holat:** ✅ Tuzatildi

---

### P4 — `get_camera_zones()` har frame'da DB ga so'rov yuboradi
- **Fayl:** `backend/ai_factory/monitor/stream_views.py`
- **Qator:** 103
- **Muammo:** `generate_stream()` loopida har frame uchun `DangerZone.objects.filter()` chaqiriladi.
  4 kamera × 30 FPS = 120 ta DB query/s.
- **Yechim:** 30 soniyalik modul-darajadagi kesh qo'shish.
- **Ta'sir:** O'rta.
- **Holat:** ✅ Tuzatildi

---

### P5 — MJPEG streaming busy-wait
- **Fayl:** `backend/ai_factory/monitor/stream_views.py`
- **Qatorlar:** 94, 137
- **Muammo:** `if not frame_queues[cam_id].empty():` … `else: time.sleep(0.01)` — bu busy-wait pattern.
  Frame yo'q bo'lganda CPU vaqt sarflaydi, lekin hech narsa qilmaydi.
- **Yechim:** `queue.get(timeout=0.033)` — frame kelguncha bloklab turadi, CPU band bo'lmaydi.
- **Ta'sir:** O'rta.
- **Holat:** ✅ Tuzatildi

---

### P6 — Har kamera uchun alohida process: modellar 4x GPU RAM'da
- **Fayl:** `backend/ai_factory/monitor/camera_loader.py`
- **Qator:** 61
- **Muammo:** `chunk_size = 1` → 4 process, har biri `best_detect.engine` (42 MB) + pose model yuklaydi.
  GPU RAM: 4 × (42 + 9) MB = ~200 MB faqat model duplikatsiyasi.
  Stream soni ko'paysa GPU memory exhaustion tezlashadi.
- **Yechim:** `chunk_size = 2` → 2 process, har biri 2 ta kamera boshqaradi. GPU memory 2x kamaytirish.
- **Ta'sir:** Katta (scale qilganda muhim).
- **Holat:** ✅ Tuzatildi

---

### P7 — `tcn_fall.py` buffer: `list.pop(0)` O(N) operatsiya
- **Fayl:** `backend/ai_factory/monitor/YOLO/tcn_fall.py`
- **Qatorlar:** 150–151
- **Muammo:** `self.buffer[cam_id].pop(0)` — listdan boshidan elementni o'chirish O(N).
  30-frame buffer bilan har frame'da 30 ta shift operatsiyasi.
- **Yechim:** `collections.deque(maxlen=30)` — avtomatik eski elementni o'chiradi, O(1).
- **Ta'sir:** Kichik (lekin to'g'ri yozish).
- **Holat:** ✅ Tuzatildi

---

## Tuzatishlar tartibi

```
P1 → P2 → P3   (streaming_manager.py — bitta fayl, ketma-ket)
P4 → P5        (stream_views.py — bitta fayl)
P6             (camera_loader.py)
P7             (tcn_fall.py)
```

## Kutilayotgan natija

| Holatlar | Oldin | Keyin |
|----------|-------|-------|
| Frame latency (main loop) | 6 ms guaranteed | ~0 ms (faqat ish vaqti) |
| Thread creation/destruction | 264/s (4 cam) | 0 (pool qayta ishlatiladi) |
| GPU sync blocking | 1–10 ms/frame | Yo'q |
| DB queries (danger zones) | 120/s (4 cam) | ~0.13/s (30s cache) |
| GPU model copies | 4x | 2x |
| CPU busy-wait (MJPEG) | Doim | Faqat ish paytida |
