# Kuko Integrated System - Voice + Vision + Movement

## 📋 Overview

**Integration:** Combines US-002 (Voice Commands) + US-003 (Multi-Object Detection) + Robot Movement

**Purpose:** Automate floor scanning with natural language commands. User speaks in Spanish/English, Kuko performs intelligent 360° scan and reports findings.

**Status:** ✅ Ready for Testing

---

## 🎯 Key Features

### 1. Voice-Activated Scanning
```
User (Spanish): "Kuko, chequea a ver si hay algo en el piso"
User (English): "Kuko, check if there's something on the floor"
  ↓
Kuko: "Estoy chequeando" / "I am checking"
  ↓
[Automated floor scan with vision system]
```

### 2. Intelligent 360° Search
- If objects detected at current position → Report immediately
- If no objects → Perform 8-position scan (45° increments)
- Automatic deduplication of objects seen from multiple angles
- Priority-based object ordering

### 3. Bilingual Voice Responses
- Detects user language (Spanish/English) automatically
- Responds in same language using native accent
- Reports object count, categories, and distances

### 4. Autonomous Movement
- Uses XGO turn() API for precise rotations
- Configurable turn angles (default: 45°)
- Automatic stabilization between captures
- Safety: slow pace for indoor navigation

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────┐
│         KUKO INTEGRATED SYSTEM PIPELINE                │
└────────────────────────────────────────────────────────┘

[1] Voice Command Input (US-002)
    User: "Kuko, chequea el piso"
    ↓
    • Google Speech Recognition (Spanish/English)
    • Gemini NLU parsing
    • Language detection
    ↓

[2] Intent Recognition
    Intent: inspect_room / check_floor
    ↓

[3] Voice Confirmation
    Kuko: "Estoy chequeando" / "I am checking"
    ↓

[4] Floor Scan at Current Position
    • Position robot (pitch +15° looking down)
    • Capture photo (Full HD)
    • US-003 detection (multi-object + priority)
    ↓

[5] Decision Logic
    ┌─────────────────────────────────┐
    │ Objects detected at position 0? │
    └─────────────────────────────────┘
              │
       Yes ───┴─── No
        │           │
        │           ├─ Turn right 45°
        │           ├─ Capture + detect
        │           ├─ Repeat 7 more times (360°)
        │           └─ Aggregate all results
        │
        ↓
[6] Object Deduplication
    • Remove duplicates from multiple angles
    • Use description similarity (3+ shared keywords)
    • Keep highest confidence detection
    ↓

[7] Voice Report
    Spanish: "Encontré 3 objetos"
    English: "I found 3 objects"
    ↓
    • Report top 3 objects
    • Category + distance for each
    ↓

[8] Save Results
    • debug_bbox.jpg (annotated image)
    • object_coordinates.json (for US-012 grasping)
```

---

## 🚀 Quick Start

### Prerequisites

1. **Hardware:**
   - XGO Lite quadruped robot
   - 5MP camera (or USB camera at index 0)
   - Microphone for voice input
   - Speaker for TTS output

2. **Software Dependencies:**
   ```bash
   # Install from requirements.txt
   pip install google-generativeai SpeechRecognition gTTS opencv-python Pillow

   # System packages (Raspberry Pi)
   sudo apt-get install flac mpg123
   ```

3. **API Keys:**
   ```bash
   export GEMINI_API_KEY="your_gemini_api_key"
   ```

### Running the Integrated System

```bash
# Full robot mode (with movement)
python kuko_integrated_system.py
```

**Expected Flow:**
```
============================================================
KUKO INTEGRATED SYSTEM
Voice + Vision + Movement
============================================================

[1] Initializing voice command system...
✓ Kuko Voice Commands ready

[2] Initializing vision system...
✓ Robot initialized (XGO Lite)

✓ All systems initialized

============================================================
KUKO INTERACTIVE MODE
============================================================

Available commands:
  🇪🇸 'Kuko, chequea a ver si hay algo en el piso'
  🇪🇸 'Kuko, revisa el piso'
  🇬🇧 'Kuko, check if there's something on the floor'
  🇬🇧 'Kuko, scan the floor'

Press Ctrl+C to exit

============================================================
🎤 SAY 'KUKO' TO GET MY ATTENTION
============================================================

👉 Press ENTER when ready to speak your command...
```

---

## 📊 System Components

### 1. Voice Command System (US-002)
**File:** `kuko_voice_commands.py`

**Features:**
- Google Speech Recognition (Spanish es-ES, English en-US)
- Gemini NLU for intent extraction
- Google TTS with native accents
- Manual wake word trigger (press ENTER)

**Integration Point:**
```python
self.voice = KukoVoiceCommands()
result = self.voice.process_command()  # Returns parsed command
```

### 2. Vision System (US-003)
**File:** `kuko_vision_mvp.py`

**Features:**
- Multi-object detection (up to 5 objects)
- Priority-based ordering (distance + size + accessibility + confidence)
- Duplicate filtering (IoU + proximity + description)
- Furniture filtering
- Distance estimation from Y-coordinate

**Integration Point:**
```python
self.vision = KukoVision(use_robot=True)
self.vision.init_camera()
result = self.vision.detect_multiple_objects_with_priority(image_path)
```

### 3. Robot Movement
**File:** `kuko_integrated_system.py`

**XGO API Methods Used:**
```python
# Rotation
robot.turn(speed)   # speed: -150 (right) to +150 (left)
robot.stop()        # Stop all movement

# Configuration
robot.pace('slow'/'normal'/'high')  # Set movement speed
robot.gait_type('trot'/'walk')      # Set gait (future use)

# Body positioning (from US-003)
robot.attitude(['r', 'p', 'y'], [0, 15, 0])  # Pitch +15° = look down
robot.translation(['x', 'y', 'z'], [0, 0, 90])  # Body height
```

**Turn Implementation:**
```python
def turn_robot(direction="right", angle=45):
    robot.pace('slow')               # Precise movement
    turn_speed = 80 if direction == "left" else -80
    duration = (angle / 45.0) * 1.0  # Calibrated timing

    robot.turn(turn_speed)
    time.sleep(duration)
    robot.stop()
```

---

## 🧪 Testing Scenarios

### Test 1: Single Object Detection (No Scan)
**Command:** "Kuko, chequea el piso"

**Expected:**
1. Kuko: "Estoy chequeando"
2. Takes photo at current position
3. Detects toy at 35cm
4. Kuko: "Encontré 1 objeto. Objeto 1: juguete a 35 centímetros"
5. Saves: `floor_scan_result.jpg`, `floor_scan_coordinates.json`

---

### Test 2: 360° Scan (Nothing at Start)
**Command:** "Kuko, check if there's something on the floor"

**Expected:**
1. Kuko: "I am checking"
2. Takes photo at position 0 (0°)
3. No objects detected
4. Kuko: "I will look around"
5. Turns right 45° → position 1 (45°)
6. Takes photo, detects trash at 50cm
7. Continues scanning positions 2-7
8. Aggregates results, deduplicates
9. Kuko: "I found 2 objects. Object 1: trash at 50 centimeters..."
10. Saves: `360_scan_result.jpg`, `360_scan_coordinates.json`

---

### Test 3: Multiple Objects with Priority
**Command:** "Kuko, revisa si hay juguetes"

**Expected:**
1. Detects 3 toys at current position
2. Reports in priority order:
   - Priority #1: Small toy, clear, 25cm (priority score: 10.2)
   - Priority #2: Medium toy, clear, 40cm (priority score: 8.5)
   - Priority #3: Large toy, blocked, 60cm (priority score: 5.1)

---

## 🔧 Configuration

### Movement Parameters
```python
# In KukoIntegratedSystem.__init__()
self.turn_angle = 45           # degrees per turn (default: 45°)
self.scan_positions = 8        # 360° / 45° = 8 positions

# Modify for different scan resolutions:
# Fine scan: turn_angle=30, positions=12
# Coarse scan: turn_angle=90, positions=4
```

### Turn Speed Calibration
```python
# In turn_robot() method
turn_speed = 80                # Speed: 0-150 (default: 80)
duration = (angle / 45.0) * 1.0  # Time multiplier (calibrate on robot)

# If robot turns too fast/slow, adjust duration multiplier:
# Slower turns: duration = (angle / 45.0) * 1.2
# Faster turns: duration = (angle / 45.0) * 0.8
```

### Voice Response Language
```python
# Automatic language detection based on user command
# Override with explicit language parameter:
kuko.check_floor(language='es')  # Force Spanish
kuko.check_floor(language='en')  # Force English
```

---

## 📝 API Reference

### KukoIntegratedSystem Class

#### `__init__()`
Initialize all subsystems (voice, vision, movement)

#### `turn_robot(direction="right", angle=45) -> bool`
Turn robot by specified angle
- **direction**: "left" or "right"
- **angle**: Rotation angle in degrees
- **Returns**: True if successful

#### `scan_360() -> List[Dict]`
Perform 360° floor scan at 8 positions
- **Returns**: List of unique detected objects

#### `check_floor(language='es') -> Dict`
Check floor at current position with voice feedback
- **language**: 'es' or 'en'
- **Returns**: Detection result dictionary

#### `report_objects(objects, language='es')`
Report detected objects via TTS
- **objects**: List of detected objects
- **language**: 'es' or 'en'

#### `handle_floor_scan_command(parsed_command) -> bool`
Handle floor scan voice command (main orchestration)
- **parsed_command**: Parsed voice command from Gemini NLU
- **Returns**: True if command handled

#### `run_interactive()`
Interactive voice command loop (main entry point)

---

## 🐛 Troubleshooting

### Issue: Robot turns too fast/slow

**Diagnosis:**
- Turn duration calculation needs calibration
- Robot hardware variance

**Solution:**
```python
# In turn_robot() method, adjust duration multiplier
duration = (angle / 45.0) * 1.2  # Increase for slower turns
duration = (angle / 45.0) * 0.8  # Decrease for faster turns
```

**Testing:**
```python
# Test turn accuracy
kuko = KukoIntegratedSystem()
kuko.turn_robot("right", 90)  # Should turn exactly 90°
# Measure actual angle and adjust multiplier
```

---

### Issue: Objects detected multiple times in 360° scan

**Diagnosis:**
- Same object seen from 2-3 adjacent positions
- Deduplication threshold too strict

**Solution:**
```python
# In _deduplicate_scan_results(), adjust similarity threshold
if len(shared_words) >= 2:  # Lower from 3 to 2
    is_duplicate = True
```

---

### Issue: "El piso está limpio" but objects visible

**Diagnosis:**
- Objects below confidence threshold (70%)
- Lighting too low (<200 lux)
- Objects categorized as furniture

**Solution:**
1. Check lighting: `mean_brightness` should be >50
2. Review Gemini confidence scores in debug output
3. Adjust furniture filtering keywords if needed

---

### Issue: Voice command not recognized

**Diagnosis:**
- Background noise
- Microphone quality
- Internet connection (Google Speech API)

**Solution:**
```bash
# Test microphone
arecord -d 3 test.wav && aplay test.wav

# Test internet
ping -c 3 google.com

# Check voice recognition logs
# Look for: "✓ Transcribed (2.3s, Spanish): '...'"
```

---

## 🔗 Integration with User Stories

### US-001: Visual Classification
- **Used by:** `detect_multiple_objects_with_priority()`
- **Input:** Image path
- **Output:** Objects with categories, confidence, bounding boxes

### US-002: Voice Commands
- **Used by:** `process_command()`
- **Input:** User voice (Spanish/English)
- **Output:** Parsed command (action, location, object, intent)

### US-003: Multi-Object Detection
- **Used by:** Main detection pipeline
- **Features:** Priority scoring, duplicate filtering, distance calculation

### US-006: Coordinate Navigation (Week 3) - Future
```python
# After detecting objects, navigate to them
for obj in objects:
    robot.navigate_to(obj['grasp_point'])  # US-006
    robot.grasp_object(obj)                # US-012
```

### US-012: Object Grasping (Week 5) - Future
```python
# Uses coordinates saved by integrated system
with open('floor_scan_coordinates.json') as f:
    objects = json.load(f)['objects']

for obj in objects:
    # Grasp point already calculated
    robot.approach(obj['grasp_point'])
    robot.grasp()
```

---

## 📚 File Structure

```
Xentauri_Robots/
├── kuko_integrated_system.py          # NEW: Integrated system (this file)
├── kuko_voice_commands.py             # US-002: Voice commands
├── kuko_vision_mvp.py                 # US-003: Multi-object detection
├── INTEGRATED_SYSTEM_README.md        # NEW: This documentation
├── US-002_README.md                   # US-002 docs
├── US-003_README.md                   # US-003 docs
├── requirements.txt                   # Python dependencies
└── CLAUDE.md                          # Project instructions
```

---

## 🎉 Next Steps

After validating the integrated system:

### Week 3: Navigation (US-006, US-007, US-008)
- [ ] **US-006:** Coordinate navigation (move to detected object)
- [ ] **US-007:** Teaching mode (record waypoints)
- [ ] **US-008:** Navigate by room name

### Week 4: Advanced Navigation
- [ ] **US-009:** Obstacle avoidance
- [ ] **US-010:** IMU odometry
- [ ] **US-011:** Visual landmark correction

### Week 5: Object Manipulation (US-012-016)
- [ ] **US-012:** Grasp objects <100g
- [ ] **US-014:** Deposit in container
- [ ] **US-015:** Transport objects

### Week 6: Complete Missions (US-017-020)
- [ ] **US-017:** Room inspection mission
- [ ] **US-018:** Selective object collection
- [ ] **US-019:** Contextual reasoning
- [ ] **US-020:** Intelligent reports

---

## 📖 Related Documentation

- **User Stories:** `user_history.md`
- **Project Instructions:** `CLAUDE.md`
- **US-002 README:** `US-002_README.md` (Voice Commands)
- **US-003 README:** `US-003_README.md` (Multi-Object Detection)
- **XGO Movement Examples:** `DOGZILLA_Lite_class/3.Dog Base Control/`

---

**Status:** ✅ **Integrated System Complete - Ready for Testing**
**Last Updated:** 2025-10-12
**Author:** Kuko Robot Project Team

---

## 💡 Usage Tips

1. **Clear Speech:** Speak directly at microphone, avoid background noise
2. **Lighting:** Ensure >200 lux for reliable object detection
3. **Floor Space:** Clear 2m radius for 360° scan
4. **Calibration:** First run may need turn duration adjustments
5. **Language:** System auto-detects Spanish/English, responds in same language
