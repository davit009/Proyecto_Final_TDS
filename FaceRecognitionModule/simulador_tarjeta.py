import paho.mqtt.client as mqtt
import json
import time

# --- CONFIGURACIÓN ---
# Usa la misma IP que pusiste en main_security_v2.py
# Si estás probando todo en tu misma PC, puedes usar "localhost" o "127.0.0.1"
BROKER = "192.168.2.10" 
TOPIC = "rfid/valid"

# ID DE TARJETA QUE YA TENGAS REGISTRADA EN TU BD
# (Revisa tu phpMyAdmin si no recuerdas cuál registraste)
TARJETA_A_PROBAR = "042116E25D6580" 

def simular_lectura():
    try:
        client = mqtt.Client("SimuladorPC")
        client.connect(BROKER)
        
        # Creamos el mensaje JSON igual que el ESP32
        mensaje = json.dumps({"card_id": TARJETA_A_PROBAR})
        
        client.publish(TOPIC, mensaje)
        print(f"📡 [SIMULADOR] Enviando tarjeta: {TARJETA_A_PROBAR}")
        print("✅ Mensaje enviado al Broker MQTT.")
        
        client.disconnect()
    except Exception as e:
        print(f"❌ Error conectando al Broker: {e}")
        print("Asegúrate de que Mosquitto esté corriendo y la IP sea correcta.")

if __name__ == "__main__":
    simular_lectura()