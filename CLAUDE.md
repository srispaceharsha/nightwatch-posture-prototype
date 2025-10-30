# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python CLI prototype for an elder care posture monitoring system. The goal is to test an 8-state machine that detects when a person in bed sits up, using webcam input and MediaPipe Pose detection. This prototype validates the state machine logic before building an iOS app.

## Commands

### Setup and Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# Dependencies: opencv-python, mediapipe, pyyaml, numpy
```

### Running the Application
```bash
# Run with default config
python main.py

# Run with custom config file
python main.py --config my_config.yaml

# Run with video file instead of webcam (for testing)
python main.py --video test_recording.mp4

# Run without camera window (logs/terminal only)
python main.py --no-window
```

### Testing
No formal test suite is specified yet. Testing is manual via:
- Phase 1: Desk testing with live webcam
- Phase 2: Overnight recording in real conditions
- Phase 3: Parameter tuning based on logs

## Architecture

### State Machine (8 States)

The core of the system is an 8-state finite state machine implemented in `state_machine.py`:

1. **MONITORING_LYING** - Baseline state, person lying down normally
2. **RESTLESS_MOVEMENT** - Transitional state, brief motion detected but not yet classified
3. **PROPPED_UP** - Semi-reclined position (30-60° torso angle)
4. **SITTING_DETECTED** - Full sitting posture confirmed, persistence timer running
5. **ALERT_ACTIVE** - Alert triggered after persistence timer completes
6. **ALERT_COOLDOWN** - Post-alert suppression period (default 5 minutes)
7. **DETECTION_UNCERTAIN** - Low confidence in pose detection
8. **PERSON_ABSENT** - No person detected for threshold period (default 20s)

### Critical State Transition Rules

These transitions are the core behavior to implement correctly:

- **MONITORING_LYING** → **RESTLESS_MOVEMENT**: Any non-lying posture detected
- **RESTLESS_MOVEMENT** → **SITTING_DETECTED**: Sitting posture sustained
- **RESTLESS_MOVEMENT** → **MONITORING_LYING**: Reverts to lying within 2 seconds
- **SITTING_DETECTED** → **ALERT_ACTIVE**: Persistence timer completes (default 5s)
- **SITTING_DETECTED** → **MONITORING_LYING**: Person lies back down before timer completes
- **ALERT_ACTIVE** → **ALERT_COOLDOWN**: Alert dismissed (manual or auto)
- **Any state** → **DETECTION_UNCERTAIN**: Pose confidence drops below threshold
- **Any state** → **PERSON_ABSENT**: No person detected for absence threshold period

### Component Architecture

The system is structured as a pipeline:

```
Camera Input → Pose Detection → Metrics Calculation → State Machine → Logging/Display
```

**Files to implement:**

- `main.py` - Entry point, main loop orchestration, terminal output
- `state_machine.py` - 8-state FSM logic, timer management, transition rules
- `pose_detector.py` - MediaPipe Pose wrapper, landmark extraction
- `metrics_calculator.py` - Torso angle calculation, posture classification
- `config.yaml` - Tunable detection parameters
- `logs/state_transitions.log` - Timestamped state transition history

### Pose Detection Algorithm

**Key landmarks used:** Shoulders (11, 12) and Hips (23, 24)

**Metrics calculated per frame:**
1. Shoulder midpoint and hip midpoint from landmarks
2. Average confidence of the 4 key landmarks
3. Torso angle (degrees) using atan2 on torso vector
4. Vertical difference (hip.y - shoulder.y) for height classification

**Posture classification thresholds (from config):**
- **SITTING**: 70-110° angle AND vertical_diff > 0.15
- **PROPPED**: 30-60° angle AND vertical_diff > 0.08
- **LYING**: -20 to 20° OR 160-200° angle range
- **TRANSITIONING**: Anything else

### Configuration System

All detection parameters live in `config.yaml` to enable tuning without code changes:

**Critical parameters:**
- `persistence_duration` (5s default) - How long sitting must be sustained before alert
- `cooldown_duration` (300s default) - Post-alert suppression period
- `confidence_threshold` (0.7 default) - Minimum pose confidence to use detection
- `absence_threshold` (20s default) - Time before declaring person absent
- Angle thresholds for sitting/propped/lying classification
- Vertical difference thresholds

### Logging Format

State transitions are logged to `logs/state_transitions.log` with format:
```
YYYY-MM-DD HH:MM:SS.mmm | TYPE | Details
```

**Log types:**
- `TRANSITION` - State changes with metrics (confidence, angle, vdiff)
- `TIMER` - Persistence timer events (started, completed)
- `ALERT` - Alert triggered or dismissed

This log is the primary artifact for analyzing false positive rates and parameter tuning.

## Implementation Notes

### Persistence Timer
The SITTING_DETECTED state must track elapsed time in the sitting posture. Only after `persistence_duration` seconds should it transition to ALERT_ACTIVE. If the person lies back down before the timer completes, cancel the timer and return to MONITORING_LYING. This prevents false alerts from brief sit-ups.

### Cooldown Mechanism
After an alert is dismissed (ALERT_ACTIVE → ALERT_COOLDOWN), the system must suppress new alerts for `cooldown_duration` seconds even if sitting is detected again. This prevents alert fatigue from repeated movements.

### Confidence Handling
If pose detection confidence falls below `confidence_threshold`, transition to DETECTION_UNCERTAIN state. Stay in this state until confidence improves. This prevents acting on unreliable data.

### Angle Normalization
MediaPipe returns landmarks in normalized coordinates. When calculating torso angle with atan2, normalize the result to 0-180° range by adding 180 if negative. The angle represents the tilt of the torso vector from horizontal.

### Optional Camera Window
When `display.show_camera_window` is true, show an OpenCV window with the camera feed and skeleton overlay. Support keyboard commands for manual testing (s=simulate sitting, l=simulate lying, etc.). This is for debugging only.

## Project File Structure

```
ElderCareMonitor/
├── README.md              - Full specification and requirements
├── CLAUDE.md              - This file
├── requirements.txt       - Python dependencies
├── config.yaml            - Detection parameters (create this)
├── main.py                - Entry point (implement)
├── state_machine.py       - 8-state FSM (implement)
├── pose_detector.py       - MediaPipe wrapper (implement)
├── metrics_calculator.py  - Posture math (implement)
└── logs/
    └── state_transitions.log - Auto-generated logs
```

## Development Workflow

1. Start by implementing `pose_detector.py` to wrap MediaPipe and extract the 4 key landmarks
2. Implement `metrics_calculator.py` to compute angle, confidence, and vertical diff from landmarks
3. Implement `state_machine.py` with all 8 states and transition logic, including timers
4. Implement `main.py` to orchestrate the pipeline and handle terminal output
5. Create `config.yaml` with the default parameters from README
6. Test iteratively: desk testing → overnight testing → parameter tuning

## Success Criteria

The prototype is complete when all 8 states are reachable, state transitions follow the documented rules, the persistence timer prevents false alerts, cooldown suppresses repeated alerts, and all transitions are logged with timestamps.
