import { initGEVIntegration } from './gev.js';
import { initSensors } from './sensors.js';
import { initNotifications, showDanielaNotification } from './notifications.js';

class App {
  constructor() {
    this.views = {};
    this.currentView = null;
    this.refreshInterval = null;
    this.deferredPrompt = null;
    this.container = document.getElementById('view-content');
    this.nav = document.getElementById('bottom-nav');
    this.offlineBanner = document.getElementById('offline-banner');
    this.installPrompt = document.getElementById('install-prompt');

    this.init();
  }

  init() {
    this.registerSW();
    this.setupRouter();
    this.setupNav();
    this.setupPullToRefresh();
    this.setupOfflineDetection();
    this.setupInstallPrompt();
    this.setupPushNotifications();
    
    // Inicializar integración con GEV, sensores y notificaciones
    this.setupGEVIntegration();
    this.setupSensors();
    this.setupDanielaNotifications();
    
    this.navigate(this.getHash() || 'home');
  }

  setupGEVIntegration() {
    try {
      initGEVIntegration();
      console.log('[App] Integración GEV inicializada');
    } catch (error) {
      console.error('[App] Error inicializando GEV:', error);
    }
  }

  setupSensors() {
    try {
      initSensors();
      console.log('[App] Sensores inicializados');
    } catch (error) {
      console.error('[App] Error inicializando sensores:', error);
    }
  }

  setupDanielaNotifications() {
    try {
      initNotifications();
      console.log('[App] Notificaciones de Daniela inicializadas');
    } catch (error) {
      console.error('[App] Error inicializando notificaciones:', error);
    }
  }

  registerSW() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').then((reg) => {
        console.log('SW registered:', reg.scope);
        reg.addEventListener('updatefound', () => {
          console.log('SW update found');
        });
      }).catch((err) => {
        console.error('SW registration failed:', err);
      });
    }
  }

  setupRouter() {
    window.addEventListener('hashchange', () => {
      this.navigate(this.getHash());
    });
  }

  getHash() {
    return window.location.hash.replace('#', '').replace('/', '') || 'home';
  }

  setupNav() {
    this.nav.querySelectorAll('.nav-item').forEach((btn) => {
      btn.addEventListener('click', () => {
        const view = btn.dataset.view;
        window.location.hash = view;
      });
    });
  }

  setupPullToRefresh() {
    let startY = 0;
    let pulling = false;
    const container = document.querySelector('.view-container');
    const indicator = document.getElementById('pull-indicator');

    container.addEventListener('touchstart', (e) => {
      if (container.scrollTop === 0) {
        startY = e.touches[0].clientY;
        pulling = true;
      }
    }, { passive: true });

    container.addEventListener('touchmove', (e) => {
      if (!pulling) return;
      const diff = e.touches[0].clientY - startY;
      if (diff > 60) {
        indicator.classList.add('visible');
      }
    }, { passive: true });

    container.addEventListener('touchend', async () => {
      if (indicator.classList.contains('visible')) {
        await this.refreshCurrentView();
        indicator.classList.remove('visible');
      }
      pulling = false;
    });
  }

  setupOfflineDetection() {
    const updateStatus = () => {
      this.offlineBanner.classList.toggle('hidden', navigator.onLine);
    };
    window.addEventListener('online', updateStatus);
    window.addEventListener('offline', updateStatus);
    updateStatus();
  }

  setupInstallPrompt() {
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      this.deferredPrompt = e;
      window.deferredPrompt = e;
      this.installPrompt.classList.remove('hidden');
    });

    document.getElementById('install-accept')?.addEventListener('click', async () => {
      if (this.deferredPrompt) {
        this.deferredPrompt.prompt();
        const result = await this.deferredPrompt.userChoice;
        console.log('Install:', result.outcome);
        this.deferredPrompt = null;
        this.installPrompt.classList.add('hidden');
      }
    });

    document.getElementById('install-dismiss')?.addEventListener('click', () => {
      this.installPrompt.classList.add('hidden');
    });

    window.addEventListener('appinstalled', () => {
      this.installPrompt.classList.add('hidden');
    });
  }

  async setupPushNotifications() {
    if (!('Notification' in window) || !('serviceWorker' in navigator)) return;

    try {
      const permission = await Notification.requestPermission();
      if (permission === 'granted') {
        const reg = await navigator.serviceWorker.ready;
        const sub = await reg.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: this.urlBase64ToUint8Array(
            'BEl62iUYcUvxYVxk6A6lZ4KEORmrOsRxvyfPIhNLOlhAP9c8ZiFjUYdUnS8Tc4P8nD6nQ6cK2fQ'
          ),
        });
        console.log('Push subscription:', sub);
      }
    } catch (err) {
      console.log('Push notifications not available:', err);
    }
  }

  urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const raw = window.atob(base64);
    return Uint8Array.from([...raw].map((c) => c.charCodeAt(0)));
  }

  navigate(viewName) {
    const [mainView, ...sub] = viewName.split('/');
    this.updateNav(mainView);
    this.clearAutoRefresh();

    switch (mainView) {
      case 'home':
        this.renderView(new HomeView(this.container));
        break;
      case 'daniela':
        this.renderView(new DanielaView(this.container));
        break;
      case 'gev':
        // God's Eye: una PANTALLA de Daniela, no un modulo aparte.
        this.renderView(new GevView(this.container));
        break;
      case 'hermes':
        this.renderView(new HermesView(this.container));
        break;
      case 'engines':
        this.renderView(new EnginesView(this.container));
        break;
      case 'gateway':
        this.renderView(new GatewayView(this.container));
        break;
      case 'settings':
        this.renderView(new SettingsView(this.container));
        break;
      default:
        this.renderView(new HomeView(this.container));
    }
  }

  async renderView(view) {
    // Libera el renderer WebGL y los listeners de la vista anterior. Las vistas
    // que no definan destroy() siguen funcionando igual que antes.
    this.currentView?.destroy?.();
    this.currentView = view;
    await view.render();
    this.startAutoRefresh();
  }

  updateNav(viewName) {
    this.nav.querySelectorAll('.nav-item').forEach((btn) => {
      btn.classList.toggle('active', btn.dataset.view === viewName);
    });
  }

  startAutoRefresh() {
    this.clearAutoRefresh();
    this.refreshInterval = setInterval(() => {
      if (this.currentView && navigator.onLine) {
        this.currentView.loadData?.();
      }
    }, 30000);
  }

  clearAutoRefresh() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
      this.refreshInterval = null;
    }
  }

  async refreshCurrentView() {
    if (this.currentView) {
      await this.currentView.loadData?.();
    }
  }
}

const app = new App();
window.app = app;
