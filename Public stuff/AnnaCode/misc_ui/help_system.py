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

# Training-mode buttons (Training shows the short text only, so all the wording goes in the first slot)
HELP.update({
    "record": ("Press Record, then push the robot through its paces by hand. About ten times a second it saves the sensor "
               "reading and the motor value(s) as one dot. Press again to stop.", ""),
    "undo": ("Brings back the points you just removed (or cleared). You can undo several times.", ""),
    "remove_zero": ("Deletes recorded points where every motor reads zero. Those are the moments the robot paused.", ""),
    "clear": ("Deletes all recorded points and the loss history. Undo can bring the points back.", ""),
    "save": ("Downloads the recorded points as a file so you can keep a good run or share it.", ""),
    "load": ("Adds the points from a saved file to the ones you have. The file needs the same number of inputs and outputs "
             "as your network. Press Clear first to replace instead of add.", ""),
    "example": ("Fills the plot with a noisy example curve (a line, V, sine wave and more) to practise on. It is either this "
                "or Record: it is only available while there is no data. A hint below tells you how to shape the network.", ""),
    "randomize": ("Resets every weight and bias to small random numbers and clears the loss plot, so you can train from scratch.", ""),
    "act_toggle": ("Show or hide the activation functions and the layer and neuron controls. Activations are applied "
                   "whether or not they are visible; the label lists any that are on while hidden. An activation lets the "
                   "line bend, so compare the fit with and without one.", ""),
    "step": ("One pass over all your points, nudging the weight and bias a little to shrink the error.", ""),
    "train": ("Fifty passes in a row. Watch the green line move toward the dots and the loss curve fall.", ""),
    "lr": ("How big each nudge is. Too small and it learns slowly; too big and the loss bounces or grows. "
           "Start at 0.05 and lower it if the loss rises.", ""),
    "live": ("Shows where the robot is right now as a ring: sensor reading across, motor value up. Drive it again and see "
             "whether the ring lands on the green line.", ""),
    "dataplot": ("Each dot is one recorded sample, light for early and dark for late. The green line is what your network "
                 "predicts. Click a dot, or drag a box around several, to remove them.", ""),
    "loss": ("How far the line is from the dots on average. It should fall as you train and flatten out when learning is "
             "done. If it rises, lower the learning rate.", ""),
})

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
    # Controls tagged data-tip="id" get the same text as a mouseover tooltip
    for el in document.querySelectorAll("[data-tip]"):
        el.title = HELP[el.dataset.tip][0]
