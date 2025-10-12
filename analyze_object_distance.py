#!/usr/bin/env python3
"""
Analyze object distances from robot based on bounding box coordinates
For use with object_coordinates.json output from kuko_vision_mvp.py
"""

import json
import sys

def calculate_distance_from_bbox(bbox, image_height=1080):
    """
    Calculate relative distance from robot based on Y coordinate

    For camera looking DOWN at floor:
    - Higher Y (bottom of image) = CLOSER to robot
    - Lower Y (top of image) = FARTHER from robot

    Args:
        bbox: [x_min, y_min, x_max, y_max]
        image_height: Image height in pixels

    Returns:
        dict with distance info
    """
    y_bottom = bbox[3]  # Bottom of bounding box
    distance_score = y_bottom / image_height

    # Rough distance estimate (needs camera calibration)
    # Assuming robot height ~45cm, camera tilt 15°:
    # - Top of image (y=0) ≈ 80cm away
    # - Bottom of image (y=1080) ≈ 20cm away
    estimated_distance_cm = 80 - (distance_score * 60)

    return {
        'y_bottom': y_bottom,
        'distance_score': distance_score,
        'estimated_distance_cm': round(estimated_distance_cm, 1)
    }

def analyze_object_file(json_file):
    """Analyze objects from JSON file"""
    with open(json_file, 'r') as f:
        data = json.load(f)

    print("="*60)
    print("Object Distance Analysis")
    print("="*60)
    print(f"Timestamp: {data.get('timestamp', 'N/A')}")
    print(f"Total objects: {len(data['objects'])}")
    print()

    # Calculate distance for each object
    objects_with_distance = []
    for obj in data['objects']:
        bbox = obj['bbox']
        distance_info = calculate_distance_from_bbox(bbox)

        obj_analysis = {
            'id': obj['id'],
            'category': obj['category'],
            'description': obj['description'],
            'confidence': obj['confidence'],
            'bbox': bbox,
            'grasp_point': obj['grasp_point'],
            **distance_info
        }
        objects_with_distance.append(obj_analysis)

    # Sort by distance (closest first)
    objects_with_distance.sort(key=lambda x: x['distance_score'], reverse=True)

    print("Objects ranked by distance (closest first):")
    print("-" * 60)
    for rank, obj in enumerate(objects_with_distance, 1):
        print(f"\n{rank}. {obj['category'].upper()} (Object ID: {obj['id']})")
        print(f"   Description: {obj['description']}")
        print(f"   Confidence: {obj['confidence']}%")
        print(f"   Bounding box: {obj['bbox']}")
        print(f"   Y-bottom coordinate: {obj['y_bottom']} px")
        print(f"   Distance score: {obj['distance_score']:.3f} (1.0 = closest)")
        print(f"   Estimated distance: ~{obj['estimated_distance_cm']} cm")
        print(f"   Grasp point (x,y): ({obj['grasp_point'][0]:.0f}, {obj['grasp_point'][1]:.0f})")

    print("\n" + "="*60)
    print(f"🎯 NEAREST OBJECT: {objects_with_distance[0]['category'].upper()}")
    print(f"   ID: {objects_with_distance[0]['id']}")
    print(f"   Distance: ~{objects_with_distance[0]['estimated_distance_cm']} cm")
    print("="*60)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_object_distance.py <object_coordinates.json>")
        print("\nAnalyzing example data from your message...")

        # Use the example data from user's message
        example_data = {
            "timestamp": "2025-10-13 01:47:03",
            "objects": [
                {
                    "id": 0,
                    "category": "toy",
                    "description": "Pink stuffed animal with blue feet lying on the floor.",
                    "confidence": 94,
                    "bbox": [309, 169, 585, 349],
                    "grasp_point": [447.0, 259.0]
                },
                {
                    "id": 1,
                    "category": "toy",
                    "description": "Green and red stuffed animal lying on the floor.",
                    "confidence": 96,
                    "bbox": [627, 388, 962, 646],
                    "grasp_point": [794.5, 517.0]
                },
                {
                    "id": 2,
                    "category": "toy",
                    "description": "White fluffy stuffed animal behind the green and red one.",
                    "confidence": 86,
                    "bbox": [619, 107, 869, 379],
                    "grasp_point": [744.0, 243.0]
                }
            ]
        }

        # Analyze example
        print("="*60)
        print("Object Distance Analysis (EXAMPLE)")
        print("="*60)
        print(f"Timestamp: {example_data['timestamp']}")
        print(f"Total objects: {len(example_data['objects'])}")
        print()

        objects_with_distance = []
        for obj in example_data['objects']:
            distance_info = calculate_distance_from_bbox(obj['bbox'])
            objects_with_distance.append({**obj, **distance_info})

        objects_with_distance.sort(key=lambda x: x['distance_score'], reverse=True)

        print("Objects ranked by distance (closest first):")
        print("-" * 60)
        for rank, obj in enumerate(objects_with_distance, 1):
            print(f"\n{rank}. {obj['category'].upper()} (Object ID: {obj['id']})")
            print(f"   Description: {obj['description']}")
            print(f"   Y-bottom: {obj['y_bottom']} px")
            print(f"   Distance score: {obj['distance_score']:.3f}")
            print(f"   Estimated distance: ~{obj['estimated_distance_cm']} cm")

        print("\n" + "="*60)
        print(f"🎯 NEAREST OBJECT: Object {objects_with_distance[0]['id']} - {objects_with_distance[0]['category'].upper()}")
        print(f"   {objects_with_distance[0]['description']}")
        print(f"   Distance: ~{objects_with_distance[0]['estimated_distance_cm']} cm")
        print("="*60)

    else:
        analyze_object_file(sys.argv[1])
