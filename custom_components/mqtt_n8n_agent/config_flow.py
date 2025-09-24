import logging

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class MqttN8nAgentConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MQTT + n8n conversation agent."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        if user_input is None:
            # Lazy import heavy libs here to avoid blocking import warning
            import voluptuous as vol
            import aiohttp

            from .const import (
                CONF_N8N_HOST, CONF_N8N_PORT,
                CONF_WEBHOOK_LIST_MODELS, CONF_WEBHOOK_CHAT, CONF_WEBHOOK_STREAM,
                CONF_MQTT_HOST, CONF_MQTT_PORT, CONF_MQTT_USERNAME, CONF_MQTT_PASSWORD, CONF_MQTT_TLS,
                CONF_CONTEXT_WINDOW, CONF_MAX_HISTORY, CONF_KEEP_ALIVE,
                CONF_SHOW_THINKING,
                DEFAULT_MQTT_PORT, DEFAULT_N8N_PORT,
                DEFAULT_CONTEXT_WINDOW, DEFAULT_MAX_HISTORY, DEFAULT_KEEP_ALIVE, DEFAULT_SHOW_THINKING,
            )

            schema = vol.Schema({
                vol.Required(CONF_N8N_HOST): str,
                vol.Optional(CONF_N8N_PORT, default=DEFAULT_N8N_PORT): int,
                vol.Optional(CONF_WEBHOOK_LIST_MODELS, default=""): str,
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

        # If webhook_list_models provided, try to fetch models
        models = None
        if user_input.get("webhook_list_models"):
            import aiohttp
            try:
                url = user_input["webhook_list_models"]
                async with aiohttp.ClientSession() as session:
                    resp = await session.get(url, timeout=10)
                    resp.raise_for_status()
                    data = await resp.json()
                models = data.get("models", [])
                if not isinstance(models, list):
                    _LOGGER.warning("webhook_list_models did not return a list under 'models'")
                    models = None
            except Exception as e:
                _LOGGER.warning("Could not fetch models from webhook_list_models: %s", e)
                models = None

        if models:
            return await self.async_step_model(user_input, models)

        return self.async_create_entry(
            title=f"n8n @ {user_input['n8n_host']}",
            data=user_input
        )

    async def async_step_model(self, user_input, models):
        import voluptuous as vol

        context = self.context.setdefault("user_input", {})
        context.update(user_input)

        schema = vol.Schema({
            vol.Required("model", default=models[0]): vol.In(models),
        })
        return self.async_show_form(
            step_id="model",
            data_schema=schema,
            description_placeholders={"models": ", ".join(models)},
        )

    async def async_step_model_finish(self, user_input_model):
        stored = self.context.get("user_input", {})
        stored["model"] = user_input_model["model"]
        return self.async_create_entry(
            title=f"n8n @ {stored['n8n_host']} (model: {user_input_model['model']})",
            data=stored,
        )
