# Research Idea: MVTIN
# Multi-View Temporal Irreversibility Network for Self-Supervised Fall Detection

**Target:** AAAI 2026 / 2027
**Core idea:** Falls are physically irreversible. Multi-camera view removes occlusion.
**Key strength:** No labeled fall data needed for pretraining.

---

## Slide 1 — Title

**Title:**
> MVTIN: Multi-View Temporal Irreversibility Network
> for Self-Supervised Fall Detection

**Subtitle:**
> When Physics Meets Multi-Camera Safety Monitoring

**Authors:**
> [Your name] · Chungbuk National University — Data Analytics Lab
> NVIDIA TITAN RTX · Real RTSP 4-Camera System · AAAI 2026

---

## Slide 2 — The Core Problem: Two Unsolved Challenges

**Title:** Why Current Methods Still Fail

**Challenge 1 — Labeled Data Bottleneck:**

All existing methods (TCNTE, ST-GCN, TCN-Attention) share the same assumption:
> "To detect falls, we must first see hundreds of labeled falls."

| Method | Fall labels needed |
|--------|-----------------:|
| TCNTE (2025) | ~1,000+ |
| ST-GCN | ~800+ |
| TCN-Attention (ours) | ~600+ |
| **MVTIN (proposed)** | **0 (pretraining)** |

In the real world: falls are rare, dangerous to script, and vary infinitely.
**Collecting diverse labeled fall data is expensive and incomplete.**

**Challenge 2 — Single Camera Blindspot:**

```
          👤 ← person
          |
   [cam1] [cam2] [cam3]
     ✓      ✗      ✓
           (occluded by shelf)

cam2 misses the fall entirely.
All current papers use only one camera.
```

**Our answer:** Physics tells us what a fall looks like — no labels needed.
Multiple cameras eliminate blindspots.

---

## Slide 3 — Key Insight: The Physics of Falling

**Title:** Falls Violate Time Symmetry — A Physical Law

**The observation:**

Normal human motion is approximately **time-reversible**:

```
Walking forward:    🚶→   frames: [A][B][C][D]
Walking backward:   ←🚶  frames: [D][C][B][A]

Are these distinguishable? Barely.
A model predicting "next frame" OR "previous frame" performs equally well.
```

A fall is **thermodynamically irreversible**:

```
Falling:            🚶💥  frames: [A][B!][C!!][D!!!]
"Un-falling":       ??    frames: [D!!!][C!!][B!][A]  ← physically impossible

Reversing a fall looks WRONG. No model can predict it correctly.
```

**The physical law:**
> Falling transfers kinetic energy to the ground through impact.
> This process cannot be reversed. Time symmetry is broken.

**Our signal:**
> `Irreversibility Score = Error(predict backward) − Error(predict forward)`
>
> Normal motion: score ≈ 0 (both directions predictable)
> Fall motion:   score >> 0 (backward is impossible to predict)

---

## Slide 4 — Core Idea A: Temporal Irreversibility Score

**Title:** Measuring What Physics Already Knows

**Architecture (per camera):**

```
Skeleton sequence:  [t-T] ... [t-2] [t-1] [t]
                                           ↓
                    ┌─────────────────────────┐
                    │   Skeleton Encoder      │
                    │   (Transformer)         │
                    └────────┬────────────────┘
                             │ latent z_t
                   ┌─────────┴─────────┐
                   ↓                   ↓
          Forward Predictor    Backward Predictor
          predicts [t+1]       predicts [t-1]
                   ↓                   ↓
            err_fwd              err_bwd
                   └─────────┬─────────┘
                             ↓
                  I_score = err_bwd − err_fwd
                             ↓
                   I_score > θ → FALL DETECTED
```

**Training — completely self-supervised:**

```python
# Only normal activity data needed — no fall labels!
# Pre-train on: NTU RGB+D, Kinetics-Skeleton, or target dataset normal clips

Loss = MSE(forward_pred, frame[t+1]) + MSE(backward_pred, frame[t-1])

# Model learns: "what normal motion looks like in both time directions"
# Falls never seen during training → reconstruction fails → high I_score
```

**Key property:** A model trained only on normal activities will fail to reconstruct
the backward direction of a fall — because it never happens in nature.

---

## Slide 5 — Core Idea B: Multi-View Fusion Problem

**Title:** One Camera is Never Enough

**The multi-camera challenge:**

```
Industrial environment — 4 cameras:

    cam1 ──┐
    cam2 ──┤  Different angles, different occlusions
    cam3 ──┤  Same person, different views
    cam4 ──┘

Questions:
  1. Which camera's I_score to trust?
  2. What if cam2 is occluded? (I_score unreliable)
  3. How to combine 4 different views of the same event?
```

**Naive fusion (wrong):**
```
Final = mean(I_score_cam1, I_score_cam2, I_score_cam3, I_score_cam4)
```
Problem: Occluded camera produces noisy I_score → pollutes decision.

**Visibility-aware fusion needed:**
> A camera that sees the person clearly should contribute more.
> A camera where the person is partially occluded should contribute less.
> This must be **learned automatically** — no manual calibration.

---

## Slide 6 — Full Architecture: MVTIN

**Title:** Multi-View Temporal Irreversibility Network

```
┌─────────────────────────────────────────────────────────────────┐
│                        MVTIN Architecture                        │
└─────────────────────────────────────────────────────────────────┘

Input: N cameras × T frames × K keypoints × 2 (xy coords)

cam1: [skeleton seq] → [Encoder] → z¹_t → [Fwd/Bwd Pred] → I¹_score + v¹
cam2: [skeleton seq] → [Encoder] → z²_t → [Fwd/Bwd Pred] → I²_score + v²
cam3: [skeleton seq] → [Encoder] → z³_t → [Fwd/Bwd Pred] → I³_score + v³
cam4: [skeleton seq] → [Encoder] → z⁴_t → [Fwd/Bwd Pred] → I⁴_score + v⁴
                                                    ↓
                              ┌─────────────────────────────┐
                              │   Cross-View Attention      │
                              │                             │
                              │  Q = [I¹, I², I³, I⁴]      │
                              │  K,V = [z¹, z², z³, z⁴]    │
                              │                             │
                              │  Attention weight = f(v^n)  │
                              │  (v^n = visibility score)   │
                              └──────────────┬──────────────┘
                                             ↓
                                   I_fused (weighted sum)
                                             ↓
                                   I_fused > θ → FALL
                                   I_fused ≤ θ → SAFE

Where:
  v^n = visibility confidence from pose detector (keypoint conf mean)
  Encoder = shared weights across all cameras (camera-agnostic)
  Cross-View Attention = learns "trust" per camera dynamically
```

**Parameter sharing across cameras:**
- Encoder weights are shared → camera-view invariant representation
- Each camera produces its own I_score independently
- Cross-view attention learns to trust clearer views

---

## Slide 7 — Training Strategy: Two Stages

**Title:** Learning to Detect Falls Without Seeing Falls

**Stage 1 — Self-Supervised Pretraining (no fall labels)**

```
Dataset: Normal activities only
  - NTU RGB+D: 120 action classes (no fall) → 200K+ skeleton clips
  - UPFall normal: walking, sitting, standing, bending, jumping
  - Your RTSP cameras: unlabeled daily workplace footage

Objective: minimize forward + backward prediction error
  Loss_pre = α·MSE(fwd_pred, frame[t+1])
           + β·MSE(bwd_pred, frame[t-1])
           + γ·consistency(view1, view2)  ← same event, different cameras

Result: encoder learns rich motion representations
        backward predictor learns "what normal looks like reversed"
        → Falls will cause high I_score automatically (zero-shot!)
```

**Stage 2 — Optional Few-Shot Fine-Tuning**

```
Dataset: Just 5–50 labeled fall examples
  (compare: TCNTE needs 600+)

Objective: calibrate threshold θ per environment
  Loss_ft = BCE(I_fused > θ, fall_label)

Result: SOTA-level accuracy with minimal labels
```

**Cross-view consistency loss (Stage 1):**
> If cam1 and cam2 see the same event, their latent representations should agree.
> This forces the encoder to be view-invariant.

---

## Slide 8 — Expected Results & Baselines

**Title:** How We Validate and What We Expect

**Datasets:**

| Dataset | Type | Subjects | Cameras |
|---------|------|:--------:|:-------:|
| UPFall | Lab, scripted | 17 | 2 views |
| UR-Fall | Lab, depth | 5 | 2 views |
| Le2i | Indoor, varied | — | 1 view |
| **Our industrial** | **Real RTSP** | **—** | **4 cameras** |

**Experiments:**

1. **Zero-shot fall detection** — pretraining only, no labeled falls
2. **Few-shot learning curve** — 1 / 5 / 10 / 50 / all examples
3. **Occlusion robustness** — artificially block 1-2 cameras
4. **Cross-dataset generalization** — train UPFall → test Le2i
5. **Ablation** — remove multi-view / remove irreversibility / remove pretraining

**Expected competitive claims:**

| Metric | TCNTE | ST-GCN | MVTIN (ours) |
|--------|:-----:|:------:|:------------:|
| UPFall accuracy | 99.58% | ~97% | ~99%+ |
| Zero-shot capability | ✗ | ✗ | ✓ |
| 5-shot accuracy | ✗ | ✗ | ~95%+ (expected) |
| Multi-camera fusion | ✗ | ✗ | ✓ |
| Labels for pretraining | 1000+ | 800+ | **0** |
| Cross-dataset drop | ~8% | ~10% | **~3% (expected)** |

---

## Slide 9 — Why This is Novel: Contribution Summary

**Title:** Four Contributions, Zero Overlap with Existing Work

**C1 — Temporal Irreversibility as Fall Signal (new physical insight)**
> First work to formalize the thermodynamic irreversibility of falls as a
> measurable signal for fall detection. Requires NO fall labels for pretraining.

**C2 — Multi-View Cross-Camera Fusion (new problem formulation)**
> First fall detection paper with principled multi-camera fusion using
> cross-view attention weighted by per-camera visibility confidence.

**C3 — Self-Supervised + Few-Shot Learning Pipeline**
> Addresses the fundamental data scarcity problem in fall detection:
> from 600+ labels (TCNTE) to 5 labels (MVTIN) with competitive accuracy.

**C4 — Real Industrial Multi-Camera Dataset**
> First publicly released fall detection dataset collected in a real
> industrial environment with 4 RTSP cameras and natural occlusions.

**Novelty comparison:**

| Dimension | TCNTE | CrossMax (AAAI'24) | MVTIN |
|-----------|:-----:|:-----------------:|:-----:|
| Physics-informed | ✗ | ✗ | ✓ |
| Self-supervised | ✗ | ✗ | ✓ |
| Multi-camera | ✗ | ✗ | ✓ |
| Open-set detection | ✗ | ✓ | ✓ |
| Real industrial eval | ✗ | ✗ | ✓ |
| Occlusion handling | ✗ | ✗ | ✓ |

---

## Slide 10 — Research Roadmap

**Title:** Implementation Plan

**Phase 1 — Foundation (Month 1–2)**
- [ ] Implement forward/backward skeleton predictor (Transformer-based)
- [ ] Verify I_score on UPFall: do falls produce higher backward error?
- [ ] This is the core hypothesis test — everything depends on this

**Phase 2 — Architecture (Month 2–3)**
- [ ] Multi-camera encoder with shared weights
- [ ] Cross-view attention module
- [ ] Visibility confidence from pose keypoint scores

**Phase 3 — Training & Experiments (Month 3–5)**
- [ ] Pretrain on NTU RGB+D normal activities
- [ ] Zero-shot eval on UPFall, UR-Fall, Le2i
- [ ] Few-shot learning curve experiments
- [ ] Collect industrial dataset (your 4 RTSP cameras)

**Phase 4 — Ablation & Writing (Month 5–6)**
- [ ] Full ablation: each component's contribution
- [ ] Comparison with 10+ baselines
- [ ] Paper writing → AAAI 2026 submission (August 2026 deadline)

**Earliest verifiable milestone:**
> Month 1 experiment: plot I_score distribution for normal vs fall on UPFall.
> If the distributions are separable → hypothesis confirmed → proceed.
> If not → adjust predictor architecture and retry.

---

## Key Message (One Sentence)

> **MVTIN detects falls by measuring how impossible it would be to reverse
> the observed motion — a physical truth that requires no labeled fall data
> and works reliably even when cameras are partially occluded.**
