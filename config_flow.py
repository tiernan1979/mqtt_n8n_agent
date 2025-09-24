import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from .const import (
    DOMAIN,
    CONF_N8N_HOST, CONF_N8N_PORT,
    CONF_WEBHOOK_LIST_MODELS, CONF_WEBHOOK_CHAT, CONF_WEBHOOK_STREAM,
    CONF_MQTT_HOST, CONF_MQTT_PORT, CONF_MQTT_USERNAME, CONF_MQTT_PASSWORD, CONF_MQTT_TLS,
    CONF_CONTEXT_WINDOW, CONF_MAX_HISTORY, CONF_KEEP_ALIVE,
    CONF_SHOW_THINKING,
    DEFAULT_MQTT_PORT, DEFAULT_N8N_PORT,
    DEFAULT_CONTEXT_WINDOW, DEFAULT_MAX_HISTORY, DEFAULT_KEEP_ALIVE, DEFAULT_SHOW_THINKING,
)

class MqttN8nAgentConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MQTT + n8n conversation agent."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is None:
            schema = vol.Schema({
                vol.Required(CONF_N8N_HOST): str,
                vol.Optional(CONF_N8N_PORT, default=DEFAULT_N8N_PORT): int,
                vol.Required(CONF_WEBHOOK_LIST_MODELS): str,
                vol.Required(CONF_WEBHOOK_CHAT): str,
                vol.Optional(CONF_WEBHOOK_STREAM, default=""): str,
                vol.Required(CONF_MQTT_HOST): str,
                vol.Optional(CONF_MQTT_PORT, default=DEFAULT_MQTT_PORT): int,
                vol.Optional(CONF_MQTT_USERNAME, default=""): str,
                vol.Optional(CONF_MQTT_PASSWORD, default=""): str,
                vol.Optional(CONF_MQTT_TLS, default=False): bool,
                vol.Optional(CONF_CONTEXT_WINDOW, default=DEFAULT_CONTEXT_WINDOW): int,
                vol.Optional(CONF_MAX_HISTORY, default=DEFAULT_MAX_HISTORY): int,
                vol.Optional(CONF_KEEP_ALIVE, default=DEFAULT_KEEP_ALIVE): int,
                vol.Optional(CONF_SHOW_THINKING, default=DEFAULT_SHOW_THINKING): bool,
            })
            return self.async_show_form(step_id="user", data_schema=schema)

        # Validate user_input if needed (e.g. ping n8n, check webhooks endpoints)
        # For now, assume valid.

        return self.async_create_entry(
            title=f"n8n @ {user_input[CONF_N8N_HOST]}",
            data=user_input
        )
