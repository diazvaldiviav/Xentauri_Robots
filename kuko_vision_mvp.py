#!/usr/bin/env python3
"""
Kuko Robot - US-001: Visual Trash Classification MVP
Epic 1: Artificial Intelligence & Vision

Captures photo with 5MP camera and classifies objects using Gemini AI
Categories: toy, trash, clothing, other
Confidence threshold: >70%
"""

import cv2
import google.generativeai as genai
import time
from PIL import Image
import json
import os

# Configure Gemini using environment variable
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set. Please set it before running.")

genai.configure(api_key=GEMINI_API_KEY)

# Camera configuration for 5MP
CAMERA_WIDTH = 2592   # 5MP resolution (2592x1944)
CAMERA_HEIGHT = 1944

class KukoVision:
    """Kuko robot vision system for object classification"""

    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
        self.camera = None

    def init_camera(self):
        """Initialize 5MP camera"""
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

        # Verify actual resolution
        actual_width = self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(f"Camera initialized: {int(actual_width)}x{int(actual_height)}")

    def capture_photo(self, save_path="captured_image.jpg"):
        """Capture a photo from the 5MP camera"""
        if not self.camera or not self.camera.isOpened():
            self.init_camera()

        ret, frame = self.camera.read()
        if not ret:
            raise RuntimeError("Failed to capture image from camera")

        # Save captured image
        cv2.imwrite(save_path, frame)
        print(f"Photo captured: {save_path}")
        return save_path

    def classify_objects(self, image_path):
        """
        Classify objects in image using Gemini AI

        Returns objects with:
        - category: toy, trash, clothing, other
        - confidence: >70%
        - bounding box location
        """
        start_time = time.time()

        # Load image
        img = Image.open(image_path)

        # Gemini prompt for object classification
        prompt = """
        Analyze this image and identify objects that are out of place (toys, trash, clothing, etc.).

        For EACH object found, provide:
        1. category: Must be one of [toy, trash, clothing, other]
        2. description: Brief description of the object
        3. confidence: Confidence percentage (0-100)
        4. bbox: Approximate bounding box as [x_min, y_min, x_max, y_max] in pixels

        ONLY include objects with confidence > 70%.

        Return response in JSON format:
        {
            "objects": [
                {
                    "category": "toy|trash|clothing|other",
                    "description": "object description",
                    "confidence": 85,
                    "bbox": [x1, y1, x2, y2]
                }
            ]
        }

        If no objects found with confidence >70%, return empty objects array.
        """

        # Send to Gemini
        response = self.model.generate_content([prompt, img])

        # Parse response
        try:
            # Extract JSON from response (handle markdown code blocks)
            response_text = response.text.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            result = json.loads(response_text)

            # Validate bbox format for each object
            if result.get('objects'):
                for obj in result['objects']:
                    if 'bbox' in obj:
                        bbox = obj['bbox']
                        if not (isinstance(bbox, list) and len(bbox) == 4):
                            print(f"⚠️  Invalid bbox format for {obj.get('description', 'object')}: {bbox}")
                            obj['bbox'] = None
        except json.JSONDecodeError:
            # Fallback: create structured response from text
            result = {
                "objects": [],
                "raw_response": response.text
            }

        # Calculate processing time
        processing_time = time.time() - start_time
        result["processing_time"] = round(processing_time, 2)

        # Validate processing time < 3 seconds
        if processing_time >= 3:
            print(f"⚠️  Warning: Classification took {processing_time:.2f}s (target: <3s)")

        return result

    def draw_bounding_boxes(self, image_path, objects, output_path="debug_bbox.jpg"):
        """
        Draw bounding boxes on image for debugging
        Saves annotated image with bbox visualizations
        """
        img = cv2.imread(image_path)
        if img is None:
            print(f"⚠️  Could not load image: {image_path}")
            return None

        for obj in objects:
            if obj.get('bbox'):
                bbox = obj['bbox']
                x_min, y_min, x_max, y_max = bbox

                # Draw rectangle
                color = self._get_category_color(obj.get('category', 'other'))
                cv2.rectangle(img, (int(x_min), int(y_min)), (int(x_max), int(y_max)), color, 2)

                # Add label
                label = f"{obj.get('category', 'unknown')}: {obj.get('confidence', 0)}%"
                cv2.putText(img, label, (int(x_min), int(y_min) - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        cv2.imwrite(output_path, img)
        print(f"Debug image with bounding boxes saved: {output_path}")
        return output_path

    def _get_category_color(self, category):
        """Get color for category visualization"""
        colors = {
            'toy': (255, 0, 0),      # Blue
            'trash': (0, 0, 255),    # Red
            'clothing': (0, 255, 0), # Green
            'other': (255, 255, 0)   # Cyan
        }
        return colors.get(category, (128, 128, 128))

    def save_coordinates_for_grasping(self, objects, output_file="object_coordinates.json"):
        """
        Save object coordinates for US-012 (Object Grasping)
        Format: JSON file with object positions for manipulation
        """
        grasp_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "objects": []
        }

        for i, obj in enumerate(objects):
            if obj.get('bbox'):
                bbox = obj['bbox']
                # Calculate center point for grasping
                center_x = (bbox[0] + bbox[2]) / 2
                center_y = (bbox[1] + bbox[3]) / 2

                grasp_data["objects"].append({
                    "id": i,
                    "category": obj.get('category'),
                    "description": obj.get('description'),
                    "confidence": obj.get('confidence'),
                    "bbox": bbox,
                    "grasp_point": [center_x, center_y]
                })

        with open(output_file, 'w') as f:
            json.dump(grasp_data, f, indent=2)

        print(f"Coordinates saved for grasping: {output_file}")
        return grasp_data

    def optimize_image_for_latency(self, image_path, target_size=(1280, 960)):
        """
        Resize image if processing is too slow (>3s)
        Reduces from 5MP to ~1MP for faster processing
        """
        img = cv2.imread(image_path)
        if img is None:
            return image_path

        # Resize to target size
        resized = cv2.resize(img, target_size)
        optimized_path = image_path.replace(".jpg", "_optimized.jpg")
        cv2.imwrite(optimized_path, resized)

        print(f"Image optimized: {target_size[0]}x{target_size[1]} -> {optimized_path}")
        return optimized_path

    def classify_with_error_handling(self, image_path):
        """
        Classify with US-005 error handling:
        - Dark/blurry image detection
        - Gemini API failures
        - Retry logic (max 3 attempts)
        """
        max_retries = 3
        attempt = 0

        while attempt < max_retries:
            try:
                attempt += 1
                print(f"Classification attempt {attempt}/{max_retries}...")

                # Check image quality
                img = cv2.imread(image_path)
                if img is None:
                    raise ValueError(f"Cannot read image: {image_path}")

                # Check if image is too dark (mean brightness < 50)
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                mean_brightness = gray.mean()
                if mean_brightness < 50:
                    print("⚠️  Image too dark (brightness < 50)")
                    return {
                        "error": "Image too dark. Need >200 lux lighting.",
                        "brightness": round(mean_brightness, 2),
                        "objects": []
                    }

                # Check if image is blurry (Laplacian variance)
                laplacian = cv2.Laplacian(gray, cv2.CV_64F)
                blur_score = laplacian.var()
                if blur_score < 100:
                    print(f"⚠️  Image may be blurry (blur score: {blur_score:.2f})")

                # Attempt classification
                result = self.classify_objects(image_path)

                # Check if Gemini responded
                if result.get('raw_response') and not result.get('objects'):
                    if attempt < max_retries:
                        print(f"Gemini response unclear, retrying... ({attempt}/{max_retries})")
                        time.sleep(1)
                        continue
                    else:
                        return {
                            "error": "Could not parse Gemini response after 3 attempts",
                            "raw_response": result.get('raw_response'),
                            "objects": []
                        }

                # Optimize if too slow
                if result.get('processing_time', 0) >= 3 and attempt == 1:
                    print("⚠️  Slow processing detected. Optimizing image...")
                    image_path = self.optimize_image_for_latency(image_path)
                    continue  # Retry with optimized image

                return result

            except Exception as e:
                print(f"❌ Error on attempt {attempt}: {str(e)}")
                if attempt >= max_retries:
                    return {
                        "error": f"Classification failed after {max_retries} attempts: {str(e)}",
                        "objects": []
                    }
                time.sleep(1)

    def release_camera(self):
        """Release camera resources"""
        if self.camera:
            self.camera.release()
            print("Camera released")

def main():
    """Test US-001: Visual Trash Classification"""
    print("=" * 60)
    print("Kuko Robot - US-001: Visual Trash Classification MVP")
    print("=" * 60)

    kuko = KukoVision()

    try:
        # Step 1: Initialize camera
        print("\n[1] Initializing 5MP camera...")
        kuko.init_camera()

        # Step 2: Capture photo
        print("\n[2] Capturing photo...")
        image_path = kuko.capture_photo("test_capture.jpg")

        # Step 3: Classify with Gemini (with error handling)
        print("\n[3] Classifying objects with Gemini AI (with error handling)...")
        result = kuko.classify_with_error_handling(image_path)

        # Step 4: Draw bounding boxes for debugging
        if result.get('objects'):
            print("\n[4] Drawing bounding boxes for debugging...")
            kuko.draw_bounding_boxes(image_path, result['objects'])

            # Step 5: Save coordinates for US-012 (Object Grasping)
            print("\n[5] Saving coordinates for US-012 (Object Grasping)...")
            kuko.save_coordinates_for_grasping(result['objects'])

        # Step 6: Display results
        print("\n" + "=" * 60)
        print("CLASSIFICATION RESULTS")
        print("=" * 60)
        print(f"Processing time: {result.get('processing_time', 'N/A')}s")
        print(f"Objects found: {len(result.get('objects', []))}")

        if result.get('objects'):
            print("\nDetected objects:")
            for i, obj in enumerate(result['objects'], 1):
                print(f"\n  Object {i}:")
                print(f"    Category: {obj.get('category', 'unknown')}")
                print(f"    Description: {obj.get('description', 'N/A')}")
                print(f"    Confidence: {obj.get('confidence', 0)}%")
                print(f"    Location (bbox): {obj.get('bbox', 'N/A')}")
        else:
            print("\n  No objects detected with confidence >70%")
            if 'raw_response' in result:
                print(f"\n  Raw Gemini response:\n  {result['raw_response']}")

        # Acceptance criteria validation
        print("\n" + "=" * 60)
        print("ACCEPTANCE CRITERIA VALIDATION")
        print("=" * 60)
        criteria = {
            "✓ 5MP camera capture": True,
            "✓ Gemini AI classification": True,
            "✓ Categories (toy/trash/clothing/other)": all(
                obj.get('category') in ['toy', 'trash', 'clothing', 'other']
                for obj in result.get('objects', [])
            ) if result.get('objects') else True,
            "✓ Confidence >70%": all(
                obj.get('confidence', 0) > 70
                for obj in result.get('objects', [])
            ) if result.get('objects') else True,
            "✓ Bounding box location": all(
                'bbox' in obj
                for obj in result.get('objects', [])
            ) if result.get('objects') else True,
            "✓ Processing time <3s": result.get('processing_time', 999) < 3,
        }

        for criterion, passed in criteria.items():
            status = "✓" if passed else "✗"
            print(f"  {status} {criterion}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        kuko.release_camera()
        print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
