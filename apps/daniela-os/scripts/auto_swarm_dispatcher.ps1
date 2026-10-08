# =================================================================
# DESPACHADOR CONTINUO DE TAREAS ALEATORIAS - DANIELA-OS v6.4
# =================================================================

$flaskUri = "http://192.168.1.133:5059/api/swarm/dispatch"

# Pool de instrucciones espaciales para el entorno 3D
$tasksPool = @(
    @{ agent = "orchestrator"; task = "Activar cúpula de contención de emergencia y modo visión Cyberpunk" },
    @{ agent = "rag_analyst"; task = "Sincronizar estructura de carpetas del monorepo con rag_analyst" },
    @{ agent = "vault_keeper"; task = "Verificar integridad de la Bóveda de Datos en daniela_vault.db" },
    @{ agent = "canary_guard"; task = "Ejecutar protocolo de aislamiento en la cámara de cristal" },
    @{ agent = "orchestrator"; task = "Iniciar simulación de clima de datos intensivo" },
    @{ agent = "orchestrator"; task = "Restaurar parámetros de iluminación a modo normal" }
)

Write-Host "[INICIANDO] Despachador Automatico de Swarm (Ctrl + C para detener)..." -ForegroundColor Cyan

while ($true) {
    # Seleccionar una tarea aleatoria del pool
    $selected = $tasksPool | Get-Random
    
    $body = @{
        agent_id = $selected.agent
        task     = $selected.task
    } | ConvertTo-Json -Depth 3

    try {
        $timestamp = Get-Date -Format "HH:mm:ss"
        Invoke-RestMethod -Uri $flaskUri -Method Post -Body $body -ContentType "application/json" -TimeoutSec 5 | Out-Null
        
        Write-Host "[$timestamp] [OK] DISPARO ENVIADO -> Agente: [$($selected.agent)] | Tarea: '$($selected.task)'" -ForegroundColor Green
    }
    catch {
        Write-Host "[ERROR] Error al conectar con Termux Flask Backend: $_" -ForegroundColor Red
    }

    # Esperar un intervalo aleatorio entre 6 y 12 segundos
    $waitTime = Get-Random -Minimum 6 -Maximum 12
    Write-Host "[ESPERA] Esperando $waitTime segundos para el siguiente disparo..." -ForegroundColor DarkGray
    Start-Sleep -Seconds $waitTime
}
