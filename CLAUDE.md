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
- Voice commands are in Spanish
- Project focuses on household cleaning use case (picking up toys, trash)
- Teaching mode allows users to memorize room locations with natural names
- Navigation uses IMU odometry with visual landmark correction
