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
