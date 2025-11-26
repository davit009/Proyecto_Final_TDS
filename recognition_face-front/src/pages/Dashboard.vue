<template>
  <div class="dashboard">
    <header class="header">
      <div class="title-section">
        <h1>🏢 Panel de Control</h1>
        <p class="subtitle">
          Bienvenido, {{ nombreUsuario }} 
          <span class="rol-tag" :class="esAdmin ? 'tag-admin' : 'tag-user'">
            {{ rolUsuario.toUpperCase() }}
          </span>
        </p>
      </div>
      <button class="logout-btn" @click="cerrarSesion">Cerrar Sesión</button>
    </header>

    <main class="main">
      <!-- TARJETAS DE RESUMEN (SOLO VISIBLES PARA ADMIN) -->
      <section v-if="esAdmin" class="summary">
        <div class="summary-card acceso">
          <h2>{{ accesos.length }}</h2>
          <p>Registros Totales</p>
        </div>
        <div class="summary-card permitidos">
          <h2>{{ permitidos }}</h2>
          <p>Accesos Correctos</p>
        </div>
        <div class="summary-card denegados">
          <h2>{{ denegados }}</h2>
          <p>Intentos Fallidos</p>
        </div>
      </section>

      <!-- TABLA DE HISTORIAL (SE ADAPTA AL ROL) -->
      <section class="table-section">
        <div class="table-header">
          <h2>
            {{ esAdmin ? '📋 Historial Global de Accesos' : '📅 Mi Historial de Asistencia' }}
          </h2>
          <!-- Botón de Nuevo Usuario (SOLO PARA ADMIN) -->
          <button v-if="esAdmin" @click="$router.push('/register')" class="btn-new">
            + Nuevo Usuario
          </button>
        </div>
        
        <div class="table-responsive">
          <table class="access-table">
            <thead>
              <tr>
                <th>Fecha y Hora</th>
                <!-- La columna Usuario solo la ve el Admin -->
                <th v-if="esAdmin">Usuario</th>
                <th>Estado</th>
                <th>Detalles</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="log in accesos" :key="log.id">
                <td>{{ log.fecha }}</td>
                <td v-if="esAdmin" style="font-weight:bold; color:#334155;">
                  {{ log.usuario }}
                </td>
                <td>
                  <span :class="['badge', log.tipo_evento === 'acceso' ? 'ok' : 'denied']">
                    {{ log.tipo_evento === 'acceso' ? 'PERMITIDO' : 'DENEGADO' }}
                  </span>
                </td>
                <td>{{ log.motivo || log.departamento }}</td>
              </tr>
              <tr v-if="accesos.length === 0">
                <td :colspan="esAdmin ? 4 : 3" class="empty-msg">
                  No hay registros recientes para mostrar.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </main>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "Dashboard",
  data() {
    return {
      accesos: [],
      nombreUsuario: localStorage.getItem('user_name') || 'Usuario',
      rolUsuario: localStorage.getItem('user_role') || 'user',
      userId: localStorage.getItem('user_id') || 0,
      timer: null
    };
  },
  computed: {
    esAdmin() { return this.rolUsuario === 'admin'; },
    permitidos() { return this.accesos.filter(a => a.tipo_evento === 'acceso').length; },
    denegados() { return this.accesos.filter(a => a.tipo_evento !== 'acceso').length; }
  },
  mounted() {
    this.cargarHistorial();
    // Refrescar automáticamente cada 5 segundos
    this.timer = setInterval(this.cargarHistorial, 5000);
  },
  beforeUnmount() { 
    clearInterval(this.timer); 
  },
  methods: {
    async cargarHistorial() {
      try {
        const url = import.meta.env.VITE_API_URL + '/get_history.php';
        // Enviamos rol e ID para que el PHP sepa qué devolver
        const res = await axios.get(url, {
          params: { rol: this.rolUsuario, user_id: this.userId }
        });
        this.accesos = res.data;
      } catch (e) { 
        console.error("Error cargando historial:", e); 
      }
    },
    cerrarSesion() {
      localStorage.clear();
      this.$router.push('/');
    }
  }
};
</script>

<style scoped>
.dashboard { min-height: 100vh; background: #f8fafc; font-family: 'Segoe UI', sans-serif; }
.header { background: #1e293b; color: white; padding: 20px 40px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
.title-section h1 { margin: 0; font-size: 1.5rem; }
.subtitle { font-size: 0.9rem; color: #cbd5e1; margin-top: 5px; }

.rol-tag { padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: bold; margin-left: 8px; text-transform: uppercase; }
.tag-admin { background: #3b82f6; color: white; }
.tag-user { background: #64748b; color: white; }

.logout-btn { background: #ef4444; border: none; color: white; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; transition: 0.2s; }
.logout-btn:hover { background: #dc2626; }

.main { padding: 40px; max-width: 1200px; margin: 0 auto; }

/* Tarjetas */
.summary { display: flex; gap: 20px; margin-bottom: 30px; flex-wrap: wrap; }
.summary-card { background: white; padding: 25px; border-radius: 12px; flex: 1; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05); min-width: 200px; }
.summary-card h2 { font-size: 2.5rem; margin: 10px 0; color: #0f172a; }
.summary-card p { color: #64748b; font-weight: 500; }
.acceso { border-top: 5px solid #3b82f6; } 
.permitidos { border-top: 5px solid #10b981; } 
.denegados { border-top: 5px solid #ef4444; }

/* Tabla */
.table-section { background: white; border-radius: 16px; padding: 30px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
.table-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; }
.table-header h2 { color: #1e293b; margin: 0; font-size: 1.3rem; }
.btn-new { background: #3b82f6; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-weight: bold; }
.btn-new:hover { background: #2563eb; }

.table-responsive { overflow-x: auto; }
.access-table { width: 100%; border-collapse: collapse; }
.access-table th { text-align: left; padding: 15px; border-bottom: 2px solid #e2e8f0; color: #64748b; text-transform: uppercase; font-size: 0.85rem; font-weight: 700; }
.access-table td { padding: 15px; border-bottom: 1px solid #f1f5f9; color: #475569; }
.badge { padding: 6px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: bold; }
.ok { background: #dcfce7; color: #166534; } 
.denied { background: #fee2e2; color: #991b1b; }
.empty-msg { text-align: center; padding: 30px; color: #94a3b8; font-style: italic; }

@media (max-width: 768px) {
  .header { flex-direction: column; text-align: center; gap: 15px; }
  .summary { flex-direction: column; }
  .table-header { flex-direction: column; gap: 15px; align-items: stretch; }
  .btn-new { width: 100%; }
}
</style>