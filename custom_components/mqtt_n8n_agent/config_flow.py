import logging

from homeassistant import config_entries
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class MqttN8nAgentConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        if user_input is None:
            import voluptuous as vol  # <-- Lazy import here
            import aiohttp  # <-- Lazy import here

            schema = vol.Schema({
                vol.Required("n8n_host"): str,
                vol.Optional("n8n_port", default=443): int,
                vol.Optional("webhook_list_models", default=""): str,
                vol.Required("webhook_chat"): str,
                vol.Optional("webhook_stream", default=""): str,
                vol.Required("mqtt_host"): str,
                vol.Optional("mqtt_port", default=1883): int,
                vol.Optional("mqtt_username", default=""): str,
                vol.Optional("mqtt_password", default=""): str,
                vol.Optional("mqtt_tls", default=False): bool,
                vol.Optional("context_window", default=10): int,
                vol.Optional("max_history", default=10): int,
                vol.Optional("keep_alive", default=60): int,
                vol.Optional("show_thinking", default=True): bool,
            })
            return self.async_show_form(step_id="user", data_schema=schema)

        # If webhook_list_models provided, try to fetch models
        models = None
        if user_input.get("webhook_list_models"):
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
        import voluptuous as vol  # lazy again

        context = self.context.setdefault("user_input", {})
        context.update(user_input)

        schema = vol.Schema({
            vol.Required("model", default=models[0]): vol.In(models),
        })
        return self.async_show_form(
            step_id="model",
            data_schema=schema,
            description_placeholders={"models": ", ".join(models)}
        )

    async def async_step_model_finish(self, user_input_model):
        stored = self.context.get("user_input", {})
        stored["model"] = user_input_model["model"]
        return self.async_create_entry(
            title=f"n8n @ {stored['n8n_host']} (model: {user_input_model['model']})",
            data=stored
        )
