"""Whistle detection: bandpass filter + dominance ratio + duration gate.

Usage:
    detector = WhistleDetector(sample_rate=44100, center_freq=3000, bandwidth=200)
    ...
    is_whistle = detector.process(chunk)  # chunk = 1-D float array, one audio block
"""

import numpy as np
from scipy.signal import butter, sosfilt, sosfilt_zi


class WhistleDetector:
    """Detects a sustained whistle tone in a stream of audio chunks.

    Each call to process() runs three checks, in order:

    1. Bandpass filter -- the raw chunk is passed through a strict IIR
       bandpass filter centered on `center_freq` with total width
       `bandwidth` (so `center_freq` +/- `bandwidth/2`). The filter keeps
       state (`self._zi`) across calls, so it filters the audio as one
       continuous stream instead of restarting (and glitching) at every
       chunk boundary.

    2. Dominance ratio -- RMS(filtered chunk) / RMS(raw chunk). This is
       "what fraction of this chunk's total loudness lives inside the
       whistle band". A pure tone at center_freq scores near 1.0; broadband
       noise (a hammer strike, a drill, speech) spreads its energy across
       the whole spectrum and scores low even if it's loud.

    3. Duration gate -- the dominance ratio must stay >= dominance_threshold
       *continuously* for at least min_duration seconds before process()
       returns True. This rejects brief broadband transients that might
       momentarily spike the ratio, and matches how an actual whistle
       sounds: a held tone, not an instant.
    """

    def __init__(
        self,
        sample_rate,
        center_freq=3000.0,       # Hz -- tune this to your whistle's pitch
        bandwidth=200.0,          # Hz -- total pass width (+/- bandwidth/2)
        dominance_threshold=0.6,  # filtered/raw RMS ratio required to count as "whistling"
        min_duration=0.4,         # seconds the ratio must hold continuously to trigger
        filter_order=4,
    ):
        self.sample_rate = sample_rate
        self.dominance_threshold = dominance_threshold
        self.min_duration = min_duration

        nyquist = sample_rate / 2
        low = max((center_freq - bandwidth / 2) / nyquist, 1e-6)
        high = min((center_freq + bandwidth / 2) / nyquist, 1 - 1e-6)
        if not low < high:
            raise ValueError("bandwidth/center_freq produce an empty passband")

        self._sos = butter(filter_order, [low, high], btype="bandpass", output="sos")
        self._zi = sosfilt_zi(self._sos) * 0.0  # filter's internal state, starts at rest

        # Public, read-only-in-spirit: last computed values, handy for a UI
        # (see whistle_visualizer.py) that wants to show *why* it did or
        # didn't trigger, without recomputing anything.
        self.dominance = 0.0
        self.seconds_above = 0.0  # how long the dominance ratio has held, continuously

    def process(self, chunk):
        """Feed one chunk of raw audio (1-D array-like). Returns True the
        moment the duration gate is satisfied, False otherwise."""
        chunk = np.asarray(chunk, dtype=np.float64)

        filtered, self._zi = sosfilt(self._sos, chunk, zi=self._zi)

        raw_rms = np.sqrt(np.mean(chunk ** 2)) + 1e-12
        band_rms = np.sqrt(np.mean(filtered ** 2))
        self.dominance = band_rms / raw_rms

        chunk_seconds = len(chunk) / self.sample_rate
        if self.dominance >= self.dominance_threshold:
            self.seconds_above += chunk_seconds
        else:
            self.seconds_above = 0.0

        return self.seconds_above >= self.min_duration

    def reset(self):
        """Clear filter and duration-gate state (e.g. after a trigger, or
        when switching to a different audio source)."""
        self._zi = sosfilt_zi(self._sos) * 0.0
        self.dominance = 0.0
        self.seconds_above = 0.0
