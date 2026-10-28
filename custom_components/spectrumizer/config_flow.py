"""Config flow for Spectrumizer."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    ALLOWED_WINDOW_SIZES,
    CONF_NAME as CONF_SENSOR_NAME,
    CONF_SAMPLING_RATE,
    CONF_SOURCE_ENTITY,
    CONF_WINDOW_SIZE,
    DEFAULT_NAME,
    DEFAULT_SAMPLING_RATE,
    DEFAULT_WINDOW_SIZE,
    DOMAIN,
    MAX_SAMPLING_RATE,
    MIN_SAMPLING_RATE,
)


def _schema(defaults: dict) -> vol.Schema:
    """Build the configuration schema."""
    return vol.Schema(
        {
            vol.Required(
                CONF_SOURCE_ENTITY, default=defaults.get(CONF_SOURCE_ENTITY)
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            vol.Required(
                CONF_SENSOR_NAME,
                default=defaults.get(CONF_SENSOR_NAME, DEFAULT_NAME),
            ): str,
            vol.Required(
                CONF_SAMPLING_RATE,
                default=defaults.get(CONF_SAMPLING_RATE, DEFAULT_SAMPLING_RATE),
            ): vol.All(vol.Coerce(float), vol.Range(min=MIN_SAMPLING_RATE, max=MAX_SAMPLING_RATE)),
            vol.Required(
                CONF_WINDOW_SIZE,
                default=defaults.get(CONF_WINDOW_SIZE, DEFAULT_WINDOW_SIZE),
            ): vol.In(ALLOWED_WINDOW_SIZES),
        }
    )


class SpectrumizerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle Spectrumizer setup."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Set up a source sensor and FFT parameters."""
        if user_input is not None:
            source = user_input[CONF_SOURCE_ENTITY]
            if self.hass.states.get(source) is None:
                return self.async_show_form(
                    step_id="user", data_schema=_schema(user_input),
                    errors={CONF_SOURCE_ENTITY: "entity_not_found"},
                )
            await self.async_set_unique_id(
                f"{source}_{user_input[CONF_WINDOW_SIZE]}_{user_input[CONF_SAMPLING_RATE]}"
            )
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input[CONF_SENSOR_NAME], data=user_input
            )
        return self.async_show_form(step_id="user", data_schema=_schema({}))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow."""
        return SpectrumizerOptionsFlow(config_entry)


class SpectrumizerOptionsFlow(config_entries.OptionsFlow):
    """Allow FFT settings to be changed."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle options."""
        current = {**self.config_entry.data, **self.config_entry.options}
        if user_input is not None:
            if self.hass.states.get(user_input[CONF_SOURCE_ENTITY]) is None:
                return self.async_show_form(
                    step_id="init", data_schema=_schema(user_input),
                    errors={CONF_SOURCE_ENTITY: "entity_not_found"},
                )
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(step_id="init", data_schema=_schema(current))
