#!/usr/bin/env python3
"""
Camera diagnostic tool for Kuko Robot
Tests camera availability and capture functionality
"""

import cv2
import os
import sys
import time

print("="*60)
print("Kuko Camera Diagnostics")
print("="*60)

# Test 1: Check OpenCV version
print(f"\n[1] OpenCV Version: {cv2.__version__}")

# Test 2: Try to open camera at index 0
print("\n[2] Testing camera at index 0...")

# Try V4L2 backend first (better for Raspberry Pi)
camera = cv2.VideoCapture(0, cv2.CAP_V4L2)

if not camera.isOpened():
    print("⚠️  Failed with V4L2 backend, trying default...")
    camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("❌ FAILED: Cannot open camera at index 0")
    print("\nTroubleshooting:")
    print("  - On macOS: Grant Terminal camera permissions in System Settings > Privacy")
    print("  - On Raspberry Pi: Check camera connection (ribbon cable)")
    print("  - Try different camera index: VideoCapture(1) or VideoCapture(2)")
    sys.exit(1)

print("✓ Camera opened successfully")

# Set MJPEG format (better compatibility)
camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))

# Test 3: Check camera properties
width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(camera.get(cv2.CAP_PROP_FPS))

print(f"\n[3] Camera properties:")
print(f"  Resolution: {width}x{height}")
print(f"  FPS: {fps}")

# Test 4: Try to capture frames with validation
print("\n[4] Testing frame capture...")

# Warm up camera (read multiple frames)
ret = False
frame = None
for i in range(5):
    ret, frame = camera.read()
    if ret and frame is not None:
        # Validate frame shape
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            print(f"✓ Frame captured on attempt {i+1}: {frame.shape}")
            break
        else:
            print(f"⚠️  Attempt {i+1}: Invalid frame shape {frame.shape}, retrying...")
    time.sleep(0.2)

if not ret or frame is None:
    print("❌ FAILED: Camera opened but cannot capture frames")
    print("\nTroubleshooting:")
    print("  - Camera might be in use by another application")
    print("  - Camera hardware might be faulty")
    camera.release()
    sys.exit(1)

# Validate frame shape
if len(frame.shape) != 3 or frame.shape[2] != 3:
    print(f"❌ FAILED: Invalid frame shape {frame.shape}")
    print(f"\nExpected: (height, width, 3) e.g. (480, 640, 3)")
    print(f"Got: {frame.shape}")
    print("\nTroubleshooting:")
    print("  - Camera driver might need reconfiguration")
    print("  - Try: sudo modprobe bcm2835-v4l2  (Raspberry Pi)")
    print("  - Check: ls -l /dev/video*")
    camera.release()
    sys.exit(1)

print(f"✓ Frame shape validated: {frame.shape}")

# Test 5: Try to save image
test_path = os.path.abspath("camera_diagnostic_test.jpg")
print(f"\n[5] Testing image save to: {test_path}")

success = cv2.imwrite(test_path, frame)

if not success:
    print(f"❌ FAILED: Could not write image to {test_path}")
    print("\nTroubleshooting:")
    print("  - Check write permissions in current directory")
    print("  - Check disk space")
    camera.release()
    sys.exit(1)

if not os.path.exists(test_path):
    print(f"❌ FAILED: Image file not found after write")
    camera.release()
    sys.exit(1)

file_size = os.path.getsize(test_path)
print(f"✓ Image saved successfully ({file_size} bytes)")

# Test 6: Try to read the saved image
print(f"\n[6] Testing image read...")
test_read = cv2.imread(test_path)

if test_read is None:
    print(f"❌ FAILED: Could not read back saved image")
    camera.release()
    sys.exit(1)

print(f"✓ Image read successfully: {test_read.shape}")

# Cleanup
camera.release()
os.remove(test_path)

print("\n" + "="*60)
print("✅ ALL TESTS PASSED - Camera is working correctly!")
print("="*60)
print("\nYou can now run: python kuko_vision_mvp.py")
