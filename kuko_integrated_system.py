#!/usr/bin/env python3
"""
Kuko Integrated System - Voice + Vision + Movement
Combines US-002 (Voice Commands) with US-003 (Multi-Object Detection)

Features:
- Voice-activated floor scanning
- Automatic 360° search if nothing detected
- Bilingual responses (Spanish/English)
- Priority-based object reporting

Author: Kuko Robot Project
Epic: EPIC 1 - Artificial Intelligence & Vision
"""

import time
from typing import Dict, List
from kuko_voice_commands import KukoVoiceCommands
from kuko_vision_mvp import KukoVision


class KukoIntegratedSystem:
    """
    Integrated system combining voice commands, vision detection, and movement
    """

    def __init__(self):
        """Initialize all subsystems"""
        print("=" * 60)
        print("KUKO INTEGRATED SYSTEM")
        print("Voice + Vision + Movement")
        print("=" * 60)

        # Initialize voice command system
        print("\n[1] Initializing voice command system...")
        self.voice = KukoVoiceCommands()

        # Initialize vision system
        print("\n[2] Initializing vision system...")
        self.vision = KukoVision(use_robot=True)

        # Robot instance (shared with vision system)
        self.robot = self.vision.robot
        self.use_robot = self.vision.use_robot

        # Movement parameters
        self.turn_angle = 45  # degrees per turn
        self.scan_positions = 8  # 360° / 45° = 8 positions

        print("\n✓ All systems initialized")

    def turn_robot(self, direction: str = "right", angle: int = 45) -> bool:
        """
        Turn robot left or right by specified angle

        Uses XGO turn() API:
        - Positive values = turn left
        - Negative values = turn right
        - Range: -150 to 150 (speed/intensity)

        For discrete angle turns, we use a timed approach:
        - Set turn speed
        - Wait for calculated duration
        - Stop

        Args:
            direction: "left" or "right"
            angle: Rotation angle in degrees (default: 45°)

        Returns:
            bool: True if successful
        """
        if not self.use_robot or not self.robot:
            print(f"🔄 [Simulated] Turning {direction} {angle}°...")
            time.sleep(0.5)
            return True

        try:
            print(f"🔄 Turning {direction} {angle}°...")

            # Set slow pace for precise turns
            self.robot.pace('slow')

            # Calculate turn speed and duration
            # At turn speed 80, robot rotates approximately 45° per second
            turn_speed = 80
            turn_direction = turn_speed if direction == "left" else -turn_speed

            # Calculate duration based on angle (calibration needed)
            # Rough estimate: 45° takes ~1 second at speed 80
            duration = (angle / 45.0) * 1.0

            # Execute turn
            self.robot.turn(turn_direction)
            time.sleep(duration)
            self.robot.stop()

            print(f"✓ Turned {direction} {angle}°")
            return True

        except Exception as e:
            print(f"⚠️  Turn failed: {e}")
            return False

    def scan_360(self) -> List[Dict]:
        """
        Perform 360° scan looking for objects on floor

        Takes photos at 8 positions (every 45°) and aggregates results

        Returns:
            List of all unique objects detected during scan
        """
        print("\n" + "=" * 60)
        print("360° FLOOR SCAN")
        print("=" * 60)

        all_objects = []
        positions_scanned = 0

        for position in range(self.scan_positions):
            print(f"\n📍 Scan position {position + 1}/{self.scan_positions} ({position * self.turn_angle}°)")

            # Capture and analyze at current position
            try:
                # Initialize camera if not already done
                if not self.vision.camera or not self.vision.camera.isOpened():
                    self.vision.init_camera()

                # Capture photo
                image_path = self.vision.capture_photo(f"scan_{position}.jpg")

                # Detect objects
                result = self.vision.detect_multiple_objects_with_priority(image_path)

                # Add objects to aggregate list
                if result.get('objects'):
                    for obj in result['objects']:
                        obj['scan_position'] = position
                        obj['scan_angle'] = position * self.turn_angle
                        all_objects.append(obj)
                    print(f"  ✓ Found {len(result['objects'])} objects at this position")
                else:
                    print(f"  ○ No objects at this position")

                positions_scanned += 1

            except Exception as e:
                print(f"  ⚠️  Scan failed at position {position}: {e}")

            # Turn to next position (except on last iteration)
            if position < self.scan_positions - 1:
                self.turn_robot("right", self.turn_angle)
                time.sleep(0.5)  # Wait for robot to stabilize

        print(f"\n✓ Scan complete: {positions_scanned} positions checked")

        # Deduplicate objects seen from multiple angles
        unique_objects = self._deduplicate_scan_results(all_objects)
        print(f"✓ Total unique objects found: {len(unique_objects)}")

        return unique_objects

    def _deduplicate_scan_results(self, objects: List[Dict]) -> List[Dict]:
        """
        Deduplicate objects detected from multiple scan positions

        Uses description similarity and category matching
        (spatial deduplication not possible across different positions)

        Args:
            objects: List of detected objects from all scan positions

        Returns:
            List of unique objects
        """
        if len(objects) <= 1:
            return objects

        unique = []

        for obj in objects:
            # Check if similar object already in unique list
            is_duplicate = False

            for existing in unique:
                # Same category
                if obj.get('category') != existing.get('category'):
                    continue

                # Similar description (shared keywords)
                obj_desc = set(obj.get('description', '').lower().split())
                exist_desc = set(existing.get('description', '').lower().split())
                shared_words = obj_desc.intersection(exist_desc)

                if len(shared_words) >= 3:  # High similarity threshold
                    is_duplicate = True
                    # Keep the one with higher confidence
                    if obj.get('confidence', 0) > existing.get('confidence', 0):
                        unique.remove(existing)
                        unique.append(obj)
                    break

            if not is_duplicate:
                unique.append(obj)

        return unique

    def check_floor(self, language: str = 'es') -> Dict:
        """
        Check floor for objects at current position

        Args:
            language: 'es' for Spanish, 'en' for English

        Returns:
            Detection result dictionary
        """
        # Speak confirmation
        checking_msg = "Estoy chequeando" if language == 'es' else "I am checking"
        print(f"\n🔊 {checking_msg}")
        self.voice.speak_response(checking_msg, language=language)

        # Initialize camera if needed
        if not self.vision.camera or not self.vision.camera.isOpened():
            self.vision.init_camera()

        # Capture photo
        image_path = self.vision.capture_photo("floor_check.jpg")

        # Detect objects with US-003 pipeline
        result = self.vision.detect_multiple_objects_with_priority(image_path)

        return result

    def report_objects(self, objects: List[Dict], language: str = 'es'):
        """
        Report detected objects via voice

        Args:
            objects: List of detected objects
            language: 'es' for Spanish, 'en' for English
        """
        if not objects:
            # No objects found
            msg = "El piso está limpio" if language == 'es' else "The floor is clean"
            print(f"\n🔊 {msg}")
            self.voice.speak_response(msg, language=language)
            return

        # Objects found - report summary
        count = len(objects)

        if language == 'es':
            msg = f"Encontré {count} objeto{'s' if count > 1 else ''}"
        else:
            msg = f"I found {count} object{'s' if count > 1 else ''}"

        print(f"\n🔊 {msg}")
        self.voice.speak_response(msg, language=language)

        # Report each object
        for i, obj in enumerate(objects[:3], 1):  # Report top 3
            category = obj.get('category', 'objeto')
            distance = obj.get('distance_info', {}).get('estimated_distance_cm', 'unknown')

            if language == 'es':
                category_es = {
                    'toy': 'juguete',
                    'trash': 'basura',
                    'clothing': 'ropa',
                    'other': 'objeto'
                }.get(category, category)

                obj_msg = f"Objeto {i}: {category_es} a {distance} centímetros"
            else:
                obj_msg = f"Object {i}: {category} at {distance} centimeters"

            print(f"   {obj_msg}")
            time.sleep(0.5)

    def handle_floor_scan_command(self, parsed_command: Dict) -> bool:
        """
        Handle "check floor" voice command

        Args:
            parsed_command: Parsed voice command from Gemini NLU

        Returns:
            bool: True if command handled successfully
        """
        intent = parsed_command.get('intent', '').lower()
        action = parsed_command.get('action', '').lower()
        language = parsed_command.get('detected_language', 'es')

        # Check if this is a floor scanning command
        is_scan_command = (
            'inspect' in intent or
            'check' in intent or
            'scan' in intent or
            'check' in action or
            'inspect' in action or
            'scan' in action
        )

        if not is_scan_command:
            return False

        print("\n" + "=" * 60)
        print("FLOOR SCANNING INITIATED")
        print("=" * 60)

        # Step 1: Check floor at current position
        result = self.check_floor(language=language)

        # Step 2: If objects found, report and finish
        if result.get('objects'):
            print(f"\n✓ Objects detected at current position: {len(result['objects'])}")
            self.report_objects(result['objects'], language=language)

            # Save results
            self.vision.draw_bounding_boxes("floor_check.jpg", result['objects'], "floor_scan_result.jpg")
            self.vision.save_coordinates_for_grasping(result['objects'], "floor_scan_coordinates.json")
            return True

        # Step 3: No objects at current position - perform 360° scan
        print("\n⚠️  No objects at current position")

        scanning_msg = "Voy a buscar alrededor" if language == 'es' else "I will look around"
        print(f"🔊 {scanning_msg}")
        self.voice.speak_response(scanning_msg, language=language)

        all_objects = self.scan_360()

        # Step 4: Report results
        self.report_objects(all_objects, language=language)

        # Save aggregated results if objects found
        if all_objects:
            self.vision.draw_bounding_boxes("scan_0.jpg", all_objects, "360_scan_result.jpg")
            self.vision.save_coordinates_for_grasping(all_objects, "360_scan_coordinates.json")

        return True

    def run_interactive(self):
        """
        Interactive mode - listen for voice commands and execute
        """
        print("\n" + "=" * 60)
        print("KUKO INTERACTIVE MODE")
        print("=" * 60)
        print("\nAvailable commands:")
        print("  🇪🇸 'Kuko, chequea a ver si hay algo en el piso'")
        print("  🇪🇸 'Kuko, revisa el piso'")
        print("  🇪🇸 'Kuko, busca juguetes'")
        print("  🇬🇧 'Kuko, check if there's something on the floor'")
        print("  🇬🇧 'Kuko, scan the floor'")
        print("\nPress Ctrl+C to exit\n")

        try:
            while True:
                # Process voice command
                result = self.voice.process_command()

                # Check if it's a floor scanning command
                if result.get('confidence', 0) > 50:
                    handled = self.handle_floor_scan_command(result)

                    if not handled:
                        # Not a floor scan command - generic response
                        print(f"\n⚠️  Command understood but not implemented yet")
                        print(f"   Intent: {result.get('intent')}")
                        print(f"   Action: {result.get('action')}")
                else:
                    print("\n⚠️  Command not understood clearly")

                # Continue?
                print("\n" + "-" * 60)
                cont = input("Give another command? (ENTER=yes, 'q'=quit): ")
                if cont.lower() == 'q':
                    break

        except KeyboardInterrupt:
            print("\n\n✓ Exiting...")

        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        print("\n🧹 Cleaning up resources...")

        # Release camera
        if self.vision:
            self.vision.release_camera()

        # Clean up voice system
        if self.voice:
            self.voice.cleanup()

        print("✓ Cleanup complete")


def main():
    """Main execution"""
    kuko = KukoIntegratedSystem()
    kuko.run_interactive()


if __name__ == "__main__":
    main()
