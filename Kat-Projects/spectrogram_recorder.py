"""Record 5 seconds of audio from the default microphone and plot its spectrogram.

Requires: sounddevice, numpy, matplotlib, scipy
Install with: pip install sounddevice numpy matplotlib scipy
"""

import argparse

import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
from scipy import signal

DURATION = 5  # seconds
SAMPLE_RATE = 44100  # Hz
MAX_FREQ = 4000  # Hz; top of the plot -- covers singing and whistling

# Note labeling (--label)
NOTE_NAMES = ["C", "C#/Db", "D", "D#/Eb", "E", "F", "F#/Gb", "G", "G#/Ab", "A", "A#/Bb", "B"]
MIN_NOTE_FREQ = 80  # Hz; ignore mains hum and rumble below this
SILENCE_DB = 30  # frames this far below the loudest frame are treated as silence
MIN_NOTE_DURATION = 0.1  # seconds; shorter blips are not labeled


def record_audio(duration, sample_rate):
    print(f"Recording {duration}s of audio at {sample_rate} Hz...")
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype="float64")
    sd.wait()
    print("Recording complete.")
    return audio.flatten()


def freq_to_note(freq):
    """Classify a frequency into the nearest equal-tempered note, e.g. 440 -> 'A4'."""
    # MIDI numbering: A4 = 440 Hz = note 69, 12 semitones per octave, C4 = 60
    midi = int(round(69 + 12 * np.log2(freq / 440.0)))
    octave = midi // 12 - 1
    return f"{NOTE_NAMES[midi % 12]}{octave}"


def detect_notes(frequencies, times, Sxx):
    """Return a list of (start_time, end_time, freq, note_name) for sustained pitches."""
    usable = frequencies >= MIN_NOTE_FREQ
    band_freqs, band = frequencies[usable], Sxx[usable]
    bin_width = frequencies[1] - frequencies[0]

    peak_idx = np.argmax(band, axis=0)
    peak_power = band[peak_idx, np.arange(band.shape[1])]
    loud_enough = 10 * np.log10(peak_power + 1e-12) > 10 * np.log10(peak_power.max() + 1e-12) - SILENCE_DB

    # Classify each frame's dominant frequency, refined with parabolic interpolation
    # since the raw FFT bins (~21 Hz) are coarser than a semitone at low pitches
    frame_notes = []
    frame_freqs = []
    for col, i in enumerate(peak_idx):
        if not loud_enough[col]:
            frame_notes.append(None)
            frame_freqs.append(None)
            continue
        freq = band_freqs[i]
        if 0 < i < len(band_freqs) - 1:
            a, b, c = np.log(band[i - 1:i + 2, col] + 1e-12)
            denom = a - 2 * b + c
            if denom != 0:
                freq += 0.5 * (a - c) / denom * bin_width
        frame_notes.append(freq_to_note(freq))
        frame_freqs.append(freq)

    # Group consecutive frames with the same note into segments
    notes = []
    start = 0
    for col in range(1, len(frame_notes) + 1):
        if col == len(frame_notes) or frame_notes[col] != frame_notes[start]:
            name = frame_notes[start]
            if name is not None and times[col - 1] - times[start] >= MIN_NOTE_DURATION:
                freq = float(np.median(frame_freqs[start:col]))
                notes.append((times[start], times[col - 1], freq, name))
            start = col
    return notes


def plot_spectrogram(audio, sample_rate, save_path=None, label=False):
    # Longer window gives finer frequency resolution (~21 Hz bins) for the low range we care about
    frequencies, times, Sxx = signal.spectrogram(audio, fs=sample_rate, nperseg=2048, noverlap=1536)

    keep = frequencies <= MAX_FREQ
    frequencies, Sxx = frequencies[keep], Sxx[keep]

    plt.figure(figsize=(10, 6))
    plt.pcolormesh(times, frequencies, 10 * np.log10(Sxx + 1e-12), shading="gouraud")
    plt.ylabel("Frequency [Hz]")
    plt.xlabel("Time [s]")
    plt.title("Spectrogram")
    plt.colorbar(label="Power [dB]")
    if label:
        notes = detect_notes(frequencies, times, Sxx)
        for start, end, freq, name in notes:
            plt.hlines(freq, start, end, colors="white", linewidth=1.5)
            plt.annotate(name, xy=((start + end) / 2, freq), xytext=(0, 6), textcoords="offset points",
                         ha="center", va="bottom", fontsize=9, color="black",
                         bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.8))
        print("Detected notes: " + (", ".join(n[3] for n in notes) or "none"))
    plt.tight_layout()
    if save_path:
        # Save before show(), since closing the window discards the figure
        plt.savefig(save_path, dpi=150)
        print(f"Saved spectrogram to {save_path}")
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Record audio and plot its spectrogram.")
    parser.add_argument("--runnow", action="store_true", help="Skip the prompt and start recording immediately.")
    parser.add_argument("--save", metavar="FILENAME", help="Save the spectrogram image to this file (e.g. out.png).")
    parser.add_argument("--label", action="store_true", help="Label the spectrogram with the detected musical notes.")
    args = parser.parse_args()

    if not args.runnow:
        input("Press Enter to start recording...")

    audio = record_audio(DURATION, SAMPLE_RATE)
    plot_spectrogram(audio, SAMPLE_RATE, save_path=args.save, label=args.label)
