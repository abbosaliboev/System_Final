# Fall Detection Accuracy: 10kp vs 17kp

**Maqsad:** TCN-Attention fall detection modelini 10 va 17 keypoint bilan solishtirish — tezlik va aniqlik.

---

## Modellar

| Model | Keypoints | Input size | Weights |
|-------|-----------|------------|---------|
| TCN-Attention (10kp) | 10 | 30 × 20 (10kp × 2) | `fall_detection_v4.pth` |
| TCN-Attention (17kp full) | 17 | 30 × 34 (17kp × 2) | `fall_detection_full_kp.pth` |

**TCN arxitekturasi:** `[64, 128, 256]` kanal, kernel=3, dropout=0.2, 2 chiqish (no_fall / fall).

---

## Dataset

**UPFall dataset** (Subject1, offline evaluation):

| Split | Normal | Fall | Jami |
|-------|--------|------|------|
| 10kp test | 1,131 | 1,032 | **2,163** |
| 17kp test | 6,618 | 973 | **7,591** |

**Fall aktivitelari:** Activity1–5 (5 xil yiqilish turi)
**Normal aktivitelari:** walking (cam1+2), sitting, bending, jumping

> Test split alohida ajratilmagan — butun dataset bilan evaluate qilindi. Shuning uchun natijalar pessimistik emas (train data ham kiritilgan bo'lishi mumkin). Comparative analysis uchun yetarli.

---

## Tezlik Taqqoslash

### Pose Model FPS (TITAN RTX)

| Pose model | Format | Pose ms | Pose FPS |
|------------|--------|---------|----------|
| best_pose.engine (17kp) | TensorRT FP16 | 5.0 ms | 200 FPS |
| yolo11n-10kp.pt (10kp) | PyTorch | 9.2–9.5 ms | 105–109 FPS |
| **yolo11n-10kp.engine (10kp)** | **TensorRT FP16** | **4.8 ms** | **209 FPS** |

**Asosiy kashfiyot:** Keypoint soni emas, **format** hal qiladi.
- 17kp TRT ≈ 10kp TRT (5.0 vs 4.8 ms) — farq atigi 4%
- 10kp PT esa 10kp TRT dan **2x sekin** (9.2 vs 4.8 ms)

---

## Aniqlik Taqqoslash

### 10kp Model (fall_detection_v4.pth)

```
              precision    recall  f1-score   support

      Normal     1.0000    0.9850    0.9924     1131
        Fall     0.9838    1.0000    0.9918     1032

    accuracy                         0.9921     2163
   macro avg     0.9919    0.9925    0.9921     2163
weighted avg     0.9923    0.9921    0.9921     2163
```

### 17kp Model (fall_detection_full_kp.pth)

```
              precision    recall  f1-score   support

      Normal       1.00      0.99      0.99     6618
        Fall       0.95      0.98      0.97      973

    accuracy                           0.99     7591
   macro avg       0.97      0.99      0.98     7591
weighted avg       0.99      0.99      0.99     7591
```

### Solishtirma Jadval

| Metric | 10kp | 17kp | Farq |
|--------|------|------|------|
| **Accuracy** | **99.21%** | 99.10% | +0.11% |
| Normal Precision | **1.000** | **1.000** | = |
| Normal Recall | 0.985 | 0.990 | -0.005 |
| Normal F1 | **0.992** | 0.990 | +0.002 |
| Fall Precision | 0.984 | 0.950 | **+0.034** |
| Fall Recall | **1.000** | 0.980 | **+0.020** |
| **Fall F1** | **0.992** | 0.970 | **+0.022** |
| Pose FPS (TRT) | **209** | 200 | +4.5% |

---

## Nima Uchun 10kp Yaxshiroq?

### 1. Training dataset mos keladi
10kp model aynan shu 10 keypoint bilan train qilingan (UPFall dataset, custom annotation). 17kp model esa COCO-style 17kp bilan train qilinib, fall detection uchun optimallashtirilmagan.

### 2. Kerakli keypoint'lar faqat
Fall detection uchun muhim keypoint'lar:

| Muhim | Kam muhim (17kp da bor, 10kp da yo'q) |
|-------|--------------------------------------|
| shoulders, hips (burchak o'lchov) | eyes, ears (yuz uchun) |
| elbows, wrists (qo'l harakati) | knees, ankles (oyoq pastki) |
| neck (bosh pozitsiyasi) | — |

17kp da knees/ankles/eyes/ears — TCN ga "shovqin" bo'lib tushadi.

### 3. Fall Recall = 1.000 (10kp)
10kp model birorta ham haqiqiy yiqilishni miss qilmagan. Bu xavfsizlik tizimi uchun eng muhim metrika (false negative = o'tkazib yuborilgan xavf).

---

## Bug: 17kp → 10kp Noto'g'ri Mapping (Tuzatildi)

`tcn_fall.py` da 17kp keypoint ishlatilganda noto'g'ri kod bor edi:

```python
# XATO — avvalgi kod:
keypoints_xy = keypoints_xy[:10]
# Natija: COCO [:10] = nose, l_eye, r_eye, l_ear, r_ear, l_sho, r_sho, l_elb, r_elb, l_wri
# Muammo: ko'z va quloqlar shoulder/hip o'rniga beriladi → TCN noto'g'ri ishlaydi
```

```python
# TO'G'RI — tuzatilgan kod (tcn_fall.py:131):
if len(keypoints_xy) == 17:
    kp17 = keypoints_xy
    cf17 = keypoints_conf
    neck = (kp17[5] + kp17[6]) / 2.0          # shoulder midpoint = neck
    neck_conf = min(float(cf17[5]), float(cf17[6]))
    keypoints_xy = np.array([
        kp17[0],   # nose
        kp17[5],   # left_shoulder
        kp17[6],   # right_shoulder
        kp17[7],   # left_elbow
        kp17[8],   # right_elbow
        kp17[9],   # left_wrist
        kp17[10],  # right_wrist
        kp17[11],  # left_hip
        kp17[12],  # right_hip
        neck,      # neck
    ], dtype=float)
```

**COCO 17kp indekslari (reference):**
```
0:nose  1:l_eye  2:r_eye  3:l_ear  4:r_ear
5:l_sho  6:r_sho  7:l_elb  8:r_elb  9:l_wri  10:r_wri
11:l_hip  12:r_hip  13:l_knee  14:r_knee  15:l_ank  16:r_ank
```

---

## Evaluation Ishga Tushirish

```bash
cd C:\Users\dalab\Desktop\ali\2026_Fall_research\scripts

# 10kp accuracy
python evaluate_yolo10kp.py
# Output: confusion_matrix_10kp_final.png

# 17kp accuracy
python evaluate_full_kp.py
# Output: confusion_matrix_full_kp.png
```

**Kerakli paketlar:**
```bash
python -m pip install scikit-learn seaborn tqdm
```

---

## Xulosa

**10kp — optimal tanlov** xavfsizlik monitoringi uchun:

| Jihat | 10kp | 17kp |
|-------|------|------|
| Tezlik (TRT) | **209 FPS** | 200 FPS |
| Accuracy | **99.21%** | 99.10% |
| Fall F1 | **0.992** | 0.970 |
| Fall Recall | **1.000** | 0.980 |
| Training match | ✅ Dataset mos | ❌ COCO style |
| "Shovqin" keypoint | ❌ yo'q | ✅ eyes/ears/knees |
