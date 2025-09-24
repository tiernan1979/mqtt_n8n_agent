# MQTT N8N Conversation Agent for Home Assistant

A custom [Home Assistant](https://www.home-assistant.io/) integration that allows you to use **n8n + Ollama** as a **conversation agent**, with **streamed replies via MQTT**.

This component enables HA to offload conversation processing to `n8n` (which in turn can call [Ollama](https://ollama.com/)) via MQTT message passing.

---

## 🔧 Features

- 🔄 MQTT-based communication between Home Assistant and n8n
- 📡 Streaming response support
- 🧠 Context and history tracking per conversation
- 💬 Works with [Ollama](https://ollama.com/) via `n8n` HTTP/Webhook nodes
- 🤖 Full integration with Home Assistant’s `conversation:` system
- 🧩 webhook_list_models endpoint for live model selection

---

## 🚀 How It Works

1. Home Assistant sends user input to MQTT (`n8n/voice/input/<conversation_id>`)
2. n8n listens to that topic and processes the message:
   - Uses [Ollama](https://ollama.com/) via HTTP API or Docker socket
   - Publishes streaming responses to `n8n/voice/output/<conversation_id>`
3. Home Assistant subscribes to the output topic, assembles the reply, and displays it to the user

---

## 📦 Installation

1. Clone or download this repository into your Home Assistant `custom_components/` folder:

```bash
cd config/custom_components
git clone https://github.com/tiernan1979/mqtt_n8n_agent.git
