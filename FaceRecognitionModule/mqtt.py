import paho.mqtt.client as mqtt
import json

BROKER = "127.0.0.1"  # dirección local
TOPIC = "facial/valid"

client = mqtt.Client(protocol=mqtt.MQTTv311)

try:
    client.connect(BROKER, 1883)
    msg = {"status": "ok", "user": "David", "confidence": 97.3}
    client.publish(TOPIC, json.dumps(msg))
    client.disconnect()
    print("📡 Mensaje enviado correctamente:", msg)
except Exception as e:
    print("❌ Error al conectar con el broker MQTT:", e)
