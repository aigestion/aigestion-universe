document.addEventListener('DOMContentLoaded', () => {
    const ui = {
        hudText: document.querySelector('.hud-overlay div'),
        radialHub: document.getElementById('radialHub'),
        camHub: document.getElementById('camHub'),
        pipContainer: document.getElementById('pipContainer'),
        pipVideo: document.getElementById('pipVideo'),
        btnPlus: document.getElementById('mainPlusBtn'),
        btnCam: document.getElementById('mainCamBtn'),
        btnCamFront: document.getElementById('btnCamFront'),
        btnCamBack: document.getElementById('btnCamBack'),
        btnCamClose: document.getElementById('btnCamClose'),
        pipSnap: document.getElementById('pipSnap'),
        pipClose: document.getElementById('pipClose'),
        cmdInput: document.querySelector('.cmd-input'),
        btnSend: document.getElementById('mainSendBtn'),
        canvas: document.getElementById('webglCanvas')
    };

    let activeStream = null;
    let silenceTimer = null;
    let isListening = false;
    let sentryInterval = null;

    // --- REPRODUCCIÓN DE VOZ NEURONAL ---
    function playNeuralAudio() {
        const audio = new Audio('/api/speech?t=' + new Date().getTime());
        audio.play().catch(e => console.log("Error de reproducción de audio:", e));
    }

    // --- RECONOCIMIENTO DE VOZ ---
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition = null;

    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.lang = 'es-ES';
        recognition.continuous = true;
        recognition.interimResults = true;

        let finalTranscript = '';

        recognition.onstart = () => {
            isListening = true;
            finalTranscript = '';
            if (ui.hudText) ui.hudText.textContent = "🎙️ ESCUCHANDO...";
        };

        recognition.onresult = (event) => {
            clearTimeout(silenceTimer);
            let interim = '';

            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) finalTranscript += event.results[i][0].transcript;
                else interim += event.results[i][0].transcript;
            }

            const currentText = finalTranscript || interim;
            if (ui.hudText && currentText) ui.hudText.textContent = `TÚ: ${currentText}`;

            silenceTimer = setTimeout(() => {
                if (currentText.trim().length > 0) recognition.stop();
            }, 1200);
        };

        recognition.onend = () => {
            isListening = false;
            if (finalTranscript.trim().length > 0) {
                sendToBackend({ message: finalTranscript });
            } else {
                if (ui.hudText) ui.hudText.textContent = "DANIELA OS // OPERACIONAL";
            }
        };
    }

    function triggerVoiceInput() {
        if (isListening) {
            clearTimeout(silenceTimer);
            if (recognition) recognition.stop();
            return;
        }
        if (recognition) {
            try { recognition.start(); } catch (e) {}
        }
    }

    // --- CÁMARA PIP Y CENTINELA ---
    async function startCamera(facingMode) {
        if (ui.camHub) ui.camHub.classList.remove('open');
        if (activeStream) activeStream.getTracks().forEach(track => track.stop());
        try {
            activeStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: facingMode } });
            if (ui.pipVideo) ui.pipVideo.srcObject = activeStream;
            if (ui.pipContainer) ui.pipContainer.style.display = 'block';
            if (ui.hudText) ui.hudText.textContent = `🎥 SENSORES VISUALES ACTIVOS`;
        } catch (e) {
            if (ui.hudText) ui.hudText.textContent = "⚠️ ERROR: No se puede acceder a la cámara.";
        }
    }

    function captureSentryFrame() {
        if (!ui.pipVideo || ui.pipContainer.style.display === 'none') return;
        const canvas = document.createElement('canvas');
        canvas.width = ui.pipVideo.videoWidth || 640;
        canvas.height = ui.pipVideo.videoHeight || 480;
        canvas.getContext('2d').drawImage(ui.pipVideo, 0, 0, canvas.width, canvas.height);
        
        sendToBackend({ message: "Vigilancia activa.", image: canvas.toDataURL('image/jpeg'), sentry: true });
    }

    // --- ENVIAR AL BACKEND ---
    async function sendToBackend(payload) {
        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            
            if (payload.sentry && data.response === "") return;

            const textToDisplay = data.response.replace(/\[ALERTA\]/g, '').replace(/\[STATE:.*?\]/g, '');
            if (ui.hudText && textToDisplay.trim()) {
                ui.hudText.textContent = `DANIELA: ${textToDisplay}`;
            }

            if (data.audio) {
                playNeuralAudio();
            }
        } catch (e) {
            if (ui.hudText) ui.hudText.textContent = "⚠️ ERROR DE SERVIDOR";
        }
    }

    // --- VINCULACIÓN DE EVENTOS ---
    if (ui.btnPlus) ui.btnPlus.onclick = () => { if (ui.radialHub) ui.radialHub.classList.toggle('open'); };
    if (ui.btnCam) ui.btnCam.onclick = () => { if (ui.camHub) ui.camHub.classList.toggle('open'); };
    if (ui.btnCamFront) ui.btnCamFront.onclick = () => startCamera('user');
    if (ui.btnCamBack) ui.btnCamBack.onclick = () => startCamera('environment');
    if (ui.btnCamClose) ui.btnCamClose.onclick = () => { if (ui.camHub) ui.camHub.classList.remove('open'); };

    if (ui.pipClose) ui.pipClose.onclick = () => {
        if (sentryInterval) { clearInterval(sentryInterval); sentryInterval = null; }
        if (activeStream) activeStream.getTracks().forEach(track => track.stop());
        if (ui.pipContainer) ui.pipContainer.style.display = 'none';
        if (ui.hudText) ui.hudText.textContent = "DANIELA OS // OPERACIONAL";
    };

    if (ui.btnSend) {
        ui.btnSend.onclick = () => {
            if (!ui.cmdInput) return;
            const txt = ui.cmdInput.value.trim();
            if (!txt) return;
            ui.cmdInput.value = '';
            sendToBackend({ message: txt });
        };
    }

    if (ui.cmdInput) {
        ui.cmdInput.onkeypress = (e) => {
            if (e.key === 'Enter' && ui.btnSend) ui.btnSend.click();
        };
    }

    if (ui.camHub && !document.getElementById('sentryBtn')) {
        const btn = document.createElement('button');
        btn.id = 'sentryBtn'; 
        btn.innerHTML = '👁️ CENTINELA (OFF)'; 
        btn.style = 'background: #300; width: 100%; border: 1px solid #f00; padding: 10px; color: #fff; margin-top: 10px; border-radius: 8px;';
        btn.onclick = () => {
            if (sentryInterval) { 
                clearInterval(sentryInterval); 
                sentryInterval = null; 
                btn.innerHTML = '👁️ CENTINELA (OFF)';
                btn.style.background = '#300'; 
            } else { 
                sentryInterval = setInterval(captureSentryFrame, 10000); 
                btn.innerHTML = '👁️ CENTINELA (ON)';
                btn.style.background = '#030'; 
            }
        };
        ui.camHub.appendChild(btn);
    }

    if (ui.canvas) ui.canvas.addEventListener('click', triggerVoiceInput);
});
