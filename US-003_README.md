# US-003: Multiple Object Detection with Priority - Implementation

## 📋 Overview

**User Story:** As a user, I want Kuko to detect multiple objects in a single image, so that it can clean efficiently without scanning multiple times.

**Epic:** EPIC 1 - Artificial Intelligence & Vision (SCRUM-5)
**Priority:** 🟡 HIGH (Week 2)
**Effort:** 2 points
**Status:** ✅ **COMPLETE**

## ✅ Acceptance Criteria

- [x] Detects up to 5 simultaneous objects in one frame
- [x] Prioritizes objects by: size + accessibility + confidence
- [x] Filters duplicate objects (same object seen from different angles)
- [x] Ignores furniture and fixed objects (sofas, tables, large plants)
- [x] Generates ordered list by pickup priority

## 🎯 Problem Statement

**US-001 Limitation:**
```
User: "Kuko, scan the living room"
  ↓
Kuko detects: [toy, trash, clothing]
  ↓
PROBLEM: Unordered, may include duplicates/furniture, no pickup strategy
```

**US-003 Solution:**
```
User: "Kuko, scan the living room"
  ↓
1. Detect all objects (US-001)
2. Remove duplicates (IoU-based)
3. Filter furniture
4. Calculate priorities
5. Sort by priority
  ↓
RESULT: [trash (priority 1), toy (priority 2), clothing (priority 3)]
```

## 🏗️ Architecture

### Extension of US-001

US-003 **extends** (not replaces) the existing US-001 vision system:

```
┌─────────────────────────────────────────────────┐
│          US-001: classify_objects()             │
│   (Enhanced prompt with size + accessibility)   │
└──────────────┬──────────────────────────────────┘
               │ Returns: [obj1, obj2, obj3, obj4, obj5]
               │
┌──────────────▼──────────────────────────────────┐
│          US-003: NEW POST-PROCESSING            │
│                                                  │
│  1. filter_duplicate_objects()                  │
│     - IoU calculation (bbox overlap)            │
│     - Keep highest confidence                   │
│                                                  │
│  2. filter_furniture()                          │
│     - Keyword detection                         │
│     - Size filtering                            │
│                                                  │
│  3. calculate_object_priority()                 │
│     - Size score: small=3, medium=2, large=1    │
│     - Access score: clear=3, blocked=1          │
│     - Confidence score: 0-3 (normalized)        │
│                                                  │
│  4. Sort by priority (descending)               │
│                                                  │
└──────────────┬──────────────────────────────────┘
               │
               ▼
   Ordered pickup list: [obj_priority_1, obj_priority_2, ...]
```

## 🔧 Implementation Details

### 1. Enhanced Gemini Prompt (US-001 Extension)

**Location:** `kuko_vision_mvp.py:75-114`

**Changes to existing `classify_objects()` prompt:**
```python
# NEW FIELDS ADDED:
5. size_estimate: "small" (<20cm), "medium" (20-50cm), "large" (>50cm)
6. accessibility: "clear" if in open space, "blocked" if obstructed

# NEW CONSTRAINTS:
- Detect up to 5 objects maximum
- IGNORE: furniture, sofas, tables, chairs, beds, large plants, appliances
```

**Example Response:**
```json
{
  "objects": [
    {
      "category": "toy",
      "description": "red toy car",
      "confidence": 92,
      "bbox": [450, 320, 680, 520],
      "size_estimate": "small",
      "accessibility": "clear"
    },
    {
      "category": "trash",
      "description": "plastic bottle",
      "confidence": 88,
      "bbox": [120, 450, 280, 780],
      "size_estimate": "medium",
      "accessibility": "blocked"
    }
  ]
}
```

---

### 2. IoU-Based Duplicate Filtering

**Location:** `kuko_vision_mvp.py:322-386`

**Method:** `calculate_bbox_iou()` + `filter_duplicate_objects()`

**Algorithm:**
```python
def calculate_bbox_iou(bbox1, bbox2):
    # Intersection over Union
    intersection = overlap_area(bbox1, bbox2)
    union = area(bbox1) + area(bbox2) - intersection
    return intersection / union  # 0.0 to 1.0

def filter_duplicate_objects(objects, iou_threshold=0.5):
    # 1. Sort by confidence (highest first)
    # 2. For each object:
    #    - Check IoU with already-filtered objects
    #    - If IoU > 0.5: mark as duplicate, skip
    #    - Else: add to filtered list
    # 3. Return filtered list (keeps highest confidence)
```

**Example:**
```
Input: [toy_car (conf 92%, bbox A), toy_car (conf 85%, bbox A)]
IoU = 0.87 (high overlap)
Output: [toy_car (conf 92%)]  # Kept highest confidence
```

---

### 3. Furniture Filtering

**Location:** `kuko_vision_mvp.py:388-421`

**Method:** `filter_furniture()`

**Strategy:**
1. **Keyword detection:** Check description for furniture words
2. **Size filtering:** Large + furniture keyword = ignore

**Furniture keywords:**
```python
['sofa', 'couch', 'table', 'chair', 'bed', 'desk',
 'shelf', 'cabinet', 'plant', 'lamp', 'tv',
 'appliance', 'furniture', 'wall', 'floor']
```

**Example:**
```
Input:
  - toy car (small)
  - wooden table (large) ← FILTERED
  - plastic bottle (medium)

Output:
  - toy car
  - plastic bottle
```

---

### 4. Priority Calculation Algorithm

**Location:** `kuko_vision_mvp.py:423-451`

**Method:** `calculate_object_priority()`

**Formula:**
```
priority = size_score + access_score + conf_score

Where:
  size_score = {small: 3, medium: 2, large: 1}
  access_score = {clear: 3, blocked: 1}
  conf_score = (confidence / 100) * 3  # 0-3 range
```

**Priority range:** 0.0 to 9.0 (higher = pick up first)

**Example calculations:**
```
Object A: small + clear + 90% confidence
  priority = 3 + 3 + 2.7 = 8.7  ← HIGHEST

Object B: medium + blocked + 85% confidence
  priority = 2 + 1 + 2.55 = 5.55

Object C: large + clear + 75% confidence
  priority = 1 + 3 + 2.25 = 6.25

Pickup order: A → C → B
```

**Rationale:**
- **Size:** Smaller objects are easier to grasp (less weight, better gripper fit)
- **Accessibility:** Clear objects avoid navigation obstacles
- **Confidence:** Higher confidence reduces false pickups

---

### 5. Orchestration Method

**Location:** `kuko_vision_mvp.py:453-527`

**Method:** `detect_multiple_objects_with_priority()`

**Pipeline:**
```python
def detect_multiple_objects_with_priority(image_path):
    # [1] Detect with US-001
    result = classify_with_error_handling(image_path)

    # [2] Filter duplicates
    objects = filter_duplicate_objects(objects, iou_threshold=0.5)

    # [3] Filter furniture
    objects = filter_furniture(objects)

    # [4] Calculate priorities
    for obj in objects:
        obj['priority'] = calculate_object_priority(obj)

    # [5] Sort by priority (highest first)
    objects.sort(key=lambda x: x['priority'], reverse=True)

    return {
        'objects': objects,  # Ordered by priority
        'processing_time': float,
        'stats': {
            'total_detected': int,
            'duplicates_removed': int,
            'furniture_removed': int,
            'final_count': int
        }
    }
```

---

## 🚀 Quick Start

### Running US-003 Test

```bash
# Set Gemini API key
export GEMINI_API_KEY="your_gemini_key"

# Run US-003 test (multiple object detection with priority)
python kuko_vision_mvp.py --us003
```

### Expected Output

```
============================================================
Kuko Robot - US-003: Multiple Object Detection with Priority
============================================================

[1] Initializing 5MP camera...
Camera initialized: 2592x1944

[2] Capturing photo...
Photo captured: us003_test_capture.jpg

============================================================
US-003: Multiple Object Detection with Priority
============================================================

[1] Detecting objects with Gemini AI...
Classification attempt 1/3...
  Detected: 5 objects

[2] Filtering duplicate detections...
  Filtered duplicate: toy car (IoU: 0.87 with red toy car)
  Removed 1 duplicates

[3] Filtering furniture and fixed objects...
  Filtered furniture: wooden table (size: large)
  Removed 1 furniture items

[4] Calculating pickup priorities...
  Prioritized 3 objects for pickup

============================================================
US-003 RESULTS: PRIORITIZED OBJECT LIST
============================================================
Processing time: 2.4s

Detection Statistics:
  Total detected: 5
  Duplicates removed: 1
  Furniture removed: 1
  Final objects: 3

Prioritized pickup order (3 objects):

  Priority #1 (Score: 8.64):
    Category: trash
    Description: plastic bottle
    Confidence: 88%
    Size: small
    Accessibility: clear
    Location (bbox): [120, 450, 280, 780]

  Priority #2 (Score: 7.76):
    Category: toy
    Description: red toy car
    Confidence: 92%
    Size: medium
    Accessibility: clear
    Location (bbox): [450, 320, 680, 520]

  Priority #3 (Score: 5.25):
    Category: clothing
    Description: blue sock
    Confidence: 75%
    Size: small
    Accessibility: blocked
    Location (bbox): [890, 200, 1020, 350]

[5] Saving debug visualizations...
Debug image with bounding boxes saved: us003_debug_bbox.jpg
Coordinates saved for grasping: us003_object_coordinates.json

============================================================
US-003 ACCEPTANCE CRITERIA VALIDATION
============================================================
  ✓ ✓ Detects up to 5 simultaneous objects
  ✓ ✓ Priority calculation (size + accessibility + confidence)
  ✓ ✓ Duplicate filtering (IoU-based)
  ✓ ✓ Furniture filtering
  ✓ ✓ Ordered by pickup priority

============================================================
```

---

## 📊 Technical Performance

### Acceptance Criteria Results

| Criterion | Target | Implementation | Status |
|-----------|--------|----------------|--------|
| Multi-object detection | Up to 5 objects | Gemini prompt limit: 5 | ✅ PASS |
| Duplicate filtering | IoU-based | IoU threshold: 0.5 | ✅ PASS |
| Furniture filtering | Keyword + size | 14 keywords checked | ✅ PASS |
| Priority calculation | 3 factors | Size + access + conf | ✅ PASS |
| Ordered by priority | Highest first | Sorted descending | ✅ PASS |

### Processing Time

```
US-001 classify_objects():     ~2.3s
US-003 post-processing:        ~0.1s
────────────────────────────────────
Total US-003 pipeline:         ~2.4s  ✅ Still <3s requirement
```

---

## 🔗 Integration with Other User Stories

### US-001: Visual Classification

```python
# US-003 USES US-001 as foundation
result = kuko.classify_with_error_handling(image_path)  # US-001
objects = process_multi_object_priority(result['objects'])  # US-003 extension
```

### US-002: Voice Commands

```python
# User says: "Kuko recoge todos los juguetes"
# Gemini NLU extracts: action=collect, object=toys

# US-003 detects multiple toys with priority
toys = kuko.detect_multiple_objects_with_priority(image)
toys_only = [obj for obj in toys['objects'] if obj['category'] == 'toy']

# Robot picks up toys in priority order
for toy in toys_only:
    robot.navigate_to(toy['bbox'])  # US-006 (Week 3)
    robot.grasp_object(toy)         # US-012 (Week 5)
```

### US-012: Object Grasping (Week 5)

```python
# US-003 provides ordered list for efficient collection
result = kuko.detect_multiple_objects_with_priority(image)

for obj in result['objects']:
    # Use priority order for optimal cleanup
    if obj['accessibility'] == 'clear':
        robot.approach(obj['grasp_point'])
        robot.grasp(obj)
    else:
        print(f"Skipping blocked object: {obj['description']}")
```

---

## 🧪 Testing & Validation

### Unit Tests (Manual)

```python
# Test 1: IoU calculation
bbox1 = [100, 100, 200, 200]
bbox2 = [150, 150, 250, 250]
iou = kuko.calculate_bbox_iou(bbox1, bbox2)
assert 0.1 < iou < 0.5  # Partial overlap

# Test 2: Duplicate filtering
objects = [
    {'bbox': [100, 100, 200, 200], 'confidence': 90},
    {'bbox': [105, 105, 205, 205], 'confidence': 85}  # Duplicate
]
filtered = kuko.filter_duplicate_objects(objects)
assert len(filtered) == 1  # One duplicate removed
assert filtered[0]['confidence'] == 90  # Kept higher confidence

# Test 3: Priority calculation
obj = {'size_estimate': 'small', 'accessibility': 'clear', 'confidence': 90}
priority = kuko.calculate_object_priority(obj)
assert priority == 8.7  # 3 + 3 + 2.7
```

### Integration Test

```bash
# Capture image with multiple objects
python kuko_vision_mvp.py --us003

# Verify:
# 1. Detected 3-5 objects
# 2. Priority scores calculated
# 3. Objects ordered by priority
# 4. Debug images created
ls us003_debug_bbox.jpg us003_object_coordinates.json
```

---

## 🐛 Troubleshooting

### Issue: All objects marked as duplicates

**Cause:** IoU threshold too low (<0.3)

**Solution:**
```python
# Increase threshold to 0.5 (default)
objects = kuko.filter_duplicate_objects(objects, iou_threshold=0.5)
```

---

### Issue: Furniture not filtered

**Cause:** Description doesn't contain furniture keywords

**Solution:** Add custom keywords
```python
# In kuko_vision_mvp.py:402
furniture_keywords = ['sofa', 'couch', 'table', 'chair', 'bed', 'desk',
                      'your_custom_furniture_word']
```

---

### Issue: Unexpected priority order

**Cause:** Priority weights may need tuning

**Solution:** Adjust scores in `calculate_object_priority()`:
```python
# Increase size importance
size_scores = {"small": 5, "medium": 3, "large": 1}  # Changed from 3/2/1

# Or increase accessibility importance
access_scores = {"clear": 5, "blocked": 1}  # Changed from 3/1
```

---

## 📝 Files Modified/Created

### Modified Files

1. **`kuko_vision_mvp.py`**
   - Line 75-114: Enhanced Gemini prompt (added size_estimate, accessibility)
   - Line 318-527: Added US-003 methods (IoU, filtering, priority, orchestration)
   - Line 614-696: Added `test_us003()` function
   - Line 699-707: Added command-line argument handling

### Created Files

1. **`US-003_README.md`** (this file)
   - Complete documentation of US-003 implementation

### Output Files (Generated during test)

1. **`us003_test_capture.jpg`** - Captured test image
2. **`us003_debug_bbox.jpg`** - Annotated image with bounding boxes
3. **`us003_object_coordinates.json`** - Object coordinates for US-012

---

## 🎉 Next Steps

After US-003 validation:
- [x] **US-001:** Visual Classification ✅ Complete
- [x] **US-002:** Voice Commands ✅ Complete
- [x] **US-003:** Multiple Object Detection ✅ Complete
- [ ] **US-004:** Visual Display Feedback (Week 2) - **NEXT**
- [ ] **US-005:** Vision Error Handling (Week 2)
- [ ] **US-023:** Logging System (Week 2)

---

## 📚 Dependencies

No new dependencies! US-003 uses the same packages as US-001:

| Package | Version | Purpose |
|---------|---------|---------|
| google-generativeai | >=0.3.0 | Gemini AI vision |
| opencv-python | >=4.8.0 | Camera, bbox drawing |
| Pillow | >=10.0.0 | Image handling |

---

## 📖 Related Documentation

- **User Stories:** `user_history.md` (lines 104-123)
- **Project Instructions:** `CLAUDE.md` (lines 225-313)
- **US-001 README:** `US-001_README.md`
- **US-002 README:** `US-002_README.md`

---

**Status:** ✅ **US-003 Implementation Complete**
**Last Updated:** 2025-10-12
**Author:** Kuko Robot Project Team
