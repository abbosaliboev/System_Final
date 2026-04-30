from multiprocessing import Manager, Process, Queue
from .YOLO.streaming_manager import camera_process

# Camera definitions with RTSP stream
CAMERA_SOURCES = [

    # {"id": "cam1", "url": "rtsp://admin:Aminok434*@10.198.137.222:554/stream1"},
    # {"id": "cam2", "url": "rtsp://admin:Aminok434*@10.198.137.222:554/stream1"},
    # {"id": "cam3", "url": "rtsp://admin:Aminok434*@10.198.137.221:554/stream1"},
    # {"id": "cam4", "url": "rtsp://admin:Aminok434*@10.198.137.221:554/stream1"},
    # {"id": "cam5", "url": "rtsp://admin:Aminok434*@10.198.137.221:554/stream1"},
    # {"id": "cam6", "url": "rtsp://admin:Aminok434*@10.198.137.222:554/stream1"},
    #{"id": "cam2", "url": "monitor/videos/poly.mp4"},
    # You can add more RTSP cameras:
    #{"id": "cam1", "url": "rtsp://admin:Aminok434*@10.198.137.221:554/stream1"},
    # {"id": "cam3", "url": "rtsp://admin:Lab59423!@192.168.0.5:554/stream1"},
    # Or mix with video files:

    # {"id": "cam1", "url": "monitor/videos/test1.mp4"},
    # {"id": "cam2", "url": "monitor/videos/poly1.mp4"},
    # {"id": "cam3", "url": "monitor/videos/test2.mp4"},
    # {"id": "cam4", "url": "monitor/videos/test4.mp4"},
    {"id":"cam1","url":"rtsp://admin:dalab%24123@10.198.137.208:554/stream1"},
    {"id":"cam2","url":"rtsp://admin:dalab%24123@10.198.137.159:554/stream1"},
    {"id":"cam3","url":"rtsp://admin:dalab%24123@10.198.137.122:554/stream1"},
    {"id":"cam4","url":"rtsp://admin:dalab%24123@10.198.137.122:554/stream1"},

    # {"id":"cam1","url":"monitor/videos/test1.mp4"},
    # {"id":"cam2","url":"monitor/videos/test2.mp4"},
    # {"id":"cam3","url":"monitor/videos/test3.mp4"},
    # {"id":"cam4","url":"monitor/videos/test4.mp4"},
    # {"id":"cam5","url":"monitor/videos/test5.mp4"},
    # {"id":"cam6","url":"monitor/videos/test7.mp4"},
    # {"id":"cam4","url":"rtsp://admin:dalab%24123@10.198.137.122:554/stream1"},
    # {"id":"cam3","url":"rtsp://admin:dalab%24123@10.198.137.122:554/stream1"},
    # {"id":"cam4","url":"rtsp://admin:dalab%24123@10.198.137.122:554/stream1"},


    
    # {"id":"cam3","url":"rtsp://admin:dalab%24123@10.198.137.122:554/stream1"},
    # {"id":"cam4","url":"rtsp://admin:dalab%24123@10.198.137.159:554/stream1"},
    # {"id":"cam4","url":"rtsp://admin:dalab%24123@10.198.137.159:554/stream1"},
    # {"id":"cam3","url":"rtsp://admin:dalab%24123@10.198.137.212:554/stream1"},
    # {"id":"cam4","url":"rtsp://admin:dalab%24123@10.198.137.216:554/stream1"}
    # {"id": "cam1", "url": "monitor/videos/test4.mp4"}, # 자연 영상
    # {"id": "cam2", "url": "monitor/videos/test7.mp4"}, # 화재 영상
    # {"id": "cam3", "url": "monitor/videos/test2.mp4"},
    # {"id": "cam4", "url": "monitor/videos/test7.mp4"}


]

manager = Manager()
camera_results = manager.dict()

# ✅ Queue for frontend streaming (one frame per cam)
frame_queues = {cam["id"]: Queue(maxsize=1) for cam in CAMERA_SOURCES}

processes = []

def start_all():
    print("🚀 Starting multiprocessing camera detection...")

    # P6: 2 cameras per process — halves GPU model duplication (was chunk_size=1 = 4x copies)
    chunk_size = 2
    cam_chunks = [CAMERA_SOURCES[i:i + chunk_size] for i in range(0, len(CAMERA_SOURCES), chunk_size)]

    # cam_chunks = [CAMERA_SOURCES] #2026-03-12

    for chunk in cam_chunks:
        # ⬇️ Pass matching queues only
        queues = {cam["id"]: frame_queues[cam["id"]] for cam in chunk}
        p = Process(target=camera_process, args=(chunk, camera_results, queues), daemon=True)
        p.start()
        processes.append(p)

    print(f"✅ Started {len(processes)} processes for {len(CAMERA_SOURCES)} cameras.")
