// Daniela OS - Mobile-PC Bi-directional Sync Module v8.5
(function() {
    console.log('📱 [DANIELA OS]: Sincronizador Satélite Móvil Activo.');

    // Detector de dispositivo móvil
    const esMovil = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

    if (esMovil) {
        document.body.classList.add('mobile-view');
        console.log('⚡ Conectado desde dispositivo móvil. Optimizando renderizado...');
    }

    // Mantener la pantalla encendida mientras el HUD está activo (WakeLock API)
    if ('wakeLock' in navigator) {
        navigator.wakeLock.request('screen').catch(err => {});
    }
})();
