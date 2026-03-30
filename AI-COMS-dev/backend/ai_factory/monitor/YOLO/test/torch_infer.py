import torch
import cv2
import time
from ultralytics import YOLO

# ✅ Load YOLOv8 PyTorch model (ppe.pt)
model = YOLO( r"C:\Users\dalab\Desktop\azimjaan21\AI-COMS\backend\ai_factory\monitor\YOLO\models\ppe.pt" )  # adjust path if needed
model.fuse()  # optional: fuses Conv+BN for slightly faster inference

# ✅ Load video
video_path = r"C:\Users\dalab\Desktop\azimjaan21\AI-COMS\backend\ai_factory\monitor\videos\test1.mp4"
cap = cv2.VideoCapture(video_path)

# ✅ Inference loop
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    start = time.time()
    results = model.predict(source=frame, imgsz=640, conf=0.4, verbose=False)[0]
    end = time.time()
    infer_time = end - start

    # 🔍 Draw detections
    for box in results.boxes:
        cls_id = int(box.cls)
        conf = float(box.conf)
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

        label = f"{results.names[cls_id]} {conf:.2f}"
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, label, (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    cv2.putText(frame, f"Infer: {infer_time*1000:.1f}ms", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

    cv2.imshow("YOLOv8 PyTorch Inference", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroy
