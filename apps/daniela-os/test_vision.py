import os

from verificar_rostro import verificar_usuario

print("--- INICIANDO ESCANEO DE PRUEBA ---")
# Verificamos si existe el archivo de referencia (el rostro guardado)
if not os.path.exists("rostro_referencia.npy"):
    print("❌ ERROR CRÍTICO: No existe archivo 'rostro_referencia.npy'.")
    print("¡Daniela no sabe qué cara buscar! Debes ejecutar el script de registro primero.")
else:
    print("✅ Archivo de referencia encontrado. Iniciando cámara...")
    resultado = verificar_usuario()
    print(f"Resultado de la identificación: {resultado}")
