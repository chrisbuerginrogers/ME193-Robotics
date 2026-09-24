'''
Shared MQTT wrapper for all ME193 examples.

Usage:
    from mqttlib import MQTTClient
'''

import os
import ssl
import uuid

import paho.mqtt.client as mqtt

BROKER_HOST = "2a411b7826e6425fa5313a38bd87bb65.s1.eu.hivemq.cloud"
BROKER_PORT = 8883  # TLS port; HiveMQ Cloud requires TLS + auth, no plaintext option


class MQTTClient:
    """Thin wrapper around paho-mqtt for topic subscribe/publish with
    per-topic callbacks. Use as a context manager so the connection is
    always closed cleanly:

        with MQTTClient() as client:
            client.subscribe(TOPIC, on_message)
            client.publish(TOPIC, "hello world")

    This broker requires a username/password. Rather than hardcoding
    them here, set them as environment variables before running:

        PowerShell:  $env:MQTT_USERNAME = "..."; $env:MQTT_PASSWORD = "..."
        Bash:        export MQTT_USERNAME=...; export MQTT_PASSWORD=...

    or pass username=/password= explicitly to MQTTClient().
    """

    def __init__(
        self,
        host=BROKER_HOST,
        port=BROKER_PORT,
        client_id=None,
        username=None,
        password=None,
        use_tls=True,
    ):
        self.host = host
        self.port = port
        self._callbacks = {}

        client_id = client_id or f"me193-{uuid.uuid4().hex[:8]}"
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
        self._client.on_message = self._on_message

        if use_tls:
            self._client.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT)

        username = username or os.environ.get("MQTT_USERNAME")
        password = password or os.environ.get("MQTT_PASSWORD")
        if username:
            self._client.username_pw_set(username, password)

    def connect(self):
        self._client.connect(self.host, self.port)
        self._client.loop_start()
        return self

    def disconnect(self):
        self._client.loop_stop()
        self._client.disconnect()

    def subscribe(self, topic, callback):
        """Subscribe to topic, calling callback(topic, payload) for each message."""
        self._callbacks[topic] = callback
        self._client.subscribe(topic)

    def publish(self, topic, payload):
        self._client.publish(topic, payload)

    def _on_message(self, client, userdata, message):
        callback = self._callbacks.get(message.topic)
        if callback:
            callback(message.topic, message.payload.decode())

    def __enter__(self):
        return self.connect()

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()
