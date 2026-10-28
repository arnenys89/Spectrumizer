"""Sensor platform for Sensor Doubler."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_FACTOR,
    CONF_SOURCE_ENTITY,
    DEFAULT_FACTOR,
    DEFAULT_NAME,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the doubled sensor."""
    settings = {**entry.data, **entry.options}
    async_add_entities([DoubledSensor(hass, entry, settings)])


class DoubledSensor(SensorEntity):
    """Sensor entity whose value is source state multiplied by a factor."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, settings: dict) -> None:
        self.hass = hass
        self._entry = entry
        self._source_entity = settings[CONF_SOURCE_ENTITY]
        self._factor = float(settings.get(CONF_FACTOR, DEFAULT_FACTOR))
        self._attr_name = settings.get(CONF_NAME, DEFAULT_NAME)
        self._attr_unique_id = f"{entry.entry_id}_scaled"
        self._attr_extra_state_attributes = {
            "source_entity": self._source_entity,
            "multiplier": self._factor,
        }
        self._source_unit = None
        self._native_value = None
        self._unsub = None

    @property
    def native_value(self):
        """Return source value multiplied by the configured factor."""
        return self._native_value

    @property
    def native_unit_of_measurement(self):
        """Keep the source sensor's unit when available."""
        state = self.hass.states.get(self._source_entity)
        if state is not None:
            return state.attributes.get("unit_of_measurement")
        return self._source_unit

    async def async_added_to_hass(self) -> None:
        """Subscribe to source updates and populate initial state."""
        self._unsub = async_track_state_change_event(
            self.hass, [self._source_entity], self._async_source_changed
        )
        self._update_from_source()

    async def async_will_remove_from_hass(self) -> None:
        """Remove source-state listener."""
        if self._unsub:
            self._unsub()
            self._unsub = None

    @callback
    def _async_source_changed(self, event) -> None:
        """Handle changes to the source sensor."""
        self._update_from_source()

    @callback
    def _update_from_source(self) -> None:
        """Refresh the calculated value from the source sensor."""
        state = self.hass.states.get(self._source_entity)
        if state is None or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            self._native_value = None
            self.async_write_ha_state()
            return

        try:
            self._native_value = float(state.state) * self._factor
        except (TypeError, ValueError, OverflowError):
            self._native_value = None

        self._source_unit = state.attributes.get("unit_of_measurement")
        self._attr_extra_state_attributes = {
            "source_entity": self._source_entity,
            "source_value": state.state,
            "multiplier": self._factor,
        }
        self.async_write_ha_state()
