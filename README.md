# 🚗 Drowsiness Detector — Real-time Driver Monitoring System

A **computer vision application** that detects driver/person drowsiness in real-time using a webcam. It monitors eye states frame-by-frame, classifies the person as **Active**, **Drowsy**, or **Sleeping**, captures snapshot images on state changes, logs structured JSON events, and optionally triggers external alerts via serial communication (e.g., Arduino).

![Detection Status](https://img.shields.io/badge/status-operational-brightgreen)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-4.13.0-green)

---

## 📋 Table of Contents

1. [How It Works (Internal Logic)](#-how-it-works-internal-logic)
2. [Project Structure](#-project-structure)
3. [Prerequisites](#-prerequisites)
4. [How to Run](#-how-to-run)
5. [Usage Guide](#-usage-guide)
6. [Output Artifacts](#-output-artifacts)
7. [Troubleshooting](#-troubleshooting)
8. [Technical Details](#-technical-details)

---

## 🧠 How It Works (Internal Logic)

The application follows a continuous loop that processes each webcam frame through these stages:

### 1. Frame Capture
- Opens the webcam (tries index `1` first, falls back to `0`)
- Reads frames one by one at ~20–30 FPS

### 2. Face Detection
- Converts each frame to **grayscale**
- Runs the **Haar Cascade classifier** (`haarcascade_frontalface_default.xml`) to detect faces
- Draws a **green bounding box** around each detected face

### 3. Eye Detection
- For each detected face, extracts the face region (ROI)
- Runs the **eye Haar Cascade** (`haarcascade_eye_tree_eyeglasses.xml`) inside the face ROI
- Draws **yellow rectangles** around detected eyes
- Classifies eye state as:
  - `0` — **No eyes detected** (eyes closed / not visible)
  - `1` — **One eye detected** (partial visibility)
  - `2` — **Both eyes detected** (eyes open)

### 4. State Machine
Three frame counters are maintained: `sleep`, `drowsy`, `active`. They work as follows:

| Eye State | Counter Incremented | Other Counters | Threshold | Resulting Status | Display Color |
|-----------|-------------------|----------------|-----------|------------------|---------------|
| 0 (no eyes) | `sleep++` | `drowsy=0`, `active=0` | `sleep > 6` | **SLEEPING !!!** | 🔴 Red |
| 1 (one eye) | `drowsy++` | `sleep=0`, `active=0` | `drowsy > 6` | **Drowsy !** | 🔴 Red |
| 2 (both eyes) | `active++` | `sleep=0`, `drowsy=0` | `active > 6` | **Active :)** | 🟢 Green |

> **Why 6 frames?** At ~25 FPS, 6 frames ≈ 0.24 seconds. This prevents false positives from brief blinks or momentary head movements. The threshold is hardcoded but adjustable (see [Technical Details](#-technical-details)).

### 5. On State Change
When a state **transitions** (counters cross the threshold):
1. **Snapshot captured** — The current frame is saved as a PNG image to `snapshots/{sleeping|drowsy|active}/`
2. **JSON event logged** — A structured event is appended to `events/drowsiness_events.json`
3. **Serial command sent** (optional) — If a device is connected on `COM5`:
   - `'a'` sent for **Sleeping** or **Drowsy** states (alert)
   - `'b'` sent for **Active** state (all clear)
4. **Status text displayed** on the video feed window

### 6. Exit
- Press **`ESC`** to exit the live loop
- Or run with **`--test`** to process a single frame and exit (useful for verification)

### Visual Flow Diagram

```
Webcam Frame
     │
     ▼
┌────────────────┐
│  Grayscale     │
│  Conversion    │
└───────┬────────┘
        ▼
┌────────────────┐         ┌─────────────────┐
│  Face          │────────▶│ Green Bounding   │
│  Detection     │         │ Box Around Face  │
└───────┬────────┘         └─────────────────┘
        ▼
┌────────────────┐         ┌─────────────────┐
│  Eye           │────────▶│ Yellow Boxes     │
│  Detection     │         │ Around Eyes      │
│  (in face ROI) │         └─────────────────┘
└───────┬────────┘
        ▼
┌────────────────┐
│  Eye State     │
│  Classification│── 0 eyes ──▶ sleep++
│  (0 / 1 / 2)   │── 1 eye  ──▶ drowsy++
└───────┬────────┘── 2 eyes ──▶ active++
        ▼
┌────────────────────────────────────┐
│  Threshold Check (counter > 6?)    │
│                                    │
│  ┌──────────┐  ┌────────┐  ┌────┐ │
│  │ SLEEPING │  │ Drowsy │  │Active│ │
│  └────┬─────┘  └───┬────┘  └──┬──┘ │
│       │            │          │     │
│       ▼            ▼          ▼     │
│   ┌─────────────────────────────┐   │
│   │  Capture Snapshot (PNG)     │   │
│   │  Log JSON Event             │   │
│   │  Send Serial Command (opt.) │   │
│   └─────────────────────────────┘   │
└────────────────────────────────────┘
```

---

## 📁 Project Structure

```
d:\Rabia\                              (Project Root)
│
├── src/
│   └── drowsinessDetector.py          ★ Main application (339 lines)
│
├── rabia/                              Python virtual environment (pre-built)
│
├── events/                             JSON event logs (auto-created)
│   └── drowsiness_events.json          Structured event records
│
├── logs/                               Application log files (auto-created)
│   └── drowsiness_detector.log         Detailed activity log (DEBUG/INFO/WARN/ERROR)
│
├── snapshots/                          Captured images (auto-created)
│   ├── active/                         Eyes open snapshots
│   ├── drowsy/                         One eye visible snapshots
│   └── sleeping/                       Eyes closed snapshots
│
├── requirements.txt                    Python dependencies
├── run_detector.bat                    Quick-launch batch file (Windows)
├── run_drowsiness_detector.bat         Alternative launcher
├── install_rabia_requirements.cmd      CMD dependency installer
├── install_rabia_requirements.ps1      PowerShell dependency installer
├── JSON_EVENTS_README.md               JSON event format reference
└── README.md                           This file
```

---

## ⚙️ Prerequisites

| Requirement | Details |
|-------------|---------|
| **Operating System** | Windows 10 or 11 |
| **Python** | Version 3.9 or higher |
| **Webcam** | Any USB or built-in camera |
| **RAM** | 2 GB minimum |
| **Disk Space** | ~500 MB (virtual environment + snapshot storage) |
| **Serial Device** (optional) | Arduino or microcontroller on COM port |

---

## 🚀 How to Run

### Option 1: Double-click the Batch File (Easiest ✅)

Simply double-click **`run_detector.bat`** in the project root (`d:\Rabia\`).

This will automatically:
1. Activate the pre-built virtual environment (`rabia\Scripts\activate.bat`)
2. Start the drowsiness detector in live mode
3. After exit, display where to find results

### Option 2: Command Line

```cmd
:: Step 1: Activate the virtual environment
rabia\Scripts\activate.bat

:: Step 2: Run the detector in live mode
python src\drowsinessDetector.py

:: --- OR ---

:: Run in test mode (single frame, then exit)
python src\drowsinessDetector.py --test
```

### Option 3: Using Full Python Path (Skip Activation)

```cmd
rabia\Scripts\python.exe src\drowsinessDetector.py
rabia\Scripts\python.exe src\drowsinessDetector.py --test
```

---

## 🎮 Usage Guide

### What You'll See

When the application starts, a window titled **"Frame"** appears showing the live webcam feed:

| Visual Element | Description |
|----------------|-------------|
| 🟩 Green rectangle | Bounding box around detected face |
| 🟨 Yellow rectangle | Bounding box around each detected eye |
| 🔴 **"SLEEPING !!!"** (red text, top-left) | Eyes closed — **alert state** |
| 🔴 **"Drowsy !"** (red text, top-left) | One eye visible — **warning state** |
| 🟢 **"Active :)"** (green text, top-left) | Both eyes open — **normal state** |
| No text | No face detected in frame |

### Controls

| Key | Action |
|-----|--------|
| `ESC` | Exit the application immediately |
| `--test` (CLI flag) | Process one frame, show result, then exit |

### Serial Communication (Optional)

If an Arduino or microcontroller is connected on **COM5** at 9600 baud:
- **`'a'`** is sent when user is **Sleeping** or **Drowsy** → trigger an alert (buzzer, LED, vibration motor)
- **`'b'`** is sent when user is **Active** → signal normal state

> If no serial device is available, the application logs a warning and continues without it — **no impact on core functionality**.

---

## 📦 Output Artifacts

### 1. Snapshot Images (`snapshots/`)

When a state transition occurs, the current frame is saved as a timestamped PNG:

```
snapshots/
├── sleeping/person_0_20260514_103045_123.png
├── drowsy/person_0_20260514_103050_456.png
└── active/person_0_20260514_103055_789.png
```

**Filename format:** `person_[ID]_[YYYYMMDD]_[HHMMSS]_[milliseconds].png`

### 2. JSON Event Log (`events/drowsiness_events.json`)

Each state change creates a structured event record:

```json
{
  "timestamp": "2026-05-14T10:30:45.123456",
  "person_id": 0,
  "eye_state": 0,
  "status": "SLEEPING !!!",
  "sleep_count": 7,
  "drowsy_count": 0,
  "active_count": 0,
  "eyes_closed": true,
  "is_drowsy": true,
  "is_sleeping": true,
  "is_active": false,
  "snapshot": "snapshots\\sleeping\\person_0_20260514_103045_123.png"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string | ISO 8601 timestamp of the event |
| `person_id` | int | Monitored person ID (default: `0`) |
| `eye_state` | int | `0`=no eyes, `1`=one eye, `2`=both eyes |
| `status` | string | Human-readable state message |
| `sleep_count` | int | Consecutive frames with no eyes detected |
| `drowsy_count` | int | Consecutive frames with one eye detected |
| `active_count` | int | Consecutive frames with both eyes detected |
| `eyes_closed` | bool | `true` if `eye_state == 0` |
| `is_drowsy` | bool | `true` if status is Drowsy or Sleeping |
| `is_sleeping` | bool | `true` if status is Sleeping |
| `is_active` | bool | `true` if status is Active |
| `snapshot` | string | Path to the captured snapshot image |

### 3. Application Logs (`logs/drowsiness_detector.log`)

Full debug-level activity log for troubleshooting:

```
2026-05-14 10:30:45,123 INFO  Starting drowsiness detector
2026-05-14 10:30:45,500 INFO  Opened camera index 0
2026-05-14 10:30:45,600 INFO  Loaded Haar cascade classifiers
2026-05-14 10:30:50,123 INFO  Snapshot saved: snapshots\sleeping\person_0_...png
```

---

## 🔧 Troubleshooting

### Camera Not Opening
```
Error: "Unable to open any camera"
```
**Solutions:**
1. Ensure your camera is connected and not in use by another app (Zoom, Teams, etc.)
2. Check Device Manager → Cameras
3. The code tries camera index `1` first, then falls back to `0`. To force a specific index, edit line 250 in `src/drowsinessDetector.py`:
   ```python
   camera = open_video_capture(0, logger)  # Change 1 → 0 (or 2, 3, etc.)
   ```

### Serial Port Error
```
Error: "could not open port 'COM5'"
```
**Solutions:**
1. Check Device Manager for the correct COM port number
2. Update the COM port in `src/drowsinessDetector.py` (line 249):
   ```python
   serial_port = open_serial_port('COM5', 9600, logger)  # Change COM5
   ```
3. The application works perfectly without a serial device — this error is **non-fatal**.

### No Face or Eye Detected
- Ensure **adequate lighting** (face should be well-lit)
- Position your face **directly facing the camera**
- Remove glasses or adjust lighting to **reduce glare**
- The Haar cascade can miss faces at extreme angles or in dim light

### Low Detection Rate / False Positives
Adjust detection sensitivity in `src/drowsinessDetector.py` (lines 279-285):

```python
# Lower minNeighbors = more sensitive (more faces detected, more false positives)
# Smaller minSize = detects smaller faces (useful if you're far from camera)
faces = face_cascade.detectMultiScale(
    gray,
    scaleFactor=1.1,
    minNeighbors=4,        # Default: 5. Lower = more sensitive
    minSize=(80, 80),      # Default: (100, 100). Smaller = detects smaller faces
    flags=cv2.CASCADE_SCALE_IMAGE,
)
```

---

## 🛠 Technical Details

### Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `opencv-python` | 4.13.0 | Webcam capture, face/eye detection (Haar Cascades), image display |
| `numpy` | 2.0.2 | Image array manipulation |
| `pyserial` | 3.5 | Serial communication with external devices (optional) |
| `mediapipe` | 0.10.35 | (Installed but not used by the main script) |
| `imutils` | 0.5.4 | (Installed but not used by the main script) |

### Hardcoded Configuration

| Parameter | Value | Location (line) |
|-----------|-------|-----------------|
| Camera index | `1` (fallback `0`) | Line 250 |
| Serial port | `COM5` @ 9600 baud | Line 249 |
| State threshold | 6 consecutive frames | Lines 181, 199, 217 |
| Person ID | `0` | Line 247 |
| Face min size | `(100, 100)` pixels | Line 283 |
| Eye min size | `(30, 30)` pixels | Line 301 |

### Performance

| Metric | Typical Value |
|--------|---------------|
| CPU Usage | ~5–15% on modern CPUs |
| Memory | ~150–300 MB |
| Detection Latency | <100 ms |
| Frame Rate | 20–30 FPS |

### Limitations

- **Single person tracking** — `person_id` is hardcoded to `0`. The code detects all faces in the frame but only logs events for the first one. Multi-person support would require per-face state counters.
- **No configuration file** — All settings (camera index, serial port, thresholds) are hardcoded in `src/drowsinessDetector.py`. To change them, edit the source directly.
- **Haar Cascade limitations** — Less accurate than deep learning approaches (e.g., MediaPipe, DNN). May struggle with glasses, extreme angles, or poor lighting.

### Potential Improvements

- Add `config.json` or CLI arguments for camera index, serial port, threshold values
- Implement multi-person tracking with per-person state counters
- Replace Haar Cascades with MediaPipe Face Mesh for more robust eye detection
- Add audio alerts (sounddevice is already installed)
- Implement logging rotation and snapshot retention policies

---

## 📄 License

This project is provided as-is for driver safety and drowsiness detection applications.

---

**Happy Monitoring!** 🚗👁️  
Stay safe and alert on the road.