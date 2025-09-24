from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .agent import async_setup_agent

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up via YAML (not used)."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry):
    """Set up from a config entry."""
    # Register conversation agent
    hass.components.conversation.async_register_conversation_agent(
        entry.entry_id, async_setup_agent(hass, entry, agent_id=entry.entry_id)
    )
    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    """Unload the config entry."""
    # Optionally unregister, cleanup
    return True
