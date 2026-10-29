"""Live FFT spectrum sensor."""

from __future__ import annotations

import asyncio
from collections import deque
from datetime import datetime, timedelta, timezone
import logging
import math

import numpy as np

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    CONF_SAMPLING_RATE,
    CONF_SOURCE_ENTITY,
    CONF_WINDOW_SIZE,
    DEFAULT_NAME,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up the FFT spectrum sensor."""
    settings = {**entry.data, **entry.options}
    async_add_entities([SpectrumSensor(hass, entry, settings)])


class SpectrumSensor(SensorEntity):
    """Expose the dominant frequency and full one-sided FFT spectrum."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_native_unit_of_measurement = "Hz"
    _attr_icon = "mdi:chart-bell-curve"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, settings: dict) -> None:
        self.hass = hass
        self._entry = entry
        self._source = settings[CONF_SOURCE_ENTITY]
        self._sampling_rate = float(settings[CONF_SAMPLING_RATE])
        self._window_size = int(settings[CONF_WINDOW_SIZE])
        self._attr_name = settings.get(CONF_NAME, DEFAULT_NAME)
        self._attr_unique_id = f"{entry.entry_id}_dominant_frequency"
        self._samples: deque[float] = deque(maxlen=self._window_size)
        self._native_value = None
        self._frequencies: list[float] = []
        self._magnitudes: list[float] = []
        self._history: deque[dict] = deque(maxlen=80)
        # Keep recent FFT frames for the waterfall/spectrogram view.
        self._history: deque[dict] = deque(maxlen=80)
        self._peak_magnitude = None
        self._sample_timer = None
        self._last_source_value = None
        self._attr_extra_state_attributes = {
            "source_entity": self._source,
            "sampling_rate_hz": self._sampling_rate,
            "window_size": self._window_size,
            "frequency_resolution_hz": round(self._sampling_rate / self._window_size, 6),
            "samples_collected": 0,
            "ready": False,
            "frequencies": [],
            "magnitudes": [],
            "history": [],
            "history": [],
        }

    @property
    def native_value(self):
        """Return the dominant frequency in Hz."""
        return self._native_value

    async def async_added_to_hass(self) -> None:
        """Start regular sampling."""
        self._sample_timer = async_track_time_interval(
            self.hass,
            self._sample_source,
            timedelta(seconds=1.0 / self._sampling_rate),
        )

    async def async_will_remove_from_hass(self) -> None:
        """Stop sampling timer."""
        if self._sample_timer:
            self._sample_timer()
            self._sample_timer = None

    @callback
    def _sample_source(self, now) -> None:
        """Sample the current source state at the configured rate."""
        state = self.hass.states.get(self._source)
        if state is None or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            self._samples.clear()
            self._native_value = None
            self._set_attributes(ready=False)
            self.async_write_ha_state()
            return
        try:
            value = float(state.state)
            if not math.isfinite(value):
                raise ValueError("Source value is not finite")
        except (TypeError, ValueError, OverflowError):
            self._samples.clear()
            self._native_value = None
            self._set_attributes(ready=False)
            self.async_write_ha_state()
            return

        self._last_source_value = value
        self._samples.append(value)
        if len(self._samples) < self._window_size:
            self._set_attributes(ready=False)
            self.async_write_ha_state()
            return

        self.hass.async_create_task(self._calculate_spectrum(list(self._samples)))

    async def _calculate_spectrum(self, samples: list[float]) -> None:
        """Calculate the FFT off the event loop."""
        try:
            frequencies, magnitudes = await self.hass.async_add_executor_job(
                self._fft, samples
            )
        except Exception:
            _LOGGER.exception("FFT calculation failed for %s", self._source)
            return

        if not magnitudes:
            return
        # Ignore the DC component at 0 Hz when choosing the dominant frequency.
        peak_index = max(range(1, len(magnitudes)), key=magnitudes.__getitem__) if len(magnitudes) > 1 else 0
        self._native_value = round(frequencies[peak_index], 6)
        self._peak_magnitude = round(magnitudes[peak_index], 6)
        self._frequencies = [round(float(f), 6) for f in frequencies]
        self._magnitudes = [round(float(m), 6) for m in magnitudes]
        self._history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "magnitudes": self._magnitudes,
        })
        self._set_attributes(ready=True)
        self.async_write_ha_state()

    def _fft(self, samples: list[float]) -> tuple[list[float], list[float]]:
        """Return one-sided frequency bins and normalized magnitudes."""
        signal = np.asarray(samples, dtype=float)
        signal = signal - np.mean(signal)
        # Hann window reduces spectral leakage.
        signal = signal * np.hanning(len(signal))
        n = len(signal)
        spectrum = np.fft.rfft(signal)
        magnitudes = np.abs(spectrum) * (2.0 / n)
        if len(magnitudes):
            magnitudes[0] /= 2.0
            if n % 2 == 0:
                magnitudes[-1] /= 2.0
        frequencies = np.fft.rfftfreq(n, d=1.0 / self._sampling_rate)
        return frequencies.tolist(), magnitudes.tolist()

    def _set_attributes(self, ready: bool) -> None:
        """Update attributes consumed by the Lovelace card."""
        self._attr_extra_state_attributes = {
            "source_entity": self._source,
            "sampling_rate_hz": self._sampling_rate,
            "window_size": self._window_size,
            "frequency_resolution_hz": round(self._sampling_rate / self._window_size, 6),
            "samples_collected": len(self._samples),
            "ready": ready,
            "peak_magnitude": self._peak_magnitude,
            "frequencies": self._frequencies if ready else [],
            "magnitudes": self._magnitudes if ready else [],
            "history": list(self._history),
            "history": list(self._history),
        }
