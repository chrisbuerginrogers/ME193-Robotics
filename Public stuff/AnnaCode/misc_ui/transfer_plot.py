"""
AnnaCode — transfer_plot.py

Two plots of the network's response to one swept input (any other inputs are
held at their current values; a dot marks the live point):

  Beginner -- one dark yellow line: first input vs first output, shown to the
              right of the network.
  Advanced -- below the run button: one panel per hidden layer plus one panel
              per output. Every neuron gets a solid line (after its activation)
              and a dashed line (before it).
"""
import asyncio
import json
import js
from pyscript.js_modules import Plotly

import state
import network_model

PLOT_ID = "transfer-plot"
ADV_ID = "adv-plot"
ADV_SELECT_ID = "adv-x-select"
LINE_COLOR = "#b8860b"   # dark yellow
POINTS = 41
PANEL_HEIGHT = 240
HIDDEN_COLORS = ["#2563eb", "#7c3aed", "#db2777", "#059669", "#dc2626", "#0891b2", "#9333ea", "#65a30d"]
CONFIG = {"displayModeBar": False, "staticPlot": True, "responsive": True}

_adv_panel_count = 0
_adv_select_key = ""

def _js(obj):
    return js.JSON.parse(json.dumps(obj))

def _axis_label(kind: str, item_id: int, fallback: str) -> str:
    """What the student picked for this input/output, e.g. 'Reflection (Color Sensor)'."""
    dev_el = state.get_id(f"dev-{kind}-{item_id}")
    chan_el = state.get_id(f"chan-{kind}-{item_id}")
    dev = dev_el.value if dev_el else ""
    chan = chan_el.value if chan_el else ""
    if chan and dev:
        return f"{chan} ({dev})"
    return chan or dev or fallback

def _sweep_axis(base: list[float], idx: int):
    span = max(100.0, abs(base[idx]))
    return [-span + 2 * span * k / (POINTS - 1) for k in range(POINTS)]

# ── Beginner ─────────────────────────────────────────────────────────────────

def redraw_beginner():
    if not state.inputs or not state.outputs or not state.layers:
        return
    if not state.get_id(PLOT_ID):
        return

    inp, out = state.inputs[0], state.outputs[0]
    base = [state.input_values.get(i["id"], 0.0) for i in state.inputs]
    xs = _sweep_axis(base, 0)

    def y_at(x):
        vals = network_model.evaluate([x] + base[1:])
        return vals[0] if vals else 0.0

    traces = [
        {"x": xs, "y": [y_at(x) for x in xs], "mode": "lines",
         "line": {"color": LINE_COLOR, "width": 3}, "hoverinfo": "skip"},
        {"x": [base[0]], "y": [y_at(base[0])], "mode": "markers",
         "marker": {"color": "#1a1d2e", "size": 10}, "hoverinfo": "skip"},
    ]
    layout = {
        "margin": {"l": 55, "r": 20, "t": 10, "b": 45},
        "xaxis": {"title": {"text": _axis_label("in", inp["id"], inp["name"]), "font": {"size": 13}}, "zeroline": True},
        "yaxis": {"title": {"text": _axis_label("out", out["id"], "output"), "font": {"size": 13}},
                  "zeroline": True},
        "showlegend": False,
        "paper_bgcolor": "rgba(0,0,0,0)",
    }
    Plotly.react(PLOT_ID, _js(traces), _js(layout), _js(CONFIG))

# ── Advanced ─────────────────────────────────────────────────────────────────

def _sync_x_select():
    """Keep the x-axis dropdown in step with the inputs; returns the chosen input index."""
    global _adv_select_key
    sel = state.get_id(ADV_SELECT_ID)
    names = [_axis_label("in", i["id"], i["name"]) for i in state.inputs]
    key = "|".join(names)
    if key != _adv_select_key:
        prev = int(sel.value) if sel.value else 0
        sel.innerHTML = "".join(f'<option value="{k}">{n}</option>' for k, n in enumerate(names))
        sel.value = str(min(prev, len(names) - 1))
        _adv_select_key = key
    return min(int(sel.value or 0), len(names) - 1)

def redraw_advanced():
    global _adv_panel_count
    el = state.get_id(ADV_ID)
    if not el or not state.inputs or not state.outputs or not state.layers:
        return

    xi = _sync_x_select()
    base = [state.input_values.get(i["id"], 0.0) for i in state.inputs]
    xs = _sweep_axis(base, xi)
    _update_collapse_note([_axis_label("in", i["id"], i["name"]) for i in state.inputs])

    def sweep(x):
        vals = list(base)
        vals[xi] = x
        return network_model.evaluate_layers(vals)

    sweeps = [sweep(x) for x in xs]
    live = sweep(base[xi])

    # panels: [(y-axis title, [(legend name, colour, layer idx, neuron idx)])]
    panels = []
    last = len(state.layers) - 1
    color_n = 0
    for li, layer in enumerate(state.layers[:last]):
        entries = []
        for j in range(len(layer["neurons"])):
            entries.append((f"L{li + 1} n{j + 1}", HIDDEN_COLORS[color_n % len(HIDDEN_COLORS)], li, j))
            color_n += 1
        panels.append((f"Layer {li + 1}", entries))
    for j, out in enumerate(state.outputs):
        if j < len(state.layers[last]["neurons"]):
            label = _axis_label("out", out["id"], f"output {j + 1}")
            panels.append((label, [(f"{label} (n{j + 1})", LINE_COLOR, last, j)]))

    traces, layout = [], {
        "margin": {"l": 70, "r": 20, "t": 10, "b": 45},
        "grid": {"rows": len(panels), "columns": 1, "pattern": "independent",
                 "roworder": "top to bottom", "ygap": 0.18},
        "showlegend": True,
        "legend": {"font": {"size": 11}},
        "paper_bgcolor": "rgba(0,0,0,0)",
    }
    for k, (title, entries) in enumerate(panels, start=1):
        sfx = "" if k == 1 else str(k)
        layout[f"xaxis{sfx}"] = {"zeroline": True}
        layout[f"yaxis{sfx}"] = {"title": {"text": title, "font": {"size": 12}}, "zeroline": True}
        for name, color, li, j in entries:
            group = f"{li}-{j}"
            common = {"x": xs, "mode": "lines", "legendgroup": group,
                      "xaxis": f"x{sfx}", "yaxis": f"y{sfx}", "hoverinfo": "skip"}
            traces.append({**common, "y": [s[li][j][0] for s in sweeps], "showlegend": False,
                           "line": {"color": color, "width": 1.5, "dash": "dash"}})
            traces.append({**common, "y": [s[li][j][1] for s in sweeps], "name": name,
                           "line": {"color": color, "width": 3}})
            traces.append({"x": [base[xi]], "y": [live[li][j][1]], "mode": "markers",
                           "legendgroup": group, "showlegend": False,
                           "xaxis": f"x{sfx}", "yaxis": f"y{sfx}", "hoverinfo": "skip",
                           "marker": {"color": color, "size": 9, "line": {"color": "#fff", "width": 1.5}}})
    layout[f"xaxis{len(panels) if len(panels) > 1 else ''}"]["title"] = {
        "text": _axis_label("in", state.inputs[xi]["id"], state.inputs[xi]["name"]), "font": {"size": 13}}

    el.style.height = f"{len(panels) * PANEL_HEIGHT + 60}px"
    if len(panels) != _adv_panel_count:
        Plotly.purge(ADV_ID)   # drop stale axes when panels come or go
        _adv_panel_count = len(panels)
    Plotly.react(ADV_ID, _js(traces), _js(layout), _js(CONFIG))

def _fmt(v: float) -> str:
    return f"{v:.2f}".rstrip("0").rstrip(".") or "0"

def _update_collapse_note(xi_names: list[str]):
    """With no activation anywhere, stacked layers collapse into one line per
    output -- show that line. With an activation they cannot be merged."""
    note = state.get_id("collapse-note")
    if len(state.layers) < 2:
        note.innerHTML = ""
        return
    if any(l["act_fn"] for l in state.layers):
        note.textContent = "Because of the activation, these layers can't be merged into a single line."
        return
    n = len(state.inputs)
    zero = network_model.evaluate([0.0] * n)
    lines = []
    for j, out in enumerate(state.outputs):
        if j >= len(zero):
            break
        terms = ""
        for i in range(n):
            e = [0.0] * n
            e[i] = 1.0
            m = network_model.evaluate(e)[j] - zero[j]
            if abs(m) > 1e-9:
                terms += f" {'-' if m < 0 else '+'} {_fmt(abs(m))}·{xi_names[i]}" if terms else f"{_fmt(m)}·{xi_names[i]}"
        b = zero[j]
        if abs(b) > 1e-9 or not terms:
            terms += f" {'-' if b < 0 else '+'} {_fmt(abs(b))}" if terms else _fmt(b)
        lines.append(f"<b>{_axis_label('out', out['id'], f'output {j + 1}')} = {terms}</b>")
    note.innerHTML = ("With no activation, your layers collapse into one line per output: "
                      + "; ".join(lines) + ". An activation lets the lines bend so they can't be merged.")

async def run_loop():
    while True:
        try:
            if state.beginner_mode:
                redraw_beginner()
            else:
                redraw_advanced()
        except Exception as e:
            print("transfer plot: " + str(e))
        await asyncio.sleep(0.3)
