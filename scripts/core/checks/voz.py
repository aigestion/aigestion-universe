import random

from safe_exec import run_code

FRASES = [
    "¡Ole Alejandro! ¿Qué pasa mi arma? ¿Hablamos un ratito de negocios o qué?",
    "¡Buenas Comandante! Qué arte tienes. ¿Nos ponemos al lío?",
    "¡Ay qué alegría, Alejandro! Dime qué hacemos hoy con las cosas del negocio.",
    "¡Hola mi jefe! Todo despejaíto por aquí. ¿Le damos una vuelta a los temas?"
]

def probar_voz():
    texto = random.choice(FRASES)
    print(f"🗣️ Pronunciando con voz de España: {texto}")
    # Forzamos locale es_ES (España) y velocidad natural
    run_code(f'termux-tts-speak -l es_ES -r 1.1 -p 1.05 "{texto}"')

if __name__ == "__main__":
    probar_voz()
