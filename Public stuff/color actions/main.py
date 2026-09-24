"""
Install first:
    pip install legoeducation
Then copy lelib.py from the SimpleLE repo into this project's folder.

"""

import time

import legoeducation as le
from lelib import colorSensor, controller, doubleMotor, singleMotor

# --- Bluetooth card info for your hardware -------------------------------
# Fill these in with the color/serial printed on your LEGO connection card.
# Valid values: le.LEGO_COLOR_RED, _YELLOW, _BLUE, _GREEN, _PURPLE,
# _MAGENTA, _AZURE, _ORANGE.
# Color sensor, controller, Double Motor, and Single Motor are all on the
# same physical connection card here.
COLOR_SENSOR_CARD_COLOR = le.LEGO_COLOR_RED
COLOR_SENSOR_CARD_SERIAL = 1129

CONTROLLER_CARD_COLOR = le.LEGO_COLOR_RED
CONTROLLER_CARD_SERIAL = 1129

DOUBLE_MOTOR_CARD_COLOR = le.LEGO_COLOR_RED
DOUBLE_MOTOR_CARD_SERIAL = 1129

SINGLE_MOTOR_CARD_COLOR = le.LEGO_COLOR_RED
SINGLE_MOTOR_CARD_SERIAL = 1129

POLL_DELAY_S = 0.1  # seconds between reads

# The Double Motor's two outputs aren't a car's left/right wheels here --
# the motors sit in a pillar arrangement -- so the joystick just drives
# each output independently. The Single Motor reacts to color instead.
JOYSTICK_SPEED = 50   # percent, for the Double Motor's two outputs
COLOR_MOTOR_SPEED = 60  # percent, for the Single Motor's color reactions

# Set in main() once connected, used by the handler functions below.
dm = None  # doubleMotor
sm = None  # singleMotor



# --- Empty handler functions ----------------------------------------------
# Fill these in with whatever behavior you want.

def DoRed():
    print("red")
    sm.run(COLOR_MOTOR_SPEED)


def DoYellow():
    print("yellow")
    sm.run(-COLOR_MOTOR_SPEED)


def DoBlue():
    print("blue")
    sm.run(COLOR_MOTOR_SPEED // 2)


def DoTeal():
    sm.run(-COLOR_MOTOR_SPEED // 2)


def DoGreen():
    sm.run(100)


def DoPurple():
    sm.run(-100)


def DoWhite():
    sm.stop()


def DoMagenta():
    sm.run(COLOR_MOTOR_SPEED)


def DoOrange():
    sm.run(-COLOR_MOTOR_SPEED)


def DoAzure():
    sm.run(COLOR_MOTOR_SPEED // 2)


def DoNoColor():
    sm.stop()


def DoUnknownColor():
    sm.stop()


def DoLeftUp():
    dm.motor_run(speed=JOYSTICK_SPEED, blocking=False, motor=le.MOTOR_LEFT)


def DoLeftDown():
    dm.motor_run(speed=-JOYSTICK_SPEED, blocking=False, motor=le.MOTOR_LEFT)


def DoLeftReleased():
    dm.motor_stop(motor=le.MOTOR_LEFT)


def DoRightUp():
    dm.motor_run(speed=JOYSTICK_SPEED, blocking=False, motor=le.MOTOR_RIGHT)


def DoRightDown():
    dm.motor_run(speed=-JOYSTICK_SPEED, blocking=False, motor=le.MOTOR_RIGHT)


def DoRightReleased():
    dm.motor_stop(motor=le.MOTOR_RIGHT)



# --- Dispatch helpers -------------------------------------------------

def handle_color(color_name):
    """Big switch statement on the color sensor's detected color."""
    match color_name:
        case "Red":
            DoRed()
        case "Yellow":
            DoYellow()
        case "Blue":
            DoBlue()
        case "Teal":
            DoTeal()
        case "Green":
            DoGreen()
        case "Purple":
            DoPurple()
        case "White":
            DoWhite()
        case "Magenta":
            DoMagenta()
        case "Orange":
            DoOrange()
        case "Azure":
            DoAzure()
        case "No color":
            DoNoColor()
        case _:
            DoUnknownColor()



def handle_controller(ctl):
    """Big switch statement on the controller's joystick state."""
    if ctl.left_up():
        left_state = "up"
    elif ctl.left_down():
        left_state = "down"
    else:
        left_state = "released"

    if ctl.right_up():
        right_state = "up"
    elif ctl.right_down():
        right_state = "down"
    else:
        right_state = "released"

    match left_state:
        case "up":
            DoLeftUp()
        case "down":
            DoLeftDown()
        case "released":
            DoLeftReleased()

    match right_state:
        case "up":
            DoRightUp()
        case "down":
            DoRightDown()
        case "released":
            DoRightReleased()



# --- Main loop -------------------------------------------------------------

def main():
    global dm, sm

    sensor = colorSensor()
    sensor.connect(card_serial=COLOR_SENSOR_CARD_SERIAL, card_color=COLOR_SENSOR_CARD_COLOR)

    ctl = controller()
    ctl.connect(card_serial=CONTROLLER_CARD_SERIAL, card_color=CONTROLLER_CARD_COLOR)

    dm = doubleMotor()
    dm.connect(card_serial=DOUBLE_MOTOR_CARD_SERIAL, card_color=DOUBLE_MOTOR_CARD_COLOR)

    sm = singleMotor()
    sm.connect(card_serial=SINGLE_MOTOR_CARD_SERIAL, card_color=SINGLE_MOTOR_CARD_COLOR)

    try:
        while True:
            handle_color(sensor.detect_color())
            handle_controller(ctl)
            time.sleep(POLL_DELAY_S)
    except KeyboardInterrupt:
        pass
    finally:
        dm.motor_stop(motor=le.MOTOR_LEFT)
        dm.motor_stop(motor=le.MOTOR_RIGHT)
        sm.stop()
        dm.disconnect()
        sm.disconnect()
        sensor.disconnect()
        ctl.disconnect()



if __name__ == "__main__":
    main()
