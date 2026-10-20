


def on_message(topic, payload):
    sender, _, text = payload.partition(": ")
    if sender == name:
        return  # skip the broker echoing our own message back
    print(f"\r{payload}\n> ", end="", flush=True)

try:
    from mqttlib import MQTTClient

    TOPIC = "ME193/chat"

    name = input("Your name: ").strip() or "anon"
    with MQTTClient() as client:
        client.subscribe(TOPIC, on_message)
        print(f"Chatting on '{TOPIC}' as {name}. Type 'quit' to exit.")

        while True:
            try:
                text = input("> ").strip()
            except (KeyboardInterrupt, EOFError):
                break
            if text == "quit":
                break
            if text:
                client.publish(TOPIC, f"{name}: {text}")
except Exception as e:
    print(f"Error occurred while chatting: {e}")
finally:
    print("Exiting chat.")
