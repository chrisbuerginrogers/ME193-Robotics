import lqrmpc as m
from ui import *

sel = el("track")
for name in m.TRACKS:
    sel.innerHTML += f"<option>{name}</option>"


def render():
    track = m.TRACKS[sel.value]
    qe, qth, r, v = val("qe"), val("qth"), val("r"), val("v")
    n, qv, emax = int(val("n")), 10 ** val("qv"), val("emax")
    el("qv-val").textContent = f"{qv:.3g}"

    lqr, (ke, kth) = m.run_lqr(track, v, e_max=emax, q_e=qe, q_th=qth, r=r)
    mpc = m.run_mpc(track, e_max=emax, horizon=n, q_e=qe, q_th=qth, r=r, q_v=qv)

    rows = []
    for label, cls, log in (("LQR, fixed speed", "lqr-c", lqr), ("MPC, speed scheduled", "mpc-c", mpc)):
        pk, blind, lap, mv = m.stats(log, emax)
        rows.append([f'<i class="swatch {cls}"></i>{label}', f"{pk:.1f}", f"{blind:.1f}%", f"{lap:.1f}", f"{mv:.0f}"])
    el("stats").innerHTML = table(
        ["controller", "peak |e| (mm)", "time blind", "lap (s)", "mean v (mm/s)"], rows,
        ["bad" if m.stats(lg, emax)[1] > 5 else "" for lg in (lqr, mpc)]
    ) + f'<p class="note">LQR gains at {v:.0f} mm/s: k<sub>e</sub> = {ke:.4f}, k<sub>θ</sub> = {kth:.4f}. "Blind" is the share of the run spent outside the sensor window.</p>'

    lx, ly = track.robot_xy(lqr)
    mx, my = track.robot_xy(mpc)
    leg = legend(("lqr-c", "LQR"), ("mpc-c", "MPC"))
    el("p-track").innerHTML = leg + track_plot(track, [(lx, ly, "lqr"), (mx, my, "mpc")])
    el("p-e").innerHTML = leg + line_plot(
        [(lqr[:, 0], lqr[:, 2], "lqr"), (mpc[:, 0], mpc[:, 2], "mpc")], "time (s)", "e (mm)", band=emax)
    el("p-v").innerHTML = leg + line_plot(
        [(lqr[:, 0], lqr[:, 4], "lqr"), (mpc[:, 0], mpc[:, 4], "mpc")], "time (s)", "speed (mm/s)", ymin=0)


bind(["track", "qe", "qth", "r", "v", "n", "qv", "emax"], render,
     {"qv": "{:.3g}", "n": "{:.0f}", "v": "{:.0f}"})
done()
