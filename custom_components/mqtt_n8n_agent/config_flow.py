import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import (
    DOMAIN,
    CONF_CONTEXT_WINDOW,
    CONF_MAX_HISTORY,
    CONF_KEEP_ALIVE,
    CONF_SHOW_THINKING,
)

_LOGGER = logging.getLogger(__name__)

class MqttN8nAgentConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for mqtt_n8n_agent."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step of the config flow."""
        errors = {}

        if user_input is not None:
            # You can put validation logic here if needed
            # e.g., test connection to MQTT broker or validate values
            try:
                # Example: Simple validation or call an async test function
                # await self.hass.async_add_executor_job(your_sync_test_function, user_input)

                # If all good, create entry:
                return self.async_create_entry(title="mqtt_n8n_agent", data=user_input)
            except Exception as err:
                _LOGGER.error("Error validating input: %s", err)
                errors["base"] = "cannot_connect"

        # Show form to the user
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CONTEXT_WINDOW, default=5): int,
                    vol.Required(CONF_MAX_HISTORY, default=10): int,
                    vol.Required(CONF_KEEP_ALIVE, default=True): bool,
                    vol.Required(CONF_SHOW_THINKING, default=False): bool,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return MqttN8nAgentOptionsFlow(config_entry)


class MqttN8nAgentOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for mqtt_n8n_agent."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}

        if user_input is not None:
            # Optionally validate inputs here
            try:
                # If validation needed
                return self.async_create_entry(title="", data=user_input)
            except Exception as err:
                _LOGGER.error("Error in options flow: %s", err)
                errors["base"] = "invalid_options"

        # Use current config values as defaults
        data = self.config_entry.options or self.config_entry.data

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CONTEXT_WINDOW, default=data.get(CONF_CONTEXT_WINDOW, 5)): int,
                    vol.Required(CONF_MAX_HISTORY, default=data.get(CONF_MAX_HISTORY, 10)): int,
                    vol.Required(CONF_KEEP_ALIVE, default=data.get(CONF_KEEP_ALIVE, True)): bool,
                    vol.Required(CONF_SHOW_THINKING, default=data.get(CONF_SHOW_THINKING, False)): bool,
                }
            ),
            errors=errors,
        )
