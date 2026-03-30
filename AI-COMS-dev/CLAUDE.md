# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AI-COMS** is a real-time multi-camera industrial safety monitoring system built at Chungbuk National University's Data Analytics Lab. It performs PPE compliance detection (helmets/vests), fire detection, and fall detection across RTSP camera streams using YOLOv8 and a custom TCN-Attention model.

## Commands

### Backend

```bash
cd backend/ai_factory

# Setup
pip install -r ../../requirements.txt

# Database
python manage.py migrate

# Run server
python manage.py runserver 0.0.0.0:8000

# Run tests
python manage.py test

# Single test
python manage.py test monitor.tests.TestClassName.test_method
```

### Frontend

```bash
cd frontend/my-app

npm install
npm start          # dev server at http://localhost:3000
npm run build      # production build
```

## Architecture

The system consists of three layers:

### 1. Inference Pipeline (Python Multiprocessing)

Each camera runs in its own OS process. `monitor/camera_loader.py` defines `CAMERA_SOURCES` (RTSP URLs) and spawns processes. `YOLO/streaming_manager.py` is the per-camera worker that:
- Loads models once via `YOLO/inference_utils.py` (`load_models`)
- Runs alternating inference: PPE (YOLOv8m) every 3rd frame, Pose (yolo11n-10kp) every 2nd frame using CUDA streams
- Feeds 30-frame sequences to the TCN-Attention fall detector (`YOLO/tcn_fall.py`)
- Annotates frames and pushes to a max-size-1 queue for MJPEG streaming

`YOLO/state_manager.py` tracks per-camera state (frame queues, rates). `YOLO/visualization.py` handles frame annotation. `YOLO/helpers.py` has polygon geometry for danger zone intersection checks.

### 2. Django REST API

App: `monitor/`. Core views:
- `views.py` — `get_live_detections`, `AlertListView`, `ReportListCreateView`
- `stream_views.py` — MJPEG video streaming endpoint (`/api/live/<cam_id>/`)
- `fall_views.py` — Fall alert logging and status
- `dangerzone_views.py` — Polygon zone CRUD
- `summary_views.py` — Analytics endpoints (distribution, trend, heatmap)
- `report_pdf_views.py` — PDF generation

Alert deduplication: identical alerts within 30 minutes are suppressed (in `models.py`).

URL prefix for all endpoints: `/api/`

### 3. React Frontend

`CameraContext.js` is the global state provider — polls `/api/live/` and distributes data to all components.

Page routing is in `App.js` with a `MainLayout` wrapper. Key pages: `Home.jsx` (camera grid), `Camera.jsx` (single camera), `Summary.jsx` (analytics), `SettingsPage.jsx` (danger zone configuration using Konva canvas drawing).

## Key Configuration

**Camera sources** — edit `backend/ai_factory/monitor/camera_loader.py` → `CAMERA_SOURCES`. Restart Django to apply.

**Model weights** — stored in `backend/ai_factory/monitor/YOLO/models/`:
- `yolo11n-10kp.pt` — pose estimation (10-keypoint)
- `fall_detection_v4.pth` — TCN-Attention fall classifier (30-frame input, 10 keypoints)

**PPE detection threshold** — `0.30` confidence in `inference_utils.py`

**Fall detection threshold** — `0.50` confidence with 3-frame majority voting in `tcn_fall.py`

**Django settings** — `backend/ai_factory/ai_factory/settings.py`. Uses SQLite in dev. Media files (alert frame images) stored in `backend/ai_factory/media/`.

## Fall Detection Model

The TCN-Attention model (`tcn_attention_model.py`) takes sequences of **30 frames × 10 keypoints** (nose, shoulders, elbows, wrists, hips, neck). Keypoints are root-centered (mid-hip or mid-shoulder fallback) and scale-normalized before feeding to the model. The model file is `fall_detection_v4.pth` (1.51 MB, 391K parameters).
