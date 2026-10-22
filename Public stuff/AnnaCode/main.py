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
    caption.textContent = presets.PRESETS[key]["caption"] if key else ""
    caption.classList.toggle("hidden", not key)

@when("click", "#help-close-btn")
def _on_help_close(evt):
    help_system.close_help()

@when("click", "#hint-close-btn")
def _on_hint_close(evt):
    help_system.close_hint()

def set_mode(mode: str):
    state.mode = mode
    state.beginner_mode = mode != "advanced"   # Beginner and Training hide the activations and ignore them
    wrap = state.get_id("page-wrap")
    wrap.classList.toggle("beginner", state.beginner_mode)
    wrap.classList.toggle("training", mode == "training")
    for m in ("beginner", "advanced", "training"):
        state.get_id(f"mode-{m}-btn").classList.toggle("active", m == mode)
    if mode == "training":
        network_actions.match_last_layer_to_outputs()
    else:
        training.stop_recording()
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
    help_system.setup()
    set_mode(state.mode)
    asyncio.ensure_future(transfer_plot.run_loop())
    zoom.apply_zoom()
    zoom.setup_resize_observer()
    arrows.schedule_redraw(150)

boot()
