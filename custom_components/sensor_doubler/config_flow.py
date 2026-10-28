"""Config flow for Sensor Doubler."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import CONF_FACTOR, CONF_SOURCE_ENTITY, DEFAULT_FACTOR, DEFAULT_NAME, DOMAIN


class SensorDoublerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Sensor Doubler."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Configure the source entity, output name, and multiplier."""
        errors = {}
        if user_input is not None:
            source = user_input[CONF_SOURCE_ENTITY]
            if source not in self.hass.states.async_entity_ids("sensor"):
                errors[CONF_SOURCE_ENTITY] = "entity_not_found"
            else:
                await self.async_set_unique_id(
                    f"{source}_{user_input[CONF_NAME].strip().lower()}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_NAME].strip(),
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_SOURCE_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_FACTOR, default=DEFAULT_FACTOR): vol.Coerce(float),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow handler."""
        return SensorDoublerOptionsFlow(config_entry)


class SensorDoublerOptionsFlow(config_entries.OptionsFlow):
    """Allow editing source, name and factor after setup."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle options."""
        errors = {}
        if user_input is not None:
            source = user_input[CONF_SOURCE_ENTITY]
            if source not in self.hass.states.async_entity_ids("sensor"):
                errors[CONF_SOURCE_ENTITY] = "entity_not_found"
            else:
                return self.async_create_entry(title="", data=user_input)

        current = {**self.config_entry.data, **self.config_entry.options}
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SOURCE_ENTITY,
                    default=current[CONF_SOURCE_ENTITY],
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(
                    CONF_NAME, default=current.get(CONF_NAME, DEFAULT_NAME)
                ): str,
                vol.Required(
                    CONF_FACTOR, default=current.get(CONF_FACTOR, DEFAULT_FACTOR)
                ): vol.Coerce(float),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
