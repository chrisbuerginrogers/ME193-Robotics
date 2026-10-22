"""
AnnaCode — training.py

Training mode: record (input, output) samples from the hardware while the
student pushes the robot around, clean the data up, then fit the network to it
with backprop. Training mode ignores activations (like Beginner), so every
neuron is a plain weighted sum and the activation derivative is 1.

Training happens in normalized space (stable gradients); the weights are folded
back into raw units after every epoch, so the displayed numbers, the fit line
and Run all see ordinary weights and biases.
"""
import asyncio
import json
import math

import js

import state
import Device
import sync

SAMPLE_PERIOD = 0.1   # seconds between recorded samples
EPOCH_PAUSE = 0.03    # lets the plots repaint between epochs
MAX_GRAD_NORM = 5.0

def set_status(text: str):
    el = state.get_id("train-status")
    if el:
        el.textContent = text

# ── Recording ───────────────────────────────────────────────────────────────

def _read(kind: str, item_id: int):
    """Live value at the device/channel chosen for this input ('in') or output ('out'); None if unavailable."""
    dev_el = state.get_id(f"dev-{kind}-{item_id}")
    chan_el = state.get_id(f"chan-{kind}-{item_id}")
    dev = Device.device_by_name(dev_el.value if dev_el else "")
    channel = chan_el.value if chan_el else ""
    try:
        return float(dev.state[channel]) if dev and channel else None
    except (KeyError, TypeError, ValueError):
        return None

def add_point(xs: dict, ys: dict):
    state.data_point_counter += 1
    state.training_data.append({"id": state.data_point_counter, "xs": dict(xs), "ys": dict(ys)})

MAX_UNDO = 100

def _remove_where(should_remove) -> int:
    """Remove every point the predicate matches, remembering them as one undo step."""
    removed = [p for p in state.training_data if should_remove(p)]
    if removed:
        state.training_data[:] = [p for p in state.training_data if not should_remove(p)]
        state.undo_stack.append(removed)
        del state.undo_stack[:-MAX_UNDO]
    return len(removed)

def remove_point(pid: int):
    _remove_where(lambda p: p["id"] == pid)

def remove_points(pids):
    ids = set(pids)
    n = _remove_where(lambda p: p["id"] in ids)
    if n:
        set_status(f"Removed {n} point{'s' if n != 1 else ''}. Undo brings them back.")

def clear_data(evt=None):
    _remove_where(lambda p: True)
    state.loss_history.clear()

def remove_zero_points(evt=None):
    """Drop samples where every output reads zero -- the robot had paused."""
    oids = [o["id"] for o in state.outputs]
    n = _remove_where(lambda p: not any(abs(p["ys"].get(oid, 0.0)) > 1e-9 for oid in oids))
    set_status(f"Removed {n} zero-speed points.")

def undo(evt=None):
    if not state.undo_stack:
        return
    batch = state.undo_stack.pop()
    state.training_data.extend(batch)
    state.training_data.sort(key=lambda p: p["id"])   # ids grow with recording order
    set_status(f"Restored {len(batch)} point{'s' if len(batch) != 1 else ''}.")

# ── Save / load ─────────────────────────────────────────────────────────────

def _label(kind: str, item: dict, fallback: str) -> str:
    import transfer_plot
    return transfer_plot._axis_label(kind, item["id"], fallback)

def dataset_to_json() -> str:
    """Rows are positional: x[i] belongs to the i-th input, y[j] to the j-th output."""
    in_ids = [i["id"] for i in state.inputs]
    out_ids = [o["id"] for o in state.outputs]
    return json.dumps({
        "format": "annacode-dataset", "version": 1,
        "inputs": [_label("in", i, i["name"]) for i in state.inputs],
        "outputs": [_label("out", o, f"output {k + 1}") for k, o in enumerate(state.outputs)],
        "rows": [{"x": [p["xs"].get(i, 0.0) for i in in_ids], "y": [p["ys"].get(o, 0.0) for o in out_ids]}
                 for p in state.training_data],
    })

def load_dataset(text: str) -> int:
    """Append the saved rows to the current data. Returns how many were added (0 on a mismatch)."""
    try:
        data = json.loads(text)
        rows = data["rows"]
        n_in, n_out = len(data["inputs"]), len(data["outputs"])
    except (ValueError, KeyError, TypeError):
        set_status("That doesn't look like a saved AnnaCode dataset.")
        return 0
    if n_in != len(state.inputs) or n_out != len(state.outputs):
        set_status(f"That file has {n_in} input(s) and {n_out} output(s); your network has "
                   f"{len(state.inputs)} and {len(state.outputs)}.")
        return 0
    in_ids = [i["id"] for i in state.inputs]
    out_ids = [o["id"] for o in state.outputs]
    for r in rows:
        add_point(dict(zip(in_ids, r["x"])), dict(zip(out_ids, r["y"])))
    set_status(f"Loaded {len(rows)} points.")
    return len(rows)

def save_dataset(evt=None):
    if not state.training_data:
        set_status("Nothing to save yet.")
        return
    blob = js.Blob.new([dataset_to_json()], js.JSON.parse('{"type": "application/json"}'))
    url = js.URL.createObjectURL(blob)
    a = js.document.createElement("a")
    a.href = url
    a.download = "annacode-data.json"
    a.click()
    js.URL.revokeObjectURL(url)
    set_status(f"Saved {len(state.training_data)} points.")

def _all_chosen() -> bool:
    for kind, items in (("in", state.inputs), ("out", state.outputs)):
        for it in items:
            dev_el = state.get_id(f"dev-{kind}-{it['id']}")
            chan_el = state.get_id(f"chan-{kind}-{it['id']}")
            if not (dev_el and dev_el.value and chan_el and chan_el.value):
                return False
    return True

async def _record_loop():
    while state.is_recording:
        xs = {i["id"]: _read("in", i["id"]) for i in state.inputs}
        ys = {o["id"]: _read("out", o["id"]) for o in state.outputs}
        if None not in xs.values() and None not in ys.values():
            add_point(xs, ys)
        await asyncio.sleep(SAMPLE_PERIOD)

def start_recording():
    if not _all_chosen():
        set_status("Pick a device and a value for every input and output first.")
        return
    state.is_recording = True
    btn = state.get_id("record-btn")
    btn.textContent = "Stop recording"
    btn.classList.add("recording")
    set_status("Recording… push the robot through its paces.")
    asyncio.ensure_future(_record_loop())

def stop_recording():
    state.is_recording = False
    btn = state.get_id("record-btn")
    if btn:
        btn.textContent = "Record"
        btn.classList.remove("recording")

def toggle_recording(evt=None):
    if state.is_recording:
        stop_recording()
        set_status(f"{len(state.training_data)} points recorded.")
    else:
        start_recording()

# ── Normalization (same scheme as the Network Trainer page) ─────────────────

def _col_stats(vals: list[float]):
    if len(vals) < 2:
        return 0.0, 1.0
    mean = sum(vals) / len(vals)
    return mean, math.sqrt(sum((v - mean) ** 2 for v in vals) / len(vals)) or 1.0

def _dataset_stats():
    x_stats = {i["id"]: _col_stats([p["xs"].get(i["id"], 0.0) for p in state.training_data]) for i in state.inputs}
    y_stats = {o["id"]: _col_stats([p["ys"].get(o["id"], 0.0) for p in state.training_data]) for o in state.outputs}
    return x_stats, y_stats

def _fold_input_scale(neurons, input_ids, x_stats, reverse: bool):
    for n in neurons:
        bias_adjust, new_weights = 0.0, []
        for i, w in enumerate(n["weights"]):
            mean, std = x_stats.get(input_ids[i], (0.0, 1.0)) if i < len(input_ids) else (0.0, 1.0)
            if reverse:
                new_weights.append(w * std)
                bias_adjust += w * mean
            else:
                new_weights.append(w / std)
                bias_adjust += w * mean / std
        n["bias"] = n["bias"] + bias_adjust if reverse else n["bias"] - bias_adjust
        n["weights"] = new_weights

def _to_normalized(x_stats, y_stats):
    out_ids = [o["id"] for o in state.outputs]
    for idx, n in enumerate(state.layers[-1]["neurons"]):
        if idx < len(out_ids):
            mean, std = y_stats.get(out_ids[idx], (0.0, 1.0))
            n["bias"] = (n["bias"] - mean) / std
            n["weights"] = [w / std for w in n["weights"]]
    _fold_input_scale(state.layers[0]["neurons"], [i["id"] for i in state.inputs], x_stats, reverse=True)

def _to_raw(x_stats, y_stats):
    _fold_input_scale(state.layers[0]["neurons"], [i["id"] for i in state.inputs], x_stats, reverse=False)
    out_ids = [o["id"] for o in state.outputs]
    for idx, n in enumerate(state.layers[-1]["neurons"]):
        if idx < len(out_ids):
            mean, std = y_stats.get(out_ids[idx], (0.0, 1.0))
            n["bias"] = mean + std * n["bias"]
            n["weights"] = [w * std for w in n["weights"]]

# ── Backprop ────────────────────────────────────────────────────────────────

def _clip(v: float) -> float:
    return max(-MAX_GRAD_NORM, min(MAX_GRAD_NORM, v))

def _forward(xs: list[float]):
    """Linear forward pass; returns (final outputs, the source values that fed each layer)."""
    sources, vals = [], list(xs)
    for layer in state.layers:
        sources.append(vals)
        vals = [sum(n["weights"][i] * vals[i] for i in range(min(len(n["weights"]), len(vals)))) + n["bias"]
                for n in layer["neurons"]]
    return vals, sources

def _train_epoch(lr: float, x_stats, y_stats) -> float:
    """One pass over the data, one averaged update per weight. Returns the mean squared error
    (in normalized units). Weights must already be in normalized space."""
    in_ids = [i["id"] for i in state.inputs]
    out_ids = [o["id"] for o in state.outputs]
    w_grads = [[[0.0] * len(n["weights"]) for n in l["neurons"]] for l in state.layers]
    b_grads = [[0.0] * len(l["neurons"]) for l in state.layers]
    total, terms = 0.0, 0

    for p in state.training_data:
        xs = [(p["xs"].get(iid, 0.0) - x_stats[iid][0]) / x_stats[iid][1] for iid in in_ids]
        final, sources = _forward(xs)
        deltas = [0.0] * len(final)
        for k, oid in enumerate(out_ids):
            if k >= len(final):
                break
            err = final[k] - (p["ys"].get(oid, 0.0) - y_stats[oid][0]) / y_stats[oid][1]
            total += err ** 2
            terms += 1
            deltas[k] = 2.0 * err
        for li in reversed(range(len(state.layers))):
            neurons = state.layers[li]["neurons"]
            src = sources[li]
            back = [0.0] * len(src)
            for i, n in enumerate(neurons):
                d = deltas[i] if i < len(deltas) else 0.0
                for j in range(min(len(n["weights"]), len(src))):
                    w_grads[li][i][j] += d * src[j]
                    back[j] += d * n["weights"][j]
                b_grads[li][i] += d
            deltas = back

    count = len(state.training_data)
    for li, layer in enumerate(state.layers):
        for i, n in enumerate(layer["neurons"]):
            n["weights"] = [w - lr * _clip(g / count) for w, g in zip(n["weights"], w_grads[li][i])]
            n["bias"] -= lr * _clip(b_grads[li][i] / count)
    return total / terms if terms else 0.0

def get_learning_rate() -> float:
    el = state.get_id("train-lr")
    try:
        return float(el.value)
    except (TypeError, ValueError):
        return 0.05

async def train(epochs: int):
    if state.is_training:
        return
    if not state.training_data or not state.layers or not state.outputs:
        set_status("Record some data first.")
        return
    state.is_training = True
    lr = get_learning_rate()
    x_stats, y_stats = _dataset_stats()
    set_status("Training…")
    for _ in range(epochs):
        _to_normalized(x_stats, y_stats)
        loss = _train_epoch(lr, x_stats, y_stats)
        _to_raw(x_stats, y_stats)
        state.loss_history.append(loss)
        for idx in range(len(state.layers)):
            sync.rebuild_layer_eq_html(idx)
        await asyncio.sleep(EPOCH_PAUSE)
    state.is_training = False
    set_status(f"Trained {epochs} epoch{'s' if epochs != 1 else ''}. Loss {state.loss_history[-1]:.3f}")
