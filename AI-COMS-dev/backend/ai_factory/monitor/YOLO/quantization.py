# QUANTIZATION

from ultralytics import YOLO

# #1 # Convert pose transfer learned model
# model8 = YOLO("yolo11s-pose.pt")
# model8.export(format="engine", half=True) 

#1 # Convert ppe transfer learned model
model8 = YOLO(r"C:\Users\ali\Projects\AI-COMS\backend\ai_factory\monitor\YOLO\models\best_detect.pt")
model8.export(format="engine", half=True)

