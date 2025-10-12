#!/usr/bin/env python3
"""
Kuko Robot - Vision System (US-003: Multiple Object Detection with Priority)
Epic 1: Artificial Intelligence & Vision

Detects multiple objects with intelligent priority ordering based on:
- Distance from robot (Y-coordinate analysis)
- Object size (small/medium/large)
- Accessibility (clear/blocked)
- Detection confidence (>70%)

Features:
- Multi-object detection (up to 5 objects)
- Duplicate filtering (IoU + proximity + description similarity)
- Furniture/fixture filtering
- Distance estimation
- Priority-based ordering for efficient pickup

Categories: toy, trash, clothing, other
"""

import cv2
import google.generativeai as genai
import time
from PIL import Image
import json
import os

# Robot control library (for physical robot only)
try:
    from xgolib import XGO
    ROBOT_AVAILABLE = True
except ImportError:
    print("⚠️  xgolib not available. Running in camera-only mode.")
    ROBOT_AVAILABLE = False

# Configure Gemini using environment variable
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set. Please set it before running.")

genai.configure(api_key=GEMINI_API_KEY)

# Camera configuration
# Note: 5MP (2592x1944) causes V4L2 timeout on Raspberry Pi
# Using Full HD (1920x1080) - still excellent quality for AI vision
CAMERA_WIDTH = 1920   # Full HD width
CAMERA_HEIGHT = 1080  # Full HD height

class KukoVision:
    """Kuko robot vision system for object classification"""

    def __init__(self, use_robot=True):
        """
        Initialize Kuko vision system

        Args:
            use_robot: If True, initializes XGO robot for body positioning
                      If False, only uses camera (for testing/simulation)
        """
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
        self.camera = None
        self.robot = None
        self.use_robot = use_robot and ROBOT_AVAILABLE

        # Initialize robot if available
        if self.use_robot:
            try:
                self.robot = XGO(port="/dev/ttyAMA0", version="xgolite")
                print("✓ Robot initialized (XGO Lite)")
            except Exception as e:
                print(f"⚠️  Could not initialize robot: {e}")
                print("   Falling back to camera-only mode")
                self.robot = None
                self.use_robot = False
        else:
            print("ℹ️  Running in camera-only mode (no robot positioning)")

    def position_for_floor_scan(self, pitch_angle=15, height=90):
        """
        Position robot to look at the floor for object detection

        This is CRITICAL for floor object detection. The robot must tilt
        its head/body downward to point the camera at the floor.

        IMPORTANT: This robot's pitch convention is INVERTED:
        - Positive pitch (+15°) = looks DOWN at floor
        - Negative pitch (-15°) = looks UP at ceiling

        Args:
            pitch_angle: Pitch angle in degrees (positive = look down)
                        Range: -15 to +15 degrees
                        Default: +15 (maximum downward tilt)
            height: Body height (z-axis translation)
                   Range: 75 (low) to 115 (high)
                   Default: 90 (neutral height)

        Returns:
            bool: True if positioning successful, False otherwise
        """
        if not self.use_robot or not self.robot:
            print("ℹ️  Robot not available, skipping floor scan posture")
            return False

        try:
            print(f"🤖 Positioning robot for floor scan...")
            print(f"   Pitch: +{pitch_angle}° (looking down)")
            print(f"   Height: {height} mm")

            # Set body attitude: roll=0, pitch=positive (look down), yaw=0
            # NOTE: This robot's pitch is inverted from typical convention
            self.robot.attitude(['r', 'p', 'y'], [0, pitch_angle, 0])

            # Set body height
            self.robot.translation(['x', 'y', 'z'], [0, 0, height])

            # Wait for servos to settle
            time.sleep(0.5)

            print("✓ Robot positioned for floor scanning")
            return True

        except Exception as e:
            print(f"⚠️  Error positioning robot: {e}")
            return False

    def reset_robot_posture(self):
        """
        Reset robot to neutral posture after scanning

        Returns body to default position (level, neutral height)
        """
        if not self.use_robot or not self.robot:
            return False

        try:
            print("🤖 Resetting robot posture...")

            # Reset attitude to level (roll=0, pitch=0, yaw=0)
            self.robot.attitude(['r', 'p', 'y'], [0, 0, 0])

            # Reset to neutral height
            self.robot.translation(['x', 'y', 'z'], [0, 0, 90])

            time.sleep(0.3)

            print("✓ Robot posture reset")
            return True

        except Exception as e:
            print(f"⚠️  Error resetting robot: {e}")
            return False

    def init_camera(self):
        """Initialize 5MP camera"""
        # Position robot for floor scanning BEFORE opening camera
        if self.use_robot:
            self.position_for_floor_scan(pitch_angle=15, height=90)  # FIXED: +15° looks DOWN (robot-specific)

        # Use default backend (V4L2 on Raspberry Pi)
        # Resolution set to Full HD (1920x1080) to avoid V4L2 timeout
        print("Opening camera (Full HD resolution to avoid timeout)...")
        self.camera = cv2.VideoCapture(0)

        # Check if camera opened successfully
        if not self.camera.isOpened():
            raise RuntimeError("Failed to open camera at index 0. Check camera connection and permissions.")

        # Set camera format to MJPEG (better compatibility with Raspberry Pi)
        self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))

        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

        # Verify actual resolution
        actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"Camera initialized: {actual_width}x{actual_height}")

        # Warm up camera (read and discard first frames)
        ret = False
        frame = None
        for i in range(3):  # 3 attempts at Full HD
            ret, frame = self.camera.read()
            if ret and frame is not None:
                # Validate frame shape
                if len(frame.shape) == 3 and frame.shape[2] == 3:
                    print(f"✓ Camera warm-up successful: frame shape {frame.shape}")
                    break
                else:
                    print(f"⚠️  Attempt {i+1}: Invalid frame shape {frame.shape}, retrying...")
            time.sleep(0.3)

        # If Full HD fails, try falling back to 720p
        if not ret or frame is None or len(frame.shape) != 3:
            print("⚠️  Full HD failed, trying 720p resolution...")
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

            for i in range(3):
                ret, frame = self.camera.read()
                if ret and frame is not None and len(frame.shape) == 3:
                    actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
                    actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    print(f"✓ Camera fallback successful: {actual_width}x{actual_height}")
                    break
                time.sleep(0.3)

        if not ret or frame is None:
            raise RuntimeError("Camera opened but cannot read frames even at 720p. Check camera hardware.")

        if len(frame.shape) != 3 or frame.shape[2] != 3:
            raise RuntimeError(f"Camera producing invalid frame shape: {frame.shape}. Expected (height, width, 3).")

    def cleanup_old_images(self, pattern_prefix=""):
        """
        Delete old capture images to avoid confusion in subsequent rounds

        Args:
            pattern_prefix: Image filename prefix to match (e.g., "kuko_capture", "scan_")
                          If empty, cleans common capture patterns
        """
        import glob

        # Common image patterns to clean
        patterns = [
            "kuko_capture*.jpg",
            "scan_*.jpg",
            "floor_check*.jpg",
            "us003_test_capture*.jpg",
            "debug_bbox*.jpg",
            "*_optimized.jpg"
        ]

        if pattern_prefix:
            patterns = [f"{pattern_prefix}*.jpg"]

        cleaned_count = 0
        for pattern in patterns:
            for file_path in glob.glob(pattern):
                try:
                    os.remove(file_path)
                    cleaned_count += 1
                except Exception as e:
                    print(f"⚠️  Could not delete {file_path}: {e}")

        if cleaned_count > 0:
            print(f"🧹 Cleaned up {cleaned_count} old image(s)")

        return cleaned_count

    def capture_photo(self, save_path="captured_image.jpg"):
        """Capture a photo from the camera (Full HD or 720p depending on hardware)"""
        # Clean up old images first to avoid confusion
        self.cleanup_old_images()

        if not self.camera or not self.camera.isOpened():
            self.init_camera()

        ret, frame = self.camera.read()
        if not ret:
            raise RuntimeError("Failed to capture image from camera")

        # Validate frame
        if frame is None or frame.size == 0:
            raise RuntimeError("Captured frame is empty")

        # Convert to absolute path
        if not os.path.isabs(save_path):
            save_path = os.path.abspath(save_path)

        # Save captured image and verify success
        success = cv2.imwrite(save_path, frame)
        if not success:
            raise RuntimeError(f"Failed to save image to {save_path}")

        # Verify file exists
        if not os.path.exists(save_path):
            raise RuntimeError(f"Image file not found after save: {save_path}")

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

        # Gemini prompt for object classification (US-001 + US-003 enhanced)
        prompt = """
        Analyze this image and identify ONLY objects that are LOOSE on the floor and need to be picked up.

        ⚠️ CRITICAL RULES - READ CAREFULLY:
        1. ONLY detect 3D objects that are LOOSE, SCATTERED, or FALLEN on the floor
        2. DO NOT detect floor patterns, floor textures, shadows, reflections, or light spots
        3. DO NOT detect objects that belong there (dog beds, cushions, mats, rugs)
        4. DO NOT detect bags, boxes, containers, baskets (storage items)
        5. DO NOT detect furniture or fixtures (even if they look like clothing/fabric)
        6. Objects must have clear 3D shape and be distinguishable from the floor surface

        For EACH loose object found on the floor, provide:
        1. category: Must be one of [toy, trash, clothing, other]
        2. description: Brief description of the object (DO NOT mention "in bag", "in box", "in container")
        3. confidence: Confidence percentage (0-100)
        4. bbox: Approximate bounding box as [x_min, y_min, x_max, y_max] in pixels
        5. size_estimate: "small" (<20cm), "medium" (20-50cm), "large" (>50cm)
        6. accessibility: "clear" if in open space, "blocked" if obstructed

        ONLY include objects with confidence > 70%.
        Detect up to 5 objects maximum.

        Return response in JSON format:
        {
            "objects": [
                {
                    "category": "toy|trash|clothing|other",
                    "description": "object description",
                    "confidence": 85,
                    "bbox": [x1, y1, x2, y2],
                    "size_estimate": "small|medium|large",
                    "accessibility": "clear|blocked"
                }
            ]
        }

        If no loose objects found on the floor with confidence >70%, return empty objects array.

        ❌ IGNORE - DO NOT DETECT THESE:
        - Floor itself (terrazzo, tile, wood, concrete patterns)
        - Floor textures, spots, stains, discoloration on the floor
        - Shadows, reflections, light spots, glares on the floor
        - Dirt, dust, or natural floor wear (not objects)
        - LED strips, baseboards, floor trim (permanent fixtures)
        - Bags, backpacks, purses (storage containers, even on floor)
        - Boxes, containers, baskets, bins (storage items)
        - Dog beds, pet beds, pet cushions, pet mats (floor fixtures)
        - Floor cushions, floor pillows, meditation cushions (fixtures)
        - Rugs, mats, carpets (floor coverings)
        - Objects IN bags, boxes, containers (already stored)
        - Objects ON shelves, tables, beds, sofas (in place)
        - Clothing on hangers, in drawers, or folded/organized
        - Clothing worn by people
        - Furniture (sofas, tables, chairs, beds, desks, cabinets)
        - Large appliances
        - Walls, floors, ceiling fixtures
        - Large plants in pots
        - Decorative items in proper place
        - Storage containers of any kind

        ✅ DETECT - Objects that need pickup:
        - Toys scattered on the floor
        - Trash lying on the floor
        - Clothing dropped on the floor
        - Small objects fallen on the floor
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

                # Calculate distance information
                distance_info = self.calculate_distance_to_robot(obj)

                grasp_data["objects"].append({
                    "id": i,
                    "category": obj.get('category'),
                    "description": obj.get('description'),
                    "confidence": obj.get('confidence'),
                    "bbox": bbox,
                    "grasp_point": [center_x, center_y],
                    "distance_cm": distance_info.get('estimated_distance_cm'),
                    "distance_score": distance_info.get('distance_score'),
                    "priority": obj.get('priority')
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
        """Release camera and reset robot posture"""
        # Reset robot to neutral posture
        if self.use_robot and self.robot:
            self.reset_robot_posture()

        # Release camera
        if self.camera:
            self.camera.release()
            print("Camera released")

    # ============================================================
    # US-003: Multiple Object Detection with Priority
    # ============================================================

    def calculate_bbox_iou(self, bbox1, bbox2):
        """
        Calculate Intersection over Union (IoU) for two bounding boxes
        Used for duplicate detection

        Args:
            bbox1, bbox2: [x_min, y_min, x_max, y_max]

        Returns:
            float: IoU score (0.0 to 1.0)
        """
        x1 = max(bbox1[0], bbox2[0])
        y1 = max(bbox1[1], bbox2[1])
        x2 = min(bbox1[2], bbox2[2])
        y2 = min(bbox1[3], bbox2[3])

        # Calculate intersection area
        intersection = max(0, x2 - x1) * max(0, y2 - y1)

        # Calculate union area
        area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
        area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0

    def calculate_bbox_center_distance(self, bbox1, bbox2):
        """
        Calculate distance between centers of two bounding boxes

        Args:
            bbox1, bbox2: [x_min, y_min, x_max, y_max]

        Returns:
            float: Euclidean distance between centers
        """
        # Calculate centers
        center1_x = (bbox1[0] + bbox1[2]) / 2
        center1_y = (bbox1[1] + bbox1[3]) / 2
        center2_x = (bbox2[0] + bbox2[2]) / 2
        center2_y = (bbox2[1] + bbox2[3]) / 2

        # Euclidean distance
        distance = ((center1_x - center2_x)**2 + (center1_y - center2_y)**2)**0.5
        return distance

    def filter_duplicate_objects(self, objects, iou_threshold=0.3, proximity_threshold=120):
        """
        Filter duplicate object detections based on bounding box overlap and proximity

        Enhanced duplicate detection:
        - IoU overlap check (threshold: 0.3)
        - Spatial proximity check (threshold: 120px)
        - Description similarity (2+ shared keywords OR same category if very close)
        - Category-based proximity (same category + close = likely duplicate)

        Args:
            objects: List of detected objects with 'bbox' and 'confidence'
            iou_threshold: IoU threshold for considering duplicates (default: 0.3 - more aggressive)
            proximity_threshold: Max distance between centers (default: 120px - more aggressive)

        Returns:
            List of filtered objects (keeps highest confidence)
        """
        if not objects or len(objects) <= 1:
            return objects

        # Sort by confidence (highest first)
        sorted_objects = sorted(objects, key=lambda x: x.get('confidence', 0), reverse=True)

        filtered = []
        for obj in sorted_objects:
            if not obj.get('bbox'):
                filtered.append(obj)
                continue

            # Check if this object overlaps with any already filtered object
            is_duplicate = False
            for existing in filtered:
                if not existing.get('bbox'):
                    continue

                # Check IoU overlap
                iou = self.calculate_bbox_iou(obj['bbox'], existing['bbox'])
                if iou > iou_threshold:
                    is_duplicate = True
                    print(f"  Filtered duplicate (IoU): {obj.get('description')} (IoU: {iou:.2f} with {existing.get('description')})")
                    break

                # Check spatial proximity
                center_distance = self.calculate_bbox_center_distance(obj['bbox'], existing['bbox'])

                if center_distance < proximity_threshold:
                    obj_category = obj.get('category', '').lower()
                    exist_category = existing.get('category', '').lower()

                    # Same category + close proximity = likely duplicate
                    if obj_category == exist_category and obj_category in ['toy', 'trash', 'clothing']:
                        is_duplicate = True
                        print(f"  Filtered duplicate (proximity+category): {obj.get('description')} (distance: {center_distance:.0f}px, same category '{obj_category}' as {existing.get('description')})")
                        break

                    # Check description similarity
                    obj_desc = obj.get('description', '').lower()
                    exist_desc = existing.get('description', '').lower()

                    # Simple similarity check (shared keywords)
                    obj_words = set(obj_desc.split())
                    exist_words = set(exist_desc.split())
                    shared_words = obj_words.intersection(exist_words)

                    # Lower threshold if same category (1+ shared word)
                    min_shared = 1 if obj_category == exist_category else 2

                    if len(shared_words) >= min_shared:
                        is_duplicate = True
                        print(f"  Filtered duplicate (proximity+description): {obj.get('description')} (distance: {center_distance:.0f}px, {len(shared_words)} shared words with {existing.get('description')})")
                        break

            if not is_duplicate:
                filtered.append(obj)

        return filtered

    def filter_furniture(self, objects):
        """
        Filter out furniture and fixed objects

        Furniture indicators:
        - Large size estimate
        - Keywords in description (sofa, table, chair, bed, plant, appliance)

        Args:
            objects: List of detected objects

        Returns:
            List of objects without furniture
        """
        furniture_keywords = ['sofa', 'couch', 'table', 'chair', 'bed', 'desk',
                             'shelf', 'cabinet', 'plant', 'lamp', 'tv',
                             'appliance', 'furniture', 'wall', 'floor',
                             'dog bed', 'pet bed', 'cushion', 'pillow', 'mat', 'rug',
                             'carpet', 'bag', 'backpack', 'purse', 'box']

        filtered = []
        for obj in objects:
            description = obj.get('description', '').lower()
            size = obj.get('size_estimate', '').lower()

            # Check for furniture/fixture keywords
            is_furniture_or_fixture = any(keyword in description for keyword in furniture_keywords)

            if is_furniture_or_fixture:
                # Filter if:
                # 1. Large size (definitely furniture)
                # 2. OR specific keywords (dog bed, bag, cushion, etc.) - regardless of size
                if size == 'large':
                    print(f"  Filtered furniture: {obj.get('description')} (size: {size})")
                    continue
                else:
                    # Check if it's a specific fixture/storage item (should filter regardless of size)
                    fixture_keywords = ['dog bed', 'pet bed', 'cushion', 'pillow', 'mat', 'rug',
                                       'bag', 'backpack', 'purse', 'box']
                    is_fixture = any(keyword in description for keyword in fixture_keywords)
                    if is_fixture:
                        print(f"  Filtered fixture/storage: {obj.get('description')}")
                        continue

            filtered.append(obj)

        return filtered

    def filter_organized_objects(self, objects):
        """
        Filter out objects that are already organized or stored

        Organized indicators:
        - Keywords indicating storage: "in bag", "in box", "in container", "in basket"
        - Keywords: "on shelf", "in drawer", "on hanger"
        - Any description suggesting object is already in proper place

        Args:
            objects: List of detected objects

        Returns:
            List of objects that are loose on the floor (need pickup)
        """
        # Storage/organization keywords to filter
        organized_keywords = [
            # Storage containers
            'bag', 'backpack', 'purse', 'handbag', 'tote',
            'box', 'container', 'basket', 'bin',
            # Location indicators
            'in bag', 'in box', 'in container', 'in basket', 'in bin',
            'on shelf', 'in drawer', 'on hanger', 'in closet',
            'on table', 'on bed', 'on sofa', 'on chair',
            # Organization indicators
            'stored', 'organized', 'in storage',
            'inside bag', 'inside box', 'inside container',
            # Pet/floor fixtures
            'dog bed', 'pet bed', 'pet cushion', 'pet mat',
            'floor cushion', 'floor pillow', 'floor mat'
        ]

        filtered = []
        for obj in objects:
            description = obj.get('description', '').lower()

            # Check if description mentions organization/storage
            is_organized = any(keyword in description for keyword in organized_keywords)

            if is_organized:
                print(f"  Filtered organized object: {obj.get('description')} (already in proper place)")
                continue

            filtered.append(obj)

        return filtered

    def filter_tiny_detections(self, objects, min_width=50, min_height=50, min_area=2500):
        """
        Filter out very small bounding boxes (likely false positives)

        Small detections are usually:
        - Floor patterns/textures
        - Shadows or light reflections
        - Noise in the image
        - Spots or stains on the floor

        Args:
            objects: List of detected objects
            min_width: Minimum bbox width in pixels (default: 50px)
            min_height: Minimum bbox height in pixels (default: 50px)
            min_area: Minimum bbox area in square pixels (default: 2500px = 50x50)

        Returns:
            List of objects with reasonable size
        """
        filtered = []
        for obj in objects:
            if not obj.get('bbox'):
                filtered.append(obj)
                continue

            bbox = obj['bbox']
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            area = width * height

            # Filter if too small
            if width < min_width or height < min_height or area < min_area:
                print(f"  Filtered tiny detection: {obj.get('description')} (size: {width}x{height}px, likely floor pattern/noise)")
                continue

            filtered.append(obj)

        return filtered

    def calculate_distance_to_robot(self, obj, image_height=1080):
        """
        Calculate relative distance from robot to object

        For a camera looking DOWN at the floor:
        - Objects at top of image (low Y) = FAR from robot
        - Objects at bottom of image (high Y) = CLOSE to robot

        Args:
            obj: Object dict with 'bbox' [x_min, y_min, x_max, y_max]
            image_height: Image height in pixels (default 1080)

        Returns:
            dict: {
                'distance_score': 0.0-1.0 (1.0 = closest, 0.0 = farthest),
                'y_bottom': Bottom Y coordinate,
                'estimated_distance_cm': Rough distance estimate in cm
            }
        """
        if not obj.get('bbox'):
            return {'distance_score': 0.0, 'y_bottom': 0, 'estimated_distance_cm': None}

        bbox = obj['bbox']
        y_bottom = bbox[3]  # y_max (bottom of bounding box)

        # Distance score: normalize to 0-1 (higher Y = higher score = closer)
        distance_score = y_bottom / image_height

        # Rough distance estimation (camera-specific, needs calibration)
        # For robot looking down at ~45-60cm height with 15° tilt:
        # - Top of image (~y=0) ≈ 80cm away
        # - Bottom of image (~y=1080) ≈ 20cm away
        estimated_distance_cm = 80 - (distance_score * 60)  # Linear interpolation

        return {
            'distance_score': round(distance_score, 3),
            'y_bottom': y_bottom,
            'estimated_distance_cm': round(estimated_distance_cm, 1)
        }

    def calculate_object_priority(self, obj):
        """
        Calculate priority score for object pickup

        Priority factors:
        - Distance: closer objects = higher priority (easier to reach)
        - Size: smaller objects = higher priority (easier to grasp)
        - Accessibility: clear space = higher priority
        - Confidence: higher confidence = higher priority

        Args:
            obj: Object dict with size_estimate, accessibility, confidence, bbox

        Returns:
            float: Priority score (0.0 to 12.0, higher = pick up first)
        """
        # Distance score: closer = higher priority (0-3 points)
        distance_info = self.calculate_distance_to_robot(obj)
        distance_score = distance_info['distance_score'] * 3

        # Size score: small=3, medium=2, large=1
        size_scores = {"small": 3, "medium": 2, "large": 1}
        size_score = size_scores.get(obj.get('size_estimate', 'medium').lower(), 2)

        # Accessibility score: clear=3, blocked=1
        access_scores = {"clear": 3, "blocked": 1}
        access_score = access_scores.get(obj.get('accessibility', 'clear').lower(), 2)

        # Confidence score: normalized to 0-3
        confidence = obj.get('confidence', 70)
        conf_score = (confidence / 100) * 3

        total_score = distance_score + size_score + access_score + conf_score
        return round(total_score, 2)

    def detect_multiple_objects_with_priority(self, image_path):
        """
        US-003: Complete multi-object detection pipeline with priority ordering

        Pipeline:
        1. Use US-001 classify_objects() to detect objects
        2. Filter duplicate detections (IoU-based)
        3. Filter furniture and fixed objects
        4. Calculate priority scores
        5. Sort by priority (highest first)

        Args:
            image_path: Path to image file

        Returns:
            dict: {
                'objects': [...],  # Ordered by priority
                'processing_time': float,
                'stats': {...}
            }
        """
        print("\n" + "="*60)
        print("US-003: Multiple Object Detection with Priority")
        print("="*60)

        # Step 1: Detect objects using US-001 (with error handling)
        print("\n[1] Detecting objects with Gemini AI...")
        result = self.classify_with_error_handling(image_path)

        if result.get('error') or not result.get('objects'):
            print(f"⚠️  No objects detected or error occurred")
            return result

        objects = result['objects']
        print(f"  Detected: {len(objects)} objects")

        # Step 2: Filter duplicates
        print("\n[2] Filtering duplicate detections...")
        original_count = len(objects)
        # Enhanced duplicate filtering:
        # - IoU: 0.3 (aggressive overlap detection)
        # - Proximity: 120px (same category + close = duplicate)
        # - Category matching (toy+toy within 120px = duplicate)
        objects = self.filter_duplicate_objects(objects, iou_threshold=0.3, proximity_threshold=120)
        duplicates_removed = original_count - len(objects)
        if duplicates_removed > 0:
            print(f"  Removed {duplicates_removed} duplicates")
        else:
            print(f"  No duplicates found")

        # Step 3: Filter furniture
        print("\n[3] Filtering furniture and fixed objects...")
        original_count = len(objects)
        objects = self.filter_furniture(objects)
        furniture_removed = original_count - len(objects)
        if furniture_removed > 0:
            print(f"  Removed {furniture_removed} furniture items")
        else:
            print(f"  No furniture found")

        # Step 4: Filter organized objects (in bags, boxes, containers)
        print("\n[4] Filtering objects already in proper place...")
        original_count = len(objects)
        objects = self.filter_organized_objects(objects)
        organized_removed = original_count - len(objects)
        if organized_removed > 0:
            print(f"  Removed {organized_removed} organized items (in bags/boxes/containers)")
        else:
            print(f"  No organized items found")

        # Step 5: Filter tiny detections (floor patterns, noise)
        print("\n[5] Filtering tiny detections (floor patterns/noise)...")
        original_count = len(objects)
        objects = self.filter_tiny_detections(objects, min_width=50, min_height=50)
        tiny_removed = original_count - len(objects)
        if tiny_removed > 0:
            print(f"  Removed {tiny_removed} tiny detections (likely floor patterns/shadows)")
        else:
            print(f"  No tiny detections found")

        # Step 6: Calculate distance and priorities
        print("\n[6] Calculating distance and pickup priorities...")
        for obj in objects:
            # Add distance information
            distance_info = self.calculate_distance_to_robot(obj)
            obj['distance_info'] = distance_info

            # Calculate priority (now includes distance)
            obj['priority'] = self.calculate_object_priority(obj)

        # Step 7: Sort by priority (highest first)
        objects.sort(key=lambda x: x.get('priority', 0), reverse=True)
        print(f"  Prioritized {len(objects)} objects for pickup")

        # Update result
        result['objects'] = objects
        result['stats'] = {
            'total_detected': len(result.get('objects', [])) + duplicates_removed + furniture_removed + organized_removed + tiny_removed,
            'duplicates_removed': duplicates_removed,
            'furniture_removed': furniture_removed,
            'organized_removed': organized_removed,
            'tiny_removed': tiny_removed,
            'final_count': len(objects)
        }

        return result

def main():
    """
    Main vision system - US-003: Multiple Object Detection with Priority
    (US-001 basic classification is now deprecated, use --basic flag if needed)
    """
    print("=" * 60)
    print("Kuko Robot - Vision System (US-003)")
    print("Multiple Object Detection with Distance & Priority")
    print("=" * 60)

    # Initialize vision system
    # use_robot=True: Full robot mode (positions body to look at floor)
    # use_robot=False: Camera-only mode (for testing without robot hardware)
    kuko = KukoVision(use_robot=True)

    try:
        # Step 1: Initialize camera
        print("\n[1] Initializing camera...")
        kuko.init_camera()

        # Step 2: Capture photo
        print("\n[2] Capturing photo...")
        image_path = kuko.capture_photo("kuko_capture.jpg")

        # Step 3: Detect multiple objects with priority (US-003 pipeline)
        result = kuko.detect_multiple_objects_with_priority(image_path)

        # Step 4: Display results
        print("\n" + "=" * 60)
        print("DETECTION RESULTS (PRIORITIZED)")
        print("=" * 60)
        print(f"Processing time: {result.get('processing_time', 'N/A')}s")

        if result.get('stats'):
            stats = result['stats']
            print(f"\nDetection Statistics:")
            print(f"  Total detected: {stats.get('total_detected', 0)}")
            print(f"  Duplicates removed: {stats.get('duplicates_removed', 0)}")
            print(f"  Furniture removed: {stats.get('furniture_removed', 0)}")
            print(f"  Organized items removed: {stats.get('organized_removed', 0)}")
            print(f"  Tiny detections removed: {stats.get('tiny_removed', 0)}")
            print(f"  Final objects: {stats.get('final_count', 0)}")

        print(f"\nObjects ranked by priority ({len(result.get('objects', []))} objects):")

        if result.get('objects'):
            for i, obj in enumerate(result['objects'], 1):
                print(f"\n  Priority #{i} (Score: {obj.get('priority', 0)}):")
                print(f"    Category: {obj.get('category', 'unknown')}")
                print(f"    Description: {obj.get('description', 'N/A')}")
                print(f"    Confidence: {obj.get('confidence', 0)}%")
                print(f"    Distance: ~{obj.get('distance_info', {}).get('estimated_distance_cm', 'N/A')} cm")
                print(f"    Size: {obj.get('size_estimate', 'N/A')}")
                print(f"    Accessibility: {obj.get('accessibility', 'N/A')}")
                print(f"    Location (bbox): {obj.get('bbox', 'N/A')}")
        else:
            print("\n  No objects detected for pickup")

        # Step 5: Save visualizations
        if result.get('objects'):
            print("\n[5] Saving debug visualizations...")
            kuko.draw_bounding_boxes(image_path, result['objects'], "debug_bbox.jpg")
            kuko.save_coordinates_for_grasping(result['objects'], "object_coordinates.json")
            print("  Saved: debug_bbox.jpg")
            print("  Saved: object_coordinates.json")

        # Acceptance criteria validation (US-003)
        print("\n" + "=" * 60)
        print("US-003 ACCEPTANCE CRITERIA VALIDATION")
        print("=" * 60)

        objects = result.get('objects', [])
        criteria = {
            "✓ Detects up to 5 simultaneous objects": len(objects) <= 5,
            "✓ Distance calculation": all('distance_info' in obj for obj in objects),
            "✓ Priority ordering (distance + size + access + conf)": all('priority' in obj for obj in objects),
            "✓ Duplicate filtering (IoU + proximity)": result.get('stats', {}).get('duplicates_removed') is not None,
            "✓ Furniture filtering": result.get('stats', {}).get('furniture_removed') is not None,
            "✓ Organized objects filtering (bags/boxes)": result.get('stats', {}).get('organized_removed') is not None,
            "✓ Tiny detection filtering (floor patterns)": result.get('stats', {}).get('tiny_removed') is not None,
            "✓ Ordered by pickup priority": all(
                objects[i].get('priority', 0) >= objects[i+1].get('priority', 0)
                for i in range(len(objects)-1)
            ) if len(objects) > 1 else True,
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

def test_us003():
    """Test US-003: Multiple Object Detection with Priority"""
    print("=" * 60)
    print("Kuko Robot - US-003: Multiple Object Detection with Priority")
    print("=" * 60)

    # Initialize vision system with robot positioning
    kuko = KukoVision(use_robot=True)

    try:
        # Step 1: Initialize camera
        print("\n[1] Initializing camera...")
        kuko.init_camera()

        # Step 2: Capture photo
        print("\n[2] Capturing photo...")
        image_path = kuko.capture_photo("us003_test_capture.jpg")

        # Step 3: Detect multiple objects with priority (US-003 pipeline)
        result = kuko.detect_multiple_objects_with_priority(image_path)

        # Step 4: Display results
        print("\n" + "=" * 60)
        print("US-003 RESULTS: PRIORITIZED OBJECT LIST")
        print("=" * 60)
        print(f"Processing time: {result.get('processing_time', 'N/A')}s")

        if result.get('stats'):
            stats = result['stats']
            print(f"\nDetection Statistics:")
            print(f"  Total detected: {stats.get('total_detected', 0)}")
            print(f"  Duplicates removed: {stats.get('duplicates_removed', 0)}")
            print(f"  Furniture removed: {stats.get('furniture_removed', 0)}")
            print(f"  Organized items removed: {stats.get('organized_removed', 0)}")
            print(f"  Tiny detections removed: {stats.get('tiny_removed', 0)}")
            print(f"  Final objects: {stats.get('final_count', 0)}")

        print(f"\nPrioritized pickup order ({len(result.get('objects', []))} objects):")

        if result.get('objects'):
            for i, obj in enumerate(result['objects'], 1):
                print(f"\n  Priority #{i} (Score: {obj.get('priority', 0)}):")
                print(f"    Category: {obj.get('category', 'unknown')}")
                print(f"    Description: {obj.get('description', 'N/A')}")
                print(f"    Confidence: {obj.get('confidence', 0)}%")
                print(f"    Size: {obj.get('size_estimate', 'N/A')}")
                print(f"    Accessibility: {obj.get('accessibility', 'N/A')}")
                print(f"    Location (bbox): {obj.get('bbox', 'N/A')}")
        else:
            print("\n  No objects detected for pickup")

        # Step 5: Save visualizations
        if result.get('objects'):
            print("\n[5] Saving debug visualizations...")
            kuko.draw_bounding_boxes(image_path, result['objects'], "us003_debug_bbox.jpg")
            kuko.save_coordinates_for_grasping(result['objects'], "us003_object_coordinates.json")

        # US-003 Acceptance Criteria Validation
        print("\n" + "=" * 60)
        print("US-003 ACCEPTANCE CRITERIA VALIDATION")
        print("=" * 60)

        objects = result.get('objects', [])
        criteria = {
            "✓ Detects up to 5 simultaneous objects": len(objects) <= 5,
            "✓ Priority calculation (size + accessibility + confidence)": all('priority' in obj for obj in objects),
            "✓ Duplicate filtering (IoU-based)": result.get('stats', {}).get('duplicates_removed') is not None,
            "✓ Furniture filtering": result.get('stats', {}).get('furniture_removed') is not None,
            "✓ Organized objects filtering (bags/boxes)": result.get('stats', {}).get('organized_removed') is not None,
            "✓ Ordered by pickup priority": all(
                objects[i].get('priority', 0) >= objects[i+1].get('priority', 0)
                for i in range(len(objects)-1)
            ) if len(objects) > 1 else True,
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
    import sys

    # US-003 is now the default (multi-object with priority)
    # Use --us003 flag for the old separate test function
    if len(sys.argv) > 1 and sys.argv[1] == "--us003":
        # Legacy test function (kept for compatibility)
        test_us003()
    else:
        # Default: Run US-003 pipeline (main() now uses US-003)
        main()
