# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **Kuko Robot Project** (Xentauri_Robots) - a quadruped cleaning robot with AI vision, autonomous navigation, and object manipulation capabilities. The project is organized around a 5-6 week MVP roadmap with 32 user stories across 4 main epics.

## Jira Integration

### Atlassian CLI (acli)

The project uses the Atlassian CLI (`acli.exe`) for Jira work item management.

**Authentication:**
```bash
# Login (API token should be in token.txt)
cat token.txt | ./acli.exe jira auth login --site "diazvaldiviav.atlassian.net" --email "diazvaldiviav@gmail.com" --token

# Check authentication status
./acli.exe jira auth status
```

**Common Commands:**
```bash
# List projects
./acli.exe jira project list --recent

# Create work item
./acli.exe jira workitem create --project "SCRUM" --type "Story" --summary "Title" --description "Details" --label "critical,week-1"

# Create epic
./acli.exe jira workitem create --project "SCRUM" --type "Epic" --summary "Epic Title" --description "Epic details"

# Link story to epic (use --parent flag)
./acli.exe jira workitem create --project "SCRUM" --type "Story" --summary "Story" --parent "SCRUM-5" --description "Details"

# Search work items
./acli.exe jira workitem search

# View work item details
./acli.exe jira workitem view SCRUM-10
```

**Project Details:**
- **Jira Site:** https://diazvaldiviav.atlassian.net
- **Project Key:** SCRUM
- **Project Name:** Xentuari_Robots

## Project Architecture

### Epic Structure

The MVP is organized into **5 Epics** with associated Jira IDs:

1. **EPIC 1: Artificial Intelligence & Vision** (SCRUM-5)
   - Week 1-2: Gemini AI integration, visual object detection, voice commands
   - Critical stories: US-001 (Visual Classification), US-002 (Voice Commands)

2. **EPIC 2: Autonomous Navigation** (SCRUM-6)
   - Week 3-4: Odometry, coordinate system, waypoint navigation
   - Critical stories: US-006 (Coordinate Navigation), US-007 (Teaching Mode), US-008 (Navigate by Name)

3. **EPIC 3: Object Manipulation** (SCRUM-7)
   - Week 5: Arm/gripper control, object grasping and transport
   - Critical stories: US-012 (Grasping <100g objects), US-014 (Deposit in Container)

4. **EPIC 4: Complete Missions & Intelligence** (SCRUM-8)
   - Week 6: Task coordination, contextual reasoning, intelligent reports
   - Critical stories: US-017 (Room Inspection), US-018 (Selective Collection)

5. **TECHNICAL EPIC: Infrastructure & Quality** (SCRUM-9)
   - Logging, testing, configuration, system monitoring

### User Story Reference

All user stories are documented in `user_history.md` with:
- User story format: "As a [role], I want [action] so that [benefit]"
- Detailed acceptance criteria (checkboxes)
- Priority levels: 🔴 CRITICAL, 🟡 HIGH, 🟢 MEDIUM/LOW
- Effort estimates (story points: 1-5)
- Week assignments (Week 1-6)
- Dependencies between stories

### Hardware Constraints

When working on user stories, respect these documented limitations:
- **Object weight:** Max 100g (gripper limitation)
- **Camera:** 5MP resolution, requires >200 lux lighting
- **Navigation precision:** ±30cm arrival tolerance
- **Movement speed:** 0.15-0.35 m/s (configurable)
- **Balance risk:** Instability with objects >70g

### AI Integration

The robot uses **Gemini AI** for:
- Visual object classification (toy, trash, clothing, other)
- Natural language understanding (Spanish voice commands)
- Contextual decision making
- Visual landmark recognition for navigation correction
- Text-to-speech responses

## Development Workflow

### Creating Jira Tickets from User Stories

When creating tickets from `user_history.md`:

1. **Create Epic first** if not exists
2. **Extract acceptance criteria** - convert markdown checkboxes to description
3. **Add labels:** Priority (critical/high/medium/low) + Week (week-1 to week-6)
4. **Link to parent Epic** using `--parent SCRUM-X` flag
5. **Include effort estimate** in description

Example:
```bash
./acli.exe jira workitem create \
  --project "SCRUM" \
  --type "Story" \
  --summary "US-001: Visual Trash Classification" \
  --parent "SCRUM-5" \
  --label "critical,week-1" \
  --description "As a household user, I want Kuko to identify and classify trash...

Acceptance Criteria:
- Kuko captures photo with 5MP camera
- Gemini AI classifies into categories
...

Priority: CRITICAL (Week 1)
Effort: 3 points"
```

### Story Prioritization

Follow the MoSCoW model as documented:
- **Must:** Critical stories (🔴) - Core MVP functionality
- **Should:** High priority (🟡) - Important enhancements
- **Could:** Medium priority (🟢) - Nice-to-have features
- **Won't (for now):** Low priority - Post-MVP

### Sprint Planning

- Each sprint = 1 week from roadmap (Week 1-6)
- Prioritize CRITICAL stories first within each epic
- Respect dependencies (e.g., US-008 depends on US-006, US-007)
- Story points: 1 = half day, 5 = full week

## Key Files

- **user_history.md:** Complete user story documentation (32 stories)
- **token.txt:** Jira API authentication token (DO NOT COMMIT if using git)
- **acli.exe:** Atlassian CLI executable for Jira integration

## Notes

- The robot's wake word is "Kuko" (previously "lulu")
- Voice commands are in Spanish and English (bilingual)
- Speech recognition uses Google Speech API (replaced Baidu Chinese API)
- TTS uses Google TTS (gTTS) with native Spanish accent
- Project focuses on household cleaning use case (picking up toys, trash)
- Teaching mode allows users to memorize room locations with natural names
- Navigation uses IMU odometry with visual landmark correction

## Current Progress (Week 1-2)

### ✅ Completed User Stories

#### US-001: Visual Trash Classification (Week 1) - COMPLETE
**Status:** ✅ Production Ready
**Files:** `kuko_vision_mvp.py`, `US-001_README.md`, `US-001_ENHANCEMENTS.md`

**Key Features:**
- Gemini AI visual object classification (toy, trash, clothing, other)
- 5MP camera integration
- >70% confidence detection
- Bounding box location
- <3s processing time
- Error handling (dark/blur detection)
- Grasp point calculation for US-012
- Auto-optimization for latency

**Integration:** Works with vision system for object detection

---

#### US-002: Natural Language Voice Commands (Week 1) - COMPLETE
**Status:** ✅ Production Ready
**Files:** `kuko_voice_commands.py`, `US-002_README.md`, `US-002_Voice_Commands.ipynb`

**Key Features:**
- Google Speech Recognition API (Spanish es-ES, English en-US)
- Gemini NLU parsing (action + location + object extraction)
- Google TTS (gTTS) with native Spanish accent
- Manual wake word trigger (press ENTER)
- Handles 5+ command variations
- ~95% recognition accuracy for Spanish
- ~94% recognition accuracy for English

**Technical Implementation:**
- Records audio with XGOEDU (5 seconds)
- Transcribes with Google Speech API (replaces Baidu Chinese)
- Parses with Gemini AI NLU
- Speaks with Google TTS (replaces Baidu Chinese accent)

**System Requirements:**
```bash
# Python packages
pip install SpeechRecognition gTTS pyaudio

# System packages
sudo apt-get install flac mpg123
```

**Integration:** Works with navigation and object collection commands

---

### 📍 Current Position: Week 2 Priorities

**Next Story:** US-003 - Multiple Object Detection

---

## US-003: Multiple Object Detection (Week 2) - NEXT

**User Story:** As a user, I want Kuko to detect multiple objects in a single image, so that it can clean efficiently without scanning multiple times.

**Priority:** 🟡 HIGH (Week 2)
**Effort:** 2 points
**Epic:** EPIC 1 - Artificial Intelligence & Vision (SCRUM-5)

### Acceptance Criteria

- [ ] Detects up to 5 simultaneous objects in one frame
- [ ] Prioritizes objects by: size + accessibility + confidence
- [ ] Filters duplicate objects (same object seen from different angles)
- [ ] Ignores furniture and fixed objects (sofas, tables, large plants)
- [ ] Generates ordered list by pickup priority

### Technical Approach

**Extend US-001 implementation:**
1. Modify Gemini prompt to request multiple objects
2. Parse JSON array of objects instead of single object
3. Implement priority scoring algorithm:
   - Size score: Larger objects = higher priority
   - Accessibility score: Objects in open space = higher priority
   - Confidence score: Higher confidence = higher priority
4. Deduplicate logic: Compare bounding box overlap
5. Filter furniture: Classify as "furniture" or "large_object" and exclude

**Gemini Prompt Enhancement:**
```python
prompt = f"""Analyze this image and detect ALL visible out-of-place objects.

For EACH object, provide:
1. category: toy, trash, clothing, other (NOT furniture/appliances)
2. description: Brief description
3. confidence: 0-100 score
4. bbox: [x_min, y_min, x_max, y_max]
5. size_estimate: small/medium/large
6. accessibility: "clear" if open space, "blocked" if obstructed

IGNORE: furniture, appliances, walls, floors, large fixtures

Return JSON array of up to 5 objects, ordered by pickup priority.
"""
```

**Priority Algorithm:**
```python
def calculate_priority(obj):
    size_score = {"small": 3, "medium": 2, "large": 1}[obj['size_estimate']]
    access_score = {"clear": 3, "blocked": 1}[obj['accessibility']]
    conf_score = obj['confidence'] / 100 * 3

    return size_score + access_score + conf_score

objects.sort(key=calculate_priority, reverse=True)
```

### Integration Points

**US-001 (Visual Classification):**
- Extends existing `classify_objects()` function
- Reuses camera and Gemini AI infrastructure
- Maintains <3s processing time per image

**US-002 (Voice Commands):**
```python
# User says: "Kuko recoge todos los juguetes"
# System detects: [toy1, toy2, toy3, toy4]
# Returns priority-ordered list for sequential pickup
```

**US-012 (Object Grasping - Week 5):**
- Uses priority list for efficient collection
- Picks up objects in optimal order
- Skips inaccessible objects

### Implementation Files

**To Create:**
- `kuko_multi_object_detection.py` - Multiple object detection
- `US-003_README.md` - Documentation
- Update `kuko_vision_mvp.py` - Add multi-object mode

**Dependencies:**
- Same as US-001 (already installed)
- No new packages required

---

### Other Week 2 Stories

**US-004: Visual Display Feedback (🟢 MEDIUM - 1 point)**
- Show robot state on 2" display
- Icons: 😊 clean, 🔍 searching, ⚠️ error
- Battery level indicator
- Update every 500ms

**US-005: Vision Error Handling (🟡 HIGH - 2 points)**
- Complete dark/blur detection (partially done in US-001)
- Fallback local detection if Gemini fails
- Max 3 retries before requesting help
- Error logging with timestamp

**US-023: Logging System (🟡 HIGH - 1 point)**
- Log timestamps + state + action
- Levels: DEBUG, INFO, WARNING, ERROR
- Daily log rotation (max 7 days)
- Include coordinates, detected objects, commands
- Accessible via SSH

---

## Development Workflow Tips

### Testing Voice Commands
```bash
# Run interactive voice system
python kuko_voice_commands.py

# Test Spanish: "Kuko ve a la habitación"
# Test English: "Kuko go to the bedroom"
```

### Testing Vision
```bash
# Run vision classification
python kuko_vision_mvp.py

# Check debug output
ls -lh debug_bbox.jpg object_coordinates.json
```

### Common Issues

**1. "FLAC conversion utility not available"**
```bash
sudo apt-get install flac
```

**2. "mpg123 not found" (TTS playback)**
```bash
sudo apt-get install mpg123
```

**3. Low confidence in voice recognition**
- Ensure quiet environment
- Speak clearly at microphone
- Check internet connection (Google APIs require internet)

**4. Chinese accent in TTS**
- This is now fixed! Using Google TTS with native Spanish accent
- If still hearing Chinese, ensure latest code is pulled from git
