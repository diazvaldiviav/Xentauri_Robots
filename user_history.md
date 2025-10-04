# 📋 User Stories - Kuko Robot Project

## Executive Summary

This document presents **32 user stories** organized into **4 main epics** that correspond to the MVP development phases for the Kuko robot. Stories are prioritized according to the technical roadmap (5-6 weeks) and structured to facilitate iterative agile development.

**Coverage:**
- ✅ All key MVP functionalities
- ✅ Realistic and testable use cases
- ✅ Specific acceptance criteria
- ✅ Aligned with hardware technical limitations

---

## 🎯 What are User Stories?

User stories are **short, simple descriptions** of functionality from the end user's perspective. They follow the format:

> **"As a [type of user], I want [action] so that [benefit]"**

**Key components:**
1. **Role:** Who needs the functionality
2. **Action:** What they want to do
3. **Benefit:** Why it's valuable
4. **Acceptance Criteria:** How to verify it works

**Value for this project:**
- Keep focus on the user (not on technology)
- Facilitate development prioritization
- Serve as basis for testing
- Improve team communication

---

## 📚 Epics and Organization

Stories are grouped into **4 epics** that map directly to development phases:

```
EPIC 1: Artificial Intelligence & Vision (Week 1-2)
├─ Gemini AI Integration
├─ Visual object detection
└─ Voice commands

EPIC 2: Autonomous Navigation (Week 3-4)
├─ Odometry and movement
├─ Coordinate system
└─ Memorized waypoints

EPIC 3: Object Manipulation (Week 5)
├─ Arm/gripper control
└─ Grasping and transport

EPIC 4: Complete Missions (Week 6)
├─ Task coordination
├─ Contextual reasoning
└─ Intelligent reports
```

---

## 🚀 EPIC 1: Artificial Intelligence & Vision

### US-001: Visual Trash Classification
**As a** household user  
**I want** Kuko to identify and classify trash on the floor using its camera  
**So that** I know what objects are out of place without having to check myself

**Acceptance Criteria:**
- [ ] Kuko captures photo of area with 5MP camera
- [ ] Gemini AI classifies objects into categories: toy, trash, clothing, other
- [ ] Responds with >70% confidence for each detected object
- [ ] Returns approximate location (bbox) of each object
- [ ] Classification time <3 seconds per image
- [ ] Works with normal indoor lighting (>200 lux)

**Priority:** 🔴 CRITICAL (Week 1)  
**Effort:** 3 points  
**Dependencies:** Gemini API configured

---

### US-002: Natural Language Voice Commands
**As a** user  
**I want** to give Kuko orders in Spanish speaking naturally  
**So that** I don't have to use technical commands or apps

**Acceptance Criteria:**
- [ ] Kuko responds to wake word "Kuko" (previously "lulu")
- [ ] Recognizes Spanish commands: "go to bedroom", "pick up the toys"
- [ ] Gemini NLU extracts: action + location + object from phrase
- [ ] Responds with synthesized voice confirming what was understood
- [ ] Handles 5+ variations of same command (e.g., "go", "walk", "move")
- [ ] Command→response latency <2 seconds

**Priority:** 🔴 CRITICAL (Week 1)  
**Effort:** 3 points  
**Usage example:**
```
User: "Kuko go to the bedroom and check that it's okay"
Kuko: "Going to bedroom to check" [starts navigation]
```

---

### US-003: Multiple Object Detection
**As a** user  
**I want** Kuko to detect multiple objects in a single image  
**So that** it can clean efficiently without scanning multiple times

**Acceptance Criteria:**
- [ ] Detects up to 5 simultaneous objects in one frame
- [ ] Prioritizes objects by: size + accessibility + confidence
- [ ] Filters duplicate objects (same object seen from different angles)
- [ ] Ignores furniture and fixed objects (sofas, tables, large plants)
- [ ] Generates ordered list by pickup priority

**Priority:** 🟡 HIGH (Week 2)  
**Effort:** 2 points

---

### US-004: Visual Feedback on Display
**As a** user  
**I want** to see on the robot's screen what it's doing  
**So that** I understand its state without waiting for voice responses

**Acceptance Criteria:**
- [ ] 2" display shows current state: "Navigating", "Scanning", "Grasping"
- [ ] Shows simple icons: 😊 clean, 🔍 searching, ⚠️ error
- [ ] Visually indicates battery level
- [ ] Updates every 500ms minimum
- [ ] Text readable from 2 meters distance

**Priority:** 🟢 MEDIUM (Week 2)  
**Effort:** 1 point

---

### US-005: Vision Error Handling
**As a** developer/user  
**I want** Kuko to handle errors when it can't see or classify  
**So that** it doesn't get stuck in unexpected situations

**Acceptance Criteria:**
- [ ] If image too dark/blurry: reports "I can't see well"
- [ ] If Gemini doesn't respond: uses basic local detection (fallback)
- [ ] Maximum 3 classification retries before asking for help
- [ ] Saves error log with timestamp + context
- [ ] Notifies user with TTS if intervention needed

**Priority:** 🟡 HIGH (Week 2)  
**Effort:** 2 points

---

## 🧭 EPIC 2: Autonomous Navigation

### US-006: Coordinate-Based Navigation
**As** Kuko robot  
**I want** to navigate from point (x1, y1) to another (x2, y2)  
**So that** I can move autonomously without manual control

**Acceptance Criteria:**
- [ ] Calculates direct route between origin and destination
- [ ] Uses IMU odometry for position tracking
- [ ] Arrival precision: ±30cm from target
- [ ] Adjusts speed according to remaining distance
- [ ] Avoids abrupt commands (smooth acceleration)
- [ ] Navigation time: <2 min per 3 meters

**Priority:** 🔴 CRITICAL (Week 3)  
**Effort:** 5 points  
**Technical notes:** Foundation of navigation system

---

### US-007: Teach Locations (Teaching Mode)
**As a** user  
**I want** to teach Kuko where each room is  
**So that** it can navigate using familiar names

**Acceptance Criteria:**
- [ ] Command: "Kuko memorize this place as [name]"
- [ ] Saves current coordinates + reference photo
- [ ] Accepts aliases (e.g., "bedroom", "room", "sleeping room")
- [ ] Gemini generates textual description of place
- [ ] Persists waypoints in JSON file
- [ ] Loads waypoints automatically on startup

**Priority:** 🔴 CRITICAL (Week 3)  
**Effort:** 3 points  
**Example:**
```
User: "Kuko memorize this place as living room"
Kuko: "Location 'living room' memorized. I see a gray sofa and TV"
[Saves: {x:2.5, y:3.1, aliases:["living room","lounge"]}]
```

---

### US-008: Navigate to Location by Name
**As a** user  
**I want** to tell it "Kuko go to the kitchen"  
**So that** it goes there without me giving numeric coordinates

**Acceptance Criteria:**
- [ ] Searches waypoint by name or alias
- [ ] If doesn't exist: asks "Where is the kitchen?"
- [ ] Navigates using saved coordinates
- [ ] Upon arrival: confirms with "I arrived at the kitchen"
- [ ] If fails (obstacle): reports the problem

**Priority:** 🔴 CRITICAL (Week 3)  
**Effort:** 2 points  
**Dependencies:** US-006, US-007

---

### US-009: Visual Correction with Landmarks
**As a** navigation system  
**I want** to correct odometry drift using visual references  
**So that** I maintain precision after moving for a long time

**Acceptance Criteria:**
- [ ] Every 2 minutes of movement: searches for known landmarks
- [ ] Gemini identifies fixed objects: "gray sofa", "kitchen door"
- [ ] Calculates estimated position by trilateration
- [ ] Fuses with odometry (weight 80% visual, 20% odometry)
- [ ] Resets odometry confidence after correction
- [ ] Works with 3+ landmarks in house

**Priority:** 🟡 HIGH (Week 4)  
**Effort:** 4 points  
**Notes:** Key for long navigations (>5 meters)

---

### US-010: Automatic Return to Charging Station
**As an** autonomous robot  
**I want** to return to my base when battery <20%  
**So that** I don't run out of energy far from charging

**Acceptance Criteria:**
- [ ] Monitors battery every 10 seconds
- [ ] Upon detecting <20%: pauses current mission
- [ ] Announces: "Low battery, returning to charge"
- [ ] Navigates to waypoint "home" (0, 0, 0)
- [ ] If return fails: emits audible alert
- [ ] Resumes mission after full charge (optional MVP)

**Priority:** 🟢 MEDIUM (Week 4)  
**Effort:** 2 points

---

### US-011: Unforeseen Obstacle Handling
**As a** navigating robot  
**I want** to detect when I can't advance (obstacle/error)  
**So that** I don't damage myself or get stuck

**Acceptance Criteria:**
- [ ] If odometry indicates movement but IMU doesn't change: obstacle detected
- [ ] Tries 3 strategies: back up + turn, go around left/right
- [ ] If fails: captures photo and asks Gemini "what's blocking me?"
- [ ] Reports to user: "I can't pass, there's [object] in the way"
- [ ] Marks location as "temporary obstacle"

**Priority:** 🟢 MEDIUM (Week 4)  
**Effort:** 3 points

---

## 🤖 EPIC 3: Object Manipulation

### US-012: Grasping Light Objects
**As a** cleaning robot  
**I want** to grasp objects <100g from the floor  
**So that** I can pick them up and transport them

**Acceptance Criteria:**
- [ ] Approaches object until 20-30cm away
- [ ] Extends arm to pre-grasp position
- [ ] Gripper opens → descends → closes with calibrated force
- [ ] Verifies successful grasp (gripper servo reading >100)
- [ ] Elevates object to transport position
- [ ] Success rate >60% with plush toys, >40% with paper

**Priority:** 🔴 CRITICAL (Week 5)  
**Effort:** 5 points  
**Limitation:** Only objects <100g (documented)

---

### US-013: Grasp Types by Object
**As a** manipulation system  
**I want** to use different grasping strategies depending on object type  
**So that** I maximize success and avoid damaging objects

**Acceptance Criteria:**
- [ ] Plush toys: soft grasp (force 120/255)
- [ ] Paper/cardboard: medium grasp (force 150/255)
- [ ] Empty plastic bottles: firm grasp (force 180/255)
- [ ] Gemini suggests grasp type based on image
- [ ] Calibrated sequences for each category

**Priority:** 🟡 HIGH (Week 5)  
**Effort:** 3 points

---

### US-014: Deposit in Correct Container
**As a** classifier robot  
**I want** to take each object to the appropriate container  
**So that** I separate trash from toys correctly

**Acceptance Criteria:**
- [ ] Mapping: plush toys → "toy_basket", trash → "trash_bin"
- [ ] Navigates with object in gripper (reduced speed)
- [ ] Positions over container (±15cm)
- [ ] Extends arm over container
- [ ] Releases object (gripper opens)
- [ ] Verifies successful release

**Priority:** 🔴 CRITICAL (Week 5)  
**Effort:** 3 points

---

### US-015: Balance Compensation During Manipulation
**As a** quadruped robot  
**I want** to maintain stability when extending my arm  
**So that** I don't lose balance and fall

**Acceptance Criteria:**
- [ ] IMU detects tilt >5° (pitch/roll)
- [ ] Adjusts posture automatically (leg servos)
- [ ] Auto-balance activated (imu(1)) before extending arm
- [ ] Compensates center of gravity when grasping object
- [ ] Recovers neutral posture after releasing

**Priority:** 🟡 HIGH (Week 5)  
**Effort:** 3 points  
**Risk:** Instability with objects >70g

---

### US-016: Intelligent Grasp Retries
**As a** manipulation system  
**I want** to retry failed grasp up to 3 times  
**So that** I don't give up easily but also don't get stuck

**Acceptance Criteria:**
- [ ] If grasp fails: repositions (5cm different)
- [ ] Maximum 3 attempts per object
- [ ] Adjusts approach angle between attempts
- [ ] If 3 failures: marks object as "difficult"
- [ ] Reports: "Couldn't grasp [object], need help"
- [ ] Continues with next object on list

**Priority:** 🟢 MEDIUM (Week 5)  
**Effort:** 2 points

---

## 🎯 EPIC 4: Complete Missions & Intelligence

### US-017: Room Inspection Mission
**As a** user  
**I want** Kuko to inspect a room and tell me what it finds  
**So that** I know if it needs cleaning without going in myself

**Acceptance Criteria:**
- [ ] Command: "Kuko inspect the bedroom"
- [ ] Navigates to waypoint "bedroom"
- [ ] Scans area 360° (rotates on axis capturing photos)
- [ ] Gemini analyzes photos and generates list of out-of-place objects
- [ ] Reports: "Found 2 plush toys and 1 bottle"
- [ ] Asks: "Do you want me to pick them up?"

**Priority:** 🔴 CRITICAL (Week 6)  
**Effort:** 4 points  
**Main use case**

---

### US-018: Selective Collection Mission
**As a** user  
**I want** to say "Kuko pick up all the plush toys"  
**So that** it only cleans one specific type of object

**Acceptance Criteria:**
- [ ] Filters detections by specified category
- [ ] Ignores objects from other categories
- [ ] Picks up objects one by one
- [ ] Takes each object to correct container
- [ ] Reports progress: "Picked up 3 of 5 plush toys"
- [ ] Upon completion: "Mission completed, all plush toys stored"

**Priority:** 🔴 CRITICAL (Week 6)  
**Effort:** 3 points

---

### US-019: Contextual Reasoning with Gemini
**As an** intelligent robot  
**I want** Gemini to help me decide what to do in ambiguous situations  
**So that** I make contextual decisions like a human would

**Acceptance Criteria:**
- [ ] Sends complete context to Gemini: location + seen objects + mission
- [ ] Gemini responds with decision + reasoning
- [ ] Options: "pick up object X", "explore more", "ask for help", "mission complete"
- [ ] Explains decision to user if asked
- [ ] Decision latency <3 seconds

**Priority:** 🟡 HIGH (Week 6)  
**Effort:** 3 points  
**Example prompt:**
```
I'm at: living room
Mission: pick up trash
Saw: 1 plush toy, 1 empty bottle
Already picked up: 0 objects
What do I do? A) Pick up bottle B) Ignore plush toy C) Explore more
```

---

### US-020: Intelligent Mission Report
**As a** user  
**I want** Kuko to summarize what it did after finishing  
**So that** I know the results without supervising the entire process

**Acceptance Criteria:**
- [ ] Upon mission completion: generates automatic report
- [ ] Includes: objects found, objects picked up, errors
- [ ] Gemini generates natural text (not technical)
- [ ] Presents with voice (TTS) and on display
- [ ] Report duration <30 seconds
- [ ] Example: "Picked up 3 plush toys and 1 bottle. Couldn't grasp 1 heavy can. The room is clean."

**Priority:** 🟡 HIGH (Week 6)  
**Effort:** 2 points

---

### US-021: Continuous Patrol Mode
**As a** user  
**I want** Kuko to patrol rooms automatically every hour  
**So that** I maintain cleanliness without constantly giving orders

**Acceptance Criteria:**
- [ ] Command: "Kuko activate automatic patrol"
- [ ] Every 60 minutes: goes through list of waypoints
- [ ] Inspects each location
- [ ] If finds objects: picks them up automatically
- [ ] Reports only if finds something (no spam)
- [ ] Can pause: "Kuko stop patrol"

**Priority:** 🟢 LOW (Post-MVP)  
**Effort:** 3 points  
**Note:** Extra feature, not critical for MVP

---

### US-022: Integration with Family Routines
**As a** user  
**I want** to say "Kuko do your morning round"  
**So that** it executes pre-programmed sequence

**Acceptance Criteria:**
- [ ] Defines routines with name: "morning", "night", "before_guests"
- [ ] Each routine = sequence of waypoints + actions
- [ ] Example "morning": inspect_bedroom → inspect_living_room → pick_up_all
- [ ] Saves routines in config
- [ ] Executes steps sequentially

**Priority:** 🟢 LOW (Post-MVP)  
**Effort:** 2 points

---

## 🛠️ TECHNICAL EPIC: Infrastructure & Quality

### US-023: Logging System
**As a** developer  
**I want** Kuko to log all its actions  
**So that** I can debug problems and improve the system

**Acceptance Criteria:**
- [ ] Logs timestamps + state + action to file
- [ ] Levels: DEBUG, INFO, WARNING, ERROR
- [ ] Daily log rotation (max 7 days saved)
- [ ] Includes: coordinates, detected objects, received commands
- [ ] Accessible via SSH for analysis

**Priority:** 🟡 HIGH (Week 2)  
**Effort:** 1 point

---

### US-024: Test/Simulation Mode
**As a** developer  
**I want** to execute commands without the robot actually moving  
**So that** I can test logic without risk of accidents

**Acceptance Criteria:**
- [ ] Flag `--simulate` simulates movement without hardware
- [ ] Uses virtual odometry
- [ ] Processes vision with test images
- [ ] Reports actions it "would do" without executing them
- [ ] Facilitates desktop testing without robot

**Priority:** 🟢 MEDIUM (Week 3)  
**Effort:** 2 points

---

### US-025: Persistent Configuration
**As a** user/system  
**I want** configurations to be saved between sessions  
**So that** I don't have to re-teach everything on restart

**Acceptance Criteria:**
- [ ] config.json file saves: waypoints, containers, routines
- [ ] Automatic loading on robot startup
- [ ] Automatic backup before modifying
- [ ] Command: "Kuko forget everything" clears and resets
- [ ] Integrity validation when loading

**Priority:** 🟡 HIGH (Week 3)  
**Effort:** 1 point

---

### US-026: System Health Monitoring
**As an** operator  
**I want** to verify all systems are working correctly  
**So that** I detect failures before important missions

**Acceptance Criteria:**
- [ ] Command: "Kuko self-diagnostic"
- [ ] Verifies: camera, IMU, servos, Gemini connectivity
- [ ] Reports status of each component: OK | WARNING | ERROR
- [ ] Executes calibrated movement test
- [ ] Generates report in <10 seconds

**Priority:** 🟢 MEDIUM (Week 5)  
**Effort:** 2 points

---

## 📊 Additional User Stories (Refinement)

### US-027: Movement Speed Adjustment
**As a** user  
**I want** to configure whether Kuko moves fast or slow  
**So that** I balance between efficiency and safety

**Acceptance Criteria:**
- [ ] Command: "Kuko speed [slow|normal|fast]"
- [ ] Affects navigation (not manipulation)
- [ ] Slow: 0.15 m/s, Normal: 0.25 m/s, Fast: 0.35 m/s
- [ ] Persists configuration
- [ ] Default: Normal

**Priority:** 🟢 LOW  
**Effort:** 1 point

---

### US-028: Confirmation Before Critical Actions
**As a** cautious user  
**I want** Kuko to ask for confirmation before picking up valuable objects  
**So that** I avoid it picking up things it shouldn't

**Acceptance Criteria:**
- [ ] List of "valuable" categories: clothing, books, electronics
- [ ] Upon detection: asks "Should I pick up this [object]?"
- [ ] Waits for verbal confirmation: "yes"/"no"
- [ ] 10 second timeout → assumes "no"
- [ ] Can disable: "Kuko full trust mode"

**Priority:** 🟢 LOW  
**Effort:** 2 points

---

### US-029: Preference Learning
**As a** frequent user  
**I want** Kuko to learn where I prefer it to leave each type of object  
**So that** I don't have to specify it every time

**Acceptance Criteria:**
- [ ] Tracks: object_type → frequently_used_container
- [ ] After 3+ uses: suggests destination automatically
- [ ] Example: "I see you always take plush toys to the basket, should I do that?"
- [ ] Can correct: "No, take them to the bed"
- [ ] Updates preferences in config

**Priority:** 🟢 LOW (Post-MVP)  
**Effort:** 3 points

---

### US-030: Proactive Notifications
**As a** user  
**I want** Kuko to notify me when it detects clutter without me asking  
**So that** I stay informed without constantly supervising

**Acceptance Criteria:**
- [ ] During patrol: if detects >3 out-of-place objects → notifies
- [ ] Message: "Notice: the bedroom has several plush toys on the floor"
- [ ] Maximum frequency: 1 notification/hour per location
- [ ] Configurable sensitivity threshold
- [ ] Respects schedule: no notifications 10pm-7am

**Priority:** 🟢 LOW  
**Effort:** 2 points

---

### US-031: Cleaning Statistics
**As a** curious user  
**I want** to see statistics of what Kuko has cleaned  
**So that** I understand patterns and performance

**Acceptance Criteria:**
- [ ] Command: "Kuko show statistics"
- [ ] Reports: objects picked up this week by category
- [ ] Most used/messy room
- [ ] Total operation hours
- [ ] Grasp success rate
- [ ] Presents in simple, friendly format

**Priority:** 🟢 LOW  
**Effort:** 2 points

---

### US-032: Demo/Educational Mode
**As a** user showing the robot  
**I want** Kuko to do a narrated demonstration of its capabilities  
**So that** I can impress visitors and educate about its functioning

**Acceptance Criteria:**
- [ ] Command: "Kuko demo mode"
- [ ] Executes sequence: navigation → detection → grasp → deposit
- [ ] Narrates each step: "Now I'm going to scan the area..."
- [ ] Uses pre-positioned test objects
- [ ] Duration: 3-5 minutes
- [ ] Exit demo: "Kuko end demo"

**Priority:** 🟢 LOW  
**Effort:** 1 point

---

## 📋 Prioritization Matrix

| ID | Story | Priority | Effort | Week | Value/Effort |
|----|----------|-----------|----------|--------|----------------|
| US-001 | Visual Classification | 🔴 CRITICAL | 3 | 1 | ⭐⭐⭐⭐⭐ |
| US-002 | Voice Commands | 🔴 CRITICAL | 3 | 1 | ⭐⭐⭐⭐⭐ |
| US-006 | Coordinate Navigation | 🔴 CRITICAL | 5 | 3 | ⭐⭐⭐⭐ |
| US-007 | Teaching Mode | 🔴 CRITICAL | 3 | 3 | ⭐⭐⭐⭐⭐ |
| US-008 | Navigate by Name | 🔴 CRITICAL | 2 | 3 | ⭐⭐⭐⭐⭐ |
| US-012 | Object Grasping | 🔴 CRITICAL | 5 | 5 | ⭐⭐⭐⭐ |
| US-014 | Correct Deposit | 🔴 CRITICAL | 3 | 5 | ⭐⭐⭐⭐ |
| US-017 | Inspection Mission | 🔴 CRITICAL | 4 | 6 | ⭐⭐⭐⭐⭐ |
| US-018 | Selective Collection | 🔴 CRITICAL | 3 | 6 | ⭐⭐⭐⭐⭐ |
| US-003 | Multiple Objects | 🟡 HIGH | 2 | 2 | ⭐⭐⭐⭐ |
| US-009 | Visual Correction | 🟡 HIGH | 4 | 4 | ⭐⭐⭐ |
| US-013 | Grasp Types | 🟡 HIGH | 3 | 5 | ⭐⭐⭐ |
| US-019 | AI Reasoning | 🟡 HIGH | 3 | 6 | ⭐⭐⭐⭐ |

---

## 🎯 Usage Recommendations

### For Agile Development:

1. **Sprint Planning:**
   - Use these stories as backlog
   - Each sprint = 1 week from roadmap
   - Prioritize CRITICAL first

2. **Definition of Done:**
   - All acceptance criteria ✅
   - Code manually tested
   - Documentation updated
   - Working demo to product owner

3. **Estimations:**
   - Story points: 1 = half day, 5 = full week
   - Re-estimate after each sprint (team velocity)

4. **Testing:**
   - Each acceptance criterion = 1 test case
   - Use US-024 (simulation mode) to automate tests

### For Stakeholder Communication:

- **End user:** Focus on "so that" (benefit)
- **Developer:** Technical criteria are your checklist
- **Product Owner:** Prioritization matrix guides scope decisions

### Plan Adaptation:

If you encounter **technical limitations** during development:
1. Mark story as "Blocked"
2. Document specific blocker
3. Create alternative story with reduced scope
4. Example: If grasp fails → "US-012b: Grasp only soft plush toys"

---

## ✅ Next Steps

1. **Validate stories** with real users (are these the functionalities they need?)
2. **Refine criteria** after first sprint (adjust based on learnings)
3. **Add stories** as needs arise (living backlog)
4. **Prioritize with** MoSCoW model:
   - **Must:** Critical US (red)
   - **Should:** High US (yellow)
   - **Could:** Medium US (green)
   - **Won't (for now):** Low US

**These 32 stories completely cover the MVP described in the technical architecture, respecting hardware limitations and prioritizing according to the 5-6 week plan.**