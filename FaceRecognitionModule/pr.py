import cv2
import os
import numpy as np
from datetime import datetime
import insightface
from insightface.app import FaceAnalysis

# ----------------------------------------------------
# CONFIGURACIÓN
# ----------------------------------------------------
FACES_DIR = "faces1"
if not os.path.exists(FACES_DIR):
    os.makedirs(FACES_DIR)

# ----------------------------------------------------
# Cargar modelo InsightFace con GPU
# ----------------------------------------------------
print("Cargando modelo InsightFace...")
app = FaceAnalysis(name="buffalo_l")
app.prepare(ctx_id=0, det_size=(640,640))  # ctx_id=0 = GPU
print("Modelo cargado ✔")


# ----------------------------------------------------
# FUNCIÓN: Registrar rostro
# ----------------------------------------------------
def registrar_rostro(nombre):
    cam = cv2.VideoCapture(0)
    print(f"\n📸 Registrando rostro de: {nombre}")
    print("Presiona [SPACE] para capturar la imagen")
    print("Presiona [Q] para cancelar\n")

    while True:
        ret, frame = cam.read()
        if not ret:
            continue

        faces = app.get(frame)
        for f in faces:
            x1, y1, x2, y2 = f.bbox.astype(int)
            cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,0), 2)

        cv2.imshow("Registrar Rostro", frame)

        key = cv2.waitKey(1) & 0xFF

        # Capturar rostro
        if key == 32:  # SPACE
            file_name = f"{nombre}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            path = os.path.join(FACES_DIR, file_name)
            cv2.imwrite(path, frame)
            print(f"\n✔ Rostro guardado en: {path}\n")
            cam.release()
            cv2.destroyAllWindows()
            return

        # Cancelar
        elif key == ord('q'):
            cam.release()
            cv2.destroyAllWindows()
            print("\nRegistro cancelado.")
            return


# ----------------------------------------------------
# FUNCIÓN: Cargar embeddings
# ----------------------------------------------------
def cargar_embeddings():
    registrados = {}

    for file in os.listdir(FACES_DIR):
        if file.lower().endswith((".jpg", ".png")):
            img = cv2.imread(os.path.join(FACES_DIR, file))
            faces = app.get(img)
            if len(faces) == 0:
                continue
            emb = faces[0].embedding
            nombre = file.split("_")[0]
            registrados[nombre] = emb

    print(f"✔ Rostros cargados: {list(registrados.keys())}")
    return registrados


# ----------------------------------------------------
# FUNCIÓN: Reconocimiento en vivo
# ----------------------------------------------------
def reconocimiento():
    registrados = cargar_embeddings()
    if not registrados:
        print("❌ No hay rostros registrados en /faces/")
        return

    cap = cv2.VideoCapture(0)
    print("\n🔍 Iniciando reconocimiento... Presiona Q para salir\n")

    threshold = 0.45  # mientras más pequeño = más exigente

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        faces = app.get(frame)

        for face in faces:
            x1, y1, x2, y2 = face.bbox.astype(int)
            emb = face.embedding

            best_name = "Desconocido"
            best_score = 1

            for nombre, known_emb in registrados.items():
                score = 1 - np.dot(emb, known_emb) / (np.linalg.norm(emb) * np.linalg.norm(known_emb))
                if score < best_score:
                    best_score = score
                    best_name = nombre

            color = (0,255,0) if best_score < threshold else (0,0,255)
            cv2.rectangle(frame, (x1,y1), (x2,y2), color, 2)
            cv2.putText(
                frame, 
                f"{best_name} ({best_score:.3f})", 
                (x1, y1 - 10), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.8, 
                color, 
                2
            )

        cv2.imshow("Reconocimiento Facial (GPU)", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


# ----------------------------------------------------
# MENÚ PRINCIPAL
# ----------------------------------------------------
while True:
    print("\n====== MENÚ ======")
    print("1) Registrar rostro")
    print("2) Probar reconocimiento")
    print("3) Salir")

    op = input("\nElige una opción: ")

    if op == "1":
        nombre = input("Ingresa tu nombre: ").strip().lower()
        registrar_rostro(nombre)

    elif op == "2":
        reconocimiento()

    elif op == "3":
        print("Saliendo...")
        break

    else:
        print("Opción no válida.")
