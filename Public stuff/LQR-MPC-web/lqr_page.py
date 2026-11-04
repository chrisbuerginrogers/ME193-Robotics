import numpy as np

import lqrmpc as m
from ui import *


def render():
    qe, qth, r, v, dt, emax = (val(i) for i in ("qe", "qth", "r", "v", "dt", "emax"))
    ke, kth = m.lqr_gains_analytic(v, qe, qth, r)
    wn = np.sqrt(v * ke)
    zeta = kth / (2 * wn)
    kde, kdth = m.lqr_gains_discrete(v, dt, qe, qth, r)
    A, B = m.discrete_model(v, dt)
    pole = float(np.abs(np.linalg.eigvals(A - B @ np.array([[kde, kdth]])))[0])
    el("gains").innerHTML = table(["", "value"], [
        ["k<sub>e</sub> (rad/s per mm)", f"{ke:.4f}"],
        ["k<sub>θ</sub> (1/s)", f"{kth:.4f}"],
        ["natural frequency ω<sub>n</sub> (rad/s)", f"{wn:.3f}"],
        ["damping ratio ζ", f"{zeta:.3f}"],
        ["settling time 4/(ζω<sub>n</sub>) (s)", f"{4 / (zeta * wn):.2f}"],
        ["…as distance travelled (mm)", f"{4 / (zeta * wn) * v:.0f}"],
        [f"discrete gains at dt = {dt:g} s", f"{kde:.4f}, {kdth:.4f}"],
        ["closed-loop pole radius (must be &lt; 1)", f"{pole:.3f}"],
    ]) + '<p class="note">With Q<sub>θ</sub> = 0, ζ is always 1/√2: the heading gain is not free, LQR derives it.</p>'

    # step response on a straight line, using the discrete controller
    e, th, ts, es, ws = 4.0, 0.0, [], [], []
    for i in range(int(8 / dt)):
        w = -kde * m.coerce(e, emax) - kdth * th
        ts.append(i * dt); es.append(e); ws.append(w)
        e, th = m.step(e, th, v, w, 0.0, dt)
    el("p-step").innerHTML = line_plot([(ts, es, "lqr")], "time (s)", "e (mm)", band=emax)

    black, white = 12.0, 85.0
    rows = []
    for name, f in (("fully ON the line", 0.0), ("edge, drifted onto line", 0.35), ("edge, on target", 0.5),
                    ("edge, drifted off line", 0.65), ("fully OFF the line", 1.0)):
        refl = black + f * (white - black)
        e_s = float(np.clip(2 * emax * (f - 0.5), -emax, emax))
        w = -ke * e_s + 0.0
        vl, vr = m.wheel_speeds(v, w)
        rows.append([name, f"{refl:.0f}", f"{e_s:+.2f}", f"{w:+.3f}", f"{m.to_percent(vl):.0f}", f"{m.to_percent(vr):.0f}"])
    el("states").innerHTML = table(["sensor state", "reading", "e (mm)", "ω (rad/s)", "left %", "right %"], rows)

    rows, cls = [], []
    for radius in (None, 300.0, 150.0, 80.0, 40.0):
        kappa = 0.0 if radius is None else 1.0 / radius
        ess = -kappa * v / ke + 0.0
        vlim = np.inf if kappa == 0 else emax * ke / kappa
        blind = abs(ess) > emax
        rows.append(["straight" if radius is None else f"{radius:.0f} mm", f"{kappa:.5f}", f"{ess:+.2f}",
                     "BLIND" if blind else "ok", "any" if np.isinf(vlim) else f"{vlim:.0f} mm/s"])
        cls.append("bad" if blind else "")
    el("turns").innerHTML = table(["turn radius", "κ (1/mm)", f"e<sub>ss</sub> at {v:.0f} mm/s (mm)", "verdict", "max v inside window"], rows, cls)


bind(["qe", "qth", "r", "v", "dt", "emax"], render, {"v": "{:.0f}", "dt": "{:.2f}"})
done()
