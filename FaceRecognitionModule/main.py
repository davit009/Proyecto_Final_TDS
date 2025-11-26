import cv2
import face_recognition
import os
import json
import time
import mysql.connector
import paho.mqtt.client as mqtt

# --- CONFIGURACIÓN ---
BROKER = "172.20.10.2" 
TOPIC_RFID = "rfid/valid"
TOPIC_FACIAL = "facial/valid"


PATH_FOTOS_XAMPP = "C:/xampp/htdocs/proyecto_acceso/faces"

DB_CONFIG = {
    'user': 'root', 
    'password': '', 
    'host': 'localhost', 
    'database': 'seguridad_db'
}

# Variables Globales
known_face_encodings = []
known_face_names = [] # Guardaremos IDs de DB aquí para referencia
last_db_update = 0

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# --- SINCRONIZACIÓN (PYTHON <-> MYSQL <-> XAMPP) ---
def actualizar_base_datos():
    global known_face_encodings, known_face_names, last_db_update
    
    # Recargar cada 60 segundos o al inicio
    if time.time() - last_db_update < 60 and last_db_update != 0: 
        return

    print("🔄 Sincronizando usuarios desde BD...")
    temp_encs, temp_names = [], []

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Solo traemos usuarios ACTIVOS
        cursor.execute("SELECT nombre, foto_path FROM usuarios WHERE activo = 1")
        usuarios = cursor.fetchall()
        conn.close()

        for u in usuarios:
          
            filename = os.path.basename(u['foto_path'])
            full_path = os.path.join(PATH_FOTOS_XAMPP, filename)

            if os.path.exists(full_path):
                try:
                    img = face_recognition.load_image_file(full_path)
                    encs = face_recognition.face_encodings(img)
                    if encs:
                        temp_encs.append(encs[0])
                        
                        temp_names.append(u['nombre'])
                except Exception as e:
                    print(f"⚠️ Error procesando {filename}: {e}")
            else:
                print(f"⚠️ Archivo no encontrado: {full_path}")
        
        known_face_encodings = temp_encs
        known_face_names = temp_names
        last_db_update = time.time()
        print(f"✅ DB Actualizada: {len(known_face_names)} usuarios cargados.")

    except Exception as e:
        print(f"❌ Error de conexión DB: {e}")

# --- LÓGICA DE LOGS ---
def registrar_evento(usuario, evento, motivo):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "INSERT INTO logs_acceso (usuario, tipo_evento, motivo) VALUES (%s, %s, %s)"
        cursor.execute(sql, (usuario, evento, motivo))
        conn.commit()
        conn.close()
        print(f"📝 Log guardado: {usuario} -> {evento}")
    except Exception as e:
        print(f"⚠️ Error guardando log: {e}")

# --- VALIDACIÓN BIOMÉTRICA ---
def validar_rostro(usuario_esperado):
    actualizar_base_datos() # Verificar si hay cambios antes de validar
    
    cam = cv2.VideoCapture(0)
    if not cam.isOpened(): return False
    
    print(f"👁️ Validando identidad de: {usuario_esperado}")
    start = time.time()
    validado = False

    while (time.time() - start) < 8: # 8 segundos timeout
        ret, frame = cam.read()
        if not ret: break
        
        small = cv2.resize(frame, (0,0), fx=0.5, fy=0.5)
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        
        face_locs = face_recognition.face_locations(rgb)
        face_encs = face_recognition.face_encodings(rgb, face_locs)

        usuario_detectado = "Desconocido"
        
        for enc in face_encs:
            matches = face_recognition.compare_faces(known_face_encodings, enc, 0.5)
            if True in matches:
                match_idx = matches.index(True)
                usuario_detectado = known_face_names[match_idx]
                
                # Comparación flexible (ignorando mayúsculas)
                if usuario_detectado.lower() == usuario_esperado.lower():
                    validado = True
                    cv2.putText(frame, "ACCESO PERMITIDO", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
                    break
        
        cv2.imshow("Seguridad", frame)
        cv2.waitKey(1)
        if validado: 
            time.sleep(1)
            break

    cam.release()
    cv2.destroyAllWindows()
    return validado

# --- MQTT ---
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
       
        raw_card = payload.get("card_id", "")
        card_id = str(raw_card).strip()
        
        print(f"\n💳 Tarjeta recibida (limpia): [{card_id}]")

        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # OJO: Verificamos que activo=1
        cursor.execute("SELECT nombre FROM usuarios WHERE card_id = %s AND activo = 1", (card_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            usuario = result['nombre']
            print(f"👤 Usuario identificado: {usuario}")
            
            # 2. Validar Rostro
            if validar_rostro(usuario):
                res = {"command": "open", "user": usuario}
                registrar_evento(usuario, "acceso", "Verificación Exitosa")
            else:
                res = {"command": "deny", "reason": "face_fail"}
                registrar_evento(usuario, "rechazo", "Fallo Facial")
        else:
            print(f"⛔ Tarjeta NO registrada: '{card_id}'")
            res = {"command": "deny", "reason": "unknown_card"}
            registrar_evento("Desconocido", "rechazo", f"Tarjeta {card_id}")

        client.publish(TOPIC_FACIAL, json.dumps(res))

    except Exception as e:
        print(f"Error MQTT: {e}")

# --- MAIN ---
print("🚀 Iniciando Sistema de Seguridad...")
actualizar_base_datos()

client = mqtt.Client()
client.on_message = on_message
try:
    client.connect(BROKER)
    client.subscribe(TOPIC_RFID)
    print(f"📡 Conectado al Broker: {BROKER}")
    client.loop_forever()
except Exception as e:
    print(f"❌ No se pudo conectar al Broker MQTT. Verifica la IP: {e}")