<template>
  <div class="login-container">
    <div class="login-card">
      <div class="icon-header">
        🔐
      </div>
      <h2>Control de Acceso</h2>
      <p class="subtitle">Ingresa tus credenciales</p>

      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label>Usuario o Email</label>
          <input v-model="usuario" type="text" placeholder="Ej: David" class="input-gray" required />
        </div>

        <div class="form-group">
          <label>Contraseña</label>
          <input v-model="password" type="password" placeholder="••••••" class="input-gray" required />
        </div>

        <button type="submit" class="btn-login" :disabled="loading">
          {{ loading ? 'Verificando...' : 'Iniciar Sesión' }}
        </button>
      </form>

      <p v-if="error" class="error-msg">{{ error }}</p>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "Login",
  data() {
    return {
      usuario: "",
      password: "",
      loading: false,
      error: ""
    };
  },
  methods: {
    async handleLogin() {
      this.loading = true;
      this.error = "";

      try {
        const apiUrl = import.meta.env.VITE_API_URL + '/login.php';
        const res = await axios.post(apiUrl, {
          usuario: this.usuario,
          password: this.password
        });

        if (res.data.status === 'success') {
          // Guardamos TODO lo importante en el navegador
          localStorage.setItem('user_role', res.data.rol);
          localStorage.setItem('user_id', res.data.user_id);
          localStorage.setItem('user_name', res.data.nombre);
          
          // ¡Vámonos al Dashboard!
          this.$router.push('/dashboard');
        } else {
          this.error = res.data.message;
        }
      } catch (err) {
        console.error(err);
        this.error = "No se pudo conectar con el servidor";
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>

<style scoped>
.login-container {
  display: flex; justify-content: center; align-items: center;
  height: 100vh; background: #0f172a;
}
.login-card {
  background: white; padding: 40px; border-radius: 20px;
  width: 100%; max-width: 380px; text-align: center;
  box-shadow: 0 10px 25px rgba(0,0,0,0.3);
}
.icon-header { font-size: 3rem; margin-bottom: 15px; }
h2 { color: #1e293b; margin: 0; font-size: 1.8rem; }
.subtitle { color: #64748b; margin-bottom: 30px; font-size: 0.9rem; }
.form-group { text-align: left; margin-bottom: 20px; }
label { display: block; font-size: 0.9rem; font-weight: bold; color: #334155; margin-bottom: 8px; }

/* ESTILO GRIS PARA QUE NO SE VEA BLANCO SOBRE BLANCO */
.input-gray {
  width: 100%; padding: 12px; 
  background-color: #f1f5f9; 
  border: 1px solid #cbd5e1; 
  border-radius: 8px;
  box-sizing: border-box; transition: 0.3s;
  font-size: 1rem; color: #334155;
}
.input-gray:focus { border-color: #3b82f6; background-color: white; outline: none; }

.btn-login {
  width: 100%; padding: 14px; background: #3b82f6; color: white;
  border: none; border-radius: 8px; font-weight: bold; font-size: 1rem;
  cursor: pointer; transition: 0.3s;
}
.btn-login:hover { background: #2563eb; }
.btn-login:disabled { background: #94a3b8; }
.error-msg { color: #ef4444; margin-top: 15px; font-weight: bold; font-size: 0.9rem; }
</style>