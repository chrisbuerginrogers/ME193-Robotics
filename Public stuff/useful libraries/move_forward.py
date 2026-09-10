"""
Drive the double motor straight forward for a set duration.

Install first:
    pip install legoeducation
Then copy lelib.py from the SimpleLE repo into this project's folder.

Usage:
    python3 move_forward.py [duration_ms] [speed]
"""
# TEST CHANGES

import sys

from lelib import doubleMotor

DURATION_MS = 2000  # how long to drive forward
SPEED = 50           # 0-100


def move_forward(duration_ms=DURATION_MS, speed=SPEED):
    dm = doubleMotor()

    print("Connecting to double motor...")
    dm.connect(card_serial=None)

    try:
        dm.set_speed(speed)
        print(f"Driving forward for {duration_ms} ms at speed {speed}...")
        dm.run_time(duration_ms)
    finally:
        dm.stop()
        dm.disconnect()


if __name__ == "__main__":
    duration_ms = int(sys.argv[1]) if len(sys.argv) > 1 else DURATION_MS
    speed = int(sys.argv[2]) if len(sys.argv) > 2 else SPEED
    move_forward(duration_ms, speed)
