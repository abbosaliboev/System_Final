# test_rtsp.py
import cv2

url_221 = "rtsp://admin:Aminok434*@10.198.137.221:554/stream1"
url_222 = "rtsp://admin:Aminok434*@10.198.137.222:554/stream1"

def test(url, name):
    print(f"\n[{name}] Sinov boshlandi...")
    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(f"{name}_test.jpg", frame)
        print(f"{name} → MUVOFFAQIYATLI! → {name}_test.jpg")
    else:
        print(f"{name} → XATO! Kamera ulanmadi.")
    cap.release()

test(url_221, "cam1_221")
test(url_222, "cam2_222")