import asyncio
import json

import numpy as np
from pyodide.ffi import create_proxy
from pyscript import document, window

import hardware as hw
import lqrmpc as m
from ui import *

cs = hw.ColorSensorDevice()
dm = hw.DoubleMotorDevice()
cal = dict(hw.DEFAULT_CAL)
runs = {}              # latest run for each controller: name -> list of dict rows
running = {"on": False, "stop": False}
NAMES = {"bangbang": "Bang-bang", "pd": "PD", "lqr": "LQR", "mpc": "MPC"}

# -- calibration is remembered between visits ----------------------------------
try:
    saved = window.localStorage.getItem("lqrmpc-cal")
    if saved:
        cal.update(json.loads(saved))
except Exception:
    pass


def save_cal():
    try:
        window.localStorage.setItem("lqrmpc-cal", json.dumps(cal))
    except Exception:
        pass


def log(text):
    term = el("terminal")
    line = document.createElement("div")
    line.innerText = text
    term.appendChild(line)
    term.scrollTop = term.scrollHeight


def set_status(id, ok, text):
    s = el(id)
    s.textContent = text
    s.className = "status on" if ok else "status"


def refresh():
    set_status("s-cs", cs.connected, "connected" if cs.connected else "not connected")
    set_status("s-dm", dm.connected, "connected" if dm.connected else "not connected")
    el("b-cs").disabled = cs.connected
    el("b-dm").disabled = dm.connected
    el("b-black").disabled = el("b-white").disabled = not cs.connected
    el("b-drive").disabled = not dm.connected or running["on"]
    ready = cs.connected and dm.connected
    el("b-run").disabled = not ready or running["on"]
    el("b-stop").disabled = not running["on"]
    el("run-note").textContent = ("Ready. Put the robot on the line, then press run." if ready else
                                  "Connect both devices to run. Put the robot on the line first. "
                                  "It will drive as soon as you press run.")
    show_cal()


hw.hooks["log"] = log
hw.hooks["changed"] = refresh


def show_cal():
    rows = [["black reading", f"{cal['reflect_black']:.0f}"], ["white reading", f"{cal['reflect_white']:.0f}"],
            ["window e<sub>max</sub>", f"{cal['e_max_mm']:.1f} mm"],
            ["track width", f"{cal['track_width_mm']:.0f} mm"],
            ["wheel speed at 100%", f"{cal['wheel_max_mms']:.0f} mm/s"],
            ["control period", f"{cal['dt'] * 1000:.0f} ms"]]
    el("cal-table").innerHTML = table(["calibration", "value"], rows)


# -- live reflection --------------------------------------------------------------
async def live_loop():
    while True:
        r = None
        if cs.connected:
            v = cs.sensor.reflection
            if v is not None and not (isinstance(v, float) and np.isnan(v)):
                r = float(v)
        el("live").textContent = "--" if r is None else f"{r:.0f}"
        await asyncio.sleep(0.1)


async def sample(which):
    el("b-black").disabled = el("b-white").disabled = True
    out = el("r-" + which)
    vals = []
    for i in range(60):
        out.textContent = f"sampling… {3 - i * 0.05:.1f} s"
        v = cs.sensor.reflection
        if v is not None and not (isinstance(v, float) and np.isnan(v)):
            vals.append(float(v))
        await asyncio.sleep(0.05)
    if vals:
        cal["reflect_" + which] = float(np.mean(vals))
        out.textContent = f"{cal['reflect_' + which]:.0f}"
        save_cal()
        if cal["reflect_white"] - cal["reflect_black"] < 10:
            log("Black and white readings are very close. Check the sensor is over the tape, then the floor.")
    else:
        out.textContent = "no readings"
    refresh()


async def drive_test():
    el("b-drive").disabled = True
    log("Driving straight for 2 s at 100%. Measure how far it went.")
    dm.movement_move_tank(100, 100, blocking=False)
    await asyncio.sleep(2.0)
    dm.movement_stop(blocking=False)
    refresh()


def on_cal_slider(*_):
    cal["e_max_mm"] = val("emax")
    cal["track_width_mm"] = val("tw")
    cal["wheel_max_mms"] = val("dist") / 2.0
    save_cal()
    show_cal()


# -- running -----------------------------------------------------------------------
def params():
    return {"v": val("v"), "omega_mag": val("wmag"), "kp": val("kp"), "kd": val("kd"),
            "qe": val("qe"), "qth": val("qth"), "r": val("r"), "n": val("n"), "qv": 10 ** val("qv")}


def plot_runs():
    el("out").style.display = ""
    names = [n for n in NAMES if n in runs]
    leg = legend(*[(n + "-c", NAMES[n]) for n in names])
    es, vs = [], []
    for n in names:
        rows = runs[n]
        es.append(([r["t"] for r in rows], [r["e"] for r in rows], n))
        vs.append(([r["t"] for r in rows], [r["v"] for r in rows], n))
    el("p-e").innerHTML = leg + line_plot(es, "time (s)", "e (mm)", band=cal["e_max_mm"])
    el("p-v").innerHTML = line_plot(vs, "time (s)", "commanded speed (mm/s)", ymin=0)
    trs = []
    for n in names:
        rows = runs[n]
        e = np.array([r["e"] for r in rows])
        blind = 100 * np.mean([r["saturated"] for r in rows])
        trs.append([f'<i class="swatch {n}-c"></i>{NAMES[n]}', f"{np.abs(e).max():.2f}", f"{blind:.1f}%",
                    f"{np.mean([r['v'] for r in rows]):.0f}", f"{rows[-1]['t']:.1f}"])
    el("stats").innerHTML = table(["controller", "peak |e| (mm)", "blind", "mean v (mm/s)", "time (s)"], trs)


async def run():
    name = el("ctl").value
    p = params()
    duration = val("dur")
    ctl = hw.make_controller(name, p, cal)
    bot = hw.LineFollower(dm, cs, cal)
    running["on"], running["stop"] = True, False
    refresh()
    rows = []
    log(f"Running {NAMES[name]} for {duration:.0f} s at v = {p['v']:.0f} mm/s.")
    try:
        bot.start()
        async for k, t in bot.loop(duration, lambda: running["stop"] or not (dm.connected and cs.connected)):
            e, theta, sat = bot.read()
            v, omega = ctl(e, theta)
            left, right = bot.drive(v, omega)
            rows.append({"t": t, "e": e, "theta": theta, "v": v, "omega": omega,
                         "saturated": bool(sat), "left": left, "right": right})
            if k % 5 == 0 and len(rows) > 2:
                runs[name] = rows
                plot_runs()
    except Exception as exc:
        log(f"Run stopped: {exc}")
    finally:
        bot.stop()
        running["on"] = False
    if len(rows) > 2:
        runs[name] = rows
        plot_runs()
        log(f"Done: {len(rows)} samples.")
    refresh()


def csv_download(*_):
    name = el("ctl").value
    rows = runs.get(name) or (list(runs.values())[-1] if runs else None)
    if not rows:
        return
    cols = ["t", "e", "theta", "v", "omega", "saturated", "left", "right"]
    text = ",".join(cols) + "\n" + "\n".join(",".join(str(r[c]) for c in cols) for r in rows)
    a = document.createElement("a")
    a.href = "data:text/csv;charset=utf-8," + window.encodeURIComponent(text)
    a.download = f"{name}_run.csv"
    a.click()


def on(id, fn):
    el(id).addEventListener("click", create_proxy(fn))


on("b-cs", lambda e: asyncio.ensure_future(cs.connect_web()))
on("b-dm", lambda e: asyncio.ensure_future(dm.connect_web()))
on("b-black", lambda e: asyncio.ensure_future(sample("black")))
on("b-white", lambda e: asyncio.ensure_future(sample("white")))
on("b-drive", lambda e: asyncio.ensure_future(drive_test()))
on("b-run", lambda e: asyncio.ensure_future(run()))
on("b-stop", lambda e: running.update(stop=True))
on("b-csv", csv_download)
on("b-clear", lambda e: (runs.clear(), setattr(el("out").style, "display", "none")))


def reset_cal(*_):
    cal.update(hw.DEFAULT_CAL)
    el("emax").value, el("tw").value, el("dist").value = cal["e_max_mm"], cal["track_width_mm"], cal["wheel_max_mms"] * 2
    for i in ("emax", "tw", "dist"):
        el(i + "-val").textContent = f"{float(el(i).value):g}"
    el("r-black").textContent = el("r-white").textContent = ""
    save_cal()
    show_cal()


on("b-reset", reset_cal)

# sliders: show the saved calibration, then listen
el("emax").value, el("tw").value, el("dist").value = cal["e_max_mm"], cal["track_width_mm"], cal["wheel_max_mms"] * 2
bind(["emax", "tw", "dist"], on_cal_slider, {"dist": "{:.0f}", "tw": "{:.0f}"})
bind(["dur", "v", "wmag", "kp", "kd", "qe", "qth", "r", "n", "qv"], lambda: el("qv-val").__setattr__(
    "textContent", f"{10 ** val('qv'):.3g}"), {"dur": "{:.0f}", "v": "{:.0f}", "n": "{:.0f}"})
refresh()
asyncio.ensure_future(live_loop())
done()
