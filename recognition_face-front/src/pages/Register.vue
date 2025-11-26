<template>
 
  <div class="login-container step1" v-if="step === 1" style="margin-top: 10rem;">
    <p class="text-container">Recognition Face</p>
    <form @submit.prevent="nextStep">
      <input
        v-model="user.nombre"
        type="text"
        placeholder="Nombre completo"
        required
      />
      <input
        v-model="user.correo"
        type="email"
        placeholder="correo electronico"
        required
      />
      <!-- <input
        v-model="rfid"
        type="text"
        placeholder="ID de tarjeta RFID"
        required
      /> -->
      <input
        v-model="user.password"
        type="password"
        placeholder="Contraseña"
        required
      />

      <button type="submit">Continuar</button>
    </form>
    <p class="register-link">
      <router-link to="/">Volver al inicio</router-link>
    </p>
  </div>

  <div class="step2" v-else-if="step === 2">
    <h3>Registro Facial</h3>
    <div class="container-RF">
    <video ref="video" autoplay playsinline class="video-RF"></video>
      <div class="scan-frame">
        <div class="scan-line"></div>
      </div>
    </div>
    <button @click="captureFace">Capturar rostro</button>
  </div>

  <div class="step3" v-else-if="step === 3">
    <h2>Registro RFID</h2>
    <p>Acerque su tarjeta RFID al lector</p>
    <button @click="registerRFID">Registrar RFID</button>
  </div>

  <div v-else>
    <h2>Registro completado</h2>
    <router-link to="/">Ir al login</router-link>
  </div>

</template>

<script>
import API from "../services/api.js";

export default {
  data() {
    return {
      step: 1,
      user: { nombre: "", correo: "", password: "", id: null },
      faceImage: null,
      rfid: null,
    };
  },
  methods: {
    async nextStep() {
      try{
      //const res = await API.post("/usuarios/register", this.user);
      //this.user.id = res.data.id; // Guardamos id generado
      console.log("Entrando al paso 2");
      this.step = 2;
      this.startCamera();
      }catch(err){
        console.error("Error al registrar usuario:", err);
        alert("Error al registrar usuario");
      }
    },
    startCamera() {
      navigator.mediaDevices.getUserMedia({ video: true }).then((stream) => {
        this.$refs.video.srcObject = stream;
      });
    },
    captureFace() {
      try{
      const video = this.$refs.video;
      const canvas = document.createElement("canvas");
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      canvas.getContext("2d").drawImage(video, 0, 0);
      this.faceImage = canvas.toDataURL("image/png");
     }catch(e){

     }
      // Enviar al backend
      //const formData = new FormData();
      formData.append("faceImage", this.dataURLtoFile(this.faceImage, "face.png"));
      formData.append("userId", this.user.id);

      API.post("/face/register", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      }).then(() => {
        this.step = 3;
        // Aquí podría mostrar instrucciones para RFID
      });
    },
    dataURLtoFile(dataurl, filename) {
      let arr = dataurl.split(","), mime = arr[0].match(/:(.*?);/)[1],
          bstr = atob(arr[1]), n = bstr.length, u8arr = new Uint8Array(n);
      while(n--){
          u8arr[n] = bstr.charCodeAt(n);
      }
      return new File([u8arr], filename, {type:mime});
    },
    registerRFID() {
      // Ejemplo: pedir al backend que lea RFID
      API.post("/rfid/register", { userId: this.user.id }).then(() => {
        this.step = 4; // Registro completo
      });
    }
  }
};
</script>
