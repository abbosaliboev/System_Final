# MVTIN PPT — Slide Content

---

## Slide 1 — The Problem

**Title:** Current Fall Detection Methods Are Broken

**Content:**
- Need 1000+ labeled falls to train → expensive, incomplete
- Single camera → blind spots, occlusion
- Real falls are diverse and unpredictable

---

## Slide 2 — Key Insight: Falls Break Physics

**Title:** Normal Motion is Reversible. Falls Are Not.

**Content:**
- Walking forward → reverse → still looks normal
- Falling → reverse → physically impossible
- This is a law of nature, not a learned pattern

---

## Slide 3 — Idea 1: Temporal Irreversibility Score

**Title:** Train on Normal. Detect the Abnormal.

**Content:**
- Forward predictor: what comes next? → always low error
- Backward predictor: what came before? → HIGH error during fall
- **I-Score = backward error − forward error**
- No fall labels needed during pretraining

---

## Slide 4 — Why It Works

**Title:** The Score Separates Falls from Normal Automatically

**Content:**
- Normal motion → I-Score ≈ 0
- Fall motion → I-Score >> 0
- Threshold θ separates the two distributions
- Zero labeled falls required

---

## Slide 5 — Idea 2: Multi-Camera Problem

**Title:** One Camera Is Never Enough

**Content:**
- 4 cameras, same person, different angles
- Any camera can be blocked by shelf, machine, or person
- Naive average of scores = wrong (polluted by occluded camera)
- Which camera to trust?

---

## Slide 6 — Solution: Cross-View Attention

**Title:** Let the Network Decide Which Camera to Trust

**Content:**
- Each camera → own I-Score + visibility confidence
- Visibility = average keypoint confidence from pose detector
- Cross-view attention: clear view → higher weight
- Occluded camera → automatically down-weighted

---

## Slide 7 — Full Architecture: MVTIN

**Title:** Multi-View Temporal Irreversibility Network

**Content:**
```
cam1 → [Encoder] → [Fwd/Bwd] → I-score¹ ─┐
cam2 → [Encoder] → [Fwd/Bwd] → I-score² ─┤→ [Cross-View Attn] → FALL / SAFE
cam3 → [Encoder] → [Fwd/Bwd] → I-score³ ─┘

Shared encoder weights → view-agnostic representation
```

---

## Slide 8 — What Makes This New

**Title:** Nobody Has Done This

**Content:**

| | TCNTE | ST-GCN | **MVTIN** |
|---|:---:|:---:|:---:|
| Fall labels needed | 1000+ | 800+ | **0** |
| Multi-camera | ✗ | ✗ | ✓ |
| Physics-based | ✗ | ✗ | ✓ |
| Open-set falls | ✗ | ✗ | ✓ |

---

## Slide 9 — Validation Plan

**Title:** How We Prove It Works

**Content:**
- **Day 1 test:** Plot I-Score for falls vs normal on UPFall → are they separable?
- **Zero-shot:** UPFall, UR-Fall, Le2i — no labeled falls
- **Few-shot:** 5 / 10 / 50 examples vs TCNTE (1000+)
- **Occlusion test:** Block 1–2 cameras → measure accuracy drop

---

## Slide 10 — One Sentence Summary

**Title:** MVTIN in One Sentence

**Content:**

> *"MVTIN detects falls by measuring how impossible it is*
> *to reverse the observed motion —*
> *no fall labels needed, no single camera dependency."*

---
---

# MVTIN PPT — Slayd Mazmuni (O'zbek tilida)

---

## Slayd 1 — Muammo

**Sarlavha:** Hozirgi Yiqilishni Aniqlash Usullari Ishlamaydi

**Mazmun:**
- Modelni o'qitish uchun 1000+ belgilangan yiqilish kerak → qimmat, to'liq emas
- Bitta kamera → ko'r nuqtalar, to'siq
- Haqiqiy yiqilishlar xilma-xil va oldindan aytib bo'lmaydi

---

## Slayd 2 — Asosiy G'oya: Yiqilish Fizikani Buzadi

**Sarlavha:** Oddiy Harakat Qaytariladigan. Yiqilish Emas.

**Mazmun:**
- Oldinga yurish → teskari → baribir normal ko'rinadi
- Yiqilish → teskari → jismonan mumkin emas
- Bu tabiat qonuni, o'rganilgan naqsh emas

---

## Slayd 3 — G'oya 1: Vaqtinchalik Qaytarilmaslik Bahosi

**Sarlavha:** Normalda O'qit. G'ayritabiiyni Aniqa.

**Mazmun:**
- Oldinga prediktor: keyingi nima? → har doim kichik xato
- Orqaga prediktor: oldingi nima edi? → yiqilishda KATTA xato
- **I-Score = orqaga xatosi − oldinga xatosi**
- O'qitishda belgilangan yiqilish kerak emas

---

## Slayd 4 — Nima Uchun Ishlaydi

**Sarlavha:** Ball Yiqilishni Normaldan Avtomatik Ajratadi

**Mazmun:**
- Oddiy harakat → I-Score ≈ 0
- Yiqilish harakati → I-Score >> 0
- θ chegarasi ikki taqsimotni ajratadi
- Belgilangan yiqilish misollari talab qilinmaydi

---

## Slayd 5 — G'oya 2: Ko'p Kamera Muammosi

**Sarlavha:** Bitta Kamera Hech Qachon Yetarli Emas

**Mazmun:**
- 4 ta kamera, bir xil odam, turli burchaklar
- Istalgan kamera javon, mashina yoki odam tomonidan to'sib qo'yilishi mumkin
- Balllarning oddiy o'rtachasi = noto'g'ri (to'silgan kamera tomonidan buzilgan)
- Qaysi kameraga ishonish kerak?

---

## Slayd 6 — Yechim: Ko'p Ko'rinish Diqqati

**Sarlavha:** Tarmoq Qaysi Kameraga Ishonishni O'zi Hal Qilsin

**Mazmun:**
- Har bir kamera → o'z I-Score + ko'rinish ishonchi
- Ko'rinish = poza detektoridan o'rtacha kalit nuqta ishonchi
- Ko'p ko'rinish diqqati: aniq ko'rinish → yuqori og'irlik
- To'silgan kamera → avtomatik ravishda past og'irlik

---

## Slayd 7 — To'liq Arxitektura: MVTIN

**Sarlavha:** Ko'p Ko'rinishli Vaqtinchalik Qaytarilmaslik Tarmog'i

**Mazmun:**
```
kamera1 → [Encoder] → [Old/Orqa] → I-score¹ ─┐
kamera2 → [Encoder] → [Old/Orqa] → I-score² ─┤→ [Ko'p Ko'rinish Diqqati] → YIQILDI / XAVFSIZ
kamera3 → [Encoder] → [Old/Orqa] → I-score³ ─┘

Umumiy encoder og'irliklari → ko'rinishdan mustaqil vakillik
```

---

## Slayd 8 — Bu Nima Uchun Yangi

**Sarlavha:** Hech Kim Bu Ishni Qilmagan

**Mazmun:**

| | TCNTE | ST-GCN | **MVTIN** |
|---|:---:|:---:|:---:|
| Kerakli yiqilish belgilari | 1000+ | 800+ | **0** |
| Ko'p kamera | ✗ | ✗ | ✓ |
| Fizikaga asoslangan | ✗ | ✗ | ✓ |
| Yangi yiqilish turlari | ✗ | ✗ | ✓ |

---

## Slayd 9 — Tasdiqlash Rejasi

**Sarlavha:** Ishlashini Qanday Isbotlaymiz

**Mazmun:**
- **1-kun testi:** UPFall da yiqilish va normal uchun I-Score ni chiz → ajratiladimi?
- **Nol-shot:** UPFall, UR-Fall, Le2i — belgilangan yiqilishsiz
- **Kam-shot:** 5 / 10 / 50 misol vs TCNTE (1000+)
- **To'siq testi:** 1–2 kamerani to'sib qo'y → aniqlik pasayishini o'lcha

---

## Slayd 10 — Bir Jumlada Xulosa

**Sarlavha:** MVTIN Bir Jumlada

**Mazmun:**

> *"MVTIN yiqilishni kuzatilgan harakatni teskari qilishning*
> *qanchalik mumkin emasligini o'lchash orqali aniqlaydi —*
> *belgilangan misollar kerak emas, bitta kameraga bog'liqlik yo'q."*
