# LQR and MPC for a line follower (runs in the browser)

### 👉 [Click here to try it](https://chrisbuerginrogers.github.io/ME193-Robotics/Public%20stuff/LQR-MPC-web/)

Two ways to steer a two-wheeled robot along a line: LQR (a feedback law worked
out once on paper) and MPC (a small optimization re-solved every control step).
Everything is Python running in your browser through
[PyScript](https://pyscript.net), so there is nothing to install. Explore it in
simulation, then connect a LEGO Education Double Motor and Color Sensor over
Bluetooth (Chrome or Edge) and run the same controllers on a real line. The first
page you open takes about ten seconds to load Python.

## The pages

- `index.html` — start here.
- `simulate.html` — LQR and MPC drive the same track. Change the weights, speed,
  horizon and sensor window and compare where each one goes blind.
- `lqr.html` — the gains, damping and settling time, the three sensor states, and
  why a fixed gain fails on a sharp turn.
- `mpc.html` — one MPC solve candidate by candidate, and how a long horizon
  turns into LQR.
- `robot.html` — connect the Color Sensor and Double Motor over Web Bluetooth,
  calibrate (black, white, sensor window, wheel speed, track width), then run
  bang-bang, PD, LQR or MPC and compare the runs on one plot. Calibration is
  remembered in the browser.
- `reader.html` — renders the course notes in `notes/` (Markdown and maths).

## The files

- `lqrmpc.py` — the whole simulator, plain numpy. It also runs on a laptop with
  `pip install numpy`.
- `hardware.py` — the Web Bluetooth patch for the `legoeducation` library (the same
  one QLearn uses), the `LineFollower` (read an error, drive a speed and yaw rate)
  and the four controllers.
- `ble.js` — the Web Bluetooth wrapper. `robot.toml` loads it, and `legoeducation`.
- `ui.py` — sliders, tables and SVG plots shared by the pages.
- `simulate_page.py`, `lqr_page.py`, `mpc_page.py`, `robot_page.py` — one small script per page.
- `pyscript.toml` — loads numpy and the shared modules for the simulator pages.
- `style.css` — shared styling, light and dark.
- `notes/` — the written notes: the model, LQR, MPC, and LQR vs MPC.

## Running it locally

PyScript loads files over HTTP, so opening `index.html` by double-clicking will
not work. From this folder run `python3 -m http.server` and open
http://localhost:8000/.

## On the robot

Mount the Color Sensor facing down over the edge of the tape, with the Double
Motor driving. Calibrate on the Robot page, then run. On a real robot there is no
map, so MPC cannot see the curve ahead. It previews with the turn it is holding
now, which is the honest limit explained in the MPC notes. The simulator pages
use the generic reference build (96 mm track width, 6 mm sensor window, 50 ms
control period) until you calibrate.

The robot code follows the course's hardware scripts, but it has only been run
against simulated devices so far. Treat the first run on a real robot with care:
keep a hand near it and use Stop.
