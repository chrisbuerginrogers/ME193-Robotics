"""
Install first:
    pip install legoeducation
Then copy lelib.py from the SimpleLE repo into this project's folder.

"""

import time

import legoeducation as le
from lelib import colorSensor, controller, singleMotor

# --- Bluetooth card info for your hardware -------------------------------
# Fill these in with the color/serial printed on your LEGO connection card.
# Valid values: le.LEGO_COLOR_RED, _YELLOW, _BLUE, _GREEN, _PURPLE,
# _MAGENTA, _AZURE, _ORANGE.
COLOR_SENSOR_CARD_COLOR = le.LEGO_COLOR_BLUE
COLOR_SENSOR_CARD_SERIAL = 3685

CONTROLLER_CARD_COLOR = le.LEGO_COLOR_BLUE
CONTROLLER_CARD_SERIAL = 3685

MOTOR_CARD_COLOR = le.LEGO_COLOR_BLUE
MOTOR_CARD_SERIAL = 3685

# The single motor is the only device on this team's build -- no separate
# Color Sensor. Its color input comes from whatever Connection Card is
# currently tapped on the motor itself (see card_color_name() in lelib.py),
# and the same connection stays open for driving it, too. No card filter
# here since it's the only single motor on this build; add card_color=/
# card_serial= if you're ever in a room with other single motors nearby.
POLL_DELAY_S = 0.1  # seconds between reads

motor = singleMotor()  # connected in main()



# --- Empty handler functions ----------------------------------------------
# Fill these in with whatever behavior you want.

def DoRed():
    """Spin forward (clockwise) continuously for ~5 seconds."""
    print("red -- forward")
    motor.motor_run_for_time(
        MOTOR_ACTION_DURATION_MS,
        direction=le.MOTOR_MOVE_DIRECTION_CLOCKWISE,
        speed=MOTOR_SPEED,
    )



def DoYellow():
    """Spin backward (counterclockwise) continuously for ~5 seconds."""
    print("yellow -- backward")
    motor.motor_run_for_time(
        MOTOR_ACTION_DURATION_MS,
        direction=le.MOTOR_MOVE_DIRECTION_COUNTERCLOCKWISE,
        speed=MOTOR_SPEED,
    )



def DoBlue():
    """Pulse on and off five times over ~5 seconds (stop/start, not
    continuous motion)."""
    print("blue -- pulsing")
    pulse_count = 5
    pulse_ms = MOTOR_ACTION_DURATION_MS // (pulse_count * 2)
    for _ in range(pulse_count):
        motor.motor_run_for_time(pulse_ms, speed=MOTOR_SPEED)
        motor.motor_stop()
        time.sleep(pulse_ms / 1000)



def DoTeal():
    """Forward for the first half, then reverse for the second half --
    ~5 seconds total, direction changes partway through."""
    print("teal -- forward then reverse")
    half_ms = MOTOR_ACTION_DURATION_MS // 2
    motor.motor_run_for_time(
        half_ms, direction=le.MOTOR_MOVE_DIRECTION_CLOCKWISE, speed=MOTOR_SPEED
    )
    motor.motor_run_for_time(
        half_ms, direction=le.MOTOR_MOVE_DIRECTION_COUNTERCLOCKWISE, speed=MOTOR_SPEED
    )



def DoGreen():
    print("green")
    motor.motor_run_for_degrees(180, direction=le.MOTOR_MOVE_DIRECTION_COUNTERCLOCKWISE)



def DoPurple():
    print("purple")
    motor.motor_run_for_degrees(360, direction=le.MOTOR_MOVE_DIRECTION_COUNTERCLOCKWISE)



def DoWhite():
    print("white")
    motor.motor_run_for_degrees(180, direction=le.MOTOR_MOVE_DIRECTION_CLOCKWISE)



def DoMagenta():
    print("magenta")
    motor.motor_run_for_degrees(360, direction=le.MOTOR_MOVE_DIRECTION_CLOCKWISE)



def DoOrange():
    pass



def DoAzure():
    pass



def DoNoColor():
    pass



def DoUnknownColor():
    pass



def DoLeftUp():
    pass



def DoLeftDown():
    pass



def DoLeftReleased():
    print("left released")



def DoRightUp():
    print("right up")



def DoRightDown():
    print("right down")



def DoRightReleased():
    print("right released")



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
    global motor

    ctl = controller()
    ctl.connect(card_serial=CONTROLLER_CARD_SERIAL, card_color=CONTROLLER_CARD_COLOR)

    motor.connect(card_serial=MOTOR_CARD_SERIAL, card_color=MOTOR_CARD_COLOR)

    try:
        while True:
            handle_color(motor.card_color_name())
            handle_controller(ctl)
            time.sleep(POLL_DELAY_S)
    except KeyboardInterrupt:
        pass
    finally:
        motor.stop()



if __name__ == "__main__":
    main()
