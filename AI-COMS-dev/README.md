# 🧠 AI-COMS: Real-Time Multi-Camera Safety Monitoring System

A scalable and real-time computer vision system that performs **PPE compliance** and **fire detection** using **YOLOv8** models across multiple cameras — built with **Django REST API**, **React**, and **multiprocessing-based YOLO inference**.

---

## 🚀 Features

- 🔁 **Multiprocessing YOLOv8 Inference** (PPE + Fire)
- 🎥 **Live Video Streaming (MJPEG)** per camera
- 📡 Simulated **CCTV feeds** using video files
- 📦 Centralized model loading for GPU efficiency
- 🔍 Real-time detection data via `/api/live/`
- ✅ Bounding boxes and labels on video stream
- 🌐 React frontend with multiple camera display

---

## 📂 Tech Stack

| Layer | Tech |
|------|------|
| Backend | Django + Django REST Framework |
| AI Inference | YOLOv8m (Ultralytics) |
| Streaming | OpenCV + MJPEG + Multiprocessing |
| Frontend | React.js (Card-based camera UI) |
| Video Sources | Video files simulating RTSP streams |

---

## 🎯 Demo Flow


![2025-04-1616-38-46-ezgif com-video-to-gif-converter (1)](https://github.com/user-attachments/assets/bdcee587-0ced-4092-98c5-60e8d7d2a1a3)


---

## 🤖 YOLO Classes Detected

| Model | Class |
|------|------|
|ppe.pt	|Helmet, Vest, Head|
|fire.pt |Fire, Smoke |

---

👨‍💻 Developed by

***Azimjon Akhtamov**
AI Researcher | Smart Manufacturing Safety

***Abbos Aliboev**
Computer Science Student

---
Data Analytics Lab | Chungbuk National University 🇰🇷
