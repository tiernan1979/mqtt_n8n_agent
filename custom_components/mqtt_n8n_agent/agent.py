import asyncio
import json
import logging
from typing import Optional

from homeassistant import core
from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import HomeAssistantType

from .const import (
    CONF_N8N_HOST, CONF_N8N_PORT,
    CONF_WEBHOOK_LIST_MODELS, CONF_WEBHOOK_CHAT, CONF_WEBHOOK_STREAM,
    CONF_MQTT_HOST, CONF_MQTT_PORT, CONF_MQTT_USERNAME, CONF_MQTT_PASSWORD, CONF_MQTT_TLS,
    CONF_CONTEXT_WINDOW, CONF_MAX_HISTORY, CONF_KEEP_ALIVE, CONF_SHOW_THINKING
)

_LOGGER = logging.getLogger(__name__)

try:
    from asyncio_mqtt import Client as MQTTClient, MqttError
except ImportError:
    MQTTClient = None
    MqttError = Exception


async def async_setup_agent(
    hass: HomeAssistantType, entry: ConfigEntry, agent_id: str
) -> conversation.ConversationAgent:
    """Set up the conversation agent instance."""
    config = entry.data
    return MqttN8nAgent(
        hass,
        agent_id,
        n8n_host=config[CONF_N8N_HOST],
        n8n_port=config[CONF_N8N_PORT],
        webhook_list_models=config.get(CONF_WEBHOOK_LIST_MODELS, ""),
        webhook_chat=config[CONF_WEBHOOK_CHAT],
        webhook_stream=config.get(CONF_WEBHOOK_STREAM, ""),
        mqtt_host=config[CONF_MQTT_HOST],
        mqtt_port=config[CONF_MQTT_PORT],
        mqtt_username=config.get(CONF_MQTT_USERNAME),
        mqtt_password=config.get(CONF_MQTT_PASSWORD),
        mqtt_tls=config.get(CONF_MQTT_TLS, False),
        context_window=config.get(CONF_CONTEXT_WINDOW),
        max_history=config.get(CONF_MAX_HISTORY),
        keep_alive=config.get(CONF_KEEP_ALIVE),
        show_thinking=config.get(CONF_SHOW_THINKING),
        model=config.get("model")  # new
    )


class MqttN8nAgent(conversation.ConversationAgent):
    """Conversation agent that communicates via MQTT to n8n."""

    def __init__(
        self,
        hass: HomeAssistantType,
        agent_id: str,
        n8n_host: str,
        n8n_port: int,
        webhook_list_models: str,
        webhook_chat: str,
        webhook_stream: Optional[str],
        mqtt_host: str,
        mqtt_port: int,
        mqtt_username: Optional[str],
        mqtt_password: Optional[str],
        mqtt_tls: bool,
        context_window: int,
        max_history: int,
        keep_alive: int,
        show_thinking: bool,
        model: Optional[str] = None,
    ):
        super().__init__(agent_id)
        self.hass = hass
        self.n8n_host = n8n_host
        self.n8n_port = n8n_port
        self.webhook_list_models = webhook_list_models
        self.webhook_chat = webhook_chat
        self.webhook_stream = webhook_stream
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.mqtt_username = mqtt_username
        self.mqtt_password = mqtt_password
        self.mqtt_tls = mqtt_tls
        self.context_window = context_window
        self.max_history = max_history
        self.keep_alive = keep_alive
        self.show_thinking = show_thinking
        self.model = model

        self.conversation_histories: dict[str, list[str]] = {}

async def async_process(self, request: conversation.ConversationInput) -> ConversationResult:
    if MQTTClient is None:
        _LOGGER.error("asyncio_mqtt library not installed")
        return ConversationResult(
            response=TextSpeech(type=SpeechType.PLAIN, speech="Sorry, I cannot respond right now."),
            conversation_id=request.conversation_id,
        )

    conversation_id = request.conversation_id
    user_text = request.text

    history = self.conversation_histories.get(conversation_id, [])
    history.append(user_text)
    if len(history) > self.max_history:
        history = history[-self.max_history:]
    self.conversation_histories[conversation_id] = history

    input_topic = f"n8n/voice/input/{conversation_id}"
    output_topic = f"n8n/voice/output/{conversation_id}"

    payload = {
        "text": user_text,
        "conversation_id": conversation_id,
        "history": history,
        "context_window": self.context_window,
    }
    if self.model:
        payload["model"] = self.model

    full_response = ""
    queue: asyncio.Queue[str] = asyncio.Queue()

    async def mqtt_message_handler(msg):
        try:
            tok = msg.payload.decode()
        except Exception:
            return
        await queue.put(tok)

    try:
        async with MQTTClient(
            hostname=self.mqtt_host,
            port=self.mqtt_port,
            username=self.mqtt_username,
            password=self.mqtt_password,
            tls_context=None if not self.mqtt_tls else True,
        ) as client:
            await client.subscribe(output_topic)
            client.on_message = mqtt_message_handler

            await client.publish(input_topic, json.dumps(payload))

            try:
                while True:
                    token = await asyncio.wait_for(queue.get(), timeout=self.keep_alive)
                    if token == "[END]":
                        break
                    full_response += token
            except asyncio.TimeoutError:
                _LOGGER.warning("Timeout waiting for response from n8n for conv %s", conversation_id)

            await client.unsubscribe(output_topic)
    except MqttError as e:
        _LOGGER.error("MQTT error: %s", e)
        return ConversationResult(
            response=TextSpeech(type=SpeechType.PLAIN, speech="Error communicating with assistant."),
            conversation_id=request.conversation_id,
        )

    return ConversationResult(
        response=TextSpeech(type=SpeechType.PLAIN, speech=full_response),
        conversation_id=request.conversation_id,
    )
