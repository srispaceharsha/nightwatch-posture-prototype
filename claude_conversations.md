# Claude Conversations - ElderCareMonitor Development Log

A summary of the development journey for the SeniorCare Posture Monitor prototype.

---

## Session 1: Project Initialization

### Initial Request
User ran `/init` command to analyze codebase and create CLAUDE.md documentation.

**Findings:**
- Brand new project with only README.md
- Python-based elder care monitoring system using MediaPipe Pose
- Goal: Build CLI prototype to test 8-state machine before iOS app
- User had a 3-state PoC (`elderly_monitor_old_PoC.py`)

**Deliverable:** Created comprehensive CLAUDE.md with architecture overview, state machine details, and development workflow.

---

## Session 2: Planning the Build

### Discussion Points

**Environment Setup:**
- Agreed to use Python 3.11 (stable, good package support)
- User would handle uv environment setup

**Architecture Decisions:**
- User's PoC was "spaghetti style" - build clean implementation from scratch
- Priority: State machine logic + config system first
- Start with 5 core states (skip DETECTION_UNCERTAIN and PERSON_ABSENT for now)
- Terminal output only initially (no camera window)

**Key Technical Choices:**
- Clean separation: `main.py`, `state_machine.py`, `pose_detector.py`, `metrics_calculator.py`, `config.yaml`
- MediaPipe for pose detection (4 key landmarks: shoulders + hips)
- Torso angle calculation using atan2
- Configurable parameters via YAML

---

## Session 3: Initial Implementation

### Files Created
1. **config.yaml** - Detection parameters (persistence timer: 5s, cooldown: 300s, angle thresholds)
2. **pose_detector.py** - MediaPipe wrapper, extracts 4 landmarks with confidence
3. **metrics_calculator.py** - Calculates torso angle, vertical diff, classifies posture
4. **state_machine.py** - 5-state FSM (MONITORING_LYING, RESTLESS_MOVEMENT, SITTING_DETECTED, ALERT_ACTIVE, ALERT_COOLDOWN)
5. **main.py** - Orchestration, terminal output, logging
6. **requirements.txt** - Python dependencies

**State Machine Logic:**
- MONITORING_LYING → RESTLESS_MOVEMENT (any non-lying posture)
- RESTLESS_MOVEMENT → SITTING_DETECTED (sitting posture sustained)
- SITTING_DETECTED → ALERT_ACTIVE (after 5s persistence timer)
- ALERT_ACTIVE → ALERT_COOLDOWN (when person lies back down)
- ALERT_COOLDOWN → MONITORING_LYING (after 5min cooldown)

---

## Session 4: First Test & Problem Discovery

### User's First Test Results
Checked `logs/state_transitions.log` - found significant jittering!

**Problem Found (Lines 6-14):**
```
SITTING_DETECTED → RESTLESS_MOVEMENT → SITTING_DETECTED → RESTLESS_MOVEMENT
```

**Root Cause:**
- Person clearly sitting (angles 108-111°)
- Angle 111° was 1° outside sitting threshold (70-110°)
- Frame-to-frame jitter in MediaPipe causing timer resets

**Analysis:**
- Sitting detection worked eventually (alert triggered successfully)
- But persistence timer kept resetting due to boundary fluctuations
- Needed anti-jitter mechanisms

---

## Session 5: Enhancement Planning

### User's Enhancement Requests
1. Add datetime timestamps to logs (already there, but wanted per-run log files)
2. "Detection started" message with first posture detected
3. Apply all anti-jitter fixes (Option 4 - "all of the above")
4. Add camera window for testing (see what's in/out of frame)
5. Play audio alert (3 chimes) when sitting detected

### Discussion: The Fixes
**Fix 1: Widen sitting angle range** - 70-115° (was 70-110°)

**Fix 2: Frame smoothing** - Average last 3 frames to reduce jitter

**Fix 3: Hysteresis** - Once in a state, give extra tolerance before transitioning out
- Hysteresis angle buffer: 10°
- Hysteresis vdiff buffer: 0.05

**Fix 4: Camera window** - OpenCV window with skeleton overlay + state display

**Fix 5: Audio alert** - 3x Glass.aiff chimes on macOS

---

## Session 6: Implementing All Enhancements

### Files Updated

**config.yaml:**
- Sitting angle max: 115° (was 110°)
- Added hysteresis parameters
- Added `display.show_camera_window: true`

**metrics_calculator.py:**
- Added 3-frame smoothing with deque buffers
- Added `classify_with_hysteresis()` method
- Smooths angle and vertical_diff over last 3 frames

**state_machine.py:**
- Added `get_expected_posture_for_hysteresis()` method
- Applies hysteresis when in SITTING_DETECTED or MONITORING_LYING states

**main.py:**
- Timestamped log files: `state_transitions_YYYY-MM-DD_HH-MM-SS.log`
- First detection message with posture description
- Camera window with skeleton overlay (4 keypoints + connecting lines)
- Audio alert using `afplay /System/Library/Sounds/Glass.aiff` (3 times)
- Integrated hysteresis into metrics calculation

---

## Session 7: Second Test & New Discovery

### User's Second Test
Tested while actively moving: rolling sides, moving arms, hand on hip, etc.

**Log Analysis (lines 12-34):**
```
Rapid jittering: MONITORING_LYING ↔ RESTLESS_MOVEMENT
- Angles jumping: 60°, 120°, 179°, 3° (wild variation)
- BUT vdiff consistently: 0.00 to 0.04 (nearly flat!)
```

**Key Insight from User:**
"I was constantly moving every second - sleeping on either sides, moving arms, keeping hand on hip..."

### The Real Problem Revealed
**Old logic:** Classify lying by angle ranges `[-20, 20]` or `[160, 200]`
- Works when lying straight facing camera
- FAILS when rolling on side (torso angle can be 60°, 90°, 120°)

**The Truth:** When lying on your SIDE, angle varies wildly, but `vdiff ≈ 0` is the key!

**Evidence:**
- Lines 12-34: Rolling around, vdiff=0.00-0.04 → should stay LYING
- Lines 35-37: Actually sat up, vdiff=0.48-0.55 → correctly detected SITTING

---

## Session 8: The Final Fix

### Solution: Prioritize Vertical Diff

**Updated Classification Logic:**

```python
# FIRST: Check vertical diff (primary indicator)
if abs(vertical_diff) < 0.10:
    return 'LYING'

# THEN: Check sitting (needs both angle AND high vdiff)
if (angle 70-115° AND vdiff > 0.15):
    return 'SITTING'

# THEN: Check propped (needs both angle AND moderate vdiff)
# FINALLY: Angle-based lying check (fallback)
```

**Why This Works:**
- Rolling side-to-side while flat: vdiff stays ~0.00 → LYING (stable!)
- Actually sitting up: vdiff jumps to 0.48+ → SITTING_DETECTED
- Angle becomes secondary, vdiff is primary signal

**Applied to both:**
- `_classify_posture()` - base classification
- `classify_with_hysteresis()` - hysteresis classification

---

## Session 9: Success!

### User Feedback
**"It works! Very well."**

System now correctly:
- Stays stable in MONITORING_LYING while moving/rolling around
- Detects sitting up when vdiff increases significantly
- Runs 5s persistence timer without jitter
- Triggers alert with audio chimes
- Auto-dismisses when person lies back down

### Final Status

**What Was Built:**
- Clean 5-state posture monitoring system
- Frame smoothing (3-frame average)
- Hysteresis for state stability
- Priority-based posture classification (vdiff > angle)
- Timestamped log files per run
- Camera window with skeleton overlay
- Audio alerts (3 chimes)
- Configurable parameters via YAML

**Pending:**
- Overnight real-world test
- Potential expansion to full 8 states later
- Transition from prototype to production app

---

## Key Learnings

1. **Angle-based detection is insufficient** - Body orientation relative to camera matters more than actual posture
2. **Vertical diff is the primary signal** - Nearly flat = lying, regardless of angle
3. **Real user movement patterns matter** - Lab conditions vs. actual sleep movement are very different
4. **Multiple anti-jitter mechanisms work best** - Smoothing + hysteresis + wider thresholds + priority logic
5. **Iterative testing is critical** - Each test revealed different edge cases

---

## Project Status

**Current Folder:** ElderCareMonitor (can be renamed to `nightwatch-posture-prototype`)

**Next Steps:**
- Overnight testing to measure false positive rate
- Parameter tuning based on real sleep data
- Potential expansion to 8 states (add DETECTION_UNCERTAIN, PERSON_ABSENT)
- Consider adding manual testing controls (keyboard simulation)

**Success Criteria Met:**
- ✅ State transitions follow documented rules
- ✅ Persistence timer prevents false alerts
- ✅ Cooldown suppresses repeated alerts
- ✅ System stable during normal sleep movement
- ✅ Sitting detection accurate and timely
- ✅ All transitions logged with timestamps
