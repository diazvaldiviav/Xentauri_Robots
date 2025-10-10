#!/usr/bin/env python3
"""
US-002: Natural Language Voice Commands
Kuko Robot - Production Voice Command System

Features:
- Wake word: "Kuko" to get robot's attention
- Bilingual: Spanish/English command recognition  
- Gemini NLU: Extracts action + location + object
- TTS: Spanish confirmation responses

Author: Kuko Robot Project
Epic: EPIC 1 - Artificial Intelligence & Vision (SCRUM-5)
"""

import os
import time
import json
from datetime import datetime
from typing import Dict, Optional
import google.generativeai as genai

# Robot-specific imports (XGOEDU library)
try:
    from xgoedu import XGOEDU
    ROBOT_AVAILABLE = True
except ImportError:
    ROBOT_AVAILABLE = False
    print("⚠️  xgoedu library not available. Running in simulation mode.")


class KukoVoiceCommands:
    """Voice command system for Kuko robot with Gemini NLU parsing."""

    def __init__(self):
        """Initialize voice command system."""

        # Initialize Gemini AI
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            try:
                with open('tokens.txt', 'r') as f:
                    api_key = f.read().strip()
            except FileNotFoundError:
                raise ValueError("GEMINI_API_KEY not found in environment or tokens.txt")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

        # Initialize robot hardware
        self.robot = None
        if ROBOT_AVAILABLE:
            self.robot = XGOEDU()
            print("✓ Robot initialized")

        # Command history
        self.command_history = []

        print("✓ Kuko Voice Commands ready")

    def wait_for_wake_word(self) -> bool:
        """
        Wait for user to say "Kuko" wake word.
        
        Note: Wake word "Kuko" gets the robot's attention before giving commands.
        Hardware wake word detection (Picovoice) requires additional setup.
        
        Returns:
            True when ready to listen
        """
        print("\n" + "="*60)
        print("🎤 SAY 'KUKO' TO GET MY ATTENTION")
        print("="*60)
        print("\nExamples:")
        print("  • 'Kuko, ve a la habitación'")
        print("  • 'Kuko, recoge los juguetes'")
        print("  • 'Kuko, go to the bedroom'")
        print("\n👉 Press ENTER when ready to speak your command...")
        input()
        return True

    def listen_and_transcribe(self, duration: int = 5) -> Optional[str]:
        """
        Record and transcribe voice command.

        Note: XGOEDU SpeechRecognition uses Baidu API which may transcribe
        in Chinese by default. Gemini will interpret the intent regardless.

        Args:
            duration: Recording duration in seconds

        Returns:
            Transcribed text (may be in Chinese/Spanish/English)
        """
        if not self.robot:
            print("⚠️  Robot not available. Using test command.")
            return "Kuko ve a la habitación"

        try:
            print(f"\n🎤 LISTENING FOR {duration} SECONDS...")
            print("🗣️  Speak now!")

            start_time = time.time()
            text = self.robot.SpeechRecognition(seconds=duration)
            elapsed = time.time() - start_time

            if text:
                print(f"✓ Recorded ({elapsed:.2f}s): '{text}'")
                if any('\u4e00' <= char <= '\u9fff' for char in text):
                    print("⚠️  Note: Baidu API transcribed in Chinese. Gemini will interpret intent.")
                return text
            else:
                print("❌ No speech detected")
                return None

        except Exception as e:
            print(f"❌ Transcription failed: {e}")
            return None

    def parse_command_with_gemini(self, command_text: str) -> Dict:
        """
        Parse voice command using Gemini NLU.
        
        Extracts: action, location, object, intent
        Always responds in Spanish regardless of input language.

        Args:
            command_text: Transcribed command (any language)

        Returns:
            Parsed command dictionary
        """
        prompt = f"""You are Kuko's brain - a cleaning robot NLU system.

The user said: "{command_text}"

This may be in Spanish, English, or Chinese (if speech recognition failed). 
Parse the INTENT and extract:

1. **action**: Main verb (go/ve/camina, pick_up/recoge/levanta, inspect/revisa, clean/limpia)
2. **location**: Target room (bedroom/habitación, kitchen/cocina, living_room/sala) or null
3. **object**: Target object (toys/juguetes, trash/basura, clothing/ropa) or null  
4. **intent**: High-level (navigate, collect_object, inspect_room, clean)
5. **confidence**: 0-100 score
6. **natural_response**: Brief Spanish confirmation (ALWAYS in Spanish, even if command was English/Chinese)

Handle variations:
- "go"="ve"="camina"="muévete"="walk"="move"
- "pick up"="recoge"="levanta"="agarra"="collect"
- "inspect"="revisa"="check"="verifica"

Respond ONLY with valid JSON:
{{
  "action": "string or null",
  "location": "string or null",
  "object": "string or null",
  "intent": "string",
  "confidence": number,
  "natural_response": "Spanish confirmation"
}}"""

        try:
            start_time = time.time()
            response = self.model.generate_content(prompt)
            elapsed = time.time() - start_time

            # Parse JSON
            response_text = response.text.strip()
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])
                if response_text.startswith('json'):
                    response_text = response_text[4:].strip()

            parsed = json.loads(response_text)
            parsed['parse_time'] = elapsed
            parsed['raw_command'] = command_text

            print(f"\n✓ Gemini parsed ({elapsed:.2f}s):")
            print(f"  Action: {parsed.get('action')}")
            print(f"  Location: {parsed.get('location')}")
            print(f"  Object: {parsed.get('object')}")
            print(f"  Intent: {parsed.get('intent')}")
            print(f"  Confidence: {parsed.get('confidence')}%")

            return parsed

        except Exception as e:
            print(f"❌ Parsing failed: {e}")
            return {
                "action": None,
                "location": None,
                "object": None,
                "intent": "unknown",
                "confidence": 0,
                "natural_response": "No entendí el comando",
                "error": str(e)
            }

    def speak_response(self, text: str) -> bool:
        """
        Speak text using robot TTS.

        Note: XGOEDU SpeechSynthesis uses Baidu TTS which defaults to Chinese voice.
        The text is in Spanish but may sound Chinese-accented.
        Consider using alternative TTS library for proper Spanish voice.

        Args:
            text: Spanish text to speak

        Returns:
            True if successful
        """
        if not self.robot:
            print(f"\n🔊 [Simulated]: '{text}'")
            return True

        try:
            print(f"\n🔊 Speaking: '{text}'")
            print("⚠️  Note: Baidu TTS may use Chinese voice. Text is Spanish.")

            start_time = time.time()
            self.robot.SpeechSynthesis(text)
            elapsed = time.time() - start_time

            print(f"✓ Spoken ({elapsed:.2f}s)")
            return True

        except Exception as e:
            print(f"❌ TTS failed: {e}")
            return False

    def process_command(self) -> Dict:
        """
        Complete voice command pipeline:
        1. Wait for user to say "Kuko" (press ENTER)
        2. Listen and transcribe command (5 seconds)
        3. Parse with Gemini NLU
        4. Speak Spanish confirmation

        Returns:
            Parsed command with metrics
        """
        pipeline_start = time.time()

        # Step 1: Wait for wake word
        ready = self.wait_for_wake_word()
        if not ready:
            return {"error": "Cancelled", "total_time": 0}

        # Step 2: Listen and transcribe
        command_text = self.listen_and_transcribe(duration=5)
        if not command_text:
            print("\n❌ No command detected. Try again.")
            return {"error": "No speech", "total_time": time.time() - pipeline_start}

        # Step 3: Parse with Gemini
        parsed = self.parse_command_with_gemini(command_text)

        # Step 4: Speak confirmation (only if confident)
        if parsed.get('confidence', 0) > 50 and 'natural_response' in parsed:
            self.speak_response(parsed['natural_response'])
        else:
            print("\n⚠️  Low confidence - no voice confirmation")

        # Total time
        total_time = time.time() - pipeline_start
        parsed['total_time'] = total_time

        # Log history
        self.command_history.append({
            'timestamp': datetime.now().isoformat(),
            'command': parsed
        })

        print(f"\n✓ Total time: {total_time:.2f}s")

        return parsed

    def run_interactive(self):
        """
        Interactive command loop.
        User says "Kuko" to get attention, then gives command.
        """
        print("\n" + "="*60)
        print("KUKO VOICE COMMAND SYSTEM")
        print("="*60)
        print("\nHow it works:")
        print("1. Press ENTER when ready")
        print("2. Say 'Kuko' + your command")
        print("3. Robot will understand and confirm")
        print("\nExamples:")
        print("  🇪🇸 'Kuko, ve a la habitación'")
        print("  🇪🇸 'Kuko, recoge los juguetes de la sala'")
        print("  🇬🇧 'Kuko, go to the bedroom'")
        print("\n💡 Tip: Speak clearly for 5 seconds after pressing ENTER")
        print("\nPress Ctrl+C to exit\n")

        try:
            while True:
                # Process one command
                result = self.process_command()

                # Show results
                if 'error' not in result and result.get('confidence', 0) > 50:
                    print("\n✅ COMMAND UNDERSTOOD")
                    print(f"  → Intent: {result.get('intent')}")
                    print(f"  → Action: {result.get('action')}")
                    if result.get('location'):
                        print(f"  → Location: {result.get('location')}")
                    if result.get('object'):
                        print(f"  → Object: {result.get('object')}")
                else:
                    print("\n⚠️  COMMAND NOT UNDERSTOOD")
                    if result.get('raw_command'):
                        print(f"  Heard: {result.get('raw_command')}")

                # Continue?
                print("\n" + "-"*60)
                cont = input("Give another command? (ENTER=yes, 'q'=quit): ")
                if cont.lower() == 'q':
                    break

        except KeyboardInterrupt:
            print("\n\n✓ Exiting...")

        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources."""
        if self.robot:
            del self.robot
        print("✓ Cleanup complete")


def main():
    """Main execution."""
    kuko = KukoVoiceCommands()
    kuko.run_interactive()


if __name__ == "__main__":
    main()
