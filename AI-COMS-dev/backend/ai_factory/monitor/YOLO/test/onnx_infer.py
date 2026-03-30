import onnxruntime as ort
import numpy as np
import cv2
import time

# ✅ Load ONNX model with GPU (fallback to CPU if unavailable)
providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
session = ort.InferenceSession(
    r"C:\Users\dalab\Desktop\azimjaan21\AI-COMS\backend\ai_factory\monitor\YOLO\models\ppe.onnx",
    providers=providers
)

# ✅ Video file path
video_path = r"C:\Users\dalab\Desktop\azimjaan21\AI-COMS\backend\ai_factory\monitor\videos\test1.mp4"
cap = cv2.VideoCapture(video_path)

# ✅ Helper to preprocess frames
def preprocess(frame):
    img_resized = cv2.resize(frame, (640, 640))
    img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
    img_input = img_rgb.transpose(2, 0, 1).astype(np.float32) / 255.0  # CHW, normalize
    img_input = np.expand_dims(img_input, axis=0)
    return img_input

# ✅ Inference loop
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    input_tensor = preprocess(frame)

    start = time.time()
    outputs = session.run(None, {"images": input_tensor})
    end = time.time()
    inference_time = end - start

    # 🔍 Postprocess and draw (YOLOv8 format)
    output = outputs[0]  # shape: [1, 7, 8400]
    predictions = output[0].transpose(1, 0)  # shape: [8400, 7]

    for det in predictions:
        x1, y1, x2, y2, obj_conf, cls_conf, cls_id = det
        conf = obj_conf * cls_conf
        if conf < 0.4:
            continue

        x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
        label = f"{int(cls_id)} {conf:.2f}"
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    cv2.putText(frame, f"Infer: {inference_time*1000:.1f}ms", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

    cv2.imshow("ONNX YOLOv8 Inference", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
