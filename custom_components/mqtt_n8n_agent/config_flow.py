import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_N8N_URL,
    CONF_MQTT_HOST,
    CONF_MQTT_USERNAME,
    CONF_MQTT_PASSWORD,
    CONF_CONTEXT_WINDOW,
    CONF_MAX_HISTORY,
    CONF_KEEP_ALIVE,
    CONF_ALLOW_THINKING,
    CONF_VERIFY_SSL,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_CONTEXT_WINDOW = 5
DEFAULT_MAX_HISTORY = 10
DEFAULT_KEEP_ALIVE = 60
DEFAULT_ALLOW_THINKING = False


class MqttN8nAgentConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MQTT N8N Agent."""

    VERSION = 2

    def __init__(self):
        self._n8n_url = None
        self._mqtt_host = None
        self._mqtt_username = None
        self._mqtt_password = None
        self._verify_ssl = True
        self._model = None
        self._models = []

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            verify_ssl = user_input.get(CONF_VERIFY_SSL, True)

            try:
                models = await self.hass.async_add_executor_job(
                    self._fetch_models_from_n8n_blocking,
                    user_input[CONF_N8N_URL],
                    verify_ssl,
                )
                if not models:
                    errors["base"] = "no_models_found"
                    return self.async_show_form(
                        step_id="user",
                        data_schema=self._get_user_data_schema(),
                        errors=errors,
                    )
                self._models = models
                self._model = models[0]  # Default model selection

            except Exception as err:
                _LOGGER.error("Failed to fetch models from N8N: %s", err)
                errors["base"] = "n8n_connection_failed"
                return self.async_show_form(
                    step_id="user",
                    data_schema=self._get_user_data_schema(),
                    errors=errors,
                )

            # Save user inputs
            self._n8n_url = user_input[CONF_N8N_URL]
            self._mqtt_host = user_input[CONF_MQTT_HOST]
            self._mqtt_username = user_input.get(CONF_MQTT_USERNAME)
            self._mqtt_password = user_input.get(CONF_MQTT_PASSWORD)
            self._verify_ssl = verify_ssl

            # Proceed to options step for extra config (model dropdown included)
            return self.async_show_form(
                step_id="options",
                data_schema=self._get_options_data_schema(),
            )

        return self.async_show_form(
            step_id="user",
            data_schema=self._get_user_data_schema(),
        )

    async def async_step_options(self, user_input=None):
        """Step 2: Configure agent options."""
        errors = {}

        if user_input is not None:
            if user_input[CONF_KEEP_ALIVE] <= 0:
                errors["keep_alive"] = "invalid_keep_alive"

            if not errors:
                # Create the config entry with all data
                data = {
                    CONF_N8N_URL: self._n8n_url,
                    CONF_MQTT_HOST: self._mqtt_host,
                    CONF_MQTT_USERNAME: self._mqtt_username,
                    CONF_MQTT_PASSWORD: self._mqtt_password,
                    CONF_VERIFY_SSL: self._verify_ssl,
                    "model": user_input["model"],
                    "instructions": user_input.get("instructions", ""),
                    CONF_CONTEXT_WINDOW: user_input[CONF_CONTEXT_WINDOW],
                    CONF_MAX_HISTORY: user_input[CONF_MAX_HISTORY],
                    CONF_KEEP_ALIVE: user_input[CONF_KEEP_ALIVE],
                    CONF_ALLOW_THINKING: user_input[CONF_ALLOW_THINKING],
                }
                return self.async_create_entry(title="MQTT N8N Agent", data=data)

        # Show options form with dropdown for model
        return self.async_show_form(
            step_id="options",
            data_schema=self._get_options_data_schema(),
            errors=errors,
            description_placeholders={"model": self._model or "unknown"},
        )

    def _get_user_data_schema(self):
        return vol.Schema(
            {
                vol.Required(CONF_N8N_URL): str,
                vol.Optional(CONF_VERIFY_SSL, default=True): bool,
                vol.Required(CONF_MQTT_HOST): str,
                vol.Optional(CONF_MQTT_USERNAME): str,
                vol.Optional(CONF_MQTT_PASSWORD): str,
            }
        )

    def _get_options_data_schema(self):
        defaults = {
            CONF_CONTEXT_WINDOW: 5,
            CONF_MAX_HISTORY: 10,
            CONF_KEEP_ALIVE: 60,
            CONF_ALLOW_THINKING: False,
        }

        # Defensive fallback if no models loaded yet
        models_list = self._models if self._models else [self._model] if self._model else ["unknown"]

        return vol.Schema(
            {
                vol.Required("model", default=self._model): vol.In(models_list),
                vol.Required(
                    "instructions",
                    default="You are a voice assistant for Home Assistant.",
                ): selector.selector({
                    "text": {
                        "multiline": True,
                        "min_length": 0,
                        "max_length": 10000,
                    }
                }),
                vol.Required(CONF_CONTEXT_WINDOW, default=defaults[CONF_CONTEXT_WINDOW]): int,
                vol.Required(CONF_MAX_HISTORY, default=defaults[CONF_MAX_HISTORY]): int,
                vol.Required(CONF_KEEP_ALIVE, default=defaults[CONF_KEEP_ALIVE]): int,
                vol.Required(CONF_ALLOW_THINKING, default=defaults[CONF_ALLOW_THINKING]): bool,
            }
        )

    def _fetch_models_from_n8n_blocking(self, n8n_url: str, verify_ssl: bool) -> list:
        """Blocking method to fetch list of model names from N8N."""
        import requests  # safe to import here for executor
        try:
            resp = requests.get(f"{n8n_url.rstrip('/')}/api/tags", timeout=5, verify=verify_ssl)
            resp.raise_for_status()
            data = resp.json()

            models = data.get("models", [])
            if not models:
                raise ValueError("No models found in response")

            return [model.get("model") for model in models if model.get("model")]

        except Exception as e:
            raise e

    def _test_mqtt_connection_blocking(self, host, username=None, password=None):
        """Blocking test MQTT connection using asyncio-mqtt, run in executor."""
        import asyncio
        from asyncio_mqtt import Client as MQTTClient

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def connect_test():
            async with MQTTClient(hostname=host, username=username, password=password):
                pass

        try:
            loop.run_until_complete(connect_test())
        finally:
            loop.close()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow handler."""
        # You can implement a separate OptionsFlow handler here if needed
        return MqttN8nAgentOptionsFlow(config_entry)


class MqttN8nAgentOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for MQTT N8N Agent."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}

        if user_input is not None:
            if user_input[CONF_KEEP_ALIVE] <= 0:
                errors["keep_alive"] = "invalid_keep_alive"

            if not errors:
                # Update options and finish
                return self.async_create_entry(title="", data=user_input)

        # Load defaults and current options/data
        current = self.config_entry.options if self.config_entry.options else self.config_entry.data
        defaults = {
            CONF_CONTEXT_WINDOW: 5,
            CONF_MAX_HISTORY: 10,
            CONF_KEEP_ALIVE: 60,
            CONF_ALLOW_THINKING: False,
        }

        data_schema = vol.Schema(
            {
                vol.Required(
                    "instructions",
                    default=current.get("instructions", "You are a voice assistant for Home Assistant."),
                ): str,
                vol.Required(
                    CONF_CONTEXT_WINDOW,
                    default=current.get(CONF_CONTEXT_WINDOW, defaults[CONF_CONTEXT_WINDOW]),
                ): int,
                vol.Required(
                    CONF_MAX_HISTORY,
                    default=current.get(CONF_MAX_HISTORY, defaults[CONF_MAX_HISTORY]),
                ): int,
                vol.Required(
                    CONF_KEEP_ALIVE,
                    default=current.get(CONF_KEEP_ALIVE, defaults[CONF_KEEP_ALIVE]),
                ): int,
                vol.Required(
                    CONF_ALLOW_THINKING,
                    default=current.get(CONF_ALLOW_THINKING, defaults[CONF_ALLOW_THINKING]),
                ): bool,
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema, errors=errors)
