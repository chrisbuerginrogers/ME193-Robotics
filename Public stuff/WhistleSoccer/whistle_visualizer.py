"""Live view of the whistle detector, so you can *see* what it's hearing
and tune it against workshop noise instead of guessing at thresholds.

Run this on its own (no robot needed). It runs the exact same
WhistleDetector used by whistle_drive.py, and shows two things stacked:

  Top:    a spectrogram of the raw mic input, with the detector's actual
          (narrow) passband shaded. A whistle shows up as a thin, bright,
          steady line inside the shaded strip. Workshop noise (talking,
          machinery, footsteps) shows up as broad, messy blobs -- most of
          that energy now falls *outside* the shaded strip and gets
          filtered out before it can trigger anything.

  Bottom: the dominance ratio over time (how much of the sound is inside
          that narrow band vs. the whole signal), with the trigger
          threshold marked. A hammer strike can spike this briefly, but
          the duration gate (shown as the line turning red) only fires
          after it holds continuously for MIN_DURATION seconds -- which
          random loud noises don't do, but a sustained whistle does.

Tune CENTER_FREQ/BANDWIDTH/DOMINANCE_THRESHOLD/MIN_DURATION below (and then
carry the same values into whistle_drive.py) until this cleanly separates
your whistle from the room.
"""

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import sounddevice as sd

from mic_select import choose_input_device
from whistle_detector import WhistleDetector

SAMPLE_RATE = 44100
BLOCK_SIZE = 1024
HISTORY_SECONDS = 6
DISPLAY_MAX_HZ = 8000  # most workshop/voice/whistle content is below this

# Keep these in sync with whistle_drive.py while you tune.
CENTER_FREQ = 3000.0        # Hz -- your whistle's pitch
BANDWIDTH = 200.0           # Hz -- total pass width (+/- 100 Hz here)
DOMINANCE_THRESHOLD = 0.6   # filtered/raw RMS ratio required
MIN_DURATION = 0.4          # seconds the ratio must hold continuously

detector = WhistleDetector(
    sample_rate=SAMPLE_RATE,
    center_freq=CENTER_FREQ,
    bandwidth=BANDWIDTH,
    dominance_threshold=DOMINANCE_THRESHOLD,
    min_duration=MIN_DURATION,
)

DEVICE = choose_input_device()
if DEVICE is None:
    print("Using system default input device.")
else:
    print(f"Using input device: {sd.query_devices(DEVICE)['name']}")

freqs = np.fft.rfftfreq(BLOCK_SIZE, 1 / SAMPLE_RATE)
n_cols = int(HISTORY_SECONDS * SAMPLE_RATE / BLOCK_SIZE)
spectrogram = np.full((len(freqs), n_cols), -60.0)  # dB floor
dominance_history = np.zeros(n_cols)

status = {"whistle": False}


def on_audio(indata, frames, time_info, status_flags):
    block = indata[:, 0]

    # Spectrogram is purely visual -- the actual decision comes from detector.process().
    windowed = block * np.hanning(len(block))
    spectrum = np.abs(np.fft.rfft(windowed))
    spectrogram[:, :-1] = spectrogram[:, 1:]
    spectrogram[:, -1] = 20 * np.log10(spectrum + 1e-6)

    status["whistle"] = detector.process(block)
    dominance_history[:-1] = dominance_history[1:]
    dominance_history[-1] = detector.dominance


fig, (ax_spec, ax_dom) = plt.subplots(
    2, 1, figsize=(10, 7), sharex=True, gridspec_kw={"height_ratios": [3, 1]}
)

img = ax_spec.imshow(
    spectrogram,
    origin="lower",
    aspect="auto",
    extent=[-HISTORY_SECONDS, 0, freqs[0], freqs[-1]],
    cmap="inferno",
    vmin=-60,
    vmax=20,
)
ax_spec.set_ylim(0, DISPLAY_MAX_HZ)
ax_spec.set_ylabel("Frequency (Hz)")
band_lo, band_hi = CENTER_FREQ - BANDWIDTH / 2, CENTER_FREQ + BANDWIDTH / 2
ax_spec.axhspan(band_lo, band_hi, color="cyan", alpha=0.25)
ax_spec.text(-HISTORY_SECONDS + 0.1, band_hi + 150, "detector passband", color="cyan")
title = ax_spec.set_title("listening...")

time_axis = np.linspace(-HISTORY_SECONDS, 0, n_cols)
(dom_line,) = ax_dom.plot(time_axis, dominance_history, color="black")
ax_dom.axhline(DOMINANCE_THRESHOLD, color="red", linestyle="--", linewidth=1, label="trigger threshold")
ax_dom.set_ylim(0, 1.1)
ax_dom.set_ylabel("Dominance ratio")
ax_dom.set_xlabel("Seconds ago")
ax_dom.legend(loc="upper left", fontsize=8)


def update(frame):
    img.set_data(spectrogram)
    dom_line.set_ydata(dominance_history)
    dom_line.set_color("red" if status["whistle"] else "black")

    label = "WHISTLE DETECTED" if status["whistle"] else "listening"
    title.set_text(
        f"{label}   dominance={detector.dominance:.2f} (need >={DOMINANCE_THRESHOLD})   "
        f"held {detector.seconds_above:.2f}s / {MIN_DURATION}s"
    )
    title.set_color("red" if status["whistle"] else "black")
    return img, dom_line, title


ani = animation.FuncAnimation(fig, update, interval=50, cache_frame_data=False)

print("Showing live detector view. Blow your whistle and watch the bottom "
      "trace cross the red line and hold. Close the window to stop.")
with sd.InputStream(
    channels=1,
    samplerate=SAMPLE_RATE,
    blocksize=BLOCK_SIZE,
    callback=on_audio,
    device=DEVICE,
):
    plt.show()
