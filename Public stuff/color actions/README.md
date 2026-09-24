# Color Actions

`main.py` polls a Color Sensor and a Controller (joystick) every 0.1s and
dispatches each reading to its own named handler function -- one function
per color, one function per joystick direction -- driving a Double Motor
and a Single Motor.

## Hardware

- **Color Sensor**, **Controller**, **Double Motor**, and **Single Motor**
  all connect using the *same* LEGO connection card (color + serial) --
  set once at the top of `main.py`.
- The Double Motor's two outputs are **not** a car's left/right wheels
  here -- they're mounted in a pillar arrangement, each doing its own
  independent thing. Because of that:
  - **Joystick -> Double Motor**: left stick up/down runs the Double
    Motor's `MOTOR_LEFT` output forward/reverse, right stick does the
    same for `MOTOR_RIGHT`. Releasing a stick stops that output.
  - **Color -> Single Motor**: each detected color spins the Single
    Motor at its own speed/direction (see `handle_color()`).

## Setup

```bash
pip install legoeducation
```

`lelib.py` is already copied into this folder (see `useful libraries/`
for the source). Set your hardware's connection card at the top of
`main.py`:

```python
COLOR_SENSOR_CARD_COLOR = le.LEGO_COLOR_RED
COLOR_SENSOR_CARD_SERIAL = 1129
# ...same color/serial repeated for CONTROLLER_, DOUBLE_MOTOR_, SINGLE_MOTOR_
```

Then run it:

```bash
python3 main.py
```

Press Ctrl+C to stop -- both motors are stopped and every device is
disconnected in a `finally` block, so nothing keeps spinning after exit.

## How it works

- `handle_color(color_name)` is a single `match` statement mapping each
  of the 11 colors the sensor can report (`Red`, `Yellow`, `Blue`, `Teal`,
  `Green`, `Purple`, `White`, `Magenta`, `Orange`, `Azure`, `No color`)
  plus an `_` fallback (`Unknown`) to its own `Do<Color>()` function.
- `handle_controller(ctl)` reads `left_up()/left_down()`/`right_up()/
  right_down()` off the Controller and maps each of the six resulting
  states (`left`: up/down/released, `right`: up/down/released) to its own
  `Do<State>()` function.
- Every `Do*()` function is a plain, independent function -- there's no
  shared state between them beyond the module-level `dm`/`sm` motor
  handles set once in `main()`. Add real behavior by editing the body of
  whichever `Do*()` function corresponds to the input you care about;
  nothing else needs to change.

## Notes

- The color-to-speed and joystick-to-speed mappings here (`COLOR_MOTOR_SPEED`,
  `JOYSTICK_SPEED`, and each color's specific speed/direction) are
  placeholders meant to prove every input actually moves something on
  hardware -- swap in whatever your project actually needs each color or
  joystick direction to do.
- The main loop polls at `POLL_DELAY_S` (0.1s / 10 Hz) rather than reacting
  to a single edge, so a `Do*()` function currently re-fires every tick for
  as long as its condition holds (e.g. holding the joystick up keeps
  calling `DoLeftUp()` every 0.1s). That's fine for `motor_run()`/`run()`
  calls, which just re-assert the same speed, but keep it in mind if you
  add a behavior that shouldn't repeat (add your own "did this already
  fire" flag in that case).
