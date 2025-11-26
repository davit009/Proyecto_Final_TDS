import cv2
import face_recognition
import os
import json
import time
import mysql.connector
import paho.mqtt.client as mqtt
from ultralytics import YOLO 

# --- CONFIGURACIÓN ---
BROKER = "192.168.2.10"
TOPIC_RFID = "rfid/valid"
TOPIC_FACIAL = "facial/valid"

# Rutas
PATH_BASE = "C:/xampp/htdocs/proyecto_acceso"
PATH_FOTOS_DB = os.path.join(PATH_BASE, "faces")
PATH_SCAN_WEB = os.path.join(PATH_BASE, "scan_temp/scan_pending.jpg")

# Configuración DB
DB_CONFIG = {
    'user': 'root', 
    'password': '', 
    'host': 'localhost', 
    'database': 'seguridad_db'
}

# --- CARGA DE MODELO YOLO (Cumple Rúbrica Visión) ---
print("🧠 Cargando YOLOv8...")
model = YOLO("yolov8n.pt") 

# Variables de Estado
known_face_encodings = []
known_face_names = []
last_db_update = 0

# Memoria de Corto Plazo (Para validación dual)
# Guardamos quién pasó tarjeta y quién mostró la cara con su timestamp
ultimo_rfid = {'usuario': None, 'time': 0}
ultimo_face = {'usuario': None, 'time': 0}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# --- SINCRONIZACIÓN DB ---
def actualizar_base_datos():
    global known_face_encodings, known_face_names, last_db_update
    
    # Actualizar cada 60s
    if time.time() - last_db_update < 60 and last_db_update != 0: 
        return

    print("🔄 Actualizando usuarios...")
    temp_encs, temp_names = [], []

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT nombre, foto_path FROM usuarios WHERE activo = 1")
        usuarios = cursor.fetchall()
        conn.close()

        for u in usuarios:
            filename = os.path.basename(u['foto_path'])
            full_path = os.path.join(PATH_FOTOS_DB, filename)

            if os.path.exists(full_path):
                try:
                    img = face_recognition.load_image_file(full_path)
                    encs = face_recognition.face_encodings(img)
                    if encs:
                        temp_encs.append(encs[0])
                        temp_names.append(u['nombre'])
                except: pass
        
        known_face_encodings = temp_encs
        known_face_names = temp_names
        last_db_update = time.time()
        print(f"✅ {len(known_face_names)} usuarios en memoria.")

    except Exception as e:
        print(f"❌ Error DB: {e}")

# --- LOGS ---
def registrar_evento(usuario, evento, motivo):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "INSERT INTO logs_acceso (usuario, tipo_evento, motivo) VALUES (%s, %s, %s)"
        cursor.execute(sql, (usuario, evento, motivo))
        conn.commit()
        conn.close()
        print(f"📝 Log: {usuario} -> {evento}")
    except: pass

# --- MOTOR DE DECISIÓN (VALIDACIÓN DUAL) ---
def verificar_acceso_dual(client_mqtt):
    global ultimo_rfid, ultimo_face
    
    now = time.time()
    TIEMPO_MAXIMO = 15 # Segundos para completar ambos pasos

    # Limpiar eventos viejos
    if now - ultimo_rfid['time'] > TIEMPO_MAXIMO: ultimo_rfid['usuario'] = None
    if now - ultimo_face['time'] > TIEMPO_MAXIMO: ultimo_face['usuario'] = None

    user_rfid = ultimo_rfid['usuario']
    user_face = ultimo_face['usuario']

    # Si tenemos AMBOS datos
    if user_rfid and user_face:
        print(f"⚖️ Cotejando: Tarjeta({user_rfid}) vs Cara({user_face})")
        
        if user_rfid.lower() == user_face.lower():
            print(f"🔓 ACCESO CONCEDIDO: {user_rfid}")
            
            # Ordenar apertura al ESP32
            client_mqtt.publish(TOPIC_FACIAL, json.dumps({"command": "open", "user": user_rfid}))
            registrar_evento(user_rfid, "acceso", "Validación Dual Exitosa")
            
            # Resetear para no abrir doble
            ultimo_rfid['usuario'] = None
            ultimo_face['usuario'] = None
        else:
            print(f"⛔ ALERTA: Tarjeta de {user_rfid} usada por {user_face}")
            registrar_evento(user_rfid, "rechazo", f"Rostro no coincide: {user_face}")
            
            # Borrar el evento más viejo para dar oportunidad de corregir
            if ultimo_rfid['time'] < ultimo_face['time']: ultimo_rfid['usuario'] = None
            else: ultimo_face['usuario'] = None

# --- PROCESAMIENTO DE IMAGEN (WEB -> YOLO -> FACE) ---
def procesar_foto_web():
    global ultimo_face
    
    if os.path.exists(PATH_SCAN_WEB):
        try:
            # Pequeña espera para asegurar escritura completa
            time.sleep(0.1) 
            
            # 1. FILTRO YOLOv8: ¿Es una persona?
            # conf=0.5 (50% seguridad), verbose=False (silencioso)
            results = model.predict(PATH_SCAN_WEB, conf=0.5, verbose=False)
            
            es_persona = False
            for r in results:
                for box in r.boxes:
                    # Clase 0 en COCO dataset es 'person'
                    if int(box.cls[0]) == 0: 
                        es_persona = True
                        break
            
            if not es_persona:
                # Si YOLO no ve persona, borramos y salimos. Ahorramos CPU.
                os.remove(PATH_SCAN_WEB)
                return

            print("👀 YOLO: Persona detectada. Verificando identidad...")

            # 2. FILTRO BIOMÉTRICO
            img = face_recognition.load_image_file(PATH_SCAN_WEB)
            encs = face_recognition.face_encodings(img)
            
            # Borramos archivo ya procesado
            try: os.remove(PATH_SCAN_WEB)
            except: pass

            if len(encs) > 0:
                matches = face_recognition.compare_faces(known_face_encodings, encs[0], 0.5)
                if True in matches:
                    idx = matches.index(True)
                    nombre = known_face_names[idx]
                    print(f"👤 Rostro Identificado: {nombre}")
                    
                    # Guardamos en memoria temporal para la validación dual
                    ultimo_face['usuario'] = nombre
                    ultimo_face['time'] = time.time()
                else:
                    print("❌ Rostro desconocido")
            else:
                print("⚠️ Persona detectada por YOLO, pero rostro no visible")

        except Exception as e:
            print(f"Error visión: {e}")
            try: os.remove(PATH_SCAN_WEB)
            except: pass

# --- MQTT (TARJETA) ---
def on_message(client, userdata, msg):
    global ultimo_rfid
    try:
        payload = json.loads(msg.payload.decode())
        card_id = str(payload.get("card_id", "")).strip()
        print(f"\n💳 Tarjeta: [{card_id}]")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT nombre FROM usuarios WHERE card_id = %s AND activo = 1", (card_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            nombre = result['nombre']
            print(f"✅ Tarjeta válida ({nombre}). Esperando confirmación visual...")
            
            # Guardamos en memoria temporal para la validación dual
            ultimo_rfid['usuario'] = nombre
            ultimo_rfid['time'] = time.time()
        else:
            print("⛔ Tarjeta no registrada")
            registrar_evento("Desconocido", "rechazo", f"Tarjeta {card_id}")
            client.publish(TOPIC_FACIAL, json.dumps({"command": "deny", "reason": "unknown_card"}))

    except Exception as e:
        print(f"Error MQTT: {e}")

# --- MAIN ---
print("🚀 Iniciando Sistema V2 (YOLOv8 + IoT Dual)...")
actualizar_base_datos()

client = mqtt.Client()
client.on_message = on_message

try:
    client.connect(BROKER)
    client.subscribe(TOPIC_RFID)
    client.loop_start() # Hilo secundario para MQTT
    
    print(f"📡 Conectado a {BROKER}. Esperando eventos...")

    while True:
        # 1. Vigilar carpeta por si la web mandó foto
        procesar_foto_web()
        
        # 2. Verificar si tenemos las dos llaves (Tarjeta + Cara)
        verificar_acceso_dual(client)
        
        # 3. Descanso para CPU
        time.sleep(0.1)

except Exception as e:
    print(f"❌ Error fatal: {e}")