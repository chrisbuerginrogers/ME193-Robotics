"""
AnnaCode — main.py
PyScript 2026.3.1

Structure: independent columns, chained through any number of layers.
  Inputs  -- each with its own device/channel + plot
  Layers  -- each layer has its own column of neurons AND its own
             activation block (function + optional custom piecewise editor).
             layers[0]'s neurons take a weighted sum of the raw inputs;
             every later layer's neurons take a weighted sum of the
             *previous* layer's activated neuron outputs.
             "+ Layer" (between the last activation block and the outputs)
             appends a brand new neuron layer + activation block.
  Outputs -- each with its own device/channel + plot. Outputs pair up with
             the LAST layer's neurons positionally (1st output <-> 1st
             neuron of the last layer, etc). Any neuron in the last layer
             beyond the current number of outputs is shown greyed out
             until a matching output exists.
  A column (inputs / a layer's neurons / outputs) can never be emptied --
  the last remaining item's delete button is hidden.

This file only wires up the static @when(...) handlers and boots the app --
see state.py, activations.py, network_model.py, templates.py, arrows.py,
sync.py, bindings.py, activation_editor.py, network_actions.py, zoom.py,
and Device.py for the actual implementation.
"""
from pyscript import when

import state
import Device
import arrows
import network_actions
import activation_editor
import zoom
import transfer_plot
import help_system
import presets
import training
import asyncio

# ── Static wiring ──────────────────────────────────────────────────────────────

@when("click", "#add-device-btn")
async def _on_add_device(evt):
    await Device.create_new_device()

@when("click", "#add-input-btn")
def _on_add_input(evt):
    network_actions.add_input()

@when("click", "#add-layer-btn")
def _on_add_layer(evt):
    network_actions.add_layer()

@when("click", "#add-output-btn")
def _on_add_output(evt):
    network_actions.add_output()
    if len(state.outputs) == 2:
        help_system.show_hint("outputs")

@when("click", "#play-btn")
def _on_play(evt):
    network_actions.play_network()

@when("click", "#stop-btn")
def _on_stop(evt):
    network_actions.stop_network()

@when("click", "#close-act-help-btn")
def _on_close_act_help(evt):
    activation_editor.close_act_help()

@when("click", "#zoom-out-btn")
def _on_zoom_out(evt):
    zoom.zoom_out()

@when("click", "#zoom-in-btn")
def _on_zoom_in(evt):
    zoom.zoom_in()

@when("change", "#debug-toggle")
def _on_debug_toggle(evt):
    state.debug_mode = evt.target.checked
    arrows.redraw_arrows()

@when("change", "#preset-select")
def _on_preset(evt):
    key = evt.target.value
    caption = state.get_id("preset-caption")
    presets.load(key)
    state.get_id("preset-caption-text").innerHTML = presets.PRESETS[key]["caption"] if key else ""
    caption.classList.toggle("hidden", not key)   # loading an example always brings the hint back, even if it was closed

@when("click", "#preset-caption-close")
def _on_caption_close(evt):
    state.get_id("preset-caption").classList.add("hidden")

@when("click", "#train-hint-close")
def _on_train_hint_close(evt):
    state.train_hint_closed = True

@when("click", "#help-close-btn")
def _on_help_close(evt):
    help_system.close_help()

@when("click", "#hint-close-btn")
def _on_hint_close(evt):
    help_system.close_hint()

def update_activation_toggle():
    """Label for the Training-mode toggle; when hidden, still says which activations are active."""
    btn = state.get_id("show-activation-btn")
    names = dict((v, k) for k, v in state.ACTIVATION_OPTIONS)
    active = sorted({names.get(l["act_fn"], l["act_fn"]) for l in state.layers if l["act_fn"]})
    if state.show_activation:
        btn.textContent = "− Activation layers"
    else:
        btn.textContent = "+ Activation layers" + (f" (on: {', '.join(active)})" if active else "")

@when("click", "#show-activation-btn")
def _on_toggle_activation(evt):
    state.show_activation = not state.show_activation
    set_mode(state.mode)

@when("click", "#randomize-btn")
def _on_randomize(evt):
    training.randomize_weights()

def set_mode(mode: str):
    state.mode = mode
    state.beginner_mode = mode != "advanced"           # Beginner and Training use the simplified layout
    state.use_activations = mode != "beginner"         # Beginner ignores activations; the others apply them
    state.show_activation_blocks = mode == "advanced" or (mode == "training" and state.show_activation)
    wrap = state.get_id("page-wrap")
    wrap.classList.toggle("beginner", state.beginner_mode)
    wrap.classList.toggle("training", mode == "training")
    wrap.classList.toggle("show-act", mode == "training" and state.show_activation)
    update_activation_toggle()
    for m in ("beginner", "advanced", "training"):
        state.get_id(f"mode-{m}-btn").classList.toggle("active", m == mode)
    if mode == "training":
        network_actions.match_last_layer_to_outputs()
    else:
        training.stop_recording()
        if not state.is_running:   # drop the live-preview numbers so they don't linger on the arrows
            for d in (state.input_values, state.neuron_pre_values, state.neuron_post_values, state.output_values):
                d.clear()
    # Layout changed (columns hidden/shown) -- re-measure the arrows
    arrows.schedule_redraw()

@when("click", "#mode-beginner-btn")
def _on_mode_beginner(evt):
    set_mode("beginner")

@when("click", "#mode-advanced-btn")
def _on_mode_advanced(evt):
    set_mode("advanced")

@when("click", "#mode-training-btn")
def _on_mode_training(evt):
    set_mode("training")

@when("click", "#record-btn")
def _on_record(evt):
    training.toggle_recording()

@when("click", "#remove-zero-btn")
def _on_remove_zero(evt):
    training.remove_zero_points()

@when("click", "#clear-data-btn")
def _on_clear_data(evt):
    training.clear_data()

@when("change", "#example-select")
def _on_example(evt):
    training.add_example(evt.target.value)

@when("click", "#undo-btn")
def _on_undo(evt):
    training.undo()

@when("click", "#save-data-btn")
def _on_save(evt):
    training.save_dataset()

@when("click", "#load-data-btn")
def _on_load_click(evt):
    state.get_id("load-file").click()

@when("change", "#load-file")
async def _on_load_file(evt):
    file = evt.target.files.item(0)
    if file:
        training.load_dataset(await file.text())
    evt.target.value = ""   # so the same file can be loaded again

@when("click", "#step-btn")
async def _on_step(evt):
    await training.train(1)

@when("click", "#train-btn")
async def _on_train(evt):
    await training.train(50)

# ── Boot ───────────────────────────────────────────────────────────────────────

def boot():
    state.get_id("loading-splash").style.display = "none"
    state.get_id("page-wrap").style.display = "flex"

    # one of each on load: 1 input, 1 layer (1 neuron + activation), 1 output
    network_actions.add_input()
    network_actions.add_layer()
    network_actions.add_output()

    presets.populate_select(state.get_id("preset-select"))
    training.populate_examples(state.get_id("example-select"))
    help_system.setup()
    set_mode(state.mode)
    asyncio.ensure_future(transfer_plot.run_loop())
    zoom.apply_zoom()
    zoom.setup_resize_observer()
    arrows.schedule_redraw(150)

boot()
