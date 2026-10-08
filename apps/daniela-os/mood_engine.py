import json
import os
import time

MOOD_FILE = os.path.expanduser("~/daniela-os/mood.json")


def get_mood():
    hour = int(time.strftime("%H"))
    if 6 <= hour < 12:
        return {
            "estado": "enérgica",
            "saludo": "¡Buenos días, Comandante! Qué ganas tenía de empezar el día.",
        }
    elif 12 <= hour < 18:
        return {"estado": "trabajadora", "saludo": "Aquí seguimos, al pie del cañón, Alejandro."}
    else:
        return {"estado": "cansada", "saludo": "La noche está tranquila... ¿descansamos ya?"}


def save_mood(mood):
    with open(MOOD_FILE, "w") as f:
        json.dump(mood, f)


if __name__ == "__main__":
    mood = get_mood()
    save_mood(mood)
    print(f"💃 Daniela ha cambiado su estado a: {mood['estado']}")
