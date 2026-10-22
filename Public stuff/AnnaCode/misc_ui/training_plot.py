"""
AnnaCode — training_plot.py

Training-mode plots: the recorded samples as dots (one panel per output, input on
the x axis) with the network's current response as a dark yellow line, plus the
loss curve. Click a dot to remove it.
"""
import json
import js
from pyscript.ffi import create_proxy
from pyscript.js_modules import Plotly

import state
import network_model
import transfer_plot
import training

DATA_ID = "train-data-plot"
LOSS_ID = "train-loss-plot"
LINE_COLOR = transfer_plot.LINE_COLOR
DOT_COLOR = "#0891b2"
PANEL_HEIGHT = 260
CONFIG = {"displayModeBar": False, "responsive": True}
STATIC = {"displayModeBar": False, "staticPlot": True, "responsive": True}

_panel_count = 0
_click_attached = False
_last_loss_len = -1
_click_proxy = None
_select_proxy = None
ORDER_SCALE = [[0, "#a5f3fc"], [1, "#164e63"]]   # light = recorded first, dark = recorded last

def _js(obj):
    return js.JSON.parse(json.dumps(obj))

def _on_point_click(pid):
    training.remove_point(int(pid))

def _on_selected(ids_json):
    training.remove_points(json.loads(ids_json))

def _redraw_data():
    global _panel_count, _click_attached, _click_proxy, _select_proxy
    el = state.get_id(DATA_ID)
    if not el or not state.inputs or not state.outputs or not state.layers:
        return
    last_neurons = state.layers[-1]["neurons"]
    outs = [(k, o) for k, o in enumerate(state.outputs) if k < len(last_neurons)]
    if not outs:
        return

    inp = state.inputs[0]
    data = state.training_data
    ids = [p["id"] for p in data]
    xs_data = [p["xs"].get(inp["id"], 0.0) for p in data]
    lo, hi = (min(xs_data), max(xs_data)) if xs_data else (-100.0, 100.0)
    pad = (hi - lo) * 0.1 or 1.0
    lo, hi = lo - pad, hi + pad
    sweep = [lo + (hi - lo) * k / 40 for k in range(41)]

    # Other inputs are held at their average recorded value (or live value if nothing is recorded)
    others = []
    for i in state.inputs[1:]:
        vals = [p["xs"].get(i["id"], 0.0) for p in data]
        others.append(sum(vals) / len(vals) if vals else state.input_values.get(i["id"], 0.0))

    # Live reading (where the robot is right now), drawn as a ring
    toggle = state.get_id("live-dot-toggle")
    live_on = bool(toggle and toggle.checked)
    x_live = training._read("in", inp["id"]) if live_on else None
    ys_live = {o["id"]: training._read("out", o["id"]) for _, o in outs} if live_on else {}

    traces = []
    layout = {
        "margin": {"l": 70, "r": 20, "t": 10, "b": 45},
        "grid": {"rows": len(outs), "columns": 1, "pattern": "independent", "roworder": "top to bottom", "ygap": 0.18},
        "showlegend": False,
        "dragmode": "select",
        "hovermode": "closest",
        "paper_bgcolor": "rgba(0,0,0,0)",
    }
    for panel, (k, out) in enumerate(outs, start=1):
        sfx = "" if panel == 1 else str(panel)
        label = transfer_plot._axis_label("out", out["id"], f"output {k + 1}")
        layout[f"xaxis{sfx}"] = {"zeroline": True}
        layout[f"yaxis{sfx}"] = {"title": {"text": label, "font": {"size": 12}}, "zeroline": True}
        axes = {"xaxis": f"x{sfx}", "yaxis": f"y{sfx}"}
        traces.append({**axes, "x": xs_data, "y": [p["ys"].get(out["id"], 0.0) for p in data],
                       "customdata": ids, "mode": "markers", "hovertemplate": "click to remove<extra></extra>",
                       "marker": {"color": list(range(len(data))), "colorscale": ORDER_SCALE, "cmin": 0,
                                  "cmax": max(1, len(data) - 1), "size": 8, "opacity": 0.85}})
        if live_on and x_live is not None and ys_live.get(out["id"]) is not None:
            traces.append({**axes, "x": [x_live], "y": [ys_live[out["id"]]], "mode": "markers", "hoverinfo": "skip",
                           "marker": {"symbol": "circle-open", "size": 18, "color": "#1a1d2e", "line": {"width": 3}}})
        fit = [network_model.evaluate_layers([x] + others)[-1][k][1] for x in sweep]
        traces.append({**axes, "x": sweep, "y": fit, "mode": "lines", "hoverinfo": "skip",
                       "line": {"color": LINE_COLOR, "width": 3}})
    layout[f"xaxis{len(outs) if len(outs) > 1 else ''}"]["title"] = {
        "text": transfer_plot._axis_label("in", inp["id"], inp["name"]), "font": {"size": 13}}

    el.style.height = f"{len(outs) * PANEL_HEIGHT + 60}px"
    if len(outs) != _panel_count:
        Plotly.purge(DATA_ID)   # drop stale axes (this also drops the click hook)
        _panel_count = len(outs)
        _click_attached = False
    Plotly.react(DATA_ID, _js(traces), _js(layout), _js(CONFIG))
    if not _click_attached:
        _click_proxy = create_proxy(_on_point_click)
        _select_proxy = create_proxy(_on_selected)
        Plotly.onPointClick(DATA_ID, _click_proxy)
        Plotly.onSelect(DATA_ID, _select_proxy)
        _click_attached = True

def _redraw_loss():
    global _last_loss_len
    if not state.get_id(LOSS_ID) or len(state.loss_history) == _last_loss_len:
        return
    _last_loss_len = len(state.loss_history)
    traces = [{"y": list(state.loss_history), "mode": "lines", "line": {"color": "#d97706", "width": 3}}]
    layout = {
        "margin": {"l": 55, "r": 20, "t": 10, "b": 45},
        "xaxis": {"title": {"text": "epoch", "font": {"size": 12}}},
        "yaxis": {"title": {"text": "loss", "font": {"size": 12}}, "rangemode": "tozero"},
        "showlegend": False,
        "paper_bgcolor": "rgba(0,0,0,0)",
    }
    Plotly.react(LOSS_ID, _js(traces), _js(layout), _js(STATIC))

def redraw():
    count = state.get_id("train-count")
    if count:
        count.textContent = f"{len(state.training_data)} points"
    undo_btn = state.get_id("undo-btn")
    if undo_btn:
        undo_btn.disabled = not state.undo_stack
    _redraw_data()
    _redraw_loss()
