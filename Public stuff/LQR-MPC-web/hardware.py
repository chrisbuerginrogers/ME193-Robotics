"""
LEGO Education Double Motor + Color Sensor, driven from the browser.

The `legoeducation` package talks Bluetooth through a background thread, which
a browser does not have. The patch below swaps that thread for Web Bluetooth
(ble.js) running on the page's own event loop. It is the same patch the QLearn
page uses.

On top of that sits `LineFollower`, the one-sensor line follower from the
course: read() gives (e, theta, saturated), drive() takes a speed and a yaw rate.
"""

import asyncio
import math
from collections import deque
from concurrent.futures import Future

import legoeducation as le
import legoeducation.background_worker as bw
from legoeducation import ColorSensor as _CS
from legoeducation import DoubleMotor as _DM
from legoeducation.rpc_message import RPC_VERSION, InfoRequest, InfoResponse
from pyodide.ffi import create_proxy
from pyscript import window
from pyscript.js_modules.ble import BLEDevice as _BLEDeviceJS

import lqrmpc as m

# The page sets these: hooks["log"](text) and hooks["changed"]() on (dis)connect.
hooks = {"log": print, "changed": lambda: None}


# -- Web Bluetooth in place of the library's BLE thread ------------------------
def _wasm_start_thread(self):
    if getattr(self, "_wasm_loop_started", False):
        return
    self._wasm_loop_started = True
    if not hasattr(self, "_js_ble_registry"):
        self._js_ble_registry = {}
    try:
        self.loop = asyncio.get_running_loop()
        self.loop_ready.set()
        asyncio.ensure_future(_wasm_worker_loop(self))
    except RuntimeError:
        pass


def _wasm_put_request(self, request):
    if not self.loop_ready.is_set():
        try:
            self.loop = asyncio.get_running_loop()
            self.loop_ready.set()
            if not hasattr(self, "_js_ble_registry"):
                self._js_ble_registry = {}
            asyncio.ensure_future(_wasm_worker_loop(self))
        except RuntimeError:
            return
    asyncio.ensure_future(self.async_put_request(request))


async def _wasm_worker_loop(worker):
    while True:
        try:
            req = await worker.request_queue.get()
            if req is None:
                break
            topic = req.get("topic")
            if topic == "send":
                js_ble = worker._js_ble_registry.get(id(req.get("msg")))
                message = req.get("msg2")
                if js_ble and message:
                    await js_ble.send(list(message))
            elif topic == "connect":
                cb = req.get("msg3")
                if cb:
                    cb(True)
            elif topic == "disconnect":
                js_ble = worker._js_ble_registry.pop(id(req.get("msg")), None)
                if js_ble:
                    js_ble.disconnect()
        except Exception as exc:
            hooks["log"](f"Worker error: {exc}")


bw.Worker.start_thread = _wasm_start_thread
bw.Worker.put_request = _wasm_put_request

SERVICE_UUID = "0000fd02-0000-1000-8000-00805f9b34fb"
WRITE_UUID = "0000fd02-0001-1000-8000-00805f9b34fb"
NOTIFY_UUID = "0000fd02-0002-1000-8000-00805f9b34fb"

NOTIFY_MS = 50  # the library's default is 100 ms (10 Hz); the control loop wants 20 Hz


UPDATE_URL = "https://code.legoeducation.com/"


def firmware_status(hub_version, library_version=RPC_VERSION):
    """'ok' for the latest firmware, 'old' if the hub needs updating, 'new' if the hub is ahead of this page."""
    hub_version, library_version = tuple(hub_version), tuple(library_version)
    if hub_version == library_version:
        return "ok"
    return "old" if hub_version < library_version else "new"


async def _check_firmware_version(device, timeout=3.0):
    """Only the latest firmware is supported.

    Returns True if the hub may be used. An older hub gets an alert telling the
    user to update at code.legoeducation.com, and False so the caller disconnects it.
    """
    msg = InfoRequest().Serialize()
    future = Future()
    device._pending_responses.setdefault(msg[0] + 1, deque()).append(future)
    device._ask("send", device.device, msg)
    try:
        payload = await asyncio.wait_for(asyncio.wrap_future(future), timeout=timeout)
    except asyncio.TimeoutError:
        hooks["log"](f"{device.label}: could not read the firmware version, so it was not checked. "
                     f"If it misbehaves, update your hardware at {UPDATE_URL}")
        return True
    info = InfoResponse.Deserialize(payload)
    version = (info.rpcMajor, info.rpcMinor, info.rpcBuild)
    status = firmware_status(version)
    if status == "old":
        text = (f"The {device.label.lower()} has older firmware than this page supports "
                f"(version {'.'.join(map(str, version))}, needs {'.'.join(map(str, RPC_VERSION))}).\n\n"
                f"Please update your hardware at {UPDATE_URL} and connect again.")
        hooks["log"](text.replace("\n\n", " "))
        window.alert(text)
        return False
    if status == "new":
        hooks["log"](f"{device.label}: the hub is newer than this page's LEGO library. "
                     f"If it misbehaves, the page needs an update.")
    return True


class WebDevice:
    def __init__(self, label):
        self.label = label
        self.connected = False
        self.js_ble = None

    async def connect_web(self):
        js_ble = _BLEDeviceJS.new()
        self._notification_proxy = create_proxy(
            lambda data: asyncio.ensure_future(self._on_notification(bytes(data.to_py()))))
        self._disconnect_proxy = create_proxy(self._on_disconnect)
        js_ble.callback = self._notification_proxy
        js_ble.disconnectCallback = self._disconnect_proxy
        if not await js_ble.connect(SERVICE_UUID, WRITE_UUID, NOTIFY_UUID):
            return False
        self.js_ble = js_ble
        self.connected = True
        self.device = self
        import legoeducation.basic_device as bd
        bd.my_worker._js_ble_registry[id(self)] = js_ble
        try:
            self.device_notification_request(NOTIFY_MS, blocking=False)
        except Exception:
            pass
        if not await _check_firmware_version(self):
            self.disconnect_web()
            return False
        hooks["log"](f"{self.label} connected.")
        hooks["changed"]()
        return True

    async def _on_notification(self, data):
        await self._device_callback(NOTIFY_UUID, data)

    def _on_disconnect(self, event):
        self.connected = False
        hooks["log"](f"{self.label} disconnected.")
        hooks["changed"]()

    def disconnect_web(self):
        if self.js_ble:
            self.js_ble.disconnect()
            self._on_disconnect(None)

    def send_command(self, packet):
        if self.js_ble is not None:
            asyncio.ensure_future(self.js_ble.send(list(packet)))


class DoubleMotorDevice(WebDevice, _DM):
    def __init__(self):
        _DM.__init__(self)
        WebDevice.__init__(self, "Motors")


class ColorSensorDevice(WebDevice, _CS):
    def __init__(self):
        _CS.__init__(self)
        WebDevice.__init__(self, "Sensor")


# -- the line follower ----------------------------------------------------------
DEFAULT_CAL = {
    "reflect_black": 12.0,   # reading fully over the tape
    "reflect_white": 85.0,   # reading fully over the background
    "e_max_mm": 6.0,         # half-width of the sensor's linear region
    "track_width_mm": 96.0,  # distance between wheel contact patches
    "wheel_max_mms": 400.0,  # wheel speed at motor speed 100%
    "dt": 0.05,              # control period
}


def curvature_estimate(omega, v, floor=20.0):
    """kappa ~= omega / v: the stand-in for track preview when there is no map."""
    return omega / max(v, floor)


class LineFollower:
    """Differential-drive robot with one downward-facing light sensor."""

    def __init__(self, motors, sensor, cal):
        self.motors, self.sensor, self.cal = motors, sensor, cal
        self.dt = cal["dt"]
        self._theta = 0.0
        self._e_prev = None
        self._v_prev = 0.0

    def start(self):
        self.motors.movement_set_acceleration(100, 100, blocking=False)
        self.motors.movement_set_end_state(le.MOTOR_END_STATE_BRAKE, blocking=False)

    def raw_reflection(self):
        r = self.sensor.sensor.reflection
        if r is None or (isinstance(r, float) and math.isnan(r)):
            return None
        return float(r)

    def normalized(self):
        """Raw reflection mapped to s in [0, 1]: 0 = fully on the tape, 1 = fully off."""
        raw = self.raw_reflection()
        if raw is None:
            return 0.5
        black, white = self.cal["reflect_black"], self.cal["reflect_white"]
        return min(1.0, max(0.0, (raw - black) / (white - black)))

    def read(self):
        """(e_mm, theta_rad, saturated). e > 0 means drifted off the line, onto the background."""
        e_max = self.cal["e_max_mm"]
        s = self.normalized()
        e = max(-e_max, min(e_max, 2.0 * e_max * (s - 0.5)))
        saturated = s <= 0.02 or s >= 0.98
        # Complementary estimate of theta: predict with the yaw rate we asked for,
        # correct with the observed drift rate e_dot = v * theta. The correction is
        # frozen while the sensor is pinned, because a pinned reading has zero slope.
        if self._e_prev is not None and not saturated and self._v_prev > 1.0:
            theta_meas = (e - self._e_prev) / (self.dt * self._v_prev)
            self._theta = 0.7 * self._theta + 0.3 * theta_meas
        self._e_prev = e
        return e, self._theta, saturated

    def drive(self, v_mms, omega_rads):
        left_mms, right_mms = m.wheel_speeds(v_mms, omega_rads, self.cal["track_width_mm"])
        left = int(round(m.to_percent(left_mms, self.cal["wheel_max_mms"])))
        right = int(round(m.to_percent(right_mms, self.cal["wheel_max_mms"])))
        self.motors.movement_move_tank(left, right, blocking=False)
        self._theta += self.dt * omega_rads
        self._v_prev = v_mms
        return left, right

    def stop(self):
        try:
            self.motors.movement_stop(blocking=False)
        except Exception as exc:
            hooks["log"](f"stop failed: {exc}")

    async def loop(self, duration_s, should_stop=lambda: False):
        """Yield (k, t) once per control period, holding the period as well as BLE allows."""
        loop = asyncio.get_running_loop()
        t0 = loop.time()
        k = 0
        while loop.time() - t0 <= duration_s and not should_stop():
            yield k, loop.time() - t0
            k += 1
            await asyncio.sleep(max(0.0, t0 + k * self.dt - loop.time()))


# -- controllers: (e, theta) -> (v, omega) --------------------------------------
def _mpc_speed(e, theta, kappa_hat, candidates, horizon, dt, e_max, v_ref, qe, qth, r, qv, pen=1e4):
    """The MPC's enumeration, with the curvature held at its current estimate.

    A real robot has no map, so the preview is "whatever turn I am holding now",
    not a true look-ahead. See the MPC notes, "Where does the preview come from?".
    """
    best_cost, best_v = float("inf"), candidates[0]
    for v in candidates:
        k_e, k_th = m.lqr_gains_discrete(float(v), dt, qe, qth, r)
        ep, thp, cost = e, theta, 0.0
        for _ in range(horizon):
            omega = -k_e * m.coerce(ep, e_max) - k_th * thp
            cost += (qe * ep ** 2 + qth * thp ** 2) * dt
            cost += pen * max(0.0, abs(ep) - e_max) ** 2 * dt
            ep, thp = m.step(ep, thp, v, omega, kappa_hat, dt)
        cost += qv * (v - v_ref) ** 2 * horizon * dt
        if cost < best_cost:
            best_cost, best_v = cost, v
    return best_v


def make_controller(name, p, cal):
    """Return ctl(e, theta) -> (v, omega) for 'bangbang', 'pd', 'lqr' or 'mpc'."""
    dt, e_max, v = cal["dt"], cal["e_max_mm"], p["v"]
    if name == "bangbang":
        return lambda e, th: (v, -p["omega_mag"] * (1.0 if e > 0 else -1.0))
    if name == "pd":
        return lambda e, th: (v, -p["kp"] * e - p["kd"] * th)
    if name == "lqr":
        k_e, k_th = m.lqr_gains_discrete(float(v), dt, p["qe"], p["qth"], p["r"])
        return lambda e, th: (v, -k_e * e - k_th * th)
    if name == "mpc":
        cands = tuple(c for c in m.CANDIDATES if c <= cal["wheel_max_mms"] * 0.95) or (v,)
        state = {"kappa": 0.0}

        def ctl(e, th):
            vv = _mpc_speed(e, th, state["kappa"], cands, int(p["n"]), dt, e_max, v,
                            p["qe"], p["qth"], p["r"], p["qv"])
            k_e, k_th = m.lqr_gains_discrete(float(vv), dt, p["qe"], p["qth"], p["r"])
            omega = -k_e * e - k_th * th
            state["kappa"] = 0.8 * state["kappa"] + 0.2 * curvature_estimate(omega, vv)
            return vv, omega
        return ctl
    raise ValueError(name)
