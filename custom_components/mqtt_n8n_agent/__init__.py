import asyncio
import logging

from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the mqtt_n8n_agent integration."""

    # Normally, config entries handle setup, so nothing here for now.
    return True

async def async_setup_entry(hass: HomeAssistant, entry):
    """Set up mqtt_n8n_agent from a config entry."""
    from aiomqtt import Client as MQTTClient, MqttError
    
    mqtt_host = entry.data.get("mqtt_host")
    mqtt_port = entry.data.get("mqtt_port", 1883)
    mqtt_user = entry.data.get("mqtt_username")
    mqtt_pass = entry.data.get("mqtt_password")
    mqtt_tls = entry.data.get("mqtt_tls", False)

    # Connect to MQTT broker using aiomqtt
    client = MQTTClient(
        hostname=mqtt_host,
        port=mqtt_port,
        username=mqtt_user or None,
        password=mqtt_pass or None,
        tls=mqtt_tls,
    )

    try:
        await client.connect()
    except MqttError as e:
        _LOGGER.error("Failed to connect to MQTT broker: %s", e)
        return False

    # Store client in hass data for future use
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["mqtt_client"] = client

    _LOGGER.info("mqtt_n8n_agent connected to MQTT broker at %s:%s", mqtt_host, mqtt_port)

    # You can start tasks here for MQTT subscriptions or communication with n8n

    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    """Unload a config entry."""

    client = hass.data[DOMAIN].get("mqtt_client")
    if client:
        await client.disconnect()

    hass.data[DOMAIN].pop("mqtt_client", None)

    return True
