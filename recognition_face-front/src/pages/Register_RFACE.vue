<template>
  <div class="face-register-container">
    <div class="card">
      <div class="card-header">
        <h2>👤 Nuevo Usuario</h2>
        <!-- Botón para volver al dashboard sin guardar -->
        <button class="btn-back" @click="$router.push('/dashboard')">Cancelar</button>
      </div>
      
      <div class="form-grid">
        <!-- COLUMNA DATOS -->
        <div class="left-col">
          <div class="form-group">
            <label>Nombre</label>
            <input v-model="nombre" type="text" placeholder="Ej: David" class="input-styled" />
          </div>
          <div class="form-group">
            <label>Apellido</label>
            <input v-model="apellido" type="text" placeholder="Ej: García" class="input-styled" />
          </div>
          <div class="form-group">
            <label>Departamento</label>
            <input v-model="departamento" type="text" placeholder="Ej: Sistemas" class="input-styled" />
          </div>
          <div class="form-group">
            <label>Email</label>
            <input v-model="email" type="email" placeholder="correo@ejemplo.com" class="input-styled" />
          </div>
          
          <!-- NUEVO CAMPO: CONTRASEÑA -->
          <div class="form-group">
            <label>Asignar Contraseña</label>
            <input v-model="password" type="password" placeholder="Mínimo 6 caracteres" class="input-styled" />
          </div>

          <div class="form-group">
            <label>ID Tarjeta (Hex)</label>
            <input v-model="cardId" type="text" placeholder="Ej: 042116E25D6580" class="input-styled input-hex" />
          </div>
        </div>

        <!-- COLUMNA CÁMARA -->
        <div class="right-col">
          <label>Captura Facial</label>
          <div class="camera-box">
            <video ref="video" autoplay playsinline muted v-show="!fotoCapturada"></video>
            <img :src="previewUrl" v-show="fotoCapturada" class="preview-img" />
            <canvas ref="canvas" style="display: none;"></canvas>
            
            <div class="camera-overlay" v-if="!fotoCapturada">
              <div class="face-guide"></div>
            </div>
          </div>
          
          <div class="camera-controls">
            <button v-if="!fotoCapturada" @click="tomarFoto" class="btn btn-capture">📷 Capturar</button>
            <button v-else @click="retomarFoto" class="btn btn-retake">🔄 Retomar</button>
          </div>
        </div>
      </div>

      <div class="actions">
        <button @click="registerFace" :disabled="loading || !fotoCapturada" class="btn-save">
          {{ loading ? 'Guardando...' : '💾 Guardar Usuario' }}
        </button>
      </div>

      <p v-if="mensaje" :class="{'msg-success': success, 'msg-error': !success}">
        {{ mensaje }}
      </p>
    </div>
  </div>
</template>

<script>
import axios from "axios"; 

export default {
  name: "Register_RFACE",
  data() {
    return {
      nombre: "", apellido: "", departamento: "", email: "", cardId: "", 
      password: "", // Variable nueva para la contraseña
      stream: null, fotoCapturada: false, previewUrl: null, fotoBlob: null,
      loading: false, mensaje: "", success: false
    };
  },
  mounted() { this.iniciarCamara(); },
  beforeUnmount() { this.detenerCamara(); },
  methods: {
    async iniciarCamara() {
      try {
        this.stream = await navigator.mediaDevices.getUserMedia({ video: true });
        this.$refs.video.srcObject = this.stream;
      } catch (err) { alert("Error cámara: " + err); }
    },
    detenerCamara() {
      if (this.stream) { this.stream.getTracks().forEach(t => t.stop()); this.stream = null; }
    },
    tomarFoto() {
      const video = this.$refs.video;
      const canvas = this.$refs.canvas;
      canvas.width = video.videoWidth; canvas.height = video.videoHeight;
      canvas.getContext('2d').drawImage(video, 0, 0);
      canvas.toBlob((blob) => {
        this.fotoBlob = blob; this.previewUrl = URL.createObjectURL(blob); this.fotoCapturada = true;
      }, 'image/jpeg', 0.95);
    },
    retomarFoto() { this.fotoCapturada = false; this.fotoBlob = null; this.previewUrl = null; },
    
    async registerFace() {
      // Validamos que existan los campos obligatorios, incluida la contraseña
      if (!this.fotoBlob || !this.nombre || !this.cardId || !this.password) {
        return alert("Por favor completa todos los campos, incluyendo la contraseña y la foto.");
      }

      this.loading = true; this.mensaje = "";
      
      const formData = new FormData();
      formData.append("nombre", this.nombre); 
      formData.append("apellido", this.apellido);
      formData.append("departamento", this.departamento); 
      formData.append("email", this.email);
      formData.append("card_id", this.cardId); 
      formData.append("password", this.password); // Enviamos la contraseña al PHP
      formData.append("foto", this.fotoBlob, "rostro.jpg");

      try {
        const apiUrl = import.meta.env.VITE_API_URL + '/registrar.php';
        const res = await axios.post(apiUrl, formData, { headers: { "Content-Type": "multipart/form-data" } });
        
        if (res.data.status === 'success') {
          this.success = true; this.mensaje = "✅ " + res.data.message;
          // Limpiar formulario
          this.nombre = ""; this.apellido = ""; this.cardId = ""; 
          this.email = ""; this.departamento = ""; this.password = "";
          this.retomarFoto();
        } else {
          this.success = false; this.mensaje = "❌ " + res.data.message;
        }
      } catch (err) { 
        this.success = false; this.mensaje = "Error de conexión"; 
      } finally { 
        this.loading = false; 
      }
    },
  },
};
</script>

<style scoped>
.face-register-container { display: flex; justify-content: center; padding: 40px; background: #f1f5f9; min-height: 90vh; }
.card { background: white; padding: 35px; border-radius: 16px; width: 100%; max-width: 900px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
h2 { margin: 0; color: #1e293b; }

.btn-back { background: transparent; border: 1px solid #cbd5e1; padding: 8px 15px; border-radius: 6px; cursor: pointer; color: #64748b; font-weight: bold; }
.btn-back:hover { background: #f1f5f9; color: #1e293b; border-color: #94a3b8; }

.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 40px; }
@media (max-width: 768px) { .form-grid { grid-template-columns: 1fr; } }
.form-group { margin-bottom: 15px; }
label { display: block; font-weight: bold; margin-bottom: 6px; color: #475569; font-size: 0.9rem; }

/* INPUTS MEJORADOS */
.input-styled { 
  width: 100%; padding: 12px; 
  background-color: #f8fafc; 
  border: 1px solid #cbd5e1; border-radius: 8px; 
  font-size: 1rem; color: #334155;
  box-sizing: border-box; transition: 0.2s;
}
.input-styled:focus { 
  border-color: #3b82f6; background-color: white; outline: none; 
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1); 
}
.input-hex { font-family: monospace; letter-spacing: 1px; }

/* CÁMARA */
.camera-box { width: 100%; height: 280px; background: #0f172a; border-radius: 10px; overflow: hidden; position: relative; border: 2px solid #cbd5e1; }
video, .preview-img { width: 100%; height: 100%; object-fit: cover; }
.face-guide { width: 160px; height: 200px; border: 2px dashed rgba(255,255,255,0.5); border-radius: 50%; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); pointer-events: none; }

.camera-controls { display: flex; gap: 10px; margin-top: 10px; }
.btn { flex: 1; padding: 10px; border-radius: 6px; border: none; font-weight: bold; color: white; cursor: pointer; }
.btn-capture { background: #3b82f6; } .btn-capture:hover { background: #2563eb; }
.btn-retake { background: #64748b; } .btn-retake:hover { background: #475569; }

.actions { margin-top: 30px; }
.btn-save { width: 100%; padding: 15px; background: #10b981; color: white; border: none; border-radius: 8px; font-weight: bold; font-size: 1.1rem; cursor: pointer; }
.btn-save:disabled { background: #94a3b8; cursor: not-allowed; }

.msg-success { color: #10b981; text-align: center; margin-top: 15px; font-weight: bold; padding: 10px; background: #dcfce7; border-radius: 8px; }
.msg-error { color: #ef4444; text-align: center; margin-top: 15px; font-weight: bold; }
</style>