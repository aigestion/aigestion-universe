// --- SUITE DE PRUEBAS UNITARIAS DE UI PARA DANIELA OS ---
console.log("=== INICIANDO TEST SUITE ===");

function assert(condition, message) {
    if (!condition) {
        console.error("❌ FALLO: " + message);
        if(typeof log === 'function') log('TEST_FAIL', message);
    } else {
        console.log("✅ PASÓ: " + message);
        if(typeof log === 'function') log('TEST_PASS', message);
    }
}

// Esperar a que la UI cargue
setTimeout(() => {
    // Test 1: Estado Inicial
    assert(document.getElementById('webglCanvas').style.display !== 'none', "Canvas 3D visible al inicio");
    assert(mat.color.getHex() === 0xf59e0b, "Esfera color ámbar inicial");

    // Test 2: Funcionalidad de Tabs
    document.getElementById('tabLogs').click();
    assert(document.getElementById('consoleLogView').style.display === 'block', "Tab LOGS muestra la terminal");
    assert(document.getElementById('webglCanvas').style.display === 'none', "Tab LOGS oculta el 3D");
    
    document.getElementById('tab3D').click();
    assert(document.getElementById('webglCanvas').style.display !== 'none', "Regreso a Tab 3D correcto");

    // Test 3: Menú Plus (+)
    document.getElementById('btnPlus').click();
    assert(document.getElementById('plusHub').classList.contains('open'), "Menú Plus abre correctamente");
    assert(mat.color.getHex() === 0xf59e0b, "Esfera ámbar en menú Plus");
    
    document.getElementById('nodeTelemetry').click();
    assert(!document.getElementById('plusHub').classList.contains('open'), "Nodo Telemetría cierra el menú");
    assert(document.getElementById('hudText').textContent.includes("TELEMETRÍA"), "Nodo Telemetría actualiza HUD");

    // Test 4: Menú Cámara (📸)
    document.getElementById('btnCam').click();
    assert(document.getElementById('cameraHub').classList.contains('open'), "Menú Cámara abre correctamente");
    assert(mat.color.getHex() === 0xa855f7, "Esfera púrpura en menú Cámara");
    
    document.getElementById('btnCam').click(); // Cerrar
    assert(!document.getElementById('cameraHub').classList.contains('open'), "Menú Cámara cierra correctamente");

    // Test 5: Micrófono (🎤)
    document.getElementById('btnMic').click();
    assert(document.getElementById('btnMic').classList.contains('active'), "Micrófono se activa");
    assert(mat.color.getHex() === 0x22c55e, "Esfera verde con micrófono");
    document.getElementById('btnMic').click(); // Desactivar

    // Test 6: Entrada de Comando (➤)
    const input = document.getElementById('cmdInput');
    input.value = "Test Comando Soberano";
    document.getElementById('btnSend').click();
    assert(input.value === "", "Campo de entrada se limpia tras envío");
    assert(document.getElementById('hudText').textContent.includes("PROCESANDO"), "HUD confirma procesamiento");

    console.log("=== TEST SUITE FINALIZADA ===");
    if(typeof log === 'function') log('SYS', 'Suite de pruebas completada. Revisa LOGS para detalles.');
}, 2000);
