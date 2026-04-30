# MVTIN PPT — Slide Content & Image Search Guide

---

## Slide 1 — The Problem

**Title:** Current Fall Detection Methods Are Broken

**Content:**
- Need 1000+ labeled falls to train → expensive, incomplete
- Single camera → blind spots, occlusion
- Real falls are diverse and unpredictable

**Google image search:**
> `hospital elderly fall surveillance camera blind spot`
> `factory worker fall detection cctv`

---

## Slide 2 — Key Insight: Falls Break Physics

**Title:** Normal Motion is Reversible. Falls Are Not.

**Content:**
- Walking forward → reverse → still looks normal
- Falling → reverse → physically impossible
- This is a law of nature, not a learned pattern

**Google image search:**
> `human motion time reversal symmetry illustration`
> `thermodynamic irreversibility arrow of time diagram`

---

## Slide 3 — Idea 1: Temporal Irreversibility Score

**Title:** Train on Normal. Detect the Abnormal.

**Content:**
- Forward predictor: what comes next? → always low error
- Backward predictor: what came before? → HIGH error during fall
- **I-Score = backward error − forward error**
- No fall labels needed during pretraining

**Google image search:**
> `forward backward prediction neural network diagram`
> `time series anomaly detection reconstruction error graph`

---

## Slide 4 — Why It Works

**Title:** The Score Separates Falls from Normal Automatically

**Content:**
- Normal motion → I-Score ≈ 0
- Fall motion → I-Score >> 0
- Threshold θ separates the two distributions
- Zero labeled falls required

**Google image search:**
> `anomaly score distribution normal vs anomaly histogram`
> `gaussian distribution overlap threshold classification`

---

## Slide 5 — Idea 2: Multi-Camera Problem

**Title:** One Camera Is Never Enough

**Content:**
- 4 cameras, same person, different angles
- Any camera can be blocked by shelf, machine, or person
- Naive average of scores = wrong (polluted by occluded camera)
- Which camera to trust?

**Google image search:**
> `multi camera surveillance system factory floor top view`
> `cctv camera occlusion blind spot industrial`

---

## Slide 6 — Solution: Cross-View Attention

**Title:** Let the Network Decide Which Camera to Trust

**Content:**
- Each camera → own I-Score + visibility confidence
- Visibility = average keypoint confidence from pose detector
- Cross-view attention: clear view → higher weight
- Occluded camera → automatically down-weighted

**Google image search:**
> `attention mechanism weights visualization heatmap`
> `multi-view fusion neural network diagram`

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

**Google image search:**
> `multi-stream neural network architecture diagram`
> `skeleton pose sequence transformer encoder diagram`

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

**Google image search:**
> `comparison table research novelty slide presentation`

*(No image needed — table is the visual)*

---

## Slide 9 — Validation Plan

**Title:** How We Prove It Works

**Content:**
- **Day 1 test:** Plot I-Score for falls vs normal on UPFall → are they separable?
- **Zero-shot:** UPFall, UR-Fall, Le2i — no labeled falls
- **Few-shot:** 5 / 10 / 50 examples vs TCNTE (1000+)
- **Occlusion test:** Block 1–2 cameras → measure accuracy drop

**Google image search:**
> `few-shot learning accuracy curve plot`
> `UPFall dataset skeleton pose benchmark`

---

## Slide 10 — One Sentence Summary

**Title:** MVTIN in One Sentence

**Content:**

> *"MVTIN detects falls by measuring how impossible it is*
> *to reverse the observed motion —*
> *no fall labels needed, no single camera dependency."*

**Google image search:**
> `human skeleton falling motion sequence pose estimation`
> `skeleton keypoint fall detection visualization`

---

## Notes

- Slides 1, 5: use real CCTV/factory images → makes it feel practical
- Slides 3, 4: use diagram/graph images → shows technical depth
- Slides 7: draw the architecture yourself (no good Google result)
- Slide 10: full-screen bold text + one background image is enough
