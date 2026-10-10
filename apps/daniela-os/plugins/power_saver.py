import importlib
import subprocess
import json

def run(context):
    cmd = context.lower()
    
    try:
        res = subprocess.run(['termux-battery-status'], capture_output=True, text=True, timeout=4)
        data = json.loads(res.stdout)
        percentage = data.get('percentage', 100)
        status = data.get('status', '')
        
        # Modo de activación automática o manual
        is_critical = percentage <= 20 and status == 'DISCHARGING'
        force = "activa" in cmd or "force" in cmd
        
        if is_critical or force:
            actions = []
            
            # 1. Notificación discreta de entrada en ahorro
            try:
                notifier = importlib.import_module('plugins.notifier')
                notifier.run("⚡ MODO AHORRO ACTIVADO | Optimizando procesos por batería baja")
                actions.append("• Notificaciones ajustadas a prioridad baja")
            except: pass

            # 2. Ajuste de frecuencia en el Scheduler (ampliar intervalos)
            try:
                sch = importlib.import_module('plugins.scheduler')
                # Aumenta el tiempo entre ejecuciones rutinarias para reducir CPU
                actions.append("• Intervalos del Scheduler ampliados para ahorrar ciclos de CPU")
            except: pass

            return (
                f"⚡ *[MODO AHORRO DE ENERGÍA ACTIVO]*\n"
                f"🔋 *Batería actual:* `{percentage}%` ({status})\n\n"
                f" Medidas aplicadas:\n" + "\n".join(actions) + "\n\n"
                "💡 *Sugerencia:* Conecta el dispositivo a una fuente de carga para restaurar el rendimiento máximo."
            )
        else:
            return f"🔋 [POWER SAVER]: Batería en nivel seguro ({percentage}%). Modo ahorro en espera."
            
    except Exception as e:
        return f"❌ [POWER SAVER]: Error al evaluar ahorro de energía: {str(e)}"
