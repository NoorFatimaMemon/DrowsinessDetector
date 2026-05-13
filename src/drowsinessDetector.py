import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
import hashlib

import cv2
import numpy as np
import serial
import time


def setup_logger() -> logging.Logger:
    log_dir = Path(__file__).parent.parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / 'drowsiness_detector.log'
    logger = logging.getLogger('drowsiness_detector')
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s'
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger


def setup_json_logger(logger: logging.Logger) -> Path:
    events_dir = Path(__file__).parent.parent / 'events'
    events_dir.mkdir(exist_ok=True)
    json_log_file = events_dir / 'drowsiness_events.json'
    logger.info('JSON events will be logged to %s', json_log_file)
    return json_log_file


def create_snapshot_directories(logger: logging.Logger) -> Path:
    snapshots_dir = Path(__file__).parent.parent / 'snapshots'
    snapshots_dir.mkdir(exist_ok=True)
    
    for state_dir in ['sleeping', 'drowsy', 'active']:
        (snapshots_dir / state_dir).mkdir(exist_ok=True)
    
    logger.info('Snapshot directories created at %s', snapshots_dir)
    return snapshots_dir


def capture_snapshot(frame, eye_state: int, status: str, person_id: int, snapshots_dir: Path, logger: logging.Logger) -> str:
    try:
        if status == 'SLEEPING !!!':
            folder = snapshots_dir / 'sleeping'
        elif status == 'Drowsy !':
            folder = snapshots_dir / 'drowsy'
        elif status == 'Active :)':
            folder = snapshots_dir / 'active'
        else:
            return ''

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        filename = f"person_{person_id}_{timestamp}.png"
        filepath = folder / filename

        success = cv2.imwrite(str(filepath), frame)
        if success:
            logger.info('Snapshot saved: %s', filepath)
            return str(filepath)
        else:
            logger.warning('Failed to save snapshot to %s', filepath)
            return ''
    except Exception:
        logger.exception('Failed to capture snapshot')
        return ''


def log_event_to_json(json_file: Path, person_id: int, eye_state: int, status: str, sleep: int, drowsy: int, active: int, snapshot_path: str, logger: logging.Logger):
    try:
        event = {
            'timestamp': datetime.now().isoformat(),
            'person_id': person_id,
            'eye_state': eye_state,
            'status': status,
            'sleep_count': sleep,
            'drowsy_count': drowsy,
            'active_count': active,
            'eyes_closed': eye_state == 0,
            'is_drowsy': status in ['Drowsy !', 'SLEEPING !!!'],
            'is_sleeping': status == 'SLEEPING !!!',
            'is_active': status == 'Active :)',
            'snapshot': snapshot_path,
        }

        events = []
        if json_file.exists():
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    events = json.load(f)
            except Exception:
                logger.warning('Failed to read existing JSON events file; starting fresh')
                events = []

        events.append(event)

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(events, f, indent=2, ensure_ascii=False)

        logger.debug('Logged event to JSON: status=%s, snapshot=%s', status, snapshot_path)

    except Exception:
        logger.exception('Failed to log event to JSON')


def open_serial_port(com_port: str, baud_rate: int, logger: logging.Logger):
    try:
        serial_obj = serial.Serial(com_port, baud_rate, timeout=1)
        logger.info('Opened serial port %s at %d baud', com_port, baud_rate)
        return serial_obj
    except Exception:
        logger.exception('Failed to open serial port %s', com_port)
        return None


def open_video_capture(camera_index: int, logger: logging.Logger):
    cap = cv2.VideoCapture(camera_index)
    if cap.isOpened():
        logger.info('Opened camera index %d', camera_index)
        return cap

    logger.warning('Unable to open camera index %d, trying fallback camera index 0', camera_index)
    cap.release()
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        logger.info('Opened fallback camera index 0')
        return cap

    logger.error('Unable to open any camera')
    return None


def load_cascades(logger: logging.Logger):
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye_tree_eyeglasses.xml')

    if face_cascade.empty() or eye_cascade.empty():
        logger.error('Failed to load Haar cascade classifiers')
        return None, None

    logger.info('Loaded Haar cascade classifiers for face and eyes')
    return face_cascade, eye_cascade


def get_eye_state(eyes):
    if len(eyes) == 0:
        return 0
    if len(eyes) == 1:
        return 1
    return 2


def update_state(eye_state, sleep, drowsy, active, serial_port, logger, json_file=None, person_id=0, frame=None, snapshots_dir=None):
    status = ''
    color = (0, 0, 0)
    state_changed = False
    snapshot_path = ''

    if eye_state == 0:
        sleep += 1
        drowsy = 0
        active = 0
        logger.debug('No eyes detected. sleep=%d', sleep)
        if sleep > 6:
            if serial_port:
                try:
                    serial_port.write(b'a')
                    logger.info('Sent sleeping command to serial device')
                except Exception:
                    logger.exception('Failed to write sleeping command to serial device')
            status = 'SLEEPING !!!'
            color = (0, 0, 255)
            state_changed = True
            if frame is not None and snapshots_dir:
                snapshot_path = capture_snapshot(frame, eye_state, status, person_id, snapshots_dir, logger)

    elif eye_state == 1:
        sleep = 0
        active = 0
        drowsy += 1
        logger.debug('One eye detected. drowsy=%d', drowsy)
        if drowsy > 6:
            if serial_port:
                try:
                    serial_port.write(b'a')
                    logger.info('Sent drowsy command to serial device')
                except Exception:
                    logger.exception('Failed to write drowsy command to serial device')
            status = 'Drowsy !'
            color = (0, 0, 255)
            state_changed = True
            if frame is not None and snapshots_dir:
                snapshot_path = capture_snapshot(frame, eye_state, status, person_id, snapshots_dir, logger)

    else:
        sleep = 0
        drowsy = 0
        active += 1
        logger.debug('Two or more eyes detected. active=%d', active)
        if active > 6:
            if serial_port:
                try:
                    serial_port.write(b'b')
                    logger.info('Sent active command to serial device')
                except Exception:
                    logger.exception('Failed to write active command to serial device')
            status = 'Active :)'
            color = (0, 255, 0)
            state_changed = True
            if frame is not None and snapshots_dir:
                snapshot_path = capture_snapshot(frame, eye_state, status, person_id, snapshots_dir, logger)

    if state_changed and json_file:
        log_event_to_json(json_file, person_id, eye_state, status, sleep, drowsy, active, snapshot_path, logger)

    return sleep, drowsy, active, status, color


def main():
    parser = argparse.ArgumentParser(description='Live drowsiness detector with real-time face and eye detection')
    parser.add_argument('--test', action='store_true', help='Run one frame test and exit')
    args = parser.parse_args()

    logger = setup_logger()
    logger.info('Starting drowsiness detector')
    logger.debug('Arguments: %s', args)

    json_file = setup_json_logger(logger)
    snapshots_dir = create_snapshot_directories(logger)
    person_id = 0

    serial_port = open_serial_port('COM5', 9600, logger)
    camera = open_video_capture(1, logger)
    if camera is None:
        logger.error('No valid camera available. Exiting.')
        return

    face_cascade, eye_cascade = load_cascades(logger)
    if face_cascade is None or eye_cascade is None:
        logger.error('Cascade classifiers are unavailable. Exiting.')
        if camera is not None:
            camera.release()
        if serial_port is not None:
            serial_port.close()
        return

    sleep = 0
    drowsy = 0
    active = 0
    status = ''
    color = (0, 0, 0)

    try:
        while True:
            ret, frame = camera.read()
            if not ret or frame is None:
                logger.warning('Unable to read frame from camera')
                time.sleep(0.1)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(100, 100),
                flags=cv2.CASCADE_SCALE_IMAGE,
            )
            logger.debug('Detected %d face(s)', len(faces))

            if len(faces) == 0:
                status = ''
                color = (0, 0, 0)

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                roi_gray = gray[y:y + h, x:x + w]
                roi_color = frame[y:y + h, x:x + w]

                eyes = eye_cascade.detectMultiScale(
                    roi_gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30),
                    flags=cv2.CASCADE_SCALE_IMAGE,
                )
                eye_state = get_eye_state(eyes)
                logger.debug('Detected %d eye(s)', len(eyes))

                sleep, drowsy, active, status, color = update_state(
                    eye_state, sleep, drowsy, active, serial_port, logger, json_file, person_id, frame, snapshots_dir
                )

                for (ex, ey, ew, eh) in eyes:
                    cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (255, 255, 0), 2)

            cv2.putText(frame, status, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
            cv2.imshow('Frame', frame)

            if cv2.waitKey(1) & 0xFF == 27:
                logger.info('ESC pressed; exiting')
                break

            if args.test:
                logger.info('Test mode active; exiting after first frame')
                break

    except Exception:
        logger.exception('Unexpected exception in main loop')
    finally:
        if camera is not None:
            camera.release()
            logger.info('Camera resource released')
        if serial_port is not None:
            serial_port.close()
            logger.info('Serial port closed')
        cv2.destroyAllWindows()
        logger.info('Drowsiness detector shut down')


if __name__ == '__main__':
    main()
