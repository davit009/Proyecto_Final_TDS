import { createRouter, createWebHistory } from 'vue-router';

// Importamos tus componentes
import Login from './pages/Login.vue';
import Dashboard from './pages/Dashboard.vue';
// IMPORTANTE: Aquí importamos el archivo corregido con cámara
import RegisterRFACE from './pages/Register_RFACE.vue'; 

const routes = [
  // Ruta por defecto (Login)
  { path: '/', component: Login },
  
  // CORRECCIÓN CRÍTICA:
  // Hacemos que la ruta '/register' use el archivo BUENO (Register_RFACE)
  // Así reemplazamos el archivo viejo sin romper los enlaces del menú
  { path: '/register', component: RegisterRFACE },
  
  // Dashboard
  { path: '/dashboard', component: Dashboard },
  
  // (Opcional) Dejamos esta ruta alternativa por si acaso
  { path: '/register_rface', component: RegisterRFACE },
];

export const router = createRouter({
  // Asegúrate que esta base coincida con tu carpeta en XAMPP
  history: createWebHistory('/proyecto_acceso/'),
  routes,
});