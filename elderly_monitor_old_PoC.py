#!/usr/bin/env python3
"""
Elderly Posture Monitor

This application monitors a person's posture using webcam and computer vision.
It detects when a person transitions from lying down to sitting up and sends alerts.
"""

import cv2
import mediapipe as mp
import time
import os


class PostureMonitor:
    """Monitors a person's posture and detects transitions from lying down to sitting up."""
    
    # State definitions
    STATE_LYING_DOWN = "lying_down"
    STATE_MAYBE_SITTING = "maybe_sitting_up"
    STATE_CONFIRMED_SITTING = "confirmed_sitting_up"
    
    def __init__(self, 
                 posture_threshold=0.2, 
                 persistence_seconds=5, 
                 alert_cooldown_seconds=30,
                 camera_id=0):
        """Initialize the posture monitor.
        
        Args:
            posture_threshold: Vertical difference threshold between shoulder and hip
            persistence_seconds: Time posture must be maintained to confirm
            alert_cooldown_seconds: Minimum time between alerts
            camera_id: ID of the camera to use
        """
        # Configuration parameters
        self.posture_threshold = posture_threshold
        self.persistence_seconds = persistence_seconds
        self.alert_cooldown_seconds = alert_cooldown_seconds
        self.camera_id = camera_id
        
        # Initialize state variables
        self.posture_state = self.STATE_LYING_DOWN
        self.state_change_time = None
        self.last_alert_time = 0
        
        # Initialize MediaPipe pose detection
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose()
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Initialize webcam
        self.cap = None
    
    def send_alert(self):
        """Send notification that person sat up."""
        os.system("""osascript -e 'display notification "Person sat up!" with title "Elderly Monitor"'""")
        print("🚨 Alert: Person sat up!")
    
    def setup_camera(self):
        """Set up the webcam capture."""
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open camera with ID {self.camera_id}")
    
    def process_frame(self, frame):
        """Process a single frame and update posture state.
        
        Args:
            frame: The video frame to process
            
        Returns:
            The processed frame with annotations
        """
        # Mirror the frame for a more intuitive view
        frame = cv2.flip(frame, 1)
        
        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the frame with MediaPipe Pose
        results = self.pose.process(rgb_frame)
        
        # Get current time for state transitions
        current_time = time.time()
        
        # Process pose landmarks if detected
        if results.pose_landmarks:
            # Draw landmarks on the frame
            self.mp_drawing.draw_landmarks(
                frame, 
                results.pose_landmarks, 
                self.mp_pose.POSE_CONNECTIONS
            )
            
            # Get relevant landmarks
            landmarks = results.pose_landmarks.landmark
            left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
            left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP]
            
            # Calculate vertical difference (positive if shoulder is above hip)
            vertical_diff = left_hip.y - left_shoulder.y
            
            # Update state based on posture
            self._update_state(vertical_diff, current_time)
        
        # Display current state on frame
        cv2.putText(
            frame, 
            f"Posture: {self.posture_state}", 
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 
            1, 
            (0, 255, 0), 
            2
        )
        
        return frame
    
    def _update_state(self, vertical_diff, current_time):
        """Update posture state based on the vertical difference between shoulder and hip.
        
        Args:
            vertical_diff: Difference between hip and shoulder y-coordinates
            current_time: Current timestamp
        """
        # Person is sitting up
        if vertical_diff > self.posture_threshold:
            if self.posture_state == self.STATE_LYING_DOWN:
                # Transition from lying down to maybe sitting
                self.posture_state = self.STATE_MAYBE_SITTING
                self.state_change_time = current_time
                print("👀 Posture change started...")
                
            elif self.posture_state == self.STATE_MAYBE_SITTING:
                # Check if posture maintained long enough to confirm
                if current_time - self.state_change_time >= self.persistence_seconds:
                    self.posture_state = self.STATE_CONFIRMED_SITTING
                    
                    # Send alert if cooldown period has passed
                    if current_time - self.last_alert_time > self.alert_cooldown_seconds:
                        self.send_alert()
                        self.last_alert_time = current_time
                        
        # Person is lying down
        else:
            if self.posture_state == self.STATE_MAYBE_SITTING:
                # Person reverted before confirmation
                print("❌ Posture reverted before confirmation.")
                self.posture_state = self.STATE_LYING_DOWN
                self.state_change_time = None
                
            elif self.posture_state == self.STATE_CONFIRMED_SITTING:
                # Person went back to lying down after being confirmed sitting
                print("✓ Person returned to lying down position.")
                self.posture_state = self.STATE_LYING_DOWN
                self.state_change_time = None
    
    def run(self):
        """Run the posture monitoring loop."""
        try:
            self.setup_camera()
            
            while True:
                success, frame = self.cap.read()
                if not success:
                    print("Failed to read frame from camera")
                    break
                
                processed_frame = self.process_frame(frame)
                
                # Display the frame
                cv2.imshow("Elderly Monitor", processed_frame)
                
                # Exit on 'q' press
                if cv2.waitKey(5) & 0xFF == ord("q"):
                    break
                    
        finally:
            # Clean up resources
            if self.cap is not None:
                self.cap.release()
            cv2.destroyAllWindows()


def main():
    """Main function to run the posture monitor."""
    # Create and run the posture monitor with default settings
    monitor = PostureMonitor()
    monitor.run()


if __name__ == "__main__":
    main()