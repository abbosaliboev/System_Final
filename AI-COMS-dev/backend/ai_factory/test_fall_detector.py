#!/usr/bin/env python
"""
Test script to verify FallDetector loads fd_best.pt model correctly
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_factory.settings')
django.setup()

import numpy as np

print("=" * 60)
print("FALL DETECTION MODEL TEST")
print("=" * 60)

# Test 1: Check if fd_best.pt exists
model_path = "monitor/YOLO/models/fd_best.pt"
if os.path.exists(model_path):
    print(f"✅ Model topildi: {model_path}")
    file_size = os.path.getsize(model_path) / (1024 * 1024)
    print(f"   Model hajmi: {file_size:.2f} MB")
else:
    print(f"❌ Model topilmadi: {model_path}")
    sys.exit(1)

# Test 2: Load FallDetector
print("\n" + "=" * 60)
print("FallDetector yuklanmoqda...")
print("=" * 60)

try:
    from monitor.YOLO.tcn_fall import FallDetector
    
    fall_detector = FallDetector()
    print("✅ FallDetector muvaffaqiyatli yuklandi!")
    print(f"   Device: {fall_detector.device}")
    print(f"   Sequence length: {fall_detector.sequence_length}")
    print(f"   Model initialized: {fall_detector._initialized}")
    
except Exception as e:
    print(f"❌ FallDetector yuklashda xatolik: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Test inference with dummy data
print("\n" + "=" * 60)
print("Test inference...")
print("=" * 60)

try:
    # Create dummy keypoints (17 keypoints, x,y coordinates)
    dummy_keypoints = np.random.rand(17, 2) * 100
    dummy_conf = np.ones(17)
    
    cam_id = "test_cam"
    
    # Run multiple times to fill the buffer (needs 15 frames)
    for i in range(16):
        result = fall_detector.predict(cam_id, dummy_keypoints, dummy_conf)
        if i < 14:
            assert result[0] is None, f"Buffer to'lmagan, natija None bo'lishi kerak (frame {i+1}/15)"
        else:
            label, confidence, draw_info = result
            print(f"   Frame {i+1}: label={label}, confidence={confidence:.3f}")
    
    print("✅ Test inference muvaffaqiyatli!")
    print(f"   Natija: {label} (confidence: {confidence:.3f})")
    
except Exception as e:
    print(f"❌ Test inference xatolik: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("BARCHA TESTLAR MUVAFFAQIYATLI! ✅")
print("=" * 60)
print("\nFall detection tizimi ishlashga tayyor!")
print("Backend serverini restart qiling: python manage.py runserver")
