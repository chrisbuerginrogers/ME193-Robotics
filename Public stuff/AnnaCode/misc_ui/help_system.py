"""
AnnaCode — help_system.py

Just-in-time help: a "?" popover on each part of the network (short text in
Beginner, longer text in Advanced) and one-time hint banners triggered by what
the student does. All wording lives in HELP / HINTS below.
"""
from pyscript import document
from pyscript.ffi import create_proxy

import state

# id -> (basic text, extra text added in Advanced)
HELP = {
    "neuron": (
        "A neuron is a simple rule: output = weight x input + bias. With 2 and 20 it computes 2 x sensor + 20.",
        "The weight is the slope and the bias is the intercept. Everything a network knows is stored in these numbers "
        "(its parameters), not in a lookup table. A neuron with several inputs adds one weight x input term for each.",
    ),
    "input": (
        "Pick a device (like a color sensor) and which of its values to read. That reading is x, the input to the neurons.",
        "More inputs give the network more to work with; each one gets its own weight in the first layer.",
    ),
    "output": (
        "Pick a motor and which value to control. The neuron's result is sent here, for example as a motor speed.",
        "Outputs pair up with the last layer's neurons in order: the 1st output with the 1st neuron, and so on. "
        "Extra neurons are greyed out until they have an output.",
    ),
    "plot": (
        "This line is your rule: for any sensor value along the bottom, it shows the motor speed up the side. "
        "The dot is where you are right now.",
        "Each neuron gets a solid line (after its activation) and a dashed line (before it). Pick which input to sweep "
        "with the x-axis menu; any other inputs are held at their live values.",
    ),
    "layer": (
        "",
        "Layers build complex features out of simpler ones. More neurons in a layer makes the network wider, more layers "
        "makes it deeper. Layers do not necessarily mean fewer neurons: a 5-point star is 10 line segments, or one "
        "triangle reused 5 times.",
    ),
}

HINTS = {
    "outputs": "Tip: if two motors are mirrored, one neuron needs a negative weight so they spin in the same direction.",
    "activation": "An activation makes the line bend. That is what stops layers from being merged into a single line.",
}
_seen = set()

def close_help(evt=None):
    state.get_id("help-popover").classList.add("hidden")

def open_help(help_id: str, anchor):
    basic, extra = HELP[help_id]
    text = basic if state.beginner_mode or not extra else (basic + " " + extra).strip()
    state.get_id("help-body").textContent = text
    pop = state.get_id("help-popover")
    pop.classList.remove("hidden")
    r = anchor.getBoundingClientRect()
    left = max(8, min(r.left, document.documentElement.clientWidth - pop.offsetWidth - 8))
    pop.style.left = f"{left}px"
    pop.style.top = f"{r.bottom + 8}px"

def show_hint(key: str):
    """Show a dismissible banner once per page load."""
    if key in _seen:
        return
    _seen.add(key)
    state.get_id("hint-text").textContent = HINTS[key]
    state.get_id("hint-banner").classList.remove("hidden")

def close_hint(evt=None):
    state.get_id("hint-banner").classList.add("hidden")

def _on_document_click(evt):
    btn = evt.target.closest(".help-btn")
    if btn and btn.dataset.help in HELP:
        open_help(btn.dataset.help, btn)
    elif not evt.target.closest("#help-popover"):
        close_help()

def setup():
    document.addEventListener("click", create_proxy(_on_document_click))
