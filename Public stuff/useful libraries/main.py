"""
Install first:
    pip install legoeducation
Then copy lelib.py from the SimpleLE repo into this project's folder.

"""

import time

import legoeducation as le
from lelib import colorSensor, controller

# --- Bluetooth card info for your hardware -------------------------------
# Fill these in with the color/serial printed on your LEGO connection card.
# Valid values: le.LEGO_COLOR_RED, _YELLOW, _BLUE, _GREEN, _PURPLE,
# _MAGENTA, _AZURE, _ORANGE.
COLOR_SENSOR_CARD_COLOR = le.LEGO_COLOR_ORANGE
COLOR_SENSOR_CARD_SERIAL = 7552

CONTROLLER_CARD_COLOR = le.LEGO_COLOR_ORANGE
CONTROLLER_CARD_SERIAL = 7552

POLL_DELAY_S = 0.1  # seconds between reads



# --- Handler functions ------------------------------------------------------
# Each one runs once when its color/joystick state starts.
# Replace the print with whatever behavior you want.

def DoRed():
    print("red")



def DoYellow():
    print("yellow")



def DoBlue():
    print("blue")



def DoTeal():
    print("teal")



def DoGreen():
    print("green")



def DoPurple():
    print("purple")



def DoWhite():
    print("white") #woohoo



def DoMagenta():
    print("magenta")



def DoOrange():
    print("orange")



def DoAzure():
    print("azure")



def DoNoColor():
    print("no color")



def DoUnknownColor():
    print("unknown color")



def DoLeftUp():
    print("left joystick up")



def DoLeftDown():
    print("left joystick down")



def DoLeftReleased():
    print("left joystick released")



def DoRightUp():
    print("right joystick up")



def DoRightDown():
    print("right joystick down")



def DoRightReleased():
    print("right joystick released")



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



def joystick_state(is_up, is_down):
    """Turn a joystick's up/down readings into "up", "down", or "released"."""
    if is_up:
        return "up"
    elif is_down:
        return "down"
    else:
        return "released"



def handle_left(state):
    """Switch statement on the left joystick's state."""
    match state:
        case "up":
            DoLeftUp()
        case "down":
            DoLeftDown()
        case "released":
            DoLeftReleased()



def handle_right(state):
    """Switch statement on the right joystick's state."""
    match state:
        case "up":
            DoRightUp()
        case "down":
            DoRightDown()
        case "released":
            DoRightReleased()



# --- Main loop -------------------------------------------------------------

def main():
    sensor = colorSensor()
    sensor.connect(card_serial=COLOR_SENSOR_CARD_SERIAL, card_color=COLOR_SENSOR_CARD_COLOR)

    ctl = controller()
    ctl.connect(card_serial=CONTROLLER_CARD_SERIAL, card_color=CONTROLLER_CARD_COLOR)

    # Remember the last state so handlers only fire when something changes.
    last_color = None
    last_left = None
    last_right = None

    try:
        while True:
            color = sensor.detect_color()
            if color != last_color:
                handle_color(color)
                last_color = color

            left = joystick_state(ctl.left_up(), ctl.left_down())
            if left != last_left:
                handle_left(left)
                last_left = left

            right = joystick_state(ctl.right_up(), ctl.right_down())
            if right != last_right:
                handle_right(right)
                last_right = right

            time.sleep(POLL_DELAY_S)
    except KeyboardInterrupt:
        print("stopped")



if __name__ == "__main__":
    main()
