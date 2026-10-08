// Daniela OS - Mobile Haptic Feedback & Gesture Module v9.0
(function() {
    console.log("📱 [DANIELA OS]: Módulo Háptico Móvil Cargado.");

    window.vibrarTelefono = function(patron) {
        if ("vibrate" in navigator) {
            if (patron === "alerta") {
                navigator.vibrate([100, 50, 100, 50, 200]);
            } else if (patron === "confirmacion") {
                navigator.vibrate([50, 30, 50]);
            } else if (patron === "sintonizacion") {
                navigator.vibrate(40);
            }
        }
    };

    const oldPlaySound = window.playUISound;
    window.playUISound = function(tipo) {
        if (oldPlaySound) oldPlaySound(tipo);
        if (tipo === "activar") window.vibrarTelefono("sintonizacion");
        if (tipo === "reposo") window.vibrarTelefono("confirmacion");
    };
})();
