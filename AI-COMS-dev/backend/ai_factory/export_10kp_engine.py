"""
Export yolo11n-10kp.pt → yolo11n-10kp.engine (TensorRT FP16)

Run from backend/ai_factory/:
    python export_10kp_engine.py

Output: monitor/YOLO/models/yolo11n-10kp.engine
"""
import os
import time
from ultralytics import YOLO

MODEL_PATH  = "monitor/YOLO/models/yolo11n-10kp.pt"
OUTPUT_DIR  = "monitor/YOLO/models"

print(f"Loading model: {MODEL_PATH}")
model = YOLO(MODEL_PATH, task="pose")

print("Exporting to TensorRT FP16 engine...")
t0 = time.time()

model.export(
    format="engine",
    half=True,          # FP16
    imgsz=640,
    workspace=4,        # GB — TRT optimizer workspace
    simplify=True,
    verbose=False,
)

elapsed = time.time() - t0
print(f"\nExport done in {elapsed:.1f}s")

# ultralytics saves .engine next to the .pt file
src = MODEL_PATH.replace(".pt", ".engine")
if os.path.exists(src):
    size_mb = os.path.getsize(src) / 1024 / 1024
    print(f"Engine saved: {src}  ({size_mb:.1f} MB)")
else:
    print(f"WARNING: engine not found at {src}")
    print("Check current directory for *.engine files")
