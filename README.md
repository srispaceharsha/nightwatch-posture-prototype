# SeniorCare State Machine Prototype - README

**Goal:** Build a Mac CLI prototype to test all 8 state transitions before building the iOS app.

**Note:** Entire code is written by Claude Code AI. A human did the orchestration and testing. 

## How to Run the app

0. Open terminal and Clone the repo `gh repo clone srispaceharsha/nightwatch-posture-prototype`
1. Change directory to project root folder, you should be in `nightwatch-posture-prototype` folder.
2. run `uv venv --python 3.11`
3. run `uv pip install -r requirements.txt`
4. run `uv run python3 main.py`

Good luck if you run in to any errors in the above steps!

---

## What to Build

A command-line Python application that:
1. Uses webcam + MediaPipe Pose to detect posture - DONE
2. Implements the full 8-state machine - DONE with 6 state for now.
3. Prints state transitions as they happen - DONE
4. Logs all state transitions with timestamps - DONE
5. Shows basic metrics when state changes - DONE
6. Allows tweaking detection parameters via config file - DONE

---

## Project Structure
```
seniorcare-prototype/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── config.yaml                  # Detection parameters
├── main.py                      # Entry point
├── state_machine.py             # 8-state logic
├── pose_detector.py             # MediaPipe wrapper
├── metrics_calculator.py        # Angle/posture math
└── logs/
    └── state_transitions.log    # Timestamped events
```

---

## State Machine (8 States)

Implement these exact states with transitions as specified:

1. **MONITORING_LYING** - Normal lying down, all clear
2. **RESTLESS_MOVEMENT** - Brief motion, not yet classified
3. **PROPPED_UP** - Semi-reclined (30-60° angle)
4. **SITTING_DETECTED** - Full sitting detected, timer counting
5. **ALERT_ACTIVE** - Alert triggered
6. **ALERT_COOLDOWN** - Post-alert suppression period
7. **DETECTION_UNCERTAIN** - Low confidence detection - TBD
8. **PERSON_ABSENT** - No person detected - TBD

---

## Detection Algorithm

### Per-Frame Metrics to Calculate
```python
# 1. Extract landmarks
left_shoulder = landmarks[11]
right_shoulder = landmarks[12]
left_hip = landmarks[23]
right_hip = landmarks[24]

shoulder_midpoint = (left_shoulder + right_shoulder) / 2
hip_midpoint = (left_hip + right_hip) / 2

# 2. Calculate metrics
avg_confidence = mean([
    left_shoulder.confidence,
    right_shoulder.confidence,
    left_hip.confidence,
    right_hip.confidence
])

torso_vector = shoulder_midpoint - hip_midpoint
angle_degrees = atan2(torso_vector.y, torso_vector.x) * 180 / π
# Normalize to 0-180° range
if angle_degrees < 0:
    angle_degrees += 180

vertical_diff = hip_midpoint.y - shoulder_midpoint.y

# 3. Classify posture
if 70° <= angle <= 110° and vertical_diff > 0.15:
    posture = SITTING
elif 30° <= angle <= 60° and vertical_diff > 0.08:
    posture = PROPPED
elif (-20° <= angle <= 20°) or (160° <= angle <= 200°):
    posture = LYING
else:
    posture = TRANSITIONING
```

### State Transition Rules

Implement the full transition logic as documented in the spec. Key transitions:

- **MONITORING_LYING** → RESTLESS_MOVEMENT (any non-lying posture)
- **RESTLESS_MOVEMENT** → SITTING_DETECTED (if sitting posture sustained)
- **RESTLESS_MOVEMENT** → MONITORING_LYING (if reverts within 2s)
- **SITTING_DETECTED** → ALERT_ACTIVE (after persistence timer completes)
- **SITTING_DETECTED** → MONITORING_LYING (if reverts before timer)
- **ALERT_ACTIVE** → ALERT_COOLDOWN (when dismissed/auto-dismiss)
- **Any state** → DETECTION_UNCERTAIN (if confidence < 0.5)
- **Any state** → PERSON_ABSENT (if no detection for 20s)

---

## Terminal Output (Simple)
```
SeniorCare Posture Monitor - Starting...
Camera initialized: 640x480 @ 30fps
Config loaded from: config.yaml
System running... (Press Ctrl+C to stop)

[00:00:15] STATE: MONITORING_LYING (confidence=0.85, angle=12°)
[00:02:34] STATE: RESTLESS_MOVEMENT (confidence=0.82, angle=45°)
[00:02:36] STATE: MONITORING_LYING (confidence=0.88, angle=15°)
[00:05:12] STATE: SITTING_DETECTED (confidence=0.91, angle=85°) - Timer started (5s)
[00:05:17] 🚨 ALERT: PERSON SITTING UP 🚨
[00:05:17] STATE: ALERT_ACTIVE
[00:05:22] Alert auto-dismissed (person lying back down)
[00:05:22] STATE: ALERT_COOLDOWN (5 minutes)
[00:10:22] STATE: MONITORING_LYING (cooldown complete)
[00:15:45] STATE: PERSON_ABSENT (no detection for 20s)
[00:15:50] STATE: MONITORING_LYING (person detected again)

^C
Shutting down...
Total runtime: 00:16:23
Total alerts: 1
State transitions logged to: logs/state_transitions.log
```

That's it. Simple text output showing what's happening.

---

## Configuration File (config.yaml)
```yaml
# Detection Parameters
detection:
  persistence_duration: 5          # seconds to confirm sitting
  cooldown_duration: 300           # seconds (5 minutes)
  alert_on_propped: false
  confidence_threshold: 0.7
  
  # Angle thresholds (degrees)
  sitting_angle_min: 70
  sitting_angle_max: 110
  propped_angle_min: 30
  propped_angle_max: 60
  lying_angle_ranges:
    - [-20, 20]
    - [160, 200]
  
  # Vertical difference thresholds
  sitting_vertical_diff: 0.15
  propped_vertical_diff: 0.08

# Absence Detection
absence:
  enable_alert: true
  absence_threshold: 20            # seconds
  
# Alert Behavior
alert:
  auto_dismiss: false              # Dismiss when person lies back down?

# Display
display:
  show_camera_window: true         # OpenCV window with skeleton overlay
  print_interval: 10               # Print status every N seconds (0 = only on transitions)

# Camera
camera:
  device_id: 0                     # 0 = default webcam
  resolution_width: 640
  resolution_height: 480
  frame_rate: 30
```

---

## Log File Format

Store in `logs/state_transitions.log`:
```
2025-10-30 02:15:30.123 | TRANSITION | MONITORING_LYING → RESTLESS_MOVEMENT | confidence=0.85 angle=45° vdiff=0.09
2025-10-30 02:15:32.456 | TRANSITION | RESTLESS_MOVEMENT → MONITORING_LYING | confidence=0.88 angle=12° vdiff=0.02
2025-10-30 02:18:45.789 | TRANSITION | MONITORING_LYING → SITTING_DETECTED | confidence=0.92 angle=85° vdiff=0.18
2025-10-30 02:18:45.789 | TIMER | persistence_timer started (5.0s)
2025-10-30 02:18:50.789 | TIMER | persistence_timer completed
2025-10-30 02:18:50.790 | TRANSITION | SITTING_DETECTED → ALERT_ACTIVE | confidence=0.91 angle=87° vdiff=0.19
2025-10-30 02:18:50.790 | ALERT | PERSON SITTING UP
2025-10-30 02:18:55.678 | ALERT | Auto-dismissed (lying detected)
2025-10-30 02:18:55.679 | TRANSITION | ALERT_ACTIVE → ALERT_COOLDOWN | cooldown=300s
2025-10-30 02:23:55.679 | TRANSITION | ALERT_COOLDOWN → MONITORING_LYING | cooldown complete
```

---

## Requirements
```txt
# requirements.txt
opencv-python==4.8.1.78
mediapipe==0.10.8
pyyaml==6.0.1
numpy==1.24.3
```

---

## Running the Prototype
```bash
# Install dependencies
pip install -r requirements.txt

# Run with default config
python main.py

# Run with custom config
python main.py --config my_config.yaml

# Run with video file instead of webcam (for testing)
python main.py --video test_recording.mp4

# Run without camera window (just logs/terminal)
python main.py --no-window
```

---

## Optional: Manual Test Controls

Add keyboard commands in the OpenCV window (only if `show_camera_window = true`):
```
While camera window is open:

's' - Force simulate sitting posture
'l' - Force simulate lying posture  
'p' - Force simulate propped up posture
'a' - Force simulate person absent
'r' - Resume normal detection
'd' - Dismiss alert (if in ALERT_ACTIVE state)
'q' - Quit
```

These help test state transitions without physically moving.

---

## Success Criteria

The prototype is working correctly when:

1. ✅ All 8 states are reachable through natural movements
2. ✅ State transitions follow the documented rules
3. ✅ Persistence timer correctly prevents false alerts (sit up briefly = no alert)
4. ✅ Cooldown period suppresses repeated alerts
5. ✅ Low confidence transitions to UNCERTAIN state
6. ✅ Person leaving frame triggers ABSENT state
7. ✅ All transitions are logged with timestamps and metrics
8. ✅ Config file changes affect behavior without code changes

---

## Key Implementation Notes

### Main Loop Structure
```python
def main():
    print("SeniorCare Posture Monitor - Starting...")
    
    # Initialize
    config = load_config('config.yaml')
    camera = init_camera(config)
    pose_detector = MediaPipePose()
    state_machine = PostureStateMachine(config)
    
    print("System running... (Press Ctrl+C to stop)\n")
    
    while True:
        frame = camera.read()
        landmarks = pose_detector.detect(frame)
        
        if landmarks:
            metrics = calculate_metrics(landmarks)
            old_state = state_machine.current_state
            state_machine.update(metrics)
            
            # Print only when state changes
            if state_machine.current_state != old_state:
                print_transition(state_machine, metrics)
                log_transition(state_machine, metrics)
        else:
            state_machine.update_no_detection()
        
        # Optional: show camera window
        if config['display']['show_camera_window']:
            cv2.imshow('SeniorCare', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
```

### Print Format
```python
def print_transition(state_machine, metrics):
    timestamp = time.strftime("%H:%M:%S")
    state = state_machine.current_state
    conf = metrics['confidence']
    angle = metrics['angle']
    
    print(f"[{timestamp}] STATE: {state} (confidence={conf:.2f}, angle={angle:.0f}°)")
    
    # Special messages for alerts
    if state == State.ALERT_ACTIVE:
        print(f"[{timestamp}] 🚨 ALERT: PERSON SITTING UP 🚨")
```

---

## Testing Strategy

### Phase 1: Basic Detection (1-2 hours)
- Run prototype while sitting at desk
- Verify lying/sitting transitions work
- Check that angles and confidence make sense

### Phase 2: Real Conditions (overnight)
- Run on laptop next to bed
- Point camera at yourself sleeping
- Review logs next morning:
  - How many false positives?
  - What states occurred?
  - What parameters need tuning?

### Phase 3: Parameter Tuning (iterative)
- Adjust persistence_duration based on Phase 2 data
- Tweak angle thresholds if needed
- Test cooldown duration (too long? too short?)

---

