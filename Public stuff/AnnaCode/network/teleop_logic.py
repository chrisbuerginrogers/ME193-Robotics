"""Pure logic for driving the Trainer's outputs from a LEGO Controller's joysticks.

No PyScript or DOM in here, so it can be unit-tested with plain Python
(see AnnaCode/tests/test_teleop_logic.py). teleop.py is the glue that feeds it
the live joystick readings and the page's settings.

Tank drive: the left stick drives the left wheel and the right stick drives the
right wheel, which is the same (left, right) action a trained network outputs.
"""

# Output channels a joystick can drive. Light/beep channels are left to the network.
DRIVE_CHANNELS = ("LeftSpeed", "RightSpeed", "BothSpeed", "Speed")

DEADBAND = 8.0          # stick percent below which the stick counts as centred
DEFAULT_MAX_SPEED = 50  # motor speed (percent) when a stick is pushed all the way


def _num(value) -> float:
    """Stick readings are None until the controller's first notification."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def stick_values(device_state: dict) -> tuple[float, float]:
    """(left, right) stick percents, each -100..100, from a controller's state dict."""
    return _num(device_state.get("LeftPercent")), _num(device_state.get("RightPercent"))


def is_deflected(left: float, right: float, deadband: float = DEADBAND) -> bool:
    """True when either stick is pushed past the deadband (the human wants control)."""
    return abs(_num(left)) > deadband or abs(_num(right)) > deadband


def _shape(value: float, deadband: float) -> float:
    """Zero inside the deadband, then rescaled so the output ramps up from 0
    (no jump from 0 to the deadband value the instant the stick leaves centre)."""
    value = max(-100.0, min(100.0, _num(value)))
    if abs(value) <= deadband:
        return 0.0
    sign = 1.0 if value > 0 else -1.0
    return sign * (abs(value) - deadband) / (100.0 - deadband) * 100.0


def command_for(channel: str, left: float, right: float, max_speed: float = DEFAULT_MAX_SPEED,
                reverse: bool = False, deadband: float = DEADBAND):
    """The integer command (-100..100) a joystick position gives one output channel,
    or None if that channel isn't one a joystick drives.

    LeftSpeed  <- left stick.
    RightSpeed <- right stick, sign flipped because the double motor is mirrored
                  (the example networks use opposite signs for the two wheels to go straight).
    BothSpeed / Speed (a single output) <- whichever stick is pushed harder.
    reverse flips every sign, for a controller whose "forward" reads negative.
    """
    if channel not in DRIVE_CHANNELS:
        return None
    l, r = _shape(left, deadband), _shape(right, deadband)
    if channel == "LeftSpeed":
        v = l
    elif channel == "RightSpeed":
        v = -r
    else:
        v = l if abs(l) >= abs(r) else r
    if reverse:
        v = -v
    scale = max(0.0, min(100.0, _num(max_speed))) / 100.0
    return int(round(max(-100.0, min(100.0, v * scale))))


LEVEL_STEPS = (-1.0, -0.5, 0.0, 0.5, 1.0)   # the five values a simplified label can take, as fractions of Max speed


def quantize(value, max_speed: float = DEFAULT_MAX_SPEED) -> float:
    """Snap a motor speed to the nearest of five levels: 0, +-1/2 and +-1 times max_speed.

    Anything below a quarter of max_speed becomes 0, below three quarters becomes half, and
    from three quarters up (including anything beyond max_speed) becomes full. The result is
    still in motor-speed units, so a network trained on it drives the motor directly.
    """
    m = _num(max_speed)
    v = _num(value)
    if m <= 0 or v != v:
        return 0.0
    step = min(1.0, int(abs(v) / m * 2 + 0.5) / 2)    # int() of a positive number rounds down: half goes up
    if step == 0.0:
        return 0.0
    return step * m if v > 0 else -step * m


def drive_hint(channels) -> str:
    """A one-line nudge about the Output boxes, or "" when they are set up to steer a car.

    channels: the channel chosen in each Output box ("" when nothing is chosen yet).
    - nothing chosen: tell the student to set the Output box first;
    - nothing the sticks can drive (e.g. only a light or beep): say so;
    - a single drive output, or not both wheels: the car can go forward and back but can't turn,
      because a turn needs the two wheels to get different commands.
    """
    chosen = [c for c in channels if c]
    if not chosen:
        return "Set the Output box first: pick a device and a speed channel (for a car: LeftSpeed and RightSpeed)."
    drive = [c for c in chosen if c in DRIVE_CHANNELS]
    if not drive:
        return "None of your outputs is a motor speed, so the controller has nothing to drive. Pick a speed channel (for a car: LeftSpeed and RightSpeed)."
    if "LeftSpeed" in drive and "RightSpeed" in drive:
        return ""
    return ("Only one wheel or one combined speed is set as an output, so the controller can drive forward and back "
            "but can't turn. To turn, use two outputs: LeftSpeed and RightSpeed.")


def commands_for_outputs(channels: dict, left: float, right: float, max_speed: float = DEFAULT_MAX_SPEED,
                         reverse: bool = False, deadband: float = DEADBAND) -> dict:
    """channels: {output_id: channel_name}. Returns {output_id: command} for the
    outputs a joystick drives; other outputs are left out."""
    out = {}
    for oid, channel in channels.items():
        cmd = command_for(channel, left, right, max_speed, reverse, deadband)
        if cmd is not None:
            out[oid] = cmd
    return out
