import numpy as np

import lqrmpc as m
from ui import *


def solve():
    s, e, th, n, qv = val("s"), val("e"), val("th"), int(val("n")), 10 ** val("qv")
    el("qv-val").textContent = f"{qv:.3g}"
    best, table_ = m.mpc_choose_speed(e, th, s, m.DEMO_TRACK, horizon=n, q_v=qv)
    rows, cls = [], []
    for v, peak, cost in table_:
        rows.append([f"{v:.0f} mm/s", f"{peak:.2f} mm", f"{cost:.2f}",
                     "◀ chosen" if v == best else ("leaves the window" if peak > m.E_MAX else "")])
        cls.append("pick" if v == best else ("bad" if peak > m.E_MAX else ""))
    el("solve").innerHTML = table(["candidate speed", "peak |e|", "cost J", ""], rows, cls)


def convergence():
    x = (val("ce"), 0.10)
    A, B = m.discrete_model(m.V_REF)
    Q, R = np.diag([m.Q_E, m.Q_TH]) * m.DT, np.array([[m.R_W * m.DT]])
    K, _ = m.dlqr(A, B, Q, R)
    u_lqr = float((-K @ np.array([[x[0]], [x[1]]]))[0, 0])
    rows = []
    for N in (1, 2, 5, 10, 20, 50, 200):
        u = m.horizon_gain(N, x)
        rows.append([str(N), f"{u:.6f}", f"{abs(u - u_lqr):.2e}"])
    rows.append(["infinite (LQR)", f"{u_lqr:.6f}", "0"])
    el("conv").innerHTML = table(["horizon N", "first move ω₀ (rad/s)", "gap to LQR"], rows)


bind(["s", "e", "th", "n", "qv"], solve, {"th": "{:.2f}", "n": "{:.0f}"})
bind(["ce"], convergence)
done()
