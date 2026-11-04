# LQR & MPC for a line-following robot

This is the web edition of a short course on two ways to steer a two-wheeled
robot along a line: **LQR** (a feedback law worked out once, on paper) and
**MPC** (a small optimization re-solved every control step).

Everything here runs in your browser. The simulator is plain Python and numpy
(via PyScript), and each page lets you change a number and watch the result.

## Start with the pages that move

- [Simulator](simulate.html): LQR and MPC drive the same track. Change the
  weights, the speed and the horizon and watch where each one goes blind.
- [LQR](lqr.html): the gains, the damping, and why a fixed gain fails on a sharp turn.
- [MPC](mpc.html): one solve, candidate by candidate, and how a long horizon turns into LQR.

## Then read the notes

1. [00 · the model](00-sim.md): the whole simulator in one file.
2. [01 · LQR](01-lqr.md): what it is, the math, a worked example.
3. [02 · MPC](02-mpc.md): what it is and why you would reach for it.
4. [03 · LQR vs MPC](03-lqr-vs-mpc.md): the difference in one page.

## About the robot

The notes were written for a LEGO line follower with one reflected-light sensor.
The simulator pages use the generic reference build (sensor window of 6 mm, 96 mm
track width, 50 ms control period). The [Robot](robot.html) page connects a real
LEGO Education Double Motor and Color Sensor over Bluetooth, calibrates them to
your tape and floor, and runs bang-bang, PD, LQR and MPC on the line. It needs
Chrome or Edge on a laptop or desktop.
