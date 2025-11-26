import cv2
import face_recognition
import os
import time

# Crear carpeta si no existe
if not os.path.exists("faces"):
    os.makedirs("faces")

# -----------------------------------------------------
# FUNCIÓN 1: REGISTRAR UN NUEVO USUARIO (TOMAR FOTO)
# -----------------------------------------------------
def registrar_rostro():
    nombre = input("✍️ Ingresa el nombre del usuario (sin espacios): ").strip().lower()
    if not nombre:
        print("❌ Nombre inválido.")
        return

    cam = cv2.VideoCapture(0)
    print("\n--- MODO REGISTRO ---")
    print(f"📸 Mira a la cámara. Presiona 'S' para GUARDAR o 'Q' para CANCELAR.")

    while True:
        ret, frame = cam.read()
        if not ret:
            print("❌ No se pudo acceder a la cámara.")
            break

        # Dibujar un marco guía para que el usuario se centre
        alto, ancho, _ = frame.shape
        cv2.rectangle(frame, (ancho//4, alto//4), (3*ancho//4, 3*alto//4), (255, 255, 0), 2)
        cv2.putText(frame, "Presiona 'S' para Guardar", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        cv2.imshow("Registro Facial", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):
            # Guardar imagen
            nombre_archivo = f"faces/{nombre}.jpg"
            cv2.imwrite(nombre_archivo, frame)
            print(f"✅ Rostro guardado exitosamente: {nombre_archivo}")
            break
        elif key == ord('q'):
            print("❌ Registro cancelado.")
            break

    cam.release()
    cv2.destroyAllWindows()

# -----------------------------------------------------
# FUNCIÓN 2: PROBAR EL RECONOCIMIENTO (MODO TEST)
# -----------------------------------------------------
def probar_sistema():
    print("\n🔄 Cargando base de datos de rostros...")
    known_encodings = []
    known_names = []

    # Cargar rostros de la carpeta
    files = os.listdir("faces")
    if not files:
        print("⚠️ No hay rostros registrados en la carpeta 'faces'. Usa la opción 1 primero.")
        return

    for f in files:
        if f.endswith((".jpg", ".png")):
            path = os.path.join("faces", f)
            img = face_recognition.load_image_file(path)
            encs = face_recognition.face_encodings(img)
            if encs:
                known_encodings.append(encs[0])
                name = os.path.splitext(f)[0] # Nombre del archivo sin .jpg
                known_names.append(name)
                print(f"  -> Cargado: {name}")

    print("✅ Sistema listo. Abre la cámara...")
    
    cam = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cam.read()
        if not ret: break

        # Procesar imagen
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        face_locs = face_recognition.face_locations(rgb_small)
        face_encs = face_recognition.face_encodings(rgb_small, face_locs)

        for (top, right, bottom, left), enc in zip(face_locs, face_encs):
            # Escalar coordenadas de vuelta al tamaño original
            top *= 2; right *= 2; bottom *= 2; left *= 2
            
            matches = face_recognition.compare_faces(known_encodings, enc, tolerance=0.5)
            name = "Desconocido"

            if True in matches:
                first_match_index = matches.index(True)
                name = known_names[first_match_index]
                color = (0, 255, 0) # Verde
            else:
                color = (0, 0, 255) # Rojo

            # Dibujar
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

        cv2.imshow("Prueba de Reconocimiento (Q para salir)", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()

# -----------------------------------------------------
# MENÚ PRINCIPAL
# -----------------------------------------------------
def menu():
    while True:
        print("\n=== GESTOR DE ROSTROS ===")
        print("1. Registrar nueva cara (Tomar foto)")
        print("2. Probar reconocimiento en vivo")
        print("3. Salir")
        
        opcion = input("Selecciona una opción: ")

        if opcion == '1':
            registrar_rostro()
        elif opcion == '2':
            probar_sistema()
        elif opcion == '3':
            print("👋 Adiós.")
            break
        else:
            print("Opción no válida.")

if __name__ == "__main__":
    menu()