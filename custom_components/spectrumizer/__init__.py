"""Home Assistant integration for live FFT spectrum analysis."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError

from .const import (
    ALLOWED_WINDOW_SIZES,
    CONF_HISTORY_BINS,
    CONF_SAMPLING_RATE,
    CONF_SOURCE_ENTITY,
    CONF_WINDOW_SIZE,
    DOMAIN,
    MAX_HISTORY_BINS,
    MAX_SAMPLING_RATE,
    MIN_HISTORY_BINS,
    MIN_SAMPLING_RATE,
    PLATFORMS,
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up Spectrumizer services."""

    async def async_set_options(call: ServiceCall) -> None:
        source = call.data[CONF_SOURCE_ENTITY]
        entry = next(
            (
                item
                for item in hass.config_entries.async_entries(DOMAIN)
                if (item.options.get(CONF_SOURCE_ENTITY) or item.data.get(CONF_SOURCE_ENTITY)) == source
            ),
            None,
        )
        if entry is None:
            raise HomeAssistantError(f"No Spectrumizer config entry found for {source}")

        new_options = {
            **entry.options,
            **entry.data,
            CONF_SOURCE_ENTITY: source,
            CONF_SAMPLING_RATE: call.data[CONF_SAMPLING_RATE],
            CONF_WINDOW_SIZE: call.data[CONF_WINDOW_SIZE],
            CONF_HISTORY_BINS: call.data[CONF_HISTORY_BINS],
        }
        hass.config_entries.async_update_entry(entry, options=new_options)

    hass.services.async_register(
        DOMAIN,
        "set_options",
        async_set_options,
        schema=vol.Schema(
            {
                vol.Required(CONF_SOURCE_ENTITY): str,
                vol.Required(CONF_SAMPLING_RATE): vol.All(
                    vol.Coerce(float),
                    vol.Range(min=MIN_SAMPLING_RATE, max=MAX_SAMPLING_RATE),
                ),
                vol.Required(CONF_WINDOW_SIZE): vol.In(ALLOWED_WINDOW_SIZES),
                vol.Required(CONF_HISTORY_BINS): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_HISTORY_BINS, max=MAX_HISTORY_BINS),
                ),
            }
        ),
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Spectrumizer from a config entry."""
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Spectrumizer."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload integration when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
