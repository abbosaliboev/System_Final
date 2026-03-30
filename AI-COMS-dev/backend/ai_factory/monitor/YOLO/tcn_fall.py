# monitor/YOLO/tcn_fall.py
import torch
import torch.nn as nn
import numpy as np
import os
from collections import deque

# Import TCN with Attention model (10 keypoint version)
from .tcn_attention_model import TCN_Attention_Model

# === Normalize function for 10 keypoints ===
def _normalize_10kp(kp_xy, kp_conf):
    """
    Normalize 10 keypoints using root-centering and scale normalization.
    
    10 Keypoint indices (custom dataset):
    0: nose, 1: left_shoulder, 2: right_shoulder,
    3: left_elbow, 4: right_elbow, 5: left_wrist, 6: right_wrist,
    7: left_hip, 8: right_hip, 9: neck
    
    Args:
        kp_xy: (10, 2) - x, y coordinates
        kp_conf: (10,) - confidence scores
    
    Returns:
        nkp: (10, 2) - normalized keypoints
    """
    NUM_KP = 10
    KP_L_SHO = 1
    KP_R_SHO = 2
    KP_L_HIP = 7
    KP_R_HIP = 8
    
    def _ok(i):
        return (i >= 0) and (i < NUM_KP) and (kp_conf[i] > 0.05)
    
    # Root: mid-hip -> mid-shoulder -> (0,0)
    if _ok(KP_L_HIP) and _ok(KP_R_HIP):
        root = (kp_xy[KP_L_HIP] + kp_xy[KP_R_HIP]) / 2.0
    elif _ok(KP_L_SHO) and _ok(KP_R_SHO):
        root = (kp_xy[KP_L_SHO] + kp_xy[KP_R_SHO]) / 2.0
    else:
        root = np.array([0.0, 0.0], dtype=float)
    
    # Scale: shoulder distance -> hip distance -> 1.0
    def _dist(a, b):
        return float(np.linalg.norm(kp_xy[a] - kp_xy[b]))
    
    scale = 1.0
    if _ok(KP_L_SHO) and _ok(KP_R_SHO):
        d = _dist(KP_L_SHO, KP_R_SHO)
        if d > 1e-3:
            scale = d
    elif _ok(KP_L_HIP) and _ok(KP_R_HIP):
        d = _dist(KP_L_HIP, KP_R_HIP)
        if d > 1e-3:
            scale = d
    
    if not (scale > 1e-6):
        scale = 1.0
    
    nkp = (kp_xy - root) / scale
    return nkp


# === Fall Detector (10 keypoint version) ===
class FallDetector:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # TCN with Attention Model (10 keypoints × 2 = 20 input size)
        self.model = TCN_Attention_Model(
            input_size=20,      # 10 keypoints × 2 (x, y)
            num_classes=2,      # no_fall, fall
            num_channels=[64, 128, 256],
            kernel_size=3,
            dropout=0.2
        ).to(self.device)
        self.model.eval()

        # Load fall_detection_v4.pth model
        ckpt_path = os.path.join(os.path.dirname(__file__), "models", "fall_detection_v4.pth")
        if not os.path.exists(ckpt_path):
            raise FileNotFoundError(f"[FallDetector] Model topilmadi: {ckpt_path}")

        try:
            ckpt = torch.load(ckpt_path, map_location=self.device, weights_only=False)
            # Try different checkpoint formats
            if isinstance(ckpt, dict):
                state_dict = ckpt.get("model_state_dict") or ckpt.get("state_dict") or ckpt.get("model") or ckpt
            else:
                state_dict = ckpt
            
            self.model.load_state_dict(state_dict, strict=False)
            print("[FallDetector] TCN-Attention model yuklandi (10 keypoint)")
        except Exception as e:
            print(f"[FallDetector] Model yuklashda xatolik: {e}")
            raise

        # Buffer settings (30 frames for temporal analysis)
        self.sequence_length = 30
        self.num_keypoints = 10
        self.buffer = {}   # cam_id -> deque(maxlen=30), filled lazily
        self.history = {}
        self._initialized = True

    @torch.no_grad()
    def predict(self, cam_id, keypoints_xy, keypoints_conf):
        """
        Predict fall from 10 keypoints sequence.
        
        Args:
            cam_id: Camera ID for buffer tracking
            keypoints_xy: (10, 2) or (17, 2) - x, y coordinates
            keypoints_conf: (10,) or (17,) - confidence scores
        
        Returns:
            tuple: (label, confidence, draw_info) or (None, 0.0, None) if buffer not full
        """
        # Handle 17 keypoints -> extract first 10
        if len(keypoints_xy) == 17:
            keypoints_xy = keypoints_xy[:10]
            keypoints_conf = keypoints_conf[:10]
        
        # Normalize keypoints
        try:
            nkp = _normalize_10kp(keypoints_xy, keypoints_conf)
        except Exception as e:
            print(f"[FallDetector] Normalize xato: {e}")
            nkp = np.zeros((10, 2))

        # Flatten to 20-dim vector
        flat = nkp.flatten().tolist()

        # P7: deque(maxlen=30) — O(1) append+auto-drop vs list.pop(0) which was O(N)
        if cam_id not in self.buffer:
            self.buffer[cam_id] = deque(maxlen=self.sequence_length)
        self.buffer[cam_id].append(flat)

        # Need full buffer (30 frames)
        if len(self.buffer[cam_id]) < self.sequence_length:
            return None, 0.0, None

        # Prepare input tensor [1, 30, 20]
        seq = np.array(self.buffer[cam_id])
        tensor = torch.tensor(seq, dtype=torch.float32).unsqueeze(0).to(self.device)

        # Model inference
        logits = self.model(tensor)
        probs = torch.softmax(logits, dim=1)[0]
        pred = torch.argmax(probs).item()
        
        # Get confidences
        confidence = probs[pred].item()
        no_fall_conf = probs[0].item()
        fall_conf = probs[1].item()
        
        # Confidence filtering (threshold for fall detection)
        if pred == 1:  # Fall class
            if fall_conf < 0.50:  # 50% threshold for fall
                pred = 0  # Reject as no_fall
        
        # Temporal smoothing (last 3 predictions - majority voting)
        if cam_id not in self.history:
            self.history[cam_id] = []
        self.history[cam_id].append(pred)
        
        if len(self.history[cam_id]) > 3:
            self.history[cam_id].pop(0)
        
        # Majority voting (if at least 3 predictions)
        if len(self.history[cam_id]) >= 3:
            from collections import Counter
            most_common = Counter(self.history[cam_id]).most_common(1)[0][0]
            label = ["no_fall", "fall"][most_common]
        else:
            label = ["no_fall", "fall"][pred]
        
        # Visualization info
        color = (0, 255, 0) if pred == 0 else (0, 0, 255)
        text = f"{label.upper()} {confidence:.2f}"

        # Compute bounding box from keypoints
        kps = np.array(keypoints_xy)
        valid = kps[:, 0] > 0
        if valid.any():
            x1, y1 = kps[valid].min(axis=0).astype(int)
            x2, y2 = kps[valid].max(axis=0).astype(int)
            bbox = [x1, y1, x2, y2]
        else:
            bbox = [0, 0, 50, 50]

        return label, confidence, {
            "bbox": bbox,
            "text": text,
            "color": color
        }