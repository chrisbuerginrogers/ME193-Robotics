"""
AnnaCode — transfer_plot.py

Beginner-mode plot under the run button: the first input on the x axis, the
first output on the y axis, and the network's response as a dark yellow line
(any other inputs are held at their current values). A dot marks the live point.
"""
import asyncio
import json
import js
from pyscript.js_modules import Plotly

import state
import network_model

PLOT_ID = "transfer-plot"
LINE_COLOR = "#b8860b"   # dark yellow
POINTS = 41

def _axis_label(kind: str, item_id: int, fallback: str) -> str:
    el = state.get_id(f"chan-{kind}-{item_id}")
    return el.value if el and el.value else fallback

def redraw():
    if not state.beginner_mode or not state.inputs or not state.outputs or not state.layers:
        return
    if not state.get_id(PLOT_ID):
        return

    inp, out = state.inputs[0], state.outputs[0]
    base = [state.input_values.get(i["id"], 0.0) for i in state.inputs]
    span = max(100.0, abs(base[0]))
    xs = [-span + 2 * span * k / (POINTS - 1) for k in range(POINTS)]

    def y_at(x):
        vals = network_model.evaluate([x] + base[1:])
        return vals[0] if vals else 0.0

    ys = [y_at(x) for x in xs]
    traces = [
        {"x": xs, "y": ys, "mode": "lines", "line": {"color": LINE_COLOR, "width": 3}, "hoverinfo": "skip"},
        {"x": [base[0]], "y": [y_at(base[0])], "mode": "markers",
         "marker": {"color": "#1a1d2e", "size": 10}, "hoverinfo": "skip"},
    ]
    layout = {
        "margin": {"l": 55, "r": 20, "t": 10, "b": 45},
        "xaxis": {"title": {"text": inp["name"], "font": {"size": 13}}, "zeroline": True},
        "yaxis": {"title": {"text": _axis_label("out", out["id"], "output"), "font": {"size": 13}},
                  "zeroline": True},
        "showlegend": False,
        "paper_bgcolor": "rgba(0,0,0,0)",
    }
    Plotly.react(PLOT_ID, js.JSON.parse(json.dumps(traces)), js.JSON.parse(json.dumps(layout)),
                 js.JSON.parse(json.dumps({"displayModeBar": False, "staticPlot": True})))

async def run_loop():
    while True:
        try:
            redraw()
        except Exception as e:
            print("transfer plot: " + str(e))
        await asyncio.sleep(0.3)
