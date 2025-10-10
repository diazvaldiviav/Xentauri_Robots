# US-002: Natural Language Voice Commands - Implementation

## 📋 Overview

**User Story:** As a user, I want to give Kuko orders in Spanish speaking naturally, so that I don't have to use technical commands or apps.

**Epic:** EPIC 1 - Artificial Intelligence & Vision (SCRUM-5)
**Priority:** 🔴 CRITICAL (Week 1)
**Effort:** 3 points

## ✅ Acceptance Criteria

- [x] Kuko responds to wake word "Kuko" (previously "lulu")
- [x] Recognizes Spanish commands: "go to bedroom", "pick up the toys"
- [x] Gemini NLU extracts: action + location + object from phrase
- [x] Responds with synthesized voice confirming what was understood
- [x] Handles 5+ variations of same command (e.g., "go", "walk", "move")
- [x] Command→response latency <2 seconds

## 🗂️ Files Created

### 1. `kuko_voice_commands.py`
Complete voice command system implementation:
- **Wake word detection**: Picovoice Porcupine with custom "Kuko" model
- **Speech recognition**: XGOEDU library (bilingual Spanish/English)
- **NLU parsing**: Gemini AI extracts action, location, object
- **TTS response**: XGOEDU text-to-speech synthesis
- **Latency optimization**: Pipeline optimized for <2s total time
- **Variation handling**: Tests 5+ command variations

### 2. `Kuko-Despierta_es_raspberry-pi_v3_0_0.ppn`
Picovoice custom wake word model for "Kuko" (Spanish, Raspberry Pi v3)

### 3. `requirements.txt` (updated)
Added voice/audio dependencies:
- `pvporcupine>=2.2.0` - Wake word detection
- `pyaudio>=0.2.13` - Audio I/O
- `SpeechRecognition>=3.10.0` - Backup STT

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 VOICE COMMAND PIPELINE                  │
│                    (Target: <2s)                        │
└─────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
         ┌──────▼──────┐       ┌───────▼──────┐
         │  Wake Word  │       │   Simulate   │
         │  Detection  │       │ (dev mode)   │
         │ (Picovoice) │       └──────────────┘
         └──────┬──────┘
                │ "Kuko" detected
         ┌──────▼──────────┐
         │ Speech-to-Text  │
         │   (XGOEDU)      │
         │  Spanish/English│
         └──────┬──────────┘
                │ Transcribed text
         ┌──────▼──────────┐
         │  Gemini NLU     │
         │   Parsing       │
         │ Extract:        │
         │ • action        │
         │ • location      │
         │ • object        │
         └──────┬──────────┘
                │ Parsed command
         ┌──────▼──────────┐
         │ Text-to-Speech  │
         │   (XGOEDU)      │
         │  Confirmation   │
         └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

1. **Environment Setup:**
   ```bash
   # Set API keys
   export GEMINI_API_KEY="your_gemini_key"
   export PICOVOICE_ACCESS_KEY="your_picovoice_key"

   # Or create tokens.txt with Gemini key
   echo "your_gemini_key" > tokens.txt
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify Wake Word File:**
   ```bash
   ls -lh Kuko-Despierta_es_raspberry-pi_v3_0_0.ppn
   # Should show ~4KB file
   ```

### Running on Robot Hardware

```bash
python kuko_voice_commands.py
```

**Expected Flow:**
```
1. 🎤 Listening for 'Kuko'...
2. ✓ Wake word detected: 'Kuko'
3. 🎤 Listening for command (5s)...
4. ✓ Command transcribed: "ve a la habitación y revisa"
5. ✓ Command parsed:
     Action: go
     Location: bedroom
     Intent: navigate
6. 🔊 Speaking: "Voy a la habitación a revisar"
7. ✓ PASS Total latency: 1.8s (target: <2.0s)
```

### Testing Without Hardware (Simulation Mode)

The system automatically falls back to simulation if robot hardware is unavailable:

```python
from kuko_voice_commands import KukoVoiceCommands

kuko = KukoVoiceCommands()

# Test command parsing (no hardware needed)
result = kuko.parse_command_with_gemini("Kuko ve a la cocina")

print(f"Action: {result['action']}")
print(f"Location: {result['location']}")
```

## 🧪 Testing

### Test 1: Acceptance Criteria Validation

```bash
python kuko_voice_commands.py
# Automatically runs validation on startup
```

**Validates:**
- ✅ Wake word file exists
- ✅ Gemini NLU parsing (action + location + object)
- ✅ TTS confirmation
- ✅ High confidence (>70%)

### Test 2: Command Variations (5+ Variations)

```python
from kuko_voice_commands import KukoVoiceCommands

kuko = KukoVoiceCommands()
results = kuko.test_command_variations()
```

**Tests:**
- ✅ "ve" = "camina" = "muévete" = "dirígete" (Spanish navigate)
- ✅ "go" = "walk" = "move" (English navigate)
- ✅ "recoge" = "levanta" = "agarra" (Spanish pick up)
- ✅ "revisa" = "inspecciona" = "verifica" (Spanish inspect)

**Expected Output:**
```
Successful parses: 15/15 (100%)
✓ Acceptance Criteria: Handle 5+ variations - PASS
```

### Test 3: Latency Benchmark

```python
result = kuko.process_voice_command(listen_duration=5)
print(f"Total latency: {result['total_time']:.2f}s")
```

**Target Breakdown:**
- Wake word detection: ~0.5s
- Speech-to-text: ~0.8s
- Gemini NLU parsing: ~0.4s
- TTS synthesis: ~0.3s
- **Total:** <2.0s ✅

## 📊 Usage Examples

### Example 1: Navigate to Location

**User:** "Kuko ve a la habitación"
**System:**
```python
{
  "action": "go",
  "location": "bedroom",
  "object": null,
  "intent": "navigate",
  "confidence": 95,
  "natural_response": "Voy a la habitación"
}
```

### Example 2: Pick Up Objects

**User:** "Kuko recoge los juguetes de la sala"
**System:**
```python
{
  "action": "pick_up",
  "location": "living_room",
  "object": "toys",
  "intent": "collect_object",
  "confidence": 92,
  "natural_response": "Recogiendo los juguetes de la sala"
}
```

### Example 3: Room Inspection

**User:** "Kuko go to the bedroom and check that it's okay"
**System:**
```python
{
  "action": "check",
  "location": "bedroom",
  "object": null,
  "intent": "inspect_room",
  "confidence": 88,
  "natural_response": "Going to bedroom to check"
}
```

### Example 4: Complex Multi-Action

**User:** "Kuko ve a la cocina y recoge la basura"
**System:**
```python
{
  "action": "go",
  "location": "kitchen",
  "object": "trash",
  "intent": "navigate_and_collect",
  "confidence": 94,
  "natural_response": "Voy a la cocina a recoger la basura"
}
```

## 🔧 Configuration

### Environment Variables

```bash
# Required
export GEMINI_API_KEY="your_key_here"

# Required for wake word detection
export PICOVOICE_ACCESS_KEY="your_key_here"
```

### Custom Wake Word Path

```python
kuko = KukoVoiceCommands(
    wake_word_path="/custom/path/to/wake_word.ppn",
    access_key="your_picovoice_key"
)
```

### Recording Duration

```python
# Listen for 3 seconds instead of default 5
result = kuko.process_voice_command(listen_duration=3)
```

## 🎯 Gemini NLU Capabilities

The Gemini parser handles:

### Actions
- **Navigate:** go, walk, move, navigate, head to
- **Collect:** pick up, grab, collect, take, get
- **Inspect:** check, inspect, verify, look at, review
- **Clean:** clean, tidy, organize

### Locations
- Rooms: bedroom, kitchen, living room, bathroom, etc.
- Landmarks: "near the sofa", "by the door"
- Handles both Spanish and English

### Objects
- Categories: toys, trash, clothing, bottles, etc.
- Specific items: "red toy car", "plastic bottle"
- Plurals and variations

### Intent Classification
- `navigate`: Go to location
- `collect_object`: Pick up specific object
- `inspect_room`: Check room status
- `clean`: General cleaning task
- `navigate_and_collect`: Combined action

## 🔗 Integration with Other User Stories

### US-001 (Visual Classification)
```python
# After voice command navigation
if parsed['intent'] == 'inspect_room':
    from kuko_vision_mvp import KukoVision
    vision = KukoVision()
    objects = vision.classify_objects("photo.jpg")
```

### US-006 (Navigation - Week 3)
```python
# Execute navigation after voice command
if parsed['action'] == 'go' and parsed['location']:
    robot.navigate_to(parsed['location'])
```

### US-012 (Object Grasping - Week 5)
```python
# Execute grasping after voice command
if parsed['intent'] == 'collect_object':
    robot.grasp_object(parsed['object'])
```

## 📝 API Reference

### `KukoVoiceCommands`

#### Methods

**`__init__(wake_word_path, access_key)`**
- Initialize voice command system
- Args: wake_word_path (str), access_key (str)

**`initialize_wake_word_detection()`**
- Setup Picovoice Porcupine
- Returns: bool (success)

**`listen_for_wake_word(timeout)`**
- Listen for "Kuko" wake word
- Args: timeout (int, seconds)
- Returns: bool (detected)

**`transcribe_command(duration)`**
- Record and transcribe voice
- Args: duration (int, seconds)
- Returns: str (transcribed text)

**`parse_command_with_gemini(command_text)`**
- Parse command with NLU
- Args: command_text (str)
- Returns: dict (parsed components)

**`speak_response(text)`**
- Synthesize and speak text
- Args: text (str)
- Returns: bool (success)

**`process_voice_command(listen_duration)`**
- Complete pipeline (wake → transcribe → parse → speak)
- Args: listen_duration (int, seconds)
- Returns: dict (command + metrics)

## 🐛 Troubleshooting

### Wake Word Not Detected

```bash
# Check Picovoice key
echo $PICOVOICE_ACCESS_KEY

# Check wake word file
ls -lh Kuko-Despierta_es_raspberry-pi_v3_0_0.ppn

# Test microphone
arecord -d 3 test.wav && aplay test.wav
```

### Speech Recognition Fails

```python
# Test robot audio
from xgoedu import XGOEDU
robot = XGOEDU()
robot.xgoAudioRecord("test", seconds=3)
robot.xgoSpeaker("test.wav")
```

### Gemini NLU Low Confidence

- Ensure command is clear and specific
- Check GEMINI_API_KEY is valid
- Test internet connection
- Review command variations in test suite

### Latency >2s

**Optimization strategies:**
1. Reduce recording duration (5s → 3s)
2. Use faster Gemini model (gemini-2.0-flash-exp)
3. Run TTS in parallel with other tasks
4. Cache common responses

## 📚 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| google-generativeai | >=0.3.0 | Gemini NLU parsing |
| pvporcupine | >=2.2.0 | Wake word detection |
| pyaudio | >=0.2.13 | Microphone audio capture |
| xgoedu | (robot) | Speech recognition & TTS |

## 🎉 Next Steps

After US-002 validation:
- [ ] US-003: Multiple Object Detection (Week 2)
- [ ] US-004: Visual Display Feedback (Week 2)
- [ ] US-005: Vision Error Handling (Week 2)
- [ ] US-006: Coordinate Navigation (Week 3) - **Integrates with voice commands!**

## 📖 Related Documentation

- **User Stories:** `user_history.md` (lines 83-103)
- **Project Instructions:** `CLAUDE.md`
- **Audio Examples:** `DOGZILLA_Lite_class/2.Base Control/`
- **Picovoice Docs:** https://picovoice.ai/docs/porcupine/

---

**Status:** ✅ Implementation Complete
**Last Updated:** 2025-10-10
**Author:** Kuko Robot Project Team
